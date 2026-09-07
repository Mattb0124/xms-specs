# Technical Spec: Platform Integrations

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Data Model](../../01-architecture/DATA-MODEL.md), [ServiceNow Sync](../servicenow-integration/TECHNICAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md), [Test Strategy](../../03-delivery/TEST-STRATEGY.md)
**Requirements covered:** INT-04, INT-05; delivery for INT-02; registry and health for SN-07 and every connector
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`, `infra`

---

## 1. Architecture context (current state, verified 2026-09-04)

| Piece | Where | Relevance |
|---|---|---|
| Connector framework: outbox, inbox, dispatcher, queues, dead letters, kill switch | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md); `sys.outbox`, `sys.inbox`, `sys.dead_letters`, `acct.connector_instances`, `acct.sync_runs` ([Data Model §4](../../01-architecture/DATA-MODEL.md)) | Every connector here is a handler on the framework; this module owns `op.connector_types` and the health computation over `sync_runs` and `dead_letters` |
| API clients | `op.api_clients`, `op.api_client_grants` ([Security §2.3](../../01-architecture/SECURITY-AND-TENANCY.md)): `xms_live_` prefix, SHA-256 lookup index, bcrypt confirmation, scopes, operator-owned | The public API authenticates with these; this module owns the admin routes and the scope catalog entries |
| Principal and guard | One composed guard producing `Principal` with `kind = api_client` ([Security §2.2](../../01-architecture/SECURITY-AND-TENANCY.md)) | Public API routes are the same controllers with scope checks, not a second API |
| Billing export production | Time & Budget writes `acct.billing_exports` with file key and checksum on period lock ([Time & Budget](../time-and-budget/TECHNICAL-SPEC.md)) | The finance connector subscribes to the outbox event `billing_period.locked` and delivers the stored file; it never recomputes it |
| Constant-time secret comparison, fail closed when unconfigured | AIX `app-api/src/guards/require-internal-secret.guard.ts` ([AIX Pattern Reuse §1](../../01-architecture/AIX-PATTERN-REUSE.md)) | Webhook signature verification helper for inbound Teams and calendar callbacks; signing for outbound webhooks |
| Degrade a broken connector, not the run | AIX `app-api/src/api/v3/mcp/internal-mcp.service.ts` `resolve-session` returning `skipped[]` | Health model: one failing instance is `failing`; nothing else changes state |
| OAuth refresh with mark-invalid-on-failure | AIX `app-api/src/api/v3/mcp/oauth-refresh.service.ts` `RefreshResult` | Calendar (Microsoft Graph) token refresh per consenting user |
| OpenAPI document | NestJS Swagger `DocumentBuilder` as in AIX `app-api/src/main.ts` (title, version, bearer auth) | The public reference is generated from the same document, filtered to public-tagged routes, and published as static HTML by the pipeline |
| Versioning | `enableVersioning({ type: URI })` ([AIX Pattern Reuse §2](../../01-architecture/AIX-PATTERN-REUSE.md)) | `v1` is the public version; internal-only routes are tagged `internal` and excluded from the published reference |
| XMS MCP server | `aix-mcp/app/modules/xms_mcp` on `aix-mcp/app/mcp_common` ([AI Integration §4](../../01-architecture/AI-INTEGRATION.md)) | Registered as a connector instance of type `mcp` for health and kill switch; the kill switch is read by the MCP through `GET /v1/internal/connectors/mcp/state` every 30 seconds |
| Notifications | `acct.notifications` and the operator group notification path ([Ticket Management](../ticket-management/TECHNICAL-SPEC.md)) | Failing-connector alerts |

Cross-module ordering: framework tables (Phase 1) before the registry; billing period locking (Phase 3) before the finance connector; API clients admin (Accounts & Administration, Phase 3) before public API keys are issued.

## 2. Data model

### 2.1 `op.connector_types` (operator, seeded by migration)

| Column | Type | Notes |
|---|---|---|
| `id` | text pk | `servicenow`, `email_inbound`, `email_outbound`, `finance_export`, `report_delivery`, `webhook`, `teams`, `slack`, `calendar`, `mcp` |
| `scope` | text | CHECK in (`account`, `operator`) |
| `supported_modes` | text[] | Subset of `off`, `ingest_only`, `bidirectional`, `outbound_only` |
| `subscribes_to` | text[] | Outbox event types the type may subscribe to (webhook and chat types intersect this with the instance's own list) |
| `expected_interval_minutes` | integer null | Health: `failing` when no success within this interval and work was pending |
| `config_schema` | jsonb | JSON Schema for the instance's `config` |
| `enabled` | boolean | Operator toggle for the type |

### 2.2 `acct.connector_instances` (framework table; columns added by this module)

The base columns are defined in [Integration Patterns §4](../../01-architecture/INTEGRATION-PATTERNS.md) (type, account, name, mode, auth reference, endpoint, schedule, kill switch, health thresholds). This module adds:

| Column | Type | Notes |
|---|---|---|
| `health` | text | CHECK in (`healthy`, `degraded`, `failing`, `paused`); recomputed by the worker health job |
| `health_reason` | text null | Human summary shown on the list |
| `last_success_at`, `last_failure_at` | timestamptz null | |
| `backlog` | integer | Undelivered outbox rows subscribed by this instance |
| `dead_letter_count` | integer | Open dead letters |
| `alert_open` | boolean | An unacknowledged failing alert exists |
| `config` | jsonb | Validated against `op.connector_types.config_schema` |

Operator-scoped instances (finance, report delivery, mcp, calendar) are stored with `account_id` set to the operator's own sentinel account row (`op.accounts.kind = operator`) so the table keeps one shape and RLS still applies.

### 2.3 `acct.webhook_subscriptions` and `acct.webhook_deliveries`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid pk | |
| `account_id` | uuid not null | The account whose events are delivered; a multi-account API client holds one subscription per account |
| `api_client_id` | uuid not null | Owner |
| `endpoint_url` | text not null | HTTPS only; private ranges rejected at registration and at delivery (SSRF guard) |
| `event_types` | text[] not null | Subset of the public event catalog |
| `secret_hash` | text not null | Argon2 hash of the signing secret; the secret is shown once |
| `secret_kid` | text not null | Key id sent in the signature header, rotated by creating a new secret |
| `status` | text | CHECK in (`active`, `paused`, `deleted`) |
| `paused_reason` | text null | `continuous_failure`, `owner`, `client_revoked` |
| `created_at`, `updated_at`, `version` | | |

`acct.webhook_deliveries` (append-only; one row per attempt):

| Column | Type | Notes |
|---|---|---|
| `id` | uuid pk | |
| `account_id` | uuid not null | |
| `subscription_id` | uuid not null | |
| `outbox_id` | uuid not null | The event delivered; idempotency key `X-XMS-Delivery: <outbox_id>` |
| `attempt` | integer | 1..5 |
| `status` | text | CHECK in (`pending`, `delivered`, `retrying`, `dead_lettered`, `replayed`) |
| `response_status` | integer null | |
| `duration_ms` | integer null | |
| `error` | text null | |
| `created_at` | timestamptz | |

### 2.4 `acct.finance_deliveries`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid pk | |
| `account_id` | uuid not null | The account of the billing period |
| `billing_export_id` | uuid not null | From Time & Budget |
| `destination_kind` | text | CHECK in (`s3`, `sftp`, `https`) |
| `manifest_key` | text | S3 key of the manifest XMS wrote |
| `status` | text | CHECK in (`pending`, `delivered`, `acknowledged`, `failed`, `superseded`) |
| `supersedes_id` | uuid null | Earlier delivery for the same period |
| `ack_received_at` | timestamptz null | |
| `error` | text null | |
| `created_at`, `updated_at`, `version` | | |

### 2.5 `acct.chat_channel_maps` and `op.calendar_consents`

| Table | Columns |
|---|---|
| `acct.chat_channel_maps` | `id`, `account_id`, `provider` (`teams`, `slack`), `channel_ref` (webhook URL reference in Secrets Manager or channel id), `event_types text[]`, `enabled`, timestamps |
| `op.calendar_consents` | `id`, `user_id`, `provider` (`microsoft`), `token_secret_name` (Secrets Manager), `refresh_state` (`valid`, `invalid`), `consented_at`, `revoked_at`; the access and refresh tokens never sit in the database |
| `acct.calendar_events` | `id`, `account_id`, `ticket_group_id` or `ticket_id`, `user_id`, `provider_event_id`, `content_hash`, timestamps; the idempotency record for pushes |

```sql
create unique index ux_webhook_subscriptions_endpoint
  on acct.webhook_subscriptions (api_client_id, account_id, endpoint_url) where status <> 'deleted';
