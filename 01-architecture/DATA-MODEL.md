# Data Model: XMS PostgreSQL

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Domain Model](./DOMAIN-MODEL.md), [Security & Tenancy](./SECURITY-AND-TENANCY.md), [Architecture](./ARCHITECTURE.md), module technical specs under `02-modules/`
**Reference implementation mined:** studio `feature/xms-ticketing` branch, `app/modules/xms_ticketing/models_db.py` (644 lines) and `service.py` (1932 lines): proven SLA pause and breach math, event model, close discipline, presigned attachment flow. Ported, not reused (ADR-07)

This document fixes conventions, the schema layout, the isolation mechanics, and the table catalog. Column-level definitions live in each module's technical spec so that a module can be reviewed in one place.

---

## 1. Conventions

| Convention | Rule |
|---|---|
| Engine | PostgreSQL 16 on Amazon RDS (Multi-AZ in prod), extensions `pgcrypto`, `pg_trgm`, `vector`, `btree_gist` |
| Access from code | Drizzle ORM with SQL-first migrations in `backend/src/db`; no query outside the data layer (repository classes), per the AIX "route database access through the data layer" standard |
| Primary keys | `uuid` default `gen_random_uuid()` |
| Display keys | Ticket `CS` + 7-digit zero-padded operator-wide sequence (`CS0001234`), article `KB` + 6 digits, contract `CT` + 5 digits; sequences are Postgres sequences, never `MAX()+1` |
| Time | `timestamptz` everywhere, stored UTC; business-calendar math converts in the service using the IANA zone on the calendar |
| Money | `numeric(14,2)` plus a `currency` char(3) column; no floats |
| Durations | Integer minutes |
| Closed vocabularies | `text` columns with `CHECK` constraints and a matching TypeScript union; no Postgres enums (adding a value must not require a type migration) |
| Mutable rows | `created_at`, `updated_at`, `version` (integer, optimistic concurrency: an update with a stale version is rejected with 409) |
| Append-only rows | `created_at` only; `UPDATE` and `DELETE` blocked by a trigger that raises; tables: `audit_events`, `security_events`, `usage_events`, `time_entries`, `time_adjustments`, `sla_pauses`, `inbound_messages`, `daily_snapshots`, `ai_suggestions` (state changes go through a separate `ai_suggestion_decisions` table), `outbox`, `inbox`, `import_records` |
| Soft delete | Only where the domain needs it (saved views, templates, articles as `retired`); tickets are cancelled, never deleted; accounts are offboarded, never deleted |
| Actor references | `actor_kind` (`user`, `portal_user`, `api_client`, `system`, `ai`) plus `actor_id text` plus denormalised `actor_name`; never a foreign key to the operator schema from an account-scoped table |
| Naming | `snake_case` tables and columns, plural table names, `<table>_id` foreign keys, indexes `ix_<table>_<cols>`, partial indexes named with `_open`/`_active` suffixes |
| Search | `tsvector` generated columns on tickets (title, description), comments, work notes, articles; `pg_trgm` on ticket display key and requester email; vector index (`ivfflat`, cosine) on `embeddings.vector` |

## 2. Schemas

| Schema | Contents | Access role |
|---|---|---|
| `op` | Operator-scoped tables: users, roles, role assignments, account grants, assignment groups, API clients, roster, skills, PTO, allocation, capacity snapshots, pipeline demand, global configuration defaults, connector registry, report templates | `xms_app` (read/write), `xms_portal` (read of a whitelist view only), `xms_worker` |
| `acct` | Every account-scoped table; every table has `account_id uuid not null references op.accounts(id)` and row-level security | `xms_app`, `xms_portal`, `xms_worker` with RLS forced; `xms_migrator` bypasses for migrations only |
| `sys` | Outbox, inbox, dead letters, job leases, schema check metadata | `xms_worker` read/write, `xms_app` insert on outbox only |
| `rpt` | Daily snapshots and materialised read models (portfolio dashboard, capacity view) | `xms_app` read, `xms_worker` write, RLS on `account_id` where present |

