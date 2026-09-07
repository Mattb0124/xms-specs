# Audit Log and User Analytics

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Security & Tenancy](./SECURITY-AND-TENANCY.md), [Data Model](./DATA-MODEL.md), [Domain Model](./DOMAIN-MODEL.md), [Platform & Operations](./PLATFORM-AND-OPERATIONS.md), [User Experience](./USER-EXPERIENCE.md), [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/TECHNICAL-SPEC.md), [Implementation Plan](../03-delivery/IMPLEMENTATION-PLAN.md)
**Requirements covered:** XA-01 (security audit log), XA-02 (user analytics), XA-03 (audit and usage reporting), XA-04 (tamper evidence and retention), plus TM-12 (immutable audit trail) and AI-10 (AI actions attributable)

Matt's direction (2026-09-04): XMS must be able to report on everything that happens in the application, for security and to understand how people use the system. This document fixes how that is captured, stored, protected, and reported, once, so every module emits into the same pipeline instead of inventing its own logging.

---

## 1. Principles

1. **One taxonomy, three streams.** Everything that happens is an event with the same envelope (who, what, where, when, in which account, under which request). The streams differ only in what they record: **domain audit** (what changed in the data), **security events** (who got in, who was refused, who reached what), **usage events** (what people did on the screens and the API).
2. **Nothing is sampled, nothing is dropped silently.** Security and domain audit are written in the same transaction as the thing they describe. Usage events are batched but acknowledged; a failed batch is retried from the client and counted when lost.
3. **Append-only and tamper-evident.** No update or delete on any event table; a daily hash digest is written to S3 with Object Lock so a modified history can be detected.
4. **Reportable by anyone with the permission, without engineering.** Search, filters, saved queries, dashboards and exports on the events themselves, plus a documented SQL surface for the analysts.
5. **Privacy by design.** Events carry identifiers and structured facts, never free text from tickets or emails; portal-user analytics obey the account's setting and the DPA; retention is a policy, not an accident.
6. **Correlated end to end.** Request id, trace id, session id and user id tie a click in the browser to the API call, the database change, the outbox row, the connector delivery and the Axel turn.

## 2. The three streams

| Stream | Table | Written by | Grain | Examples |
|---|---|---|---|---|
| Domain audit | `acct.audit_events` (exists, [Data Model](./DATA-MODEL.md)) | Every domain service in the same transaction as the change | One row per field change or lifecycle event on an account-scoped entity | ticket state Open to In progress by user U; time entry created; article published; contract rate card version 3 activated; AI suggestion accepted |
| Security events | `sys.security_events` (new; operator-scoped, `account_id` nullable) | The guard, the data layer, the adapter, the worker | One row per security-relevant decision | sign-in success or failure, token type used, session exchange with the harness, permission denied, isolation denial (row filtered by RLS on a direct-id read), API client key used, webhook signature failure, rate limit hit, admin configuration change, export produced, attachment downloaded, AI switch changed, kill switch tripped, offboarding step |
| Usage events | `rpt.usage_events` (new; `account_id` nullable, partitioned monthly) | The frontend telemetry client and the API request middleware | One row per screen view, named action, search, or API request | Queue viewed with view "Breached"; ticket record opened; "Log time" completed in 4.2 seconds; search "azure files" with 3 results; portal "This solved it" clicked; API `POST /v1/tickets` 201 in 140 ms by principal kind internal |

The existing `acct.audit_events` stays the system of record for "what changed"; this document does not move it. Security and usage are new tables in the operator (`sys`) and reporting (`rpt`) schemas because they must be queryable across accounts by the operator, while still carrying `account_id` for account-scoped reporting and portal isolation.

## 3. Event envelope (shared by all three)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `occurred_at` | timestamptz | Server clock at write; client time kept in `attrs.client_ts` for usage events |
| `stream` | text | `audit`, `security`, `usage` (present in the unified view) |
| `event_type` | text | Dotted taxonomy from the catalog in §4, e.g. `auth.signin.failed`, `ticket.transition`, `screen.view` |
| `account_id` | uuid null | Null for operator-only events (an administrator editing a global catalog) |
| `actor_kind` | text | `user`, `portal_user`, `api_client`, `system`, `ai`, `sync`, `anonymous` |
| `actor_id` | text | Opaque id; never a foreign key across the isolation boundary |
| `actor_name` | text null | Denormalised for reading |
| `principal_kind` | text null | `internal`, `portal`, `api_client`, `harness` |
| `session_id` | text null | Clerk session id or the portal session id |
| `request_id` | text null | From the API; the browser sends the id it received on the response that triggered the event |
| `trace_id` | text null | OpenTelemetry trace id |
| `correlation_id` | text null | The domain correlation id used by the outbox and connectors |
| `entity_kind`, `entity_id` | text null | Ticket, article, contract, account, user, connector instance, report pack |
| `outcome` | text | `success`, `denied`, `failed`, `withheld` |
| `attrs` | jsonb | Stream-specific structured facts (old and new value for audit; route, status, latency for API usage; screen, view, filter names, result counts for screen usage; token type, reason for security). No free text from tickets, emails or articles |
| `ip_hash`, `user_agent_family`, `geo_country` | text null | Security and usage only; IP is hashed with a rotating daily salt, never stored raw |
| `app_version` | text | Build tag |