create index ix_webhook_deliveries_sub_created on acct.webhook_deliveries (subscription_id, created_at desc);
create unique index ux_webhook_deliveries_attempt on acct.webhook_deliveries (subscription_id, outbox_id, attempt);
create unique index ux_finance_deliveries_export on acct.finance_deliveries (billing_export_id) where status <> 'superseded';
create unique index ux_calendar_events_target_user
  on acct.calendar_events (coalesce(ticket_group_id, ticket_id), user_id);
alter table acct.webhook_subscriptions enable row level security;
alter table acct.webhook_subscriptions force row level security;
create policy acct_isolation_operator on acct.webhook_subscriptions
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[]));
-- identical policies on webhook_deliveries, finance_deliveries, chat_channel_maps, calendar_events
-- portal role: no grants on any table in this module
create trigger trg_webhook_deliveries_append_only before update or delete on acct.webhook_deliveries
  for each row execute function sys.raise_append_only();
```

Webhook signing: body is the canonical JSON of `{id, type, occurred_at, account_id, data}`; headers `X-XMS-Event`, `X-XMS-Delivery` (outbox id), `X-XMS-Timestamp`, `X-XMS-Signature: kid=<secret_kid>, v1=<hex hmac-sha256(secret, timestamp + "." + body)>`. Receivers reject timestamps older than five minutes. Rotation: a subscription may hold two active secrets for 24 hours; deliveries carry both signatures.

Health computation (worker job every minute, per instance): `paused` if the kill switch is off; else `failing` if `dead_letter_count > 0` or (`backlog > 0` and `now - last_success_at > expected_interval`); else `degraded` if any `sync_runs` row in the last 15 minutes failed or `backlog > threshold`; else `healthy`. Transition into `failing` opens an alert and notifies the integrations group; acknowledging clears `alert_open` without changing health.

## 3. Producers / core logic

Worker handlers (`backend/src/worker/src/connectors/`), each a framework handler on its own queue:

| Handler | Queue | Behaviour |
|---|---|---|
| `finance-export` | `connector.finance` | On `billing_period.locked`: read `acct.billing_exports` file from S3, write manifest (`{account_key, period, file, sha256, rows, generated_at, supersedes}`), deliver by destination kind (S3 copy with `x-amz-checksum-sha256`; SFTP via `ssh2` streaming; HTTPS POST multipart with the manifest as JSON part), record `delivered`; a poll job checks S3 or SFTP for `<manifest>.ack` and flips to `acknowledged`; HTTPS acknowledges synchronously with 2xx and a body echoing the checksum |
| `webhook` | `connector.webhook` | On any public event type: for each active subscription of the event's account subscribed to the type, render the public representation through `backend/src/contracts` public mappers (which exclude internal fields by construction), sign, POST with a 10-second timeout, record the attempt; 2xx delivered, 5xx or timeout retry, 4xx (other than 408 and 429) dead letter; after 24 hours of continuous failures pause the subscription and notify the owner |
| `teams` | `connector.chat` | On mapped event types: render an Adaptive Card (key, title, priority, state, assignee, link) and POST to the channel's incoming webhook; failures retry then dead letter; the bot endpoint for message actions and commands is an API route (§4) that validates the Teams JWT and calls the ticket and time services with the mapped XMS user |
| `slack` | `connector.chat` | Same abstraction (`ChatProvider` interface with `postEvent`, `handleAction`, `handleCommand`); Block Kit rendering; Slack signing secret verification |
| `calendar` | `connector.calendar` | On ticket group or scheduled ticket create, update, cancel: for each attendee with a valid consent, upsert the Graph event (`PATCH` when `acct.calendar_events` has a `provider_event_id`, else `POST`), skip when `content_hash` unchanged; 401 from Graph triggers the refresh helper, and a failed refresh marks the consent `invalid` and stops pushing for that user (AIX `RefreshResult` semantics) |
| `mcp-health` | (none, scheduled) | Reads `aix-mcp/app/modules/xms_mcp` `/healthz` and the MCP's own success and error counters (exposed as a small JSON endpoint on the MCP), updates the `mcp` instance |
| `connector-health` | (none, scheduled) | The health computation above for every instance |

Domain services in `backend/src/domain/integrations/`: `ConnectorRegistryService` (types, instance create and update with schema validation, kill switch with audit), `WebhookSigner`, `PublicRepresentation` mappers (the only path from an entity to a webhook or chat payload; unit-tested to exclude work notes, rates, internal-only fields), `FinanceDeliveryService`, `ChatProvider` implementations, `CalendarPushService`.

The MCP kill switch: the `mcp` instance's mode is served by `GET /v1/internal/connectors/mcp/state` (internal secret guard); `aix-mcp/app/modules/xms_mcp` polls it every 30 seconds and, when `off`, returns the string "XMS tools are paused by an administrator" from every tool without calling the API.

## 4. API routes

Admin routes (internal principals, `admin:connectors`):

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/connectors/types` | `admin:connectors` | Registry types and their schemas |
| GET | `/v1/connectors?account_id=&type=&health=` | `admin:connectors` | Instance list with health |
| POST | `/v1/connectors` | `admin:connectors` | Create instance (config validated against the type schema) |
| PATCH | `/v1/connectors/{id}` | `admin:connectors` | Update config, mode, schedule |
| POST | `/v1/connectors/{id}/kill-switch` | `admin:connectors` | `{enabled, reason}`; audited |
| GET | `/v1/connectors/{id}/health` | `admin:connectors` | Hourly series and last runs |
| GET | `/v1/connectors/{id}/dead-letters` | `admin:connectors` | Open dead letters |
| POST | `/v1/connectors/{id}/dead-letters/{dlId}/replay` | `admin:connectors` | Re-enqueue with reason |
| POST | `/v1/connectors/{id}/dead-letters/{dlId}/discard` | `admin:connectors` | Discard with reason |
| POST | `/v1/connectors/{id}/alerts/ack` | `admin:connectors` | Acknowledge the failing alert |
| GET | `/v1/finance/deliveries?account_id=&period=` | `admin:connectors` or `time:lock-period` | Delivery list |
| POST | `/v1/finance/deliveries` | `time:lock-period` | Deliver or re-deliver a locked period |
| GET, PUT | `/v1/accounts/{accountId}/chat-channels` | `admin:connectors` | Teams and Slack channel maps |
| GET, POST, DELETE | `/v1/me/calendar-consent` | any internal user | Start the Microsoft consent flow, read state, revoke |
| GET | `/v1/internal/connectors/mcp/state` | internal secret | Kill switch state for the MCP |