`op.accounts` is the root row. It lives in `op` because the operator manages accounts, but every `acct.*` table points at it.

## 3. Isolation mechanics

The workbook's first requirement (TM-01) asks for hard isolation at the data layer, not row-level filtering by the application. XMS satisfies the intent with database-enforced isolation and keeps a path to physical separation:

1. **Every `acct.*` and `rpt.*` table with `account_id` has `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`** (so even the table owner is subject to it), with two policies:
   - `acct_isolation_operator`: `USING (account_id = ANY (current_setting('xms.account_ids')::uuid[]))` for role `xms_app` and `xms_worker`.
   - `acct_isolation_portal`: `USING (account_id = current_setting('xms.account_id')::uuid)` for role `xms_portal`, plus table-level `REVOKE` on `acct.work_notes`, `acct.time_entries`, `acct.rate_cards`, `acct.ai_suggestions`, and column-level grants that hide internal columns.
2. **The data layer sets the session variables in one place**: a request-scoped transaction wrapper reads the caller's account grants from the authenticated principal and runs `SET LOCAL xms.account_ids = ...` (or `xms.account_id` for portal principals) before any query. There is no code path that opens a connection without the wrapper; the connection pool's default has the variables unset, which makes every policy evaluate to false.
3. **Inserts are checked too** (`WITH CHECK`), so a bug cannot write a row into another account.
4. **No cross-account foreign keys** exist inside `acct`; shared knowledge is expressed with a visibility table (`acct.article_visibility` has one row per allowed account, plus a `global` flag on the article that the policy honours through a `SECURITY DEFINER` function `acct.article_visible(article_id)`).
5. **Attachments** are stored under `s3://<bucket>/accounts/<account_id>/...` with a bucket policy that ties the prefix to the same principal context (presigned URLs are minted only after the RLS-protected attachment row was read).
6. **Isolation tier per account** (`op.accounts.isolation_tier`): `shared` (RLS in the shared database, the default) or `dedicated` (its own RDS instance or database with the same schema). The data layer resolves the connection by account before setting the session variables; a dedicated account still runs the same RLS policies. This is the escalation path if Security or a client contract rules that shared tables are unacceptable (assessment appendix B, Juan/Security), and it can be applied to one account without touching the others.
7. **The isolation test suite** ([Test Strategy §3](../03-delivery/TEST-STRATEGY.md)) is generated from `information_schema` and fails the build when a table with `account_id` lacks RLS or a policy.

Rejected alternatives, recorded so they are not relitigated: schema-per-account (the same team works every account; portfolio, capacity and dispatch views need cross-account queries; 4 developers), application-level filtering only (the requirement rejects it, and the XMS POC audit found a cross-tenant `queue_id` leak in exactly that style of code), database-per-account for everyone (operationally heavy at this team size; kept as the `dedicated` tier for accounts that need it).

## 4. Table catalog

Owner spec is where the columns are defined.

### 4.1 `op` (operator)

| Table | Purpose | Owner spec |
|---|---|---|
| `op.accounts` | Client accounts: display key, name, status, isolation tier, residency region, default time zone, branding, offboarding state | Accounts & Administration |
| `op.users` | Internal and portal user profiles keyed by Clerk id; `kind`, `account_id` (portal only), status, display fields, time zone, locale | Accounts & Administration |
| `op.roles`, `op.role_permissions`, `op.role_assignments` | Two catalogs (operator, portal); assignments optionally scoped to accounts | Accounts & Administration |
| `op.account_grants` | Internal user to account; the source of `xms.account_ids` | Accounts & Administration |
| `op.assignment_groups`, `op.group_members` | CSM, OneStream Technical, Infrastructure, others | Accounts & Administration |
| `op.api_clients`, `op.api_client_grants` | Machine identities and their account and permission scope | Accounts & Administration |
| `op.people`, `op.skills`, `op.person_skills`, `op.certifications`, `op.person_calendars`, `op.pto`, `op.allocations`, `op.pipeline_demand` | Roster and capacity inputs | Capacity & Allocation |
| `op.config_defaults` | Operator-wide state machines, priority matrix, activity types, billable classes, resolution codes, SLA policy defaults, versioned JSON with a `kind` | Accounts & Administration (content defined in Ticket Management and Time & Budget) |
| `op.connector_types` | Registry of connector implementations and their capabilities | Platform Integrations |
| `op.report_templates` | WSR and QBR templates (PPTX masters, layout definitions) | Dashboards & Report Packs |
| `op.holiday_calendars`, `op.holidays` | Per-country calendars shared by accounts and people | Accounts & Administration |

