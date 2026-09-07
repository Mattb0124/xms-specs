# Technical Spec: Data Migration & Cutover

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [ServiceNow Sync](../servicenow-integration/TECHNICAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Test Strategy](../../03-delivery/TEST-STRATEGY.md)
**Requirements covered:** DM-01, DM-02, DM-03, DM-04
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `infra`

---

## 1. Architecture context (current state, verified 2026-09-04)

| Piece | Where | Relevance |
|---|---|---|
| Ticket, comment, work note, attachment, time entry services | XMS `backend/src/domain` and `backend` per [Ticket Management](../ticket-management/TECHNICAL-SPEC.md) and [Time & Budget](../time-and-budget/TECHNICAL-SPEC.md) | The loader calls the same services the API uses, with origin `import`, so every invariant (separate work-note table, append-only audit, locked periods) holds for migrated data |
| State, priority, group and resolution maps | `acct.state_maps`, `acct.field_maps` owned by [ServiceNow Sync](../servicenow-integration/TECHNICAL-SPEC.md) | Import and sync translate with the same versioned maps; a map version is recorded on every batch |
| Connector framework: inbox, outbox, dead letters, kill switch | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), `sys.*` tables | Shadow sync during the parallel run is the ServiceNow connector in `ingest_only` mode; the migration adds no second sync path |
| Attachment scanning | GuardDuty Malware Protection result consumer in the worker, `acct.attachments.scan_state` ([Security §6](../../01-architecture/SECURITY-AND-TENANCY.md)) | Imported attachments enter as `pending` and become downloadable only when `clean` |
| Isolation | RLS on every `acct.*` table, `xms_worker` role binding `xms.account_ids` per job ([Data Model §3](../../01-architecture/DATA-MODEL.md)) | A batch runs bound to exactly one account; an extraction that references another account's record fails closed |
| Billing periods and consumption | `acct.contract_periods`, `acct.billing_periods`, `acct.time_entries`, `acct.time_adjustments` ([Time & Budget](../time-and-budget/TECHNICAL-SPEC.md)) | Balance loads write period rows and, where chosen, a `migration_adjustment` time adjustment |
| Job claiming | `FOR UPDATE SKIP LOCKED` batch claiming in the worker, the studio `routine_engine.py` pattern from [AIX Pattern Reuse §1](../../01-architecture/AIX-PATTERN-REUSE.md) | Long-running batches survive a worker restart: a batch with a stale lease is resumed from its last checkpoint |
| ServiceNow read client precedent | `aix-mcp/app/modules/servicenow_ams_mcp/snow_client.py` (source on another branch; only compiled files on the current checkout) | Read for the Table API query shape (`sysparm_query`, `sysparm_offset`, `sysparm_limit`); the XMS extractor is written fresh in TypeScript |
| Demo seed precedent | studio `scripts/seed_xms_demo.py` on `feature/xms-ticketing` | Only prior loader of ticket data; parameterised by scope, no live credentials, informs the seed for migration tests |
| Excel export | `exceljs` in the worker ([AIX Pattern Reuse §2](../../01-architecture/AIX-PATTERN-REUSE.md): `xlsx` 0.18.5 not used) | Reconciliation report download |

Cross-module ordering: Ticket Management and ServiceNow Sync mapping tables ship before the first extractor; Time & Budget periods ship before the balance loader.

## 2. Data model

All three tables are account-scoped with RLS; `import_records` is append-only by convention (a re-run inserts a new record row per source id per run and the latest row wins in views).

### 2.1 `acct.import_batches`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid pk | |
| `account_id` | uuid not null | RLS |
| `object_kind` | text | CHECK in (`account`, `contact`, `user`, `case`, `comment`, `work_note`, `attachment`, `time_record`, `contract`, `contract_period_balance`, `people_map`) |
| `source_kind` | text | CHECK in (`servicenow_table_api`, `servicenow_export_files`, `finance_workbook`) |
| `source_ref` | jsonb | Instance profile id, or the S3 keys of the uploaded export files |
| `source_range` | jsonb | For example `{"opened_from": "2021-01-01", "opened_to": "2026-12-31"}` |
| `map_versions` | jsonb | `{state_map_version, field_map_version, resolution_map_version, people_map_batch_id}` |
| `dry_run` | boolean not null | |
| `status` | text | CHECK in (`draft`, `extracting`, `extracted`, `mapping`, `mapped`, `loading`, `loaded`, `reconciling`, `reconciled`, `signed_off`, `failed`, `superseded`) |
| `counts` | jsonb | `{extracted, loaded, updated, skipped, unmatched, errors}` |
| `checkpoint` | jsonb | Last processed source offset or sys_id, so a resumed batch continues |
| `supersedes_batch_id` | uuid null | The previous run of the same scope |
| `lease_owner`, `lease_until` | text, timestamptz | Worker claiming |
| `started_at`, `finished_at` | timestamptz | |
| `run_by` | text | Actor id |
| `error` | text null | Terminal failure message |
| `created_at`, `updated_at`, `version` | | Mutable row conventions |