API client administration (`admin:api-clients`, owned by Accounts & Administration; listed for completeness): `GET, POST /v1/api-clients`, `POST /v1/api-clients/{id}/revoke`, `POST /v1/api-clients/{id}/rotate`.

Public API (principal kind `api_client`, scope checked per route; the same controllers as the internal app, tagged `public`):

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/v1/tickets`, `/v1/tickets/{key}` | `tickets:read` | List and read, account set from the client's grants |
| POST | `/v1/tickets` | `tickets:write` | Create with origin `api` |
| POST | `/v1/tickets/{key}/transitions` | `tickets:write` | Same state machine, same rules |
| POST | `/v1/tickets/{key}/comments` | `comments:write` | Public comments only; no work-note route is exposed to API clients |
| GET | `/v1/time-entries?ticket=` | `time:read` | Hours breakdown without rates |
| GET | `/v1/exports/{id}` | `exports:read` | Presigned download of a billing export |
| GET | `/v1/kb/articles` | `kb:read` | Articles visible to the client's accounts |
| GET, POST, DELETE | `/v1/webhooks/subscriptions` | `webhooks:manage` | Manage own subscriptions |
| POST | `/v1/webhooks/subscriptions/{id}/rotate-secret` | `webhooks:manage` | Second secret for 24 hours |
| GET | `/v1/webhooks/subscriptions/{id}/deliveries` | `webhooks:manage` | Delivery history |
| POST | `/v1/webhooks/subscriptions/{id}/deliveries/{dId}/replay` | `webhooks:manage` | Replay own dead letter |

Chat provider callbacks (verified by provider signature, `@Public()` with the provider guard): `POST /v1/integrations/teams/actions`, `POST /v1/integrations/teams/commands`, `POST /v1/integrations/slack/events`, `POST /v1/integrations/slack/commands`. Microsoft consent redirect: `GET /v1/integrations/microsoft/callback`.

Rate limits: per API client 600 requests per minute default, configurable on the client; headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` on 429.

