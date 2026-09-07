# Technical Spec: ServiceNow Sync

**Status:** Draft, Brookfield facts pending (Vini, due 2026-09-25)
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Data Migration & Cutover](../data-migration/TECHNICAL-SPEC.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md)
**Requirements covered:** SN-01 to SN-09
**Repos affected:** `backend/src/worker`, `backend`, `frontend`, `backend/src/domain`, `backend/src/db`, `infra`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Connector framework: outbox, dispatcher, inbox, apply, dead letters, kill switch, configuration as data, chaos and loop tests | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) §2 to §6; tables `sys.outbox`, `sys.inbox`, `sys.dead_letters` | This module is one connector type on it; nothing below re-implements delivery or retry |
| Ticket service (single writer; `origin` on every change; `external_ref`) | [Ticket Management technical spec](../ticket-management/TECHNICAL-SPEC.md) §3; ADR-10 | Apply calls it with origin `sync:<instance id>`; the service writes audit and outbox rows and never dispatches an outbox row back to its own origin |
| AIX degradation contract (`skipped[]` instead of failing the run) | `app-api/src/api/v3/mcp/internal-mcp.service.ts` (verified 2026-09-04) | Health semantics: one failing instance never affects another |
| AIX OAuth refresh: mark credential invalid on failure, never retry blindly | `app-api/src/api/v3/mcp/oauth-refresh.service.ts` (`RefreshResult` union) | Token refresh handling for OAuth instances |
| AIX read-side ServiceNow MCP | `aix-mcp/app/modules/servicenow_ams_mcp/` (source on another branch; `snow_client.py` named in the research report, internals not read) | Starting point for the Table API client shape only; no sync logic exists there |
| Constant-time secret guard, fail closed when unconfigured | `app-api/src/guards/require-internal-secret.guard.ts` | Webhook HMAC verification in the worker |
| Postgres row claiming for pollers | studio `app/modules/agent_harness/scheduler/routine_engine.py` | Poll scheduling per instance with `SKIP LOCKED` |
| Secrets Manager references, never secrets in rows | [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md) §2.3, [Platform & Operations](../../01-architecture/PLATFORM-AND-OPERATIONS.md) §4 | `credential_secret_name` on the instance |
| Screen grammar for lists and records | `web-ui/components/aix-v3/xms/QueueTab.tsx`, `TicketDrawer.tsx`, `XmsAdminPages.tsx` | Instance record, health list, runs and dead-letter lists |

Cross-container ordering: `infra` (FIFO queue `connector.servicenow.fifo` and DLQ, webhook ALB path) -> `backend/src/db` -> `backend/src/domain` (maps, translation, reflection rule) -> `backend/src/worker` -> `backend` -> `frontend`.

## 2. Data model

All tables in schema `acct` with `account_id` and RLS. Mutable rows carry `version`.