### 2.2 `acct.import_records`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid pk | |
| `account_id` | uuid not null | RLS |
| `batch_id` | uuid not null fk `acct.import_batches` | |
| `source_id` | text not null | ServiceNow `sys_id` or the finance row key `<contract_number>:<period>` |
| `source_key` | text null | Human key, for example `CS0012345` |
| `target_table` | text null | `acct.tickets`, `acct.comments`, ... |
| `target_id` | uuid null | |
| `status` | text | CHECK in (`pending`, `loaded`, `updated`, `skipped`, `unmatched`, `error`) |
| `message` | text null | Why skipped, unmatched or errored |
| `source_payload_key` | text | S3 key of the raw source row (never the payload inline; sizes vary) |
| `source_hash` | text | SHA-256 of the normalised source row; unchanged hash on re-run means `skipped` |
| `created_at` | timestamptz | Append-only |

### 2.3 `acct.reconciliation_reports` and lines

| Column | Type | Notes |
|---|---|---|
| `id` | uuid pk | |
| `account_id` | uuid not null | RLS |
| `scope` | text | CHECK in (`batch`, `account`, `delta`) |
| `batch_id` | uuid null | For batch scope |
| `status` | text | CHECK in (`pending`, `open`, `signed_off`) |
| `snapshot_key` | text null | S3 key of the frozen Excel and JSON at sign-off |
| `signed_by`, `signed_at` | text, timestamptz | |
| `lines` | jsonb | Array of `{kind, subject, source_figure, target_figure, delta, status, explanation, explained_by, explained_at}`; `kind` in (`count_by_state`, `count_by_object`, `hours_by_contract_period`, `balance_by_contract_period`); `status` in (`matched`, `delta_explained`, `delta_open`) |
| `created_at`, `updated_at`, `version` | | |

Migration stage per account lives on `acct.account_settings.migration_stage` (`not_started`, `import`, `shadow_sync`, `freeze`, `cutover`, `parallel_run`, `decommissioned`, `rolled_back`) with a `migration_checklist jsonb` of rollback criteria and decommission items.

```sql
create unique index ux_import_batches_scope_active
  on acct.import_batches (account_id, object_kind, (source_range::text))
  where status not in ('superseded', 'failed');
create index ix_import_records_batch_status on acct.import_records (batch_id, status);
create unique index ux_import_records_batch_source on acct.import_records (batch_id, source_id);
create index ix_import_records_source on acct.import_records (account_id, object_kind_of(batch_id), source_id);
-- identity lookup across runs: the latest loaded target for a source id
create index ix_import_records_target on acct.import_records (account_id, target_table, target_id);
alter table acct.import_batches enable row level security;
alter table acct.import_batches force row level security;
create policy acct_isolation_operator on acct.import_batches
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[]));
-- identical policies on acct.import_records and acct.reconciliation_reports
-- portal role: no grant on any migration table
create trigger trg_import_records_append_only before update or delete on acct.import_records
  for each row execute function sys.raise_append_only();
```

Idempotency: the identity of a migrated row is `(account_id, object_kind, source_id)`. The loader looks up the latest `import_records` row with a `target_id` for that identity; if found and `source_hash` unchanged it records `skipped`; if found and changed it updates the target through the service and records `updated`; if absent it creates and records `loaded`. Every target table carries `external_ref text` and `external_source text` (`servicenow:<instance>`) so the sync connector's `sync_links` can be seeded from the import in one statement at cutover.

Reconciliation computation: `count_by_state` compares the source count per mapped XMS state against `select state, count(*) from acct.tickets where account_id = $1 and external_source = $2`; `hours_by_contract_period` compares the sum of source time minutes per contract per period against `sum(minutes)` of `acct.time_entries` with origin `import` joined to `acct.contract_periods`; `balance_by_contract_period` compares the finance closing balance against the XMS period position (contracted plus carry-over minus consumed). A line is `matched` when `delta = 0`; otherwise `delta_open` until an explanation is saved.

## 3. Producers / core logic

Worker jobs (`backend/src/worker/src/migration/`), each claiming a batch by lease:

| Job | What it does |
|---|---|
| `extract` | ServiceNow Table API paging (`sysparm_limit` 500, `sysparm_offset`, `sysparm_query` on the range, `sysparm_display_value=all` for reference labels) or export-file parsing (CSV, XML); writes one raw row to S3 (`accounts/<id>/migration/<batch>/raw/<sys_id>.json`) and one `import_records` row `pending`; checkpoints every page. Journal entries come from `sys_journal_field` filtered by `element in (comments, work_notes)` and are split into two logical object kinds; attachments from `sys_attachment` metadata then `attachment/<sys_id>/file` bytes streamed to S3 under the account prefix with `scan_state = pending` |
| `map` | Applies the batch's map versions and the people map; unresolved references become `unmatched` with a message; a dry run stops after this step and produces the reconciliation preview |
| `load` | Calls domain services in dependency order (accounts and contacts, then cases, then comments and work notes, then attachments, then time records), origin `import`, actor `system:migration`, audit event `imported` with `data.source_timestamp` and `data.batch_id`; no outbox rows (imported changes never dispatch to connectors or notifications); SLA clocks are not created; `created_at` on the ticket is the source opened date |
| `load_balances` | Reads the finance workbook rows, upserts `acct.contract_periods` for past periods with `locked = true` at the finance figure, and writes a `migration_adjustment` time adjustment when the operator chose "trust finance" for a delta |
| `reconcile` | Builds or refreshes the report lines for the batch or the account |
| `promote` | Copies signed batches from the migration database to production by replaying the raw rows through `map` and `load` against production with the same map versions (never a table copy, so RLS and services apply); records the promotion on the batch |
| `delta` | An `extract` with `sys_updated_on > last_watermark` used in the freeze window |

CLI commands (`backend/src/worker` nest-commander, run as one-off ECS tasks): `migration:batch:create`, `migration:batch:run --dry-run`, `migration:reconcile`, `migration:promote`, `migration:seed-sync-links` (creates `acct.sync_links` from `external_ref` at cutover), `migration:archive-source` (final ServiceNow export to S3 at decommission).

Stage transitions on the cutover card are a domain service (`MigrationStageService.advance(accountId, toStage)`) that checks: `shadow_sync` requires at least one signed account report and the ServiceNow connector instance in `ingest_only`; `freeze` requires the delta batch scheduled; `cutover` requires a signed `delta` report and every rollback criterion checked; `rolled_back` requires the connector flipped back and the XMS-created tickets exported (a list is shown before confirming); `decommissioned` requires the checklist complete. Every transition is an audit event.

## 4. API routes