## 5. Cross-cutting concerns

- **Scope enforcement.** The composed guard maps `api_client` principals to `permissions` from scopes (`tickets:read` grants `tickets:view` on the granted accounts, and nothing else); route permission declarations stay the same as for humans, so there is one enforcement path. The golden route snapshot marks which routes are `public` and fails the build if a route tagged `public` lacks a scope mapping.
- **Public representation.** `backend/src/contracts/public/*` defines the outbound shapes; mappers are the only way to produce them, and a test asserts that no public type has a field named or derived from work notes, cost rate, bill rate, AI suggestion internals or another account.
- **SSRF and egress.** Webhook and finance HTTPS destinations resolve DNS at delivery and reject private and link-local ranges; outbound traffic leaves through the NAT with the fixed egress IP ([Integration Patterns §5](../../01-architecture/INTEGRATION-PATTERNS.md)).
- **Secrets.** Channel webhook URLs, SFTP keys, Graph tokens and finance endpoint credentials live in Secrets Manager under `xms/<env>/connectors/<instance id>/...`; the instance stores names only. Rotation does not touch the database.
- **Isolation.** Every webhook delivery, chat message and calendar event is produced under the account of its outbox row; a multi-account API client's subscriptions are per account by design, so no payload merges accounts.
- **Observability.** Per-instance CloudWatch EMF metrics (`connector_success`, `connector_failure`, `connector_backlog`, `connector_dead_letters`) and alarms on `failing` health ([Platform & Operations §5](../../01-architecture/PLATFORM-AND-OPERATIONS.md)).
- **Documentation publishing.** The pipeline runs `nest` to emit the OpenAPI JSON, filters to `public` tags, renders static HTML, and uploads it to `docs.<domain>/api/v1` with a changelog generated from the contracts package version history.