### 4.2 `acct` (account-scoped, RLS)

| Table | Purpose | Owner spec |
|---|---|---|
| `acct.account_settings` | AI switch and opt-ins, consumption visibility, portal enabled, CSAT, sync mode, email branding, inbound aliases | Accounts & Administration |
| `acct.business_calendars`, `acct.calendar_hours`, `acct.calendar_holidays` | Working hours and holidays per account | Accounts & Administration |
| `acct.contacts` | People at the account (portal user or email-only) | Client Portal |
| `acct.engagements` | Commercial relationship, account owner, renewal dates | Time, Contracts & Budget |
| `acct.ticket_forms`, `acct.ticket_form_versions` | Dynamic forms per request type | Client Portal |
| `acct.config_overrides` | Per-account state machine, matrix, SLA policy overrides | Accounts & Administration |
| `acct.tickets` | The ticket | Ticket Management |
| `acct.ticket_links` | Parent/child, related, duplicate, blocks | Ticket Management |
| `acct.ticket_groups`, `acct.ticket_group_members` | Projects and change windows | Ticket Management |
| `acct.comments` | Public comments | Ticket Management |
| `acct.work_notes` | Internal notes (separate table by design) | Ticket Management |
| `acct.attachments` | Files with scan state | Ticket Management |
| `acct.sla_clocks`, `acct.sla_pauses` | Timers and pause evidence | Ticket Management |
| `acct.audit_events` | Append-only audit | Ticket Management (used by all) |
| `acct.saved_views` | User and shared views | Ticket Management |
| `acct.watchers` | Subscriptions | Ticket Management |
| `acct.csat_responses`, `acct.csat_surveys` | Surveys and answers | Client Portal |
| `acct.solution_articles`, `acct.article_versions`, `acct.article_visibility`, `acct.article_feedback` | Knowledge base | Solution Knowledge Base |
| `acct.configuration_items`, `acct.ci_links` | Asset register and links | Solution Knowledge Base |
| `acct.ticket_solutions` | Resolution record linking ticket to article version | Solution Knowledge Base |
| `acct.ticket_templates` | Pre-filled tickets | Solution Knowledge Base |
| `acct.embeddings` | Vectors for articles and resolved ticket summaries | Solution Knowledge Base |
| `acct.contracts`, `acct.contract_periods`, `acct.rate_cards`, `acct.rate_card_entries` | Commercial terms | Time, Contracts & Budget |
| `acct.time_entries`, `acct.time_adjustments`, `acct.non_ticket_buckets` | Time | Time, Contracts & Budget |
| `acct.billing_periods`, `acct.billing_exports` | Locking and exports | Time, Contracts & Budget |
| `acct.threshold_alerts`, `acct.threshold_alert_events` | Consumption alerts | Time, Contracts & Budget |
| `acct.inbound_messages`, `acct.outbound_messages`, `acct.inbound_aliases`, `acct.quarantine_items` | Email | Email Intake & Outbound |
| `acct.notifications` | In-app notifications | Ticket Management |
| `acct.report_packs`, `acct.report_schedules`, `acct.report_runs` | WSR and QBR | Dashboards & Report Packs |
| `acct.connector_instances`, `acct.field_maps`, `acct.state_maps`, `acct.sync_links`, `acct.sync_runs` | Per-account connectors | ServiceNow Sync (framework in Integration Patterns) |
| `acct.ai_settings`, `acct.ai_suggestions`, `acct.ai_suggestion_decisions`, `acct.ai_feedback` | AI | Axel AI Functionality |
| `acct.import_batches`, `acct.import_records`, `acct.reconciliation_reports` | Migration | Data Migration & Cutover |
| `acct.webhook_subscriptions`, `acct.webhook_deliveries` | Outbound webhooks per account, HMAC-signed, delivered on the connector framework | Platform Integrations |
| `acct.finance_deliveries` | Delivery records for billing exports (S3, SFTP, HTTPS) with acknowledgements | Platform Integrations |
| `acct.chat_channel_maps`, `acct.calendar_events` | Teams and calendar integrations (Phase 4) | Platform Integrations |