All under `/v1/migration`, internal principals only, permission `admin:migration` unless stated.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/batches?account_id=&object_kind=&status=` | `admin:migration` | Batch list |
| POST | `/batches` | `admin:migration` | Create draft batch (dry run flag, source, range, map versions) |
| POST | `/batches/{id}/run` | `admin:migration` | Enqueue the batch (dry or real) |
| POST | `/batches/{id}/cancel` | `admin:migration` | Stop at next checkpoint; status `failed` with reason `cancelled` |
| GET | `/batches/{id}` | `admin:migration` | Batch record with counts and log |
| GET | `/batches/{id}/records?status=&q=` | `admin:migration` | Per-record list |
| GET | `/batches/{id}/records/{recordId}` | `admin:migration` | Source payload (presigned S3) and target reference |
| POST | `/batches/{id}/records/{recordId}/resolve` | `admin:migration` | Set a target for an unmatched record (people map) |
| POST | `/uploads` | `admin:migration` | Presigned POST for export files and the finance workbook |
| GET | `/reconciliation?account_id=&scope=` | `admin:migration` | Report with lines |
| POST | `/reconciliation/{id}/lines/{n}/explain` | `admin:migration` | Save explanation and choice (`trust_finance`, `trust_entries`) |
| POST | `/reconciliation/{id}/sign-off` | `admin:migration` and not the batch runner | Freeze the report, store the snapshot |
| GET | `/reconciliation/{id}/export` | `admin:migration` | Excel download (presigned) |
| GET | `/cutover?account_id=` | `admin:migration` | Stage card |
| POST | `/cutover/{accountId}/advance` | `admin:migration` | Stage transition with checks |
| PATCH | `/cutover/{accountId}/checklist` | `admin:migration` | Tick criteria and decommission items |

Controllers are thin: DTO validation, one service call, response. Account context comes from the principal's grants; a batch for an account the caller is not granted answers 404.

## 5. Cross-cutting concerns

- **Migration environment.** A separate RDS database `xms_migration` in the dev account with the same schema, roles and RLS, provisioned by Terraform; the worker there has the ServiceNow read-only integration credential. Production never holds the credential; promotion is a replay into production from the raw rows in S3, run by a production worker task that reads the migration bucket prefix. Migration data is deleted from the migration database after the account is signed off and promoted; the raw rows and reports stay in S3 for the retention period ([Security §10](../../01-architecture/SECURITY-AND-TENANCY.md)).
- **Isolation.** A batch is bound to one `account_id`; source rows whose account reference resolves to a different XMS account are `unmatched` with reason `cross_account`, never loaded.
- **Attachments.** Streamed, never buffered; files over the per-account cap become a reference row (`acct.attachments.kind = archived_reference`) pointing at the archived export; scan state gates download exactly as live uploads.
- **No side effects.** Origin `import` suppresses outbox writes, notifications, SLA clock creation and Axel calls; the audit event is the only trace. The ticket service exposes this as an `ImportContext` flag validated to be usable only by the `system:migration` actor.
- **Identity.** People-map matching is by lowercased email, then by exact display name within the account, with confidence recorded; placeholders are contacts with `kind = placeholder` and a later merge rewrites references in one transaction and records `contact_merged` audit events.
- **Performance.** Loads are batched 200 rows per transaction with checkpointing; the largest account (estimated 50k cases, 500k journal entries) loads in under four hours on one worker task.

## 6. Web / client changes

`frontend/app/(internal)/admin/migration/*` in the ServiceNow list grammar: batches list and record (with the Records, Mapping, Log tabs), reconciliation list with inline explanation editor and the Sign off action, cutover cards with checklist. RTK Query slice `migrationApi` with tags `MigrationBatches`, `MigrationBatch`, `MigrationRecords`, `Reconciliation`, `Cutover`; running batches poll every 10 seconds, otherwise no polling. The desk banner ("ServiceNow is the system of record until <date>") is driven by `migration_stage` from account settings and rendered by Ticket Management's shell.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/data-migration-schema` (`backend/src/db`, `infra`) | Three tables, RLS, migration database and bucket prefix, ServiceNow read credential in Secrets Manager | Ticket Management and ServiceNow Sync map tables |
| 2 | `feature/data-migration-extract` (`backend/src/worker`, `backend/src/domain`) | Table API and export-file extractors, people map, dry run, reconciliation counts | 1 |
| 3 | `feature/data-migration-load` (`backend/src/worker`, `backend`) | Loader with `ImportContext`, routes, promotion | 2, attachment scanning |
| 4 | `feature/data-migration-console` (`frontend`) | Console views | 3 |
| 5 | `feature/data-migration-balances` (`backend/src/worker`, `backend`) | Finance workbook loader, hour and balance reconciliation, sign-off snapshot | Time & Budget periods |
| 6 | `feature/data-migration-cutover` (all) | Stage service, checklist, `seed-sync-links`, delta batch, archive command | ServiceNow connector production grade |

Deploy order per release: infra, db, worker, api, web.

## 8. Testing & verification

- **Domain (Jest):** state and resolution mapping through recorded map versions; people-map matching precedence and placeholder creation; journal splitting into comments vs work notes; source hash normalisation (field order and whitespace do not change the hash).
- **Extractor (Jest, fixtures):** recorded Table API pages (cases, journal, attachments, time) in `backend/test/kit/fixtures/servicenow/`; paging and checkpoint resume after a simulated failure mid-page; export-file parsing for the same objects.
- **Loader (Jest + Testcontainers):** load, re-run with no change yields `skipped` for every row and identical target counts; re-run with one changed journal entry yields exactly one `updated`; imported rows carry the source dates, one `imported` audit event each, no outbox rows, no SLA clocks, no notifications; work notes land only in `acct.work_notes` and are invisible to the portal role.
- **Reconciliation (Jest + Testcontainers):** constructed source counts and hour totals produce the expected lines; a 2.0 hour delta with `trust_finance` writes one `migration_adjustment` and locks the period at the finance figure; sign-off refused with a `delta_open` line; the signer cannot be the runner.
- **Isolation suite:** the three tables are covered by the generated suite; a cross-account source reference yields `unmatched` with `cross_account`.
- **Stage service (Jest):** each transition's preconditions; rollback lists XMS-created tickets since cutover.
- **HTTP (supertest):** every route rejects anonymous, portal and non-`admin:migration` principals; 404 for ungranted accounts.
- **Manual rehearsal (Phase 3):** full dry run for one real account in the migration environment, reconciliation signed, promotion into dev production-like database, freeze runbook walked end to end with a rollback executed once.

## 9. Risks / notes

- **ServiceNow export shape is unconfirmed** (time storage, custom fields, journal volume). The extractor is fixture-driven so the shape can change without touching the loader; Vini's documentation is due 2026-09-25.
- **Finance figures may not be monthly or per contract.** The balance loader accepts a workbook with a declared period cadence; if finance tracks by engagement, the period rows attach to a synthetic contract per engagement, flagged for cleanup.
- **Placeholder contacts can accumulate.** The console lists placeholders per account with a merge action; a report of unmerged placeholders is part of the decommission checklist.
- **Promotion replays rather than copies**, so it costs the same time as the original load. Accepted, because it keeps services and RLS in the path.
- **Rollback after email repoint** means inbound mail may land in XMS during the rollback window; the connector export covers tickets but the alias must be repointed first in the rollback runbook.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
