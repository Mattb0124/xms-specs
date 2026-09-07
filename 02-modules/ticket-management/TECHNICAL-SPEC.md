# Technical Spec: Ticket Management

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Design System](../../01-architecture/DESIGN-SYSTEM.md), [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md), [Solution Knowledge Base](../knowledge-base/TECHNICAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md), [Client Portal](../client-portal/TECHNICAL-SPEC.md), [Email Intake & Outbound](../email-intake/TECHNICAL-SPEC.md)
**Requirements covered:** TM-02, TM-03, TM-04, TM-05, TM-07, TM-09, TM-10, TM-11, TM-12, TM-13, TM-14, TM-15, TM-16, TM-18
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Conventions, schemas, RLS mechanics, append-only triggers | [Data Model §1 to §3](../../01-architecture/DATA-MODEL.md) | Every table here is `acct.*` with RLS; audit, pauses and notifications follow the append-only rule |
| Business calendar engine | [Accounts & Administration Technical §3.2](../accounts-and-administration/TECHNICAL-SPEC.md) `backend/src/domain/calendar` | The SLA engine calls `addBusinessMinutes` and `businessMinutesBetween` (TM-05, TM-06) |
| `ConfigResolver` (state machines, matrix, SLA defaults, resolution codes) | [Accounts & Administration Technical §3.4](../accounts-and-administration/TECHNICAL-SPEC.md) | Resolves the active version per account; this module stamps `config_version_id` on tickets |
| Outbox | [Integration Patterns §2](../../01-architecture/INTEGRATION-PATTERNS.md) | Every mutation writes an outbox row for notifications, sync and snapshots |
| Proven SLA math: stamp, pause and resume shift, latch-before-pause, response-met on first public non-creator comment, priority restamp | studio `app/modules/xms_ticketing/service.py` (verified 2026-09-04) | Ported into `backend/src/domain/sla` and generalized to business minutes |
| Breach sweeper: shared latch, `FOR UPDATE SKIP LOCKED`, batch cap 500, five-minute cadence, prefilter mirrors latch preconditions | studio `app/modules/xms_ticketing/sweeper.py` (verified 2026-09-04) | `backend/src/worker` `sla.sweep` job |
| Server-derived priority, resolution codes, close discipline | studio migrations 091 and 092; `web-ui/components/aix-v3/xms/vocab.ts` `derivePriority`, `RESOLUTION_CODES` (verified 2026-09-04) | Matrix in `backend/src/domain/priority`; codes in the catalog |
| Attachment cap and MIME allowlist; presigned PUT cannot carry `content-length-range` | studio `xms_ticketing/service.py` `MAX_ATTACHMENT_BYTES`, `ALLOWED_ATTACHMENT_TYPES`, commit `019dec8e` residual note (verified 2026-09-04) | XMS uses presigned POST with `content-length-range` |
| S3 checksum setting for presigned uploads | `app-api/src/files/services/file-storage.service.ts` `requestChecksumCalculation: 'WHEN_REQUIRED'` (verified 2026-09-04) | Copied verbatim with its comment |
| Notification triad: identity-key recipient, collapse key, `mutedAt`, TTL, copy file | `app-api/src/api/v3/notifications/*` (verified 2026-09-04) | `acct.notifications`, `acct.watchers`, `notification-copy.ts` |
| Activity diff capture | `app-api/src/api/v3/activity/versioning/diff.ts` (verified 2026-09-04) | `AuditService.diff(before, after)` |
| Optimistic transition with rollback on 409 | `web-ui/redux/services/xmsApi.ts:606-667` (verified 2026-09-04) | `ticketsApi.transition` |
| Screens and vocabulary | `web-ui/components/aix-v3/xms/QueueTab.tsx`, `NewTicketPage.tsx`, `TicketDrawer.tsx`, `DispatchTab.tsx`, `atoms.tsx`, `slaTime.ts` (verified 2026-09-04) | Ported to `frontend` |
| POC cross-tenant `queue_id` leak at create | POC audit P1 (studio `service.py:733`) | The RLS `WITH CHECK` plus service-level account assertions on every referenced id make this class of bug impossible |
| Golden route-table snapshot | studio `tests/golden/route_table.json` (verified 2026-09-04) | Route and permission snapshot |