### 2.1 `acct.connector_instances`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid NOT NULL | RLS |
| `type` | text NOT NULL | CHECK IN (`servicenow`, `finance_export`, `calendar`, ...) from `op.connector_types` |
| `name` | text NOT NULL | Unique per account |
| `base_url` | text NOT NULL | `https://<instance>.service-now.com` |
| `auth_kind` | text NOT NULL | CHECK IN (`oauth_client_credentials`, `basic`) |
| `credential_secret_name` | text NOT NULL | Secrets Manager name; never the secret |
| `credential_state` | text NOT NULL default `unknown` | CHECK IN (`unknown`, `valid`, `invalid`) |
| `table_name` | text NOT NULL | `sn_customerservice_case`, `incident`, or custom |
| `mode` | text NOT NULL default `off` | CHECK IN (`off`, `ingest_only`, `bidirectional`) |
| `kill_switch` | text NOT NULL default `armed` | CHECK IN (`armed`, `tripped`) |
| `trip_reason` / `tripped_at` / `tripped_by` | text / timestamptz / text | |
| `poll_interval_seconds` | integer NOT NULL default 60 | |
| `inbound_watermark` | timestamptz NOT NULL | `sys_updated_on` high-water mark |
| `inbound_watermark_sys_id` | text NULL | Tie-break for equal timestamps |
| `webhook_secret_name` | text NULL | HMAC secret reference |
| `active_field_map_id` / `active_state_map_id` | uuid NULL | Activated versions |
| `journal_public` | text NOT NULL default `comments` | Journal for XMS public comments |
| `sync_work_notes` | boolean NOT NULL default false | |
| `attachment_limit_bytes` | integer NOT NULL default 10485760 | |
| `attachment_over_limit` | text NOT NULL default `link` | CHECK IN (`link`, `skip`) |
| `error_trip_threshold` | jsonb NOT NULL | `{ratio: 0.5, window_minutes: 15, min_attempts: 10}` |
| `health` | text NOT NULL default `healthy` | Derived by the worker; CHECK IN (`healthy`, `degraded`, `failing`, `tripped`) |
| `last_success_at` / `last_error_at` / `last_error` | timestamptz / timestamptz / text | |
| `created_at` / `updated_at` / `version` | | |

### 2.2 `acct.field_maps` and `acct.state_maps` (versioned, immutable once activated)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` / `instance_id` | uuid | |
| `version` | integer NOT NULL | Increments per instance |
| `state` | text NOT NULL | CHECK IN (`draft`, `validated`, `active`, `retired`) |
| `entries` | jsonb NOT NULL | Field map: `[{external: "short_description", xms: "title", direction: "both", transform: {kind: "none"}, sor: "external_at_create_then_xms"}]`; state map: `{ticketType: {inbound: {"1": "new", "10": "open"}, outbound: {"new": "1", "open": "10", "pending_client": "18"}}}` |
| `validation_report` | jsonb NULL | Output of §3.2 |
| `sample_payloads_s3_key` | text NULL | Samples used for validation |
| `created_by` / `created_at` / `activated_at` / `activated_by` | | |

Transform kinds: `none`, `lookup` (a value table), `template` (a string template over mapped fields, used for the outbound description and journal prefix), `truncate` (with length). No scripting.

### 2.3 `acct.sync_links`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` / `instance_id` | uuid NOT NULL | |
| `ticket_id` | uuid NOT NULL | |
| `external_sys_id` | text NOT NULL | ServiceNow `sys_id` |
| `external_number` | text NOT NULL | Display number |
| `state` | text NOT NULL | CHECK IN (`linked`, `pending_external`, `pending_xms`, `conflict`, `unlinked`) |
| `last_outbound_at` / `last_outbound_hash` | timestamptz / text | Watermark of what we sent (hash of the mapped outbound payload) |
| `last_inbound_at` / `last_inbound_sys_updated_on` | timestamptz / timestamptz | Watermark of what we applied |
| `field_sor_overrides` | jsonb NULL | Per-link override of system of record (rare, admin only) |
| `last_conflict` | jsonb NULL | `{field, xmsValue, externalValue, kept, at}` |
| `created_at` / `updated_at` / `version` | | |

### 2.4 `acct.sync_journal_links` and `acct.sync_attachment_links` (append-only)

| Table | Columns |
|---|---|
| `acct.sync_journal_links` | `id`, `account_id`, `instance_id`, `ticket_id`, `xms_kind` CHECK IN (`comment`, `work_note`), `xms_id`, `external_journal_sys_id`, `direction` CHECK IN (`in`, `out`), `created_at` |
| `acct.sync_attachment_links` | `id`, `account_id`, `instance_id`, `ticket_id`, `attachment_id`, `external_attachment_sys_id`, `direction`, `outcome` CHECK IN (`copied`, `linked`, `skipped`), `created_at` |