## 4. Event catalog (the taxonomy)

The catalog lives in `backend/src/contracts/events.ts` as a typed union so an unknown event type is a build error, and it is published to the Admin screens as the filter vocabulary.

### 4.1 Security events (`sys.security_events`)

| Group | Event types |
|---|---|
| Authentication | `auth.signin.success`, `auth.signin.failed`, `auth.signout`, `auth.token.rejected` (reason: expired, bad audience, bad issuer, garbage), `auth.mfa.challenged`, `auth.mfa.failed`, `auth.session.exchanged` (harness session token minted), `auth.apikey.used`, `auth.apikey.rejected`, `auth.invite.sent`, `auth.invite.accepted` |
| Authorisation | `authz.permission.denied` (route, permission), `authz.realm.denied` (portal token on internal route or the reverse), `authz.account.denied` (no grant), `authz.isolation.filtered` (a direct-id read returned nothing under RLS, the strongest cross-account probe signal), `authz.record_rule.denied` |
| Administration | `admin.user.role_changed`, `admin.user.grants_changed`, `admin.user.deactivated`, `admin.role.changed`, `admin.config.changed` (kind, version), `admin.account.created`, `admin.account.settings_changed` (which keys), `admin.account.ai_switch_changed`, `admin.account.isolation_tier_changed`, `admin.connector.mode_changed`, `admin.connector.kill_switch`, `admin.map.activated`, `admin.alias.disabled`, `admin.offboarding.step` |
| Data movement | `data.export.produced` (view or report, row count, checksum), `data.attachment.downloaded`, `data.attachment.quarantined`, `data.report_pack.sent` (recipients count), `data.billing_export.delivered`, `data.import.batch_loaded`, `data.webhook.delivered` |
| Abuse and integrity | `abuse.rate_limited`, `abuse.webhook.bad_signature`, `abuse.email.loop_suspected`, `abuse.upload.rejected` (MIME, size), `integrity.digest.written`, `integrity.digest.mismatch` |
| AI | `ai.turn.started`, `ai.turn.failed`, `ai.suggestion.withheld` (reason), `ai.egress.redacted` (categories redacted, counts only) |

### 4.2 Usage events (`rpt.usage_events`)

| Group | Event types | Attributes |
|---|---|---|
| Screens | `screen.view`, `screen.leave` | `screen` (from the route registry: `queue`, `ticket`, `portal.home`), `view_name`, `duration_ms` on leave, `referrer_screen` |
| Actions | `action.completed`, `action.abandoned` | `action` (`ticket.create`, `ticket.transition`, `time.log`, `reply.send`, `note.add`, `solution.link`, `article.publish`, `dispatch.assign`, `export.run`, `report.approve`, `portal.request.submit`, `portal.solved_it`), `duration_ms` from first interaction, `via` (`click`, `shortcut`, `palette`, `axel_chip`) |
| Search | `search.run` | `scope` (global, solutions, portal), `term_hash`, `term_length`, `result_count`, `clicked_rank` |
| Axel | `axel.suggestion.shown`, `axel.suggestion.decided` (accepted, edited, rejected), `axel.panel.opened`, `axel.turn.completed` | capability, confidence bucket, time to decision |
| API | `api.request` | `route` (templated, never the raw path with ids), `method`, `status`, `latency_ms`, `principal_kind`, `bytes_out` bucket |
| Errors seen by users | `ui.error.shown` | `code`, `screen`, `action` |

Rules: search terms are stored as a salted hash plus length and result count, not the text (the "searches with no results" report uses the hash to group, and an administrator can opt an account into storing terms for knowledge-gap analysis, recorded as a setting change). No event ever carries ticket titles, descriptions, comments, article bodies or email content.

### 4.3 Domain audit (`acct.audit_events`)

Unchanged in shape; this document adds the requirement that every domain event type is also registered in the catalog so the unified view and the Admin filters know it.

## 5. Capture

### 5.1 Backend