Cross-module dependency and ordering: Accounts & Administration Phase 1 (accounts, calendars, groups, users) must be deployed first; Knowledge Base Phase 2 (articles) and Time & Budget Phase 2 (time entries, contracts) are required before the close discipline can be enforced, so Phase 1 of this module ships with the resolution rules configured off.

## 2. Data model

### 2.1 `acct.tickets`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | RLS |
| `number` | bigint | from sequence `acct.ticket_number_seq`; display `CS` + 7 digits (ADR-10) |
| `type` | text | CHECK in (incident, service_request, change, problem, project_task) |
| `state` | text | validated against the resolved state machine in the service, not by CHECK (machines are data) |
| `state_machine_version_id` | uuid | stamped from `ConfigResolver` at create; type change from New restamps |
| `short_description` | text (300) | |
| `description` | text null | |
| `category` | text null | |
| `impact`, `urgency` | text null | CHECK in (high, medium, low) |
| `priority` | text | CHECK in (p1, p2, p3, p4); derived unless `priority_overridden` |
| `priority_overridden` | boolean | audit carries the matrix value replaced |
| `matrix_version_id` | uuid null | |
| `source` | text | CHECK in (portal, email, internal, api, sync, import); immutable |
| `requester_contact_id` | uuid null | `acct.contacts` |
| `group_id` | text null | opaque id into `op.assignment_groups` |
| `assignee_id`, `assignee_name` | text null | opaque user id plus denormalised name |
| `contract_id` | uuid | FK `acct.contracts` ON DELETE RESTRICT (entitlement anchor) |
| `configuration_item_id` | uuid null | FK `acct.configuration_items` |
| `ticket_group_id` | uuid null | FK `acct.ticket_groups` (project or change window) |
| `out_of_scope` | text | CHECK in (none, flagged, approved, declined); default none |
| `out_of_scope_detail` | jsonb null | reason, estimated minutes, client note, decided by, decided at |
| `resolution_code` | text null | from catalog; `no_solution` flag looked up at close |
| `resolution_notes` | text null | |
| `time_exemption_reason` | text null | when resolved with zero logged time |
| `external_refs` | jsonb | e.g. `{"servicenow": "CS0012345"}` (migration and sync) |
| `reopen_count` | integer | |
| `first_response_at`, `resolved_at`, `closed_at`, `cancelled_at` | timestamptz null | |
| `sla_response_breached`, `sla_resolution_breached` | boolean | latched copies of the clock rows for cheap list reads |
| `search` | tsvector generated | short_description, description, category |
| `created_by`, `created_by_name` | text | |
| `created_at`, `updated_at`, `version` | | optimistic concurrency |

### 2.2 `acct.sla_clocks` and `acct.sla_pauses`

`acct.sla_clocks`: `id`, `account_id`, `ticket_id` FK CASCADE, `kind` (response, resolution), `policy_ref` (contract policy id or default version id), `calendar_id` (the calendar it started on), `target_minutes`, `started_at`, `due_at`, `paused_at null`, `paused_total_minutes`, `met_at null`, `breached_at null` (latch), `created_at`, `updated_at`. Unique (ticket_id, kind).

`acct.sla_pauses` (append-only): `id`, `account_id`, `ticket_id`, `clock_id null` (null means both clocks), `reason` CHECK in (awaiting_client, awaiting_third_party, scheduled_window), `note`, `started_at`, `ended_at null`, `excluded_minutes null`, `started_by`, `ended_by`. The end is written as a new row update exception: `ended_at` and `excluded_minutes` are the only columns the append-only trigger allows to move from null to a value, once.