## 6. Web / client changes

`frontend/app/(internal)/admin/connectors/*`: connectors list (health-first sort, kill switch toggle in the row), instance record with Health, Dead letters and Configuration tabs (configuration forms generated from the type's JSON Schema with a small renderer, so a new connector type needs no bespoke form), finance deliveries list and Deliver action on the billing period page (Time & Budget owns the page, this module contributes the panel), API clients and webhook subscriptions under `admin/api-clients`, chat channel map editor on the account record, and the calendar consent card on the user's profile page. RTK Query slice `connectorsApi` with tags `ConnectorTypes`, `Connectors`, `Connector`, `DeadLetters`, `FinanceDeliveries`, `WebhookSubscriptions`, `ChatChannels`, `CalendarConsent`; the connectors list polls every 30 seconds.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/integrations-registry` (`backend/src/db`, `backend/src/worker`, `backend`, `frontend`) | `op.connector_types`, health columns, health job, admin routes and screens, kill switch, MCP state endpoint | Framework tables (Phase 1) |
| 2 | `feature/integrations-finance` (`backend/src/worker`, `backend`, `infra`) | Finance handler, deliveries table, destinations, acknowledgement poll, Deliver panel | Billing period locking (Phase 3) |
| 3 | `feature/integrations-public-api` (`backend`, `backend/src/contracts`, pipeline) | Scope mapping in the guard, public mappers, `public` tagging, published reference, rate limits | API clients (Accounts & Administration, Phase 3) |
| 4 | `feature/integrations-webhooks` (`backend/src/db`, `backend/src/worker`, `backend`, `frontend`) | Subscriptions, signing, delivery handler, replay, auto-pause | 3 |
| 5 | `feature/integrations-teams` (all) | Channel maps, Adaptive Cards, bot actions and commands, app registration in `infra` | Phase 4 |
| 6 | `feature/integrations-calendar` (all) | Consent flow, Graph push, refresh handling | Phase 4 |
| 7 | `feature/integrations-slack` (`backend/src/worker`, `backend`) | Slack provider on the chat abstraction | On demand |

Deploy order per release: infra, db, worker, api, web.

## 8. Testing & verification

- **Domain (Jest):** health computation table (every combination of kill switch, dead letters, backlog, interval, recent failures); scope-to-permission mapping; public mapper exclusion test over every public type; webhook canonical JSON and signature with a known vector; rotation window accepts both secrets; SSRF guard rejects private ranges and DNS rebinding to private ranges.
- **Handlers (Jest, stubs):** finance delivery for each destination kind with a stub S3, SFTP server and HTTPS endpoint; acknowledgement poll flips status; superseding delivery on re-lock. Webhook handler: 2xx delivered, 500 then 200 yields two attempts and one delivered, five 500s yields dead letter, 400 dead letters immediately, 24 hours of failures pauses and notifies. Teams card rendering fixtures; Slack signature verification; calendar upsert idempotency by `content_hash` and `provider_event_id`; Graph 401 with failed refresh marks consent invalid.
- **Data (Testcontainers):** RLS on every table in this module; append-only trigger on deliveries; unique constraints on subscriptions and calendar events.
- **HTTP (supertest):** admin routes reject anonymous, portal and non-admin principals; public routes reject missing or wrong scopes with 403 and other accounts with 404; rate limit headers and 429; provider callbacks reject bad signatures; the route snapshot includes the `public` tag and scope map.
- **Contract:** the published OpenAPI document contains only `public`-tagged routes and no internal schema; a snapshot test guards breaking changes to `v1` (removed field or changed type fails the build).
- **Manual smoke:** lock a period on dev, confirm the manifest in the finance bucket and the acknowledgement round trip; register a webhook against a request-bin, transition a ticket, verify the signature by hand; post a P1 to a test Teams channel; create a change window and see it on a consenting user's calendar.

## 9. Risks / notes

- **Finance's destination is undecided.** All three destination kinds are cheap because delivery is a single handler with a strategy per kind; only the chosen one is enabled in prod.
- **Teams app registration and admin consent** need the Microsoft tenant administrator; incoming webhooks need no consent, which is why notifications ship first.
- **Public API stability.** Once `v1` is published, additive-only; the snapshot test is the enforcement. Breaking changes mean `v2` alongside `v1`.
- **Webhook receivers under client control** may be slow or flaky; the 10-second timeout and auto-pause protect the worker; a noisy subscription cannot starve the queue because deliveries are per subscription and the queue is standard (unordered).
- **Calendar tokens are per user** and long-lived refresh tokens are sensitive; they live in Secrets Manager with a per-user secret name and are deleted on revoke or user deactivation.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