- **Security interceptor and guard hooks.** The composed guard emits `auth.*` and `authz.*` events on every decision, including successes for sign-in and session exchange (successes are needed for "who accessed what" reports; they are cheap). The data layer emits `authz.isolation.filtered` when a by-id read inside a granted-account session returns no row for an id that exists (checked with a `SECURITY DEFINER` existence function that returns only a boolean).
- **API usage middleware.** Every request writes one `api.request` usage row asynchronously after the response (buffered in memory, flushed every second or 500 rows to the database through the worker queue, never blocking the request; a full buffer is counted and alarmed, not dropped silently).
- **Domain services** already write `acct.audit_events`; administrative services additionally write the matching `admin.*` security event in the same transaction.
- **Worker** emits `data.*`, `abuse.*`, `integrity.*` and connector events from the handlers.
- **Axel adapter** emits `ai.*` security events and the suggestion usage events.

### 5.2 Frontend

- `frontend/lib/telemetry`: a small client that queues events, batches them to `POST /v1/telemetry` every 10 seconds or 50 events, uses `fetch` with `keepalive` on unload (not `sendBeacon`, which cannot carry the bearer), retries with backoff, and stops when the account setting or the user's role forbids usage analytics.
- Screen views come from the route registry (each route declares its `screen` id), actions from a `useTrack(action)` hook wrapped around the house buttons and the command palette, searches from the omnibox and the portal search, errors from the error boundary.
- The telemetry client attaches `request_id` of the last API response it saw, so a click and its API call correlate.
- Portal: only `screen.view`, `action.completed` for submit, solved-it and comment, and `search.run` are emitted, and only when the account setting `usage_analytics_portal` is on.

### 5.3 Ingestion endpoint

`POST /v1/telemetry` accepts up to 200 events per batch from an authenticated principal, validates each against the catalog, stamps server fields (actor, principal kind, account ids from the Principal, never from the client), drops events for accounts the principal is not granted, and enqueues to the `telemetry` SQS queue; the worker writes `rpt.usage_events` in bulk. Rate limited per principal.

## 6. Storage and protection

| Concern | Decision |
|---|---|
| Tables | `sys.security_events` and `rpt.usage_events` partitioned by month; `acct.audit_events` as today. Append-only triggers on all three. Indexes on `(occurred_at)`, `(account_id, occurred_at)`, `(actor_id, occurred_at)`, `(event_type, occurred_at)`, `(request_id)`, `(entity_kind, entity_id)` |
| Isolation | `sys.security_events` readable only by `dms_app` with the `audit:read` permission (operator scope); rows with `account_id` are also exposed to account owners through an RLS-policed view `acct.security_events_v`. `rpt.usage_events` has RLS on `account_id` for account-scoped reports and an operator policy for portfolio reports. The portal role has no grant on any event table |
| Hot retention in PostgreSQL | Security 24 months, usage 13 months, domain audit life of the account plus contractual retention; older partitions detached after export |
| Cold storage | A nightly worker job exports the previous day's partitions of all three streams to S3 as Parquet under `audit/<stream>/<yyyy>/<mm>/<dd>/`, in a bucket with versioning and Object Lock (compliance mode, retention per policy); AWS Glue catalog and Athena provide SQL over the archive without any new vendor |
| Tamper evidence | The nightly job computes a SHA-256 over the day's rows per stream (ordered by id), chains it with the previous day's digest, writes `integrity.digest.written` with the value, and stores the digest file in the locked bucket. A weekly verification job recomputes and raises `integrity.digest.mismatch` plus an alarm on any difference |
| Backups | Covered by RDS point-in-time recovery and S3 versioning; the archive bucket is replicated to the second region when residency allows |
| Volume assumptions | 40 accounts, 60 internal users, 500 portal users: roughly 200k usage rows and 20k security rows per day at steady state, about 3 GB per month uncompressed; comfortable in PostgreSQL with monthly partitions and the nightly export |

## 7. Reporting

### 7.1 Admin screens

- **Audit search** (exists in the UX catalog, extended): one search over the unified view `rpt.events_v` (all three streams) with the condition builder (stream, event type, actor, account, entity, outcome, date range, request id), the record drawer showing the full envelope and, for domain audit, old and new values, "Show this request" pivoting to every event with the same request id, saved queries, export to CSV with a `data.export.produced` event of its own.
- **Security dashboard**: sign-in failures by user and IP hash, permission and realm denials by route, isolation-filtered probes by actor (the top signal for a compromised or curious account), API client usage, admin changes timeline, exports and downloads by user, integrity status (last digest, last verification).
- **Usage dashboard**: daily and weekly active users by role and by account; feature adoption (which actions each role uses, first-use dates); the core-loop funnel (ticket opened, first reply, time logged, solution linked, resolved) with drop-off; time to complete key actions (create, reply, log time) by percentile; searches with no results (knowledge gaps) and top clicked results; Axel suggestion acceptance by capability; portal deflection rate and portal active users; error rate seen by users by screen; API usage by client and route.
- **Account view**: the same usage and security panels filtered to one account, visible to its account owner.