### 4.3 `sys` and `rpt`

| Table | Purpose | Owner spec |
|---|---|---|
| `sys.outbox`, `sys.inbox`, `sys.dead_letters`, `sys.job_leases` | Connector framework | Integration Patterns |
| `sys.schema_checks` | Last isolation-suite run metadata | Test Strategy |
| `sys.security_events` | Append-only security events (auth, authz, admin, data movement, abuse, AI), monthly partitions | Audit Log and User Analytics |
| `sys.telemetry_buffer_stats` | Ingestion counters and dropped-batch accounting | Audit Log and User Analytics |
| `rpt.daily_snapshots` | Point-in-time measures per account per day | Dashboards & Report Packs |
| `rpt.portfolio_daily` | Operator roll-up (no `account_id`; built from snapshots, no client content) | Dashboards & Report Packs |
| `rpt.portal_visible_measures` | Whitelist of measures the portal role may read, enforced by policy | Dashboards & Report Packs |
| `rpt.usage_events` | Append-only usage events (screens, actions, searches, Axel decisions, API requests), monthly partitions, RLS on `account_id` | Audit Log and User Analytics |
| `rpt.events_v` | Unified read view over domain audit, security and usage events for the Admin audit search | Audit Log and User Analytics |
| `rpt.capacity_periods` | Computed capacity per person per period (no account dimension) | Capacity & Allocation |
| `rpt.capacity_actuals` | Logged minutes per person per account per month, built by the worker, RLS on `account_id` | Capacity & Allocation |
| `op.calendar_consents` | Per-user Microsoft Graph consent records for calendar push (Phase 4) | Platform Integrations |

## 5. Cross-cutting columns and triggers

- `account_id` on every `acct.*` row; RLS policies as in §3.
- `audit_events` are written by the service layer, not by database triggers, so the actor and correlation id are always known. A trigger-based safety net (`acct.audit_guard`) rejects any update on `acct.tickets`, `acct.contracts` and `acct.solution_articles` whose transaction did not also insert an audit event (checked through a transaction-local setting the service sets).
- `outbox` rows are written in the same transaction as the domain change by the service layer.
- `updated_at` maintained by a trigger; `version` incremented by the data layer's update helper, which includes `WHERE version = $expected`.

## 6. Migrations

- Drizzle SQL migrations in `backend/src/db/migrations`, numbered `0001_...`, applied by the pipeline with the `xms_migrator` role before the worker and API roll.
- Expand, migrate, contract: never rename or drop in the same release that changes code; the API must run against N and N+1.
- Every migration that creates an `acct.*` table must also create its RLS policies in the same file; the isolation suite enforces it.
- A migration dry-run against a fresh prod snapshot is a pipeline gate before prod.

## 7. Sizing assumptions

| Measure | Assumption | Consequence |
|---|---|---|
| Accounts | 10 to 40 | RLS with an array of granted accounts is cheap; no partitioning needed |
| Tickets | up to 50k per account over five years, 500k total including migrated history | Partial indexes on open tickets; audit and snapshot tables partitioned by month from day one |
| Time entries | 100k per year | Indexed by (account, entry date) and (person, entry date) |
| Inbound email | 2k per day peak during cutover weekends | Raw bodies in S3, rows small |
| Embeddings | 100k rows of 1024 dimensions | `ivfflat` with lists tuned at 1k rows per list; rebuild job monthly |