### 2.3 `acct.comments` and `acct.work_notes`

Both: `id`, `account_id`, `ticket_id` FK CASCADE, `author_kind` (user, portal_user, system, ai), `author_id`, `author_name`, `body` (markdown), `body_html` (sanitised render with inline image references), `source` (internal, portal, email, sync, ai), `external_ref jsonb null`, `search tsvector`, `created_at`. Comments add `is_first_response boolean`. No `visibility` column exists anywhere (Domain Model invariant 2). Edits are not offered; a correction is a new message referencing the old (`corrects_id`).

### 2.4 `acct.attachments`

`id`, `account_id`, `ticket_id`, `comment_id null`, `work_note_id null`, `file_name`, `content_type`, `size_bytes`, `s3_key` (`accounts/<account_id>/tickets/<ticket_id>/<uuid>-<name>`), `scan_state` CHECK in (pending, clean, quarantined), `scan_detail jsonb null`, `origin` (internal, portal, email, sync), `visibility` (public, internal; derived from where it is attached), `uploaded_by`, `uploaded_by_name`, `created_at`, `deleted_at null`.

### 2.5 Links, groups, views, watchers, notifications, audit

| Table | Columns (beyond id, account_id, timestamps) | Notes |
|---|---|---|
| `acct.ticket_links` | `from_ticket_id`, `to_ticket_id`, `type` CHECK in (parent, related, duplicate, blocks), `created_by` | unique (from, to, type); inverse derived in queries; a cycle check for parent and blocks in the service |
| `acct.ticket_groups` | `kind` (project, change_window), `name`, `owner_id`, `starts_at`, `ends_at`, `freeze_windows jsonb`, `status` | |
| `acct.ticket_group_members` | `group_id`, `ticket_id` | unique |
| `acct.saved_views` | `owner_id`, `name`, `definition jsonb` (conditions, columns, sort), `share` CHECK in (private, group, account), `share_ref`, `deleted_at` | |
| `acct.watchers` | `ticket_id`, `user_id` (identity key), `source` (creator, assignee, commenter, explicit), `muted_at null` | unique (ticket_id, user_id); unfollow sets `muted_at` |
| `acct.notifications` | `recipient_id` (identity key), `type`, `title`, `body`, `target_kind`, `target_id`, `collapse_key null`, `count`, `read_at`, `delivered_email_at`, `link` | index (recipient_id, updated_at desc); partial unique on (recipient_id, collapse_key) where read_at is null |
| `acct.audit_events` | `entity_kind`, `entity_id`, `ticket_id null` (denormalised for the Activity tab), `event_type`, `field null`, `old_value jsonb`, `new_value jsonb`, `actor_kind`, `actor_id`, `actor_name`, `correlation_id`, `ai_suggestion_id null`, `created_at` | append-only; partitioned monthly by `created_at` |

```sql
create sequence acct.ticket_number_seq start 1000001;
create unique index ux_tickets_number on acct.tickets (number);
create index ix_tickets_open on acct.tickets (account_id, state, updated_at desc)
  where state not in ('closed', 'cancelled');
create index ix_tickets_assignee_open on acct.tickets (assignee_id) where state not in ('closed', 'cancelled');
create index ix_tickets_search on acct.tickets using gin (search);
create index ix_tickets_number_trgm on acct.tickets using gin ((('CS' || lpad(number::text, 7, '0'))) gin_trgm_ops);
create index ix_sla_clocks_due_live on acct.sla_clocks (due_at)
  where met_at is null and breached_at is null and paused_at is null;
create index ix_audit_ticket on acct.audit_events (ticket_id, created_at);
create index ix_comments_ticket on acct.comments (ticket_id, created_at);
create index ix_work_notes_ticket on acct.work_notes (ticket_id, created_at);

-- RLS: operator policy on every table (pattern from Data Model §3); portal policy only where the portal may read
alter table acct.tickets enable row level security; alter table acct.tickets force row level security;
create policy acct_isolation_operator on acct.tickets
  using (account_id = any (current_setting('xms.account_ids', true)::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids', true)::uuid[]));
create policy acct_isolation_portal on acct.tickets to xms_portal
  using (account_id = current_setting('xms.account_id', true)::uuid);
revoke all on acct.work_notes from xms_portal;
revoke all on acct.audit_events from xms_portal;
revoke all on acct.sla_pauses from xms_portal;
grant select on acct.ticket_timeline_public to xms_portal;  -- view: comments + public attachments + state changes only

-- append-only guard (shared function from Data Model §1) applied to audit_events, sla_pauses, notifications history
create trigger trg_audit_events_append_only before update or delete on acct.audit_events
  for each row execute function sys.raise_append_only();
```