### 7.2 Exports and self-service

- Every dashboard tile exports its rows; the Athena tables are documented for analysts with the same names as the PostgreSQL tables; a read-only replica or the archive is the target for heavy queries, never the primary.
- The measures feed the [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/TECHNICAL-SPEC.md) catalog (utilisation and adoption measures) and, in Phase 4, the natural-language query capability (AI-15) reads the same catalog.

### 7.3 Alerts from events

| Signal | Alarm |
|---|---|
| More than N `auth.signin.failed` for one user or one IP hash in 10 minutes | Security channel; account lockout is Clerk's job, the alert is ours |
| Any `authz.isolation.filtered` burst from one actor | Security channel, immediate |
| `abuse.webhook.bad_signature` repeated from one source | Security channel |
| `integrity.digest.mismatch` | Pager |
| Telemetry buffer overflow or ingestion lag over 5 minutes | Operations channel |
| Usage drop (weekly active users down 30 percent week over week) | Product channel |

## 8. Privacy and compliance

- **Data minimisation.** No ticket, email, article or comment content in any event; search terms hashed by default; IP hashed with a daily salt; user agents reduced to family and major version.
- **Portal users.** Usage analytics per account setting (`usage_analytics_portal`, default on for internal-only pilot accounts, decided per DPA), security events always on (they protect the client too); a portal user can request their event export through the account admin; the retention clock follows the account's DPA.
- **Internal users.** Usage analytics are for product improvement and support operations, not individual performance management; the Usage dashboard aggregates by role by default and requires `analytics:read-individual` to see a named user's activity; that permission's use is itself a security event.
- **Access to the streams.** `audit:read` (operator security and audit search), `analytics:read` (aggregated usage), `analytics:read-individual`, `audit:export`. Account owners see their account's slices.
- **Right to erasure.** Events are immutable; erasure is handled by pseudonymisation of `actor_id` and `actor_name` for the subject across all three streams by a worker job that writes an `admin.user.pseudonymised` event, keeping the history intact.
- **Residency.** Event tables live with the account's database (shared or dedicated tier); the archive bucket follows the residency region.

## 9. What each module must do

| Module | Obligation |
|---|---|
| Every backend module | Register its domain audit event types and any admin events in the catalog; write admin security events in the same transaction as configuration changes |
| Frontend | Declare a `screen` id per route; wrap key actions with `useTrack`; emit search and error events; respect the account setting and role rules |
| Accounts & Administration | Own the `usage_analytics_portal` and `store_search_terms` settings and the permissions above; the Audit search, Security and Usage screens live under Admin |
| Ticket Management | Keep `acct.audit_events` as is; add `authz.record_rule.denied` from the record rules |
| Client Portal | Emit the reduced portal event set; no event tables in the portal role |
| Email, ServiceNow, Integrations | Emit `data.*` and `abuse.*` from the worker handlers |
| Axel AI | Emit `ai.*` and the suggestion usage events |
| Dashboards & Report Packs | Add adoption and utilisation measures sourced from usage events |
| Platform & Operations | The telemetry queue, the archive bucket with Object Lock, Glue and Athena, the alarms in §7.3 |

## 10. Build order (folded into the Implementation Plan)

1. Phase 1 Sprint 3: `sys.security_events` with the guard hooks and the append-only trigger, next to the isolation suite (the suite asserts that a cross-account probe writes `authz.isolation.filtered`).
2. Phase 1 Sprint 5: the event catalog in `contracts`, the API usage middleware, `rpt.usage_events`, the `telemetry` queue and ingestion endpoint, the frontend telemetry client with screen views on every route.
3. Phase 1 Sprint 7: nightly Parquet export, digest chain, Object Lock bucket, alarms.
4. Phase 2 Sprint 11: Audit search screen over the unified view with the condition builder (reuses the Queue grammar).
5. Phase 2 Sprint 19: Security and Usage dashboards next to the operations dashboard; adoption measures in the catalog.
6. Phase 3 Month 1: Glue and Athena over the archive, analyst documentation, account-owner views, pseudonymisation job, weekly digest verification.
7. Phase 4: natural-language query over the event measures (AI-15).

## 11. Open questions

- **Store search terms by default?** Default: hashed only; per-account opt-in to store terms for knowledge-gap analysis.
- **Individual-level usage reporting for internal users?** Default: aggregated by role; named-user drill-down behind `analytics:read-individual` and logged.
- **Archive query tool.** Default: Athena (no new vendor); revisit QuickSight if analysts need dashboards beyond the Admin screens.
- **Success sign-in events volume.** Default: keep them; they are the basis of the "who accessed what" report and the volume is small.