### 2.5 `acct.sync_runs` (append-only)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` / `instance_id` | uuid | |
| `direction` | text | CHECK IN (`in`, `out`, `poll`, `webhook`) |
| `ticket_id` / `external_sys_id` | uuid / text NULL | |
| `outbox_id` / `inbox_id` | uuid NULL | |
| `attempt` | integer | |
| `outcome` | text NOT NULL | CHECK IN (`success`, `retried`, `dead_lettered`, `skipped_reflection`, `skipped_policy`, `skipped_mode`) |
| `error_class` / `error_text` | text | Retryable or terminal classification |
| `duration_ms` | integer | |
| `created_at` | timestamptz | |

### 2.6 Indexes, constraints, RLS

```sql
create unique index ix_connector_instances_account_name on acct.connector_instances (account_id, name);
create index ix_connector_instances_poll on acct.connector_instances (type, mode)
  where mode <> 'off' and kill_switch = 'armed';

create unique index ix_field_maps_instance_version on acct.field_maps (instance_id, version);
create unique index ix_field_maps_active on acct.field_maps (instance_id) where state = 'active';
create unique index ix_state_maps_instance_version on acct.state_maps (instance_id, version);
create unique index ix_state_maps_active on acct.state_maps (instance_id) where state = 'active';

create unique index ix_sync_links_instance_ticket on acct.sync_links (instance_id, ticket_id);
create unique index ix_sync_links_instance_external on acct.sync_links (instance_id, external_sys_id);
create index ix_sync_links_state on acct.sync_links (account_id, state) where state in ('conflict','pending_xms','pending_external');

create unique index ix_sync_journal_links_external on acct.sync_journal_links (instance_id, external_journal_sys_id);
create unique index ix_sync_journal_links_xms on acct.sync_journal_links (instance_id, xms_kind, xms_id);
create unique index ix_sync_attachment_links_external on acct.sync_attachment_links (instance_id, external_attachment_sys_id);
create unique index ix_sync_attachment_links_xms on acct.sync_attachment_links (instance_id, attachment_id);

create index ix_sync_runs_instance_time on acct.sync_runs (instance_id, created_at desc);
create index ix_sync_runs_health on acct.sync_runs (instance_id, outcome, created_at desc);
-- monthly partitions on acct.sync_runs per DATA-MODEL §7

-- RLS pair on every table above, portal role has no grants
alter table acct.connector_instances enable row level security;
alter table acct.connector_instances force row level security;
create policy acct_isolation_operator on acct.connector_instances
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[]));
revoke all on acct.connector_instances, acct.field_maps, acct.state_maps, acct.sync_links,
  acct.sync_journal_links, acct.sync_attachment_links, acct.sync_runs from xms_portal;
create trigger sync_runs_append_only before update or delete on acct.sync_runs
  for each row execute function sys.raise_append_only();
```

### 2.7 Reflection-drop rule (`backend/src/domain/sync/reflection.ts`)

An inbound record update is a reflection and is skipped (`skipped_reflection`) when all of the following hold: the sync link exists; the record's `sys_updated_on` is not later than `last_outbound_at` plus the instance clock tolerance (default 5 seconds); and the hash of the inbound values for the fields we sent equals `last_outbound_hash`. Journal entries are additionally matched by `acct.sync_journal_links.external_journal_sys_id` (we record the `sys_id` the instance returned for our own journal write) and by the correlation prefix XMS writes into every outbound journal entry (`[XMS:<comment id short>]`, stripped when displayed). Outbound: any outbox row whose `origin` equals `sync:<this instance id>` is never dispatched to this instance (framework rule) (SN-03).

### 2.8 Conflict policy (`backend/src/domain/sync/conflict.ts`)

Per field, from the active field map, with these defaults for a CSM instance:

| XMS field | Default system of record | Rationale |
|---|---|---|
| `title`, `description`, `requester` | `external_at_create_then_xms` | The client authors the case; after intake XMS owns the record |
| `priority`, `impact`, `urgency` | `external_at_create_then_xms` | Client sets initial urgency; XMS derives priority thereafter |
| `state` | `xms` | XMS runs the state machine; inbound state changes are applied only where the state map marks them `accept_inbound` (for example the client reopening or cancelling) |
| `assignment_group`, `assignee` | `xms` | Client instance sees a vendor group only |
| `category`, `configuration_item` | `xms` | |
| `client_reference` (their number), `external_ref` | `external` | |
| `comments` journal | `merge` | Append both ways |
| `work_notes` journal | `merge` when enabled, else `none` | |
| free-text `u_client_notes` style fields | `newest` | The only place timestamps decide |

Resolution when an inbound change touches a `xms` field: the change is not applied, a `skipped_policy` run is written, and if the XMS value differs the link records `last_conflict` and state `conflict` until the next successful outbound write clears it. `newest` compares `sys_updated_on` against the XMS `updated_at` of the field's last audit event. Last-write-wins is never applied to a field without an explicit `newest` policy (SN-04).

## 3. Producers / core logic

All in `backend/src/worker` on the framework; ServiceNow-specific code lives in `backend/src/worker/src/connectors/servicenow/` and pure logic in `backend/src/domain/sync/`.

### 3.1 Client (`SnowClient`)

Table API (`/api/now/table/{table}`) with `sysparm_query`, `sysparm_fields`, `sysparm_display_value=all`, pagination by `sysparm_limit` and `sysparm_offset`; journal reads through `sys_journal_field` filtered by `element_id`; attachments through `/api/now/attachment` (`file` upload, metadata list, binary download). Authentication: OAuth client credentials with token cache and the AIX-style refresh result (`ok` or `credential_invalid`, the latter setting `credential_state = invalid` and tripping the switch); basic auth for non-production. All requests carry a correlation header (`X-XMS-Correlation-Id`) for support conversations with the client's admins. Retryable errors: 429, 5xx, timeouts; terminal: 400, 401 after refresh, 403, 404 on a known `sys_id` (link marked `unlinked`).

### 3.2 Map validation (`backend/src/domain/sync/validate.ts`)

Given the instance's `sys_dictionary` for the table, the sample payloads and the draft maps: every required XMS field (title, requester, ticket type or a constant, state) has an inbound source; every outbound field exists in the dictionary and is writable; every sample record's state value has an inbound mapping; every XMS state of every enabled ticket type has an outbound mapping or is marked `no_outbound`; no two XMS states map to one external value outbound without a `tie_break`; lookups cover every sample value. The report is stored on the map; activation requires an empty error list.

### 3.3 Inbound: poll and webhook

- **Poller**: a worker loop claims due instances (`mode <> 'off'`, armed, `next_poll_at <= now`) with `FOR UPDATE SKIP LOCKED`, queries `sys_updated_on > watermark OR (sys_updated_on = watermark AND sys_id > watermark_sys_id)` ordered by `sys_updated_on, sys_id` in pages of 200, and writes one `sys.inbox` row per record keyed (`servicenow:<instance id>`, `sys_id`, `sys_updated_on`). Journal entries since the watermark are fetched per changed record. The watermark advances only after the page is written to the inbox (at-least-once; the inbox key makes replays harmless).
- **Webhook** (optional): `POST /webhooks/servicenow/{instanceId}` on the API with an HMAC over the body using `webhook_secret_name`; the handler only writes an inbox row and returns 202. The poller remains the source of truth; the webhook shortens latency.

### 3.4 Inbound: apply

`ServiceNowApplyHandler` consumes `sys.inbox` rows for the instance in order per `sys_id`:

1. Resolve or create the sync link (`external_sys_id`). A new record creates a ticket through the ticket service with `source = sync`, `origin = sync:<instance>`, `external_ref = external_number`, requester resolved from the mapped email to `acct.contacts` (created if absent).
2. Apply the reflection rule (§2.7); skip if a reflection.
3. Translate fields through the active field map (transforms, lookups) and states through the state map; apply the conflict policy per field.
4. Call the ticket service once with the resulting patch and transition (a transition the state machine forbids becomes the nearest allowed state per the map's `fallback` entry, logged).
5. Journal entries: `comments` become public comments authored as the client-side user (a contact); `work_notes` become work notes only when `sync_work_notes` is on; each is linked in `acct.sync_journal_links`.
6. Attachments: metadata compared against `acct.sync_attachment_links`; new ones under the limit are downloaded to S3 (scan state `pending`) and registered; over the limit become a work note with the instance link (`link`) or are skipped.
7. Write the `sync_runs` row; update link watermarks; in `off` or tripped mode the handler leaves the inbox row unconsumed.

### 3.5 Outbound: dispatch and deliver

The dispatcher routes outbox events the instance subscribes to (`ticket.created` when XMS creates first and the instance is bidirectional with `create_outbound = true`, `ticket.updated` for mapped fields, `ticket.transitioned`, `comment.added`, `work_note.added` when enabled, `attachment.registered` when clean) to `connector.servicenow.fifo` with message group `ticket:<ticket id>` so a ticket's changes stay ordered. `ServiceNowDeliverHandler`:

1. Skip with `skipped_mode` when the instance is `ingest_only`, `off` or tripped (the message returns to the queue for `tripped`, is dropped for `ingest_only` and `off` since the mode change is an audited operator decision).
2. Skip when `origin = sync:<this instance>` (framework guarantee, asserted again here).
3. Build the outbound payload from the active maps; for journals, prefix the correlation marker; for state, translate through the outbound state map.
4. `PATCH /api/now/table/{table}/{sys_id}` or `POST` for creation; record the returned `sys_updated_on`, journal `sys_id` and attachment `sys_id`; set `last_outbound_at` and `last_outbound_hash`.
5. Idempotency: the outbox id is the SQS deduplication id and is stored on the run; a redelivered message with an existing `success` run for that outbox id is acknowledged without a second call.
6. Errors classified per §3.1; terminal errors go straight to the dead letter with the payload.

### 3.6 Health, trip and alarms

A worker job recomputes `health` per instance every minute from `sync_runs`: `failing` when the error ratio over the trip window exceeds half the threshold, `degraded` when inbound lag exceeds three poll intervals or the DLQ is non-empty, `tripped` when the switch is tripped. Automatic trip at the threshold writes an audit event and fires `sync.instance_tripped`. Metrics: `sync.runs{instance,outcome}`, `sync.inbound_lag_seconds`, `sync.outbound_backlog`, `sync.dlq_depth`, `sync.conflicts`.

### 3.7 Shadow sync and migration hand-off

For cutover, [Data Migration](../data-migration/TECHNICAL-SPEC.md) imports history and sets `external_ref` and sync links for imported records with `last_inbound_sys_updated_on` equal to the record's `sys_updated_on` at import. The instance then starts in `ingest_only` with `inbound_watermark` equal to the import extraction time, so the shadow period applies only deltas and creates no duplicates. Promotion to `bidirectional` is a manual step after the parallel run.

### 3.8 Local stand-in

`tools/servicenow-stand-in/`: an Express application implementing the subset used above (Table API query, get, patch, post with `sys_updated_on` stamping; `sys_journal_field`; `sys_dictionary` for two profiles, CSM and ITSM; the Attachment API; an optional auto-echo mode that re-saves every patched record to simulate reflections; fault injection through headers or a control endpoint for 429, 500, timeouts, invalid token). Runs in docker-compose and in the pipeline for contract tests.

## 4. API routes

All internal principals; permissions from the operator catalog.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/accounts/{id}/connectors` | `admin:connectors` | Instances for the account |
| POST | `/accounts/{id}/connectors/servicenow` | `admin:connectors` | Create instance (credential entered once, stored to Secrets Manager, name returned) |
| PATCH | `/connectors/{instanceId}` | `admin:connectors` | Settings, mode, poll interval, journal and attachment options |
| POST | `/connectors/{instanceId}/test-connection` | `admin:connectors` | Validates credentials and table access |
| POST | `/connectors/{instanceId}/samples` | `admin:connectors` | Fetch five recent records and the dictionary for mapping |
| GET/POST | `/connectors/{instanceId}/field-maps[...]` | `admin:connectors` | List versions, create draft |
| PUT | `/connectors/{instanceId}/field-maps/{mapId}` | `admin:connectors` | Edit a draft |
| POST | `/connectors/{instanceId}/field-maps/{mapId}/validate` | `admin:connectors` | Runs §3.2 |
| POST | `/connectors/{instanceId}/field-maps/{mapId}/activate` | `admin:connectors` | Requires `validated` |
| same set | `/connectors/{instanceId}/state-maps[...]` | `admin:connectors` | |
| POST | `/connectors/{instanceId}/kill-switch` | `admin:connectors` | `{action: trip \| arm, reason}` |
| POST | `/connectors/{instanceId}/watermark` | `admin:connectors` | Rewind with preview count |
| GET | `/connectors/health` | `admin:connectors` | Health list across granted accounts |
| GET | `/connectors/{instanceId}/runs?direction=&outcome=&from=&to=` | `admin:connectors` | Runs list |
| GET | `/connectors/{instanceId}/dead-letters` | `admin:connectors` | Dead letters |
| POST | `/connectors/{instanceId}/dead-letters/{id}/replay` and `/discard` | `admin:connectors` | Replay or discard with reason; bulk variants accept an id list |
| GET | `/tickets/{id}/sync` | `tickets:view` | Linked record card data |
| POST | `/webhooks/servicenow/{instanceId}` | `@Public()` plus HMAC guard | Inbox write only, 202 |

Idempotency keys on every POST; every route is in the route and permission snapshot test.

## 5. Cross-cutting concerns

- **Isolation:** instances, maps, links and runs are account-scoped; the poller binds `xms.account_ids` to the instance's account for each claim; a `sys_id` from one instance can never match a link of another (unique per instance).
- **Visibility:** work notes reach an instance only when `sync_work_notes` is on and only into `work_notes`; the outbound builder has no path from a work note to the public journal; the field map validator rejects a work-note source mapped to `comments`.
- **Secrets:** only secret names in rows; the worker's task role may read secrets under the `xms/connectors/` prefix only.
- **Egress:** worker tasks route through the NAT with the fixed IP clients allowlist ([Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) §5).
- **Attachments:** downloaded objects enter the scan pipeline; only `clean` attachments are sent outbound.
- **Ordering:** FIFO queue with a per-ticket message group outbound; per-`sys_id` ordering inbound through the inbox key sort.
- **Observability:** metrics of §3.6, alarms on tripped, DLQ depth, inbound lag and credential invalid.

## 6. Web / client changes

- **Account record, Integrations tab:** instance list and the full-screen instance record of functional §5.2 with Connection, Field map, State map, Journals and attachments, Validation and Activation sections; mapping grids are editable tables in the house table grammar with inline validation markers.
- **Admin, Sync health:** the list of functional §5.4 polling at 30 seconds; instance drill-down with Runs, Dead letters (with replay and discard actions and a reason dialog), Watermark controls and kill switch.
- **Ticket record:** Linked record card in the related-info rail; conflict banner; `via ServiceNow` chips on comments and work notes; ingest-only notice.
- RTK Query slice `connectorsApi` with tags `Connectors`, `ConnectorMaps`, `ConnectorRuns`, `ConnectorDeadLetters`, `SyncHealth`, `TicketSync`.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/servicenow-sync-infra` (`infra`) | FIFO queue and DLQ, webhook route on the ALB, secrets prefix and IAM | Framework queues |
| 2 | `feature/servicenow-sync-db` (`backend/src/db`) | Tables of §2 | Tickets, contacts |
| 3 | `feature/servicenow-sync-domain` (`backend/src/domain`) | Maps, validation, translation, reflection, conflict | none |
| 4 | `feature/servicenow-sync-standin` (`tools/`) | Stand-in with two profiles and fault injection | none |
| 5 | `feature/servicenow-sync-ingest` (`backend/src/worker`) | Client, poller, apply, health | 2, 3, 4 |
| 6 | `feature/servicenow-sync-api` (`backend`) | Routes of §4 | 2 |
| 7 | `feature/servicenow-sync-web` (`frontend`) | Screens of §6 | 6 |
| 8 | `feature/servicenow-sync-outbound` (`backend/src/worker`) | Deliver handler, attachments outbound, webhook, automatic trip | 5, Phase 3 |

Deploy order every release: infra -> db -> worker -> api -> web.

## 8. Testing & verification

- **Domain unit tests:** every transform kind; validation report cases (unmapped required field, unmapped state, duplicate outbound state without tie-break, lookup gap); reflection rule with clock tolerance and hash mismatch; each conflict policy including `external_at_create_then_xms` on create versus update; state fallback to the nearest allowed state.
- **Contract tests against the stand-in** (CSM and ITSM profiles): given an outbox row and map version, assert the exact PATCH body and journal prefix; given a stand-in record and journal entries, assert the exact ticket service calls; attachment under and over the limit.
- **Loop test:** stand-in auto-echo on; one XMS comment produces exactly one outbound call and zero new XMS comments; one stand-in comment produces one XMS comment and zero outbound calls.
- **Chaos tests:** 500 then 200 (one success run, one retried run, no DLQ); 400 (DLQ row, alarm metric); invalid token (credential invalid, tripped, no further calls); 429 with backoff.
- **Ordering test:** three transitions on one ticket delivered out of order by SQS redelivery are applied in order through the message group and outbox sequence.
- **Mode tests:** `ingest_only` drops outbound with `skipped_mode` and applies inbound; `tripped` leaves both queued and resumes in order after arming.
- **Multi-instance test:** two instances with different profiles and auth kinds against two stand-in containers; runs, links and health never cross.
- **Watermark test:** poller restart after writing a page but before advancing re-fetches and produces no duplicates.
- **Shadow-sync test:** imported links plus watermark at extraction time apply only deltas.
- **Isolation suite:** every table of §2 included.
- **HTTP tests:** permissions on every route; webhook rejects a bad HMAC and an unconfigured secret; portal principal rejected everywhere.
- **e2e (Playwright with the stand-in):** onboard, fail validation, fix, activate ingest-only, see a case appear, promote to bidirectional, see a comment echo suppressed, trip and replay.

## 9. Risks / notes

- **Brookfield facts may invalidate the default maps.** They are data; the stand-in profiles are updated from Vini's documentation before Phase 3 and the validator catches gaps.
- **ServiceNow instance clocks and `sys_updated_on` granularity** (seconds) make reflection detection depend on the hash, not the timestamp; the tolerance is configurable per instance.
- **Journal correlation markers** are visible in the client's journal (`[XMS:abcd1234]`); if a client objects, the fallback is matching by the returned journal `sys_id` only, which is already recorded.
- **Volume assumptions** are low; if a client generates thousands of updates per hour, the poller's page size and interval are the levers, and the FIFO queue's per-group throughput is sufficient because groups are per ticket.
- **OAuth issuance is client-side work**; onboarding checklists carry the exact scopes and the XMS egress IP.
- **The read-side MCP module in `aix-mcp`** stays for Axel's ad hoc reads of client instances; it does not participate in sync and is not a dependency.

## 10. As-built notes

To be filled during the build; graduates into `WHAT-WAS-DONE.md`.