Service logic that is not obvious:

- **Numbering** uses the sequence; gaps are acceptable; the unique index is the backstop (the POC's `FOR UPDATE` plus retry is unnecessary with a sequence).
- **Referenced ids are asserted in-account** (`contract_id`, `configuration_item_id`, `ticket_group_id`, link targets) by a service helper that loads the row under the same RLS session; a foreign id that RLS hides raises not-found (404), never 403.
- **Clock rows are the truth; the boolean columns on `tickets` are denormalised** in the same transaction for list reads and the portfolio snapshot.
- **`ticket_timeline_public`** is a `SECURITY INVOKER` view unioning comments, public attachments and state-change audit events with the state labels; it is the only timeline the portal role can read.

## 3. Producers / core logic

### 3.1 `backend/src/domain/tickets`

- `StateMachine` value object loaded from a config version: `canTransition(from, to, principal)`, `requirements(to)` (required fields, pause reason, resolution, approval), `effects(to)` (pause, resume, resolve, close, reopen, response-met).
- `PriorityMatrix.derive(impact, urgency)` with the default grid and per-account override body.
- `CloseDiscipline.check(ticket, timeLoggedMinutes, solutionLink, code)` returns the list of missing items; used by the transition service and shown in the Resolve dialog.
- `LinkRules.assertAcyclic(graph, newLink)`.

### 3.2 `backend/src/domain/sla`

- `startClocks(policy, calendar, now)`, `pause(clock, now, reason)`, `resume(clock, pause, now)` (computes `excluded_minutes = businessMinutesBetween(started, ended)` and shifts `due_at = addBusinessMinutes(due_at, excluded)`), `latch(clock, now)` (idempotent; returns whether it newly latched), `markMet(clock, now)`, `restampForPriority(clock, newTargetMinutes, now)` (remaining window from the moment of change), `remaining(clock, now)` for API responses.
- **Ordering rule kept from the POC:** on any mutation, `latch` runs before `pause` so a blown clock cannot be rescued by pausing after the fact; and `latch` runs after `resume` so resumed time counts.

### 3.3 `backend/src/tickets/*`

- `TicketsService.create` (resolve machine, matrix, policy and calendar through `ConfigResolver` and the contract; assert contract period open; start clocks; stamp versions; audit `created`; outbox `ticket.created`).
- `TicketsService.transition` (the only state writer): loads with `FOR UPDATE`, validates with `StateMachine`, runs `CloseDiscipline` when entering a resolved or fulfilled state, applies clock effects, writes pause rows, latches, audits every changed field via `AuditService.diff`, writes outbox events (`ticket.transitioned`, `sla.paused`, `sla.resumed`, `sla.breached`), updates with `version` check; returns 409 with a typed body (`invalid_transition`, `missing_requirements`, `stale_version`, `blocked_by_flag`).
- `TicketsService.patch` (properties; priority re-derivation or override; group and assignee with in-account assertions; notifications on assignment).
- `CommentsService.addPublic` (sets `is_first_response` and calls `markMet` when the author is an operator user and no response yet), `WorkNotesService.add`, both stripping HTML to the sanitiser allowlist and rewriting inline image references to attachment ids.
- `AttachmentsService.presign` (presigned POST with `content-length-range` and `Content-Type` condition; MIME and extension allowlist; creates the row as `pending`), `confirm`, `downloadUrl` (only `clean`), `delete` (soft).
- `LinksService`, `GroupsService` (change window freeze checks in Phase 4), `ViewsService`, `WatchersService`, `NotificationsService` (collapse semantics), `OutOfScopeService` (flag, approve, decline; approval requires `tickets:approve-scope` and not the flagger).
- `SearchService.query` (tsquery over tickets, comments and, for internal principals, work notes and attachment names; results ranked by `ts_rank` then updated).

### 3.4 Worker jobs (`backend/src/worker`)

| Job | Trigger | Behaviour |
|---|---|---|
| `sla.sweep` | every 5 minutes, all instances | `SELECT ... FROM acct.sla_clocks WHERE due_at < now() AND met_at IS NULL AND breached_at IS NULL AND paused_at IS NULL LIMIT 500 FOR UPDATE SKIP LOCKED`, per account set in batches, calls the same `latch` then audit, outbox and notification, per the studio sweeper |
| `sla.at_risk` | every 5 minutes | Clocks with less than 25 percent of the window remaining and no `at_risk_notified_at` get one notification |
| `notifications.deliver` | outbox `notification.created` | Email digest per user preference (immediate for assignment and breach, hourly digest otherwise) through the Email module |
| `attachments.scan_result` | S3 event via SQS (GuardDuty result) | Sets `scan_state`; on quarantine moves the object to the quarantine prefix, audits, notifies uploader and admins |
| `tickets.reopen_window` | daily | Closes the reopen window flag on resolved tickets older than the account's window |
| `tickets.bulk` | outbox `tickets.bulk_requested` (Phase 4) | Applies each action per ticket through `TicketsService`, records per-record outcome |

## 4. API routes

All under `/v1`; principal kinds: `internal` (I), `portal` (P, only routes marked), `harness` (H, read routes and `propose_*` through the MCP tools). Lists paginate with `?cursor=&limit=` (default 50, max 200) and accept a view id or inline conditions. `POST` accepts `Idempotency-Key`.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/tickets` | `tickets:view` (I, H) | List with conditions, sort, columns; returns computed SLA view per row |
| POST | `/tickets` | `tickets:create` (I); `portal:submit` (P) | Create; portal creates through the form definition |
| GET | `/tickets/{id}` | `tickets:view` (I, H); `portal:view-org-tickets` or own (P) | Record; portal gets the public projection only |
| PATCH | `/tickets/{id}` | `tickets:work` (I) | Properties with `version`; priority override needs `tickets:override-priority` |
| POST | `/tickets/{id}/transitions` | `tickets:work` (I); `portal:submit` for cancel and confirm-close (P) | `{to, reason?, resolution?, exemption?}`; 409 typed errors |
| GET | `/tickets/{id}/transitions` | as record | Allowed transitions for this principal (drives the footer) |
| GET/POST | `/tickets/{id}/comments` | `tickets:view` / `tickets:work` (I); `portal:comment` (P) | Public comments |
| GET/POST | `/tickets/{id}/work-notes` | `tickets:view` / `tickets:work` (I) | Work notes; 403 for P before any lookup |
| GET | `/tickets/{id}/timeline` | as record | Interleaved comments, work notes (I only), audit, pauses, time entries |
| POST | `/tickets/{id}/attachments/presign` | `tickets:work` (I); `portal:submit` (P) | Presigned POST |
| POST | `/tickets/{id}/attachments/{aid}/confirm` | same | Marks uploaded |
| GET | `/attachments/{aid}/download` | as record and `clean` | Presigned GET |
| DELETE | `/attachments/{aid}` | `tickets:work` (I) | Soft delete |
| GET/POST/DELETE | `/tickets/{id}/links` | `tickets:view` / `tickets:work` (I) | Links |
| POST | `/tickets/{id}/out-of-scope` and `/out-of-scope/decision` | `tickets:work`; decision `tickets:approve-scope` (I) | Flag, approve, decline (TM-11) |
| GET/POST, GET/PATCH | `/ticket-groups`, `/ticket-groups/{id}` | `tickets:work` (I) | Projects and change windows (TM-10) |
| PUT | `/ticket-groups/{id}/members` | `tickets:work` (I) | Reconcile membership |
| GET/POST, PATCH/DELETE | `/views`, `/views/{id}` | `tickets:view` (I) | Saved views (TM-15) |
| GET | `/search?q=` | `tickets:view` (I) | Full text across tickets, comments, notes, attachment names |
| GET/PUT | `/tickets/{id}/watchers/me` | `tickets:view` (I); P for own | Follow, unfollow (mute) |
| GET | `/notifications`, `/notifications/unread-count` | any (I, P) | Feed, cursor `before` |
| POST | `/notifications/read-all`, PATCH `/notifications/{id}/read` | any | Read state |
| POST | `/tickets/bulk` | `tickets:work` (I) (Phase 4) | Reassign, transition, tag; returns per-ticket outcome |
| GET | `/change-calendar?from=&to=` | `tickets:view` (I) (Phase 4) | Windows, freezes, conflicts |

Portal routes are the `/v1/portal/*` mirror defined in the Client Portal spec; they call the same services with the portal projection.

## 5. Cross-cutting concerns

- **Server owns the clocks.** Responses include `sla: {response: {dueAt, remainingMinutes, paused, breached, met}, resolution: {...}}` computed at read; the web only formats and counts down between polls (60-second list poll, focus refetch on the record). Authoritative breach is the latch, which the sweeper keeps within five minutes.
- **Work notes cannot leak:** separate table, portal role revoked, no public-direction outbox subscription accepts `work_note.created`, the timeline view for the portal is a fixed projection, exports of the portal projection reuse the same view.
- **Audit completeness:** `AuditService.diff` records every changed column on `tickets`; the `acct.audit_guard` trigger (Data Model §5) rejects a ticket update whose transaction wrote no audit event.
- **Concurrency:** `version` on tickets; the transition route locks the row; 409 `stale_version` carries the current version so the client can reload.
- **Idempotency:** `Idempotency-Key` stored with the response for 24 hours on create, comment and transition routes (email and sync retries hit these).
- **Isolation of referenced ids:** every id supplied by a client or a connector is loaded under the same RLS session before use; the POC's `queue_id` class of leak cannot occur.
- **Contract period enforcement:** create and time-relevant transitions check the contract's current period is open (Time & Budget owns the rule; this module calls it).

## 6. Web / client changes

- Routes in `frontend/app/(internal)/tickets/*`: list (`/tickets?view=`), dispatch (`/tickets/dispatch`), new (`/tickets/new`), record (`/tickets/CS0001234`), groups (`/tickets/groups/{id}`), change calendar (Phase 4).
- Components ported from the POC into `frontend/features/tickets/`: `QueueList` (from `QueueTab.tsx`: toolbar, condition builder, breadcrumb trail, stat strip, chips), `NewTicketRecord` (from `NewTicketPage.tsx`), `TicketRecord` (from `TicketDrawer.tsx`: record bar, properties, tabs, rail), `DispatchList`, `SlaBadge`, `SlaBar`, pills (from `atoms.tsx`), `slaTime.ts` display math with its tests, `vocab.ts` regenerated from `backend/src/contracts`.
- RTK slice `ticketsApi` with tags `Tickets(view)`, `Ticket(id)`, `Timeline(id)`, `Views`, `Notifications`; `transition` uses `updateQueryData` on both the list and the record with `patch.undo()` on 409 and a toast from the typed error body (the POC pattern, now with error handling the POC audit found missing); `patch` is pessimistic with a reload prompt on `stale_version`.
- Attachments: presigned POST upload component with progress and scan-state polling; the composer blocks send while any attachment is `pending` unless acknowledged.
- Notifications bell polls every 60 seconds; toasts for assignment and breach.
- Styling per [Design System](../../01-architecture/DESIGN-SYSTEM.md): `.xms-scope`, `--state-*` trios for SLA, priority and state pills.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/tickets-core` | Migrations for all tables in §2 with RLS; `backend/src/domain/tickets`, `sla`, `priority`; create, patch, transition, comments, work notes, audit, attachments with presign and scan job; routes; snapshot test | Accounts Phase 1 deployed; S3 and GuardDuty provisioned |
| 2 | `feature/tickets-web` | Queue, new record, record view, dispatch | 1 |
| 3 | `feature/tickets-sla-calendar` | Calendar-aware clocks, pauses as evidence, sweeper, at-risk job, notifications and watchers | Calendars from Accounts Phase 1 |
| 4 | `feature/tickets-views-links` | Condition builder persistence, saved views, search, links | 2 |
| 5 | `feature/tickets-close-discipline` | Resolution dialog, solution link, time check, templates | Knowledge Base Phase 2, Time & Budget Phase 2 |
| 6 | `feature/tickets-groups-scope` | Ticket groups, change approval gate, out-of-scope flag, priority override, reopen rules, external refs | Phase 3 |
| 7 | `feature/tickets-bulk-calendar` | Bulk actions, change calendar | Phase 4 |

Deploy order per release: db migration, worker, api, web.

## 8. Testing & verification

- **Domain (Jest):** state machines for all five types (every allowed and forbidden transition, required fields, portal restrictions); matrix default and override; `startClocks` and `addBusinessMinutes` on UK, Brazil and Australia calendars across weekends, holidays and DST; pause and resume shift exactly the excluded business minutes; latch-before-pause; resume-then-latch; `restampForPriority` from the moment of change; response-met only on operator public comment or in-progress transition; `CloseDiscipline` missing-item lists; link cycle detection.
- **Data layer (Testcontainers):** isolation suite for every table in §2; append-only trigger on audit events and pauses; `acct.audit_guard` rejects an unaudited ticket update; `ticket_timeline_public` returns no work notes under the portal role; sequence numbering under concurrent inserts yields unique keys.
- **HTTP (supertest):** anonymous and garbage tokens rejected on every route; portal token gets 403 on work notes before any lookup; foreign account ids return 404; transition 409 bodies typed; idempotent replays return the stored response; route and permission snapshot.
- **Worker:** sweeper latches exactly once per clock under two concurrent instances (`SKIP LOCKED`), writes one audit event and one notification; at-risk fires once; scan result quarantine flow.
- **Web (Vitest and Testing Library):** `slaTime` tones and labels (ported tests); condition builder serialises and round-trips a view; transition rollback on 409 restores both caches and shows the toast.
- **E2E (Playwright):** Functional §7 criteria: Friday-evening UK P2 due Monday; pause 90 business minutes; idle breach within five minutes (sweeper cadence shortened in test); resolve refused without time; portal sees two of five messages; quarantine placeholder; concurrent edit prompt; shared view visible to a colleague.

## 9. Risks / notes

- **Business-minute math edge cases** (DST transitions, split shifts, calendars changed mid-clock): clocks keep their starting calendar version; a calendar edit creates a new version and does not move live clocks; documented in the calendar editor.
- **Sweeper prefilter drift:** the WHERE clause must mirror `latch` preconditions (the studio sweeper's own warning); a unit test asserts both from one shared predicate.
- **Search cost** at 500k tickets: GIN indexes cover it; a dedicated search service is not planned.
- **Attachment scanning latency:** GuardDuty results can take minutes; the UI states "Scanning" rather than hiding the file; downloads wait.
- **Portal projection completeness:** every new client-visible field must be added to the projection view explicitly; a test enumerates columns the portal may see and fails on drift.
- **Auto-close and reopen rules** remain open questions; defaults are configurable per account so the pilot can tune them without a release.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
