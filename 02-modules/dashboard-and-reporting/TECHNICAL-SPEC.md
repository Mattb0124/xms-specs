# Technical Spec: Dashboards & Report Packs

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Design System](../../01-architecture/DESIGN-SYSTEM.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Axel AI Functionality](../ai-functionality/TECHNICAL-SPEC.md), [Test Strategy](../../03-delivery/TEST-STRATEGY.md)
**Requirements covered:** DR-01 to DR-10, AI-15 (data surface)
**Repos affected:** `backend/src/domain`, `backend/src/db`, `backend/src/contracts`, `backend`, `backend/src/worker`, `frontend`)

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| POC dashboard grammar | `web-ui/components/aix-v3/xms/DashboardTab.tsx` (310 lines), `atoms.tsx` (`InkBanner`, `TabHeader`), `XmsSkeleton.tsx` (verified 2026-09-04) | Layout to port: ScoreCard strip, ink banner, panels, pillar rail; the client-side aggregation over a 200-row cap is the defect XMS fixes by reading server measures |
| Studio dashboard aggregate | `os-aixelerator-studio` `feature/xms-ticketing` `app/modules/xms_ticketing/router.py:185` `GET /dashboard`, `service.py` (verified 2026-09-04) | The shape of a single aggregate payload (status counts, priority counts, compliance, per-contract burn, oldest unresolved); XMS splits it into the measure catalog |
| Polling cadence precedent | `web-ui/components/aix-v3/notifications/NotificationsBell.tsx:52` `pollingInterval: 60_000`; `web-ui/redux/services/xmsApi.ts` polls tickets and dashboard at 60 seconds (verified 2026-09-04) | DR-01 interval |
| Scheduler pattern | studio `app/modules/agent_harness/scheduler/routine_engine.py` (`FOR UPDATE SKIP LOCKED`, run row inserted in the claim transaction, watchdog for orphaned runs) (verified 2026-09-04) | Snapshot job and schedule runner in the XMS worker copy this shape |
| Report rendering in AIX | `app-api/src/reports/report.service.ts` (external Lambda via `LAMBDA_PPTX_URL`); harness `hackett_template.py` master with 48 layouts; no XLSX export utility; `xlsx` 0.18.5 import-only (verified 2026-09-04) | Rejected paths; XMS renders with `pptxgenjs` and `exceljs` in the worker (ADR-11) |
| Excel export recipe | `web-ui/components/aix-v3/opportunity/stages/project/requirements/exportRtm.ts` (SheetJS, two sheets: rows plus sources) (verified 2026-09-04) | The two-sheet shape (data plus provenance) is kept; library changed to `exceljs` |
| Connector framework | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) `connector.reports` queue, outbox, DLQ, replay | Pack delivery |
| Axel batch face | [AI Integration §3](../../01-architecture/AI-INTEGRATION.md), worker `axel.batch` queue | Narrative request |
| Domain package | `backend/src/domain` (measure definitions as pure functions over row sets, period math on calendars) | Single implementation of every measure used by API, worker and tests |
| Schemas | `rpt.daily_snapshots`, `rpt.portfolio_daily`, `acct.report_packs`, `acct.report_schedules`, `acct.report_runs`, `op.report_templates` per [Data Model §4](../../01-architecture/DATA-MODEL.md) | Owned tables |

Cross-repo dependency: none outside the XMS repositories except the narrative (harness through the adapter, optional with a templated fallback).

## 2. Data model

### 2.1 `rpt.daily_snapshots` (append-only, RLS)

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| account_id | uuid not null | RLS |
| snapshot_date | date not null | The account-local day the snapshot describes |
| taken_at | timestamptz not null | When computed |
| measure | text not null | Catalog key, for example `sla_resolution_attainment` |
| grain | jsonb not null default '{}' | Dimension values, for example `{"priority":"p1","ticket_type":"incident"}`; `{}` for account grain |
| numerator | numeric(14,4) null | For ratio measures |
| denominator | numeric(14,4) null | |
| value | numeric(14,4) not null | The reported value |
| source | text not null | `scheduled`, `backfill` |
| created_at | timestamptz not null default now() | |

### 2.2 `rpt.portfolio_daily` (operator, no RLS, no client content)

| Column | Type | Notes |
|---|---|---|
| snapshot_date | date | pk part |
| measure | text | pk part |
| grain | jsonb | pk part; group or person ids only |
| value | numeric(14,4) | |
| taken_at | timestamptz | |

### 2.3 `acct.report_schedules` (mutable, RLS)

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| account_id | uuid not null | |
| name | text not null | |
| pack_type | text not null | check in (`wsr`, `qbr`, `custom`) |
| cadence | text not null | check in (`weekly`, `monthly`, `quarterly`) |
| run_day | smallint not null | ISO weekday for weekly, day of month otherwise |
| run_time | time not null | In the account calendar time zone |
| period_kind | text not null | check in (`previous_week`, `previous_month`, `previous_quarter`, `contract_period`) |
| formats | text[] not null | subset of (`pptx`, `pdf`) |
| template_id | uuid not null | references `op.report_templates` |
| distribution | jsonb not null | `[{kind: portal_user\|contact\|internal, id, email}]` |
| review_required | boolean not null default true | |
| review_grace_hours | smallint not null default 24 | |
| enabled | boolean not null default true | |
| next_run_at | timestamptz null | Null while disabled |
| last_run_id | uuid null | |
| version, created_at, updated_at | | |

### 2.4 `acct.report_runs` (mutable status, RLS)

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| account_id | uuid not null | |
| schedule_id | uuid null | Null for "Generate now" |
| pack_type | text not null | |
| period_start, period_end | date not null | Account-local |
| status | text not null | check in (`queued`, `generating`, `ready_for_review`, `awaiting_review`, `approved`, `sending`, `sent`, `failed`, `skipped`) |
| claimed_by | text null | Worker task id |
| started_at, finished_at | timestamptz null | |
| error | text null | |
| pack_id | uuid null | |
| reviewer_id, reviewed_at | text, timestamptz null | |
| delivery | jsonb null | Per-recipient outcome |
| version, created_at, updated_at | | |

### 2.5 `acct.report_packs` (mutable narrative versions, RLS)

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| account_id | uuid not null | |
| run_id | uuid not null | |
| period_start, period_end | date not null | |
| measures | jsonb not null | The frozen measure values used, keyed by measure and grain |
| notable | jsonb not null | Frozen notable ticket rows and appendix rows |
| narrative_source | text not null | check in (`axel`, `template`) |
| narrative_versions | jsonb not null | `[{version, text, author_kind, author_id, at}]`; first is the generated one |
| suggestion_id | uuid null | Link to `acct.ai_suggestions` when Axel wrote the narrative |
| pptx_key, pdf_key | text null | S3 keys under `accounts/<account_id>/reports/<run_id>/` |
| generated_at | timestamptz not null | |
| version, created_at, updated_at | | |

### 2.6 `op.report_templates`

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| name | text not null | |
| pack_type | text not null | |
| master_key | text not null | S3 key of the operator PPTX master |
| layout | jsonb not null | Slide list with layout names, placeholder map, chart specs |
| version | integer not null | Frozen on each pack |
| is_default | boolean not null | One per pack_type |

```sql
-- Snapshot idempotency and lookups
create unique index ux_rpt_daily_snapshots_key
  on rpt.daily_snapshots (account_id, snapshot_date, measure, grain);
create index ix_rpt_daily_snapshots_series
  on rpt.daily_snapshots (account_id, measure, snapshot_date desc);
-- Monthly partitioning by snapshot_date from day one (Data Model §7)
alter table rpt.daily_snapshots enable row level security;
alter table rpt.daily_snapshots force row level security;
create policy rpt_snapshots_operator on rpt.daily_snapshots for all to xms_app, xms_worker
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[]));
create policy rpt_snapshots_portal on rpt.daily_snapshots for select to xms_portal
  using (account_id = current_setting('xms.account_id')::uuid
         and measure in (select key from rpt.portal_visible_measures));
-- Append-only guard
create trigger trg_rpt_daily_snapshots_append_only before update or delete
  on rpt.daily_snapshots for each row execute function sys.raise_append_only();
-- Schedules and runs
create index ix_acct_report_schedules_due on acct.report_schedules (next_run_at) where enabled;
create index ix_acct_report_runs_status on acct.report_runs (account_id, status, created_at desc);
create unique index ux_acct_report_runs_period
  on acct.report_runs (schedule_id, period_start) where schedule_id is not null and status <> 'skipped';
```

Portal visibility of measures is a whitelist table `rpt.portal_visible_measures` (consumption measures are present only when the account setting is on; the API also filters, the policy is the backstop).

### 2.7 Measure definitions (sketches; final SQL lives in `backend/src/db/queries/measures/*.sql` and is unit-tested)

```sql
-- sla_resolution_attainment, grain priority, for account-local day :d
with ended as (
  select c.ticket_id, c.met_at is not null and not c.breached as met, t.priority
  from acct.sla_clocks c join acct.tickets t on t.id = c.ticket_id
  where c.kind = 'resolution' and c.account_id = :account
    and (c.met_at at time zone :tz)::date = :d or (c.breached_at at time zone :tz)::date = :d
)
select priority, count(*) filter (where met) as numerator, count(*) as denominator
from ended group by priority;

-- mttr_by_type: business minutes creation -> resolved, minus paused minutes
select t.ticket_type,
       avg(c.elapsed_business_minutes) as value
from acct.sla_clocks c join acct.tickets t on t.id = c.ticket_id
where c.kind = 'resolution' and c.met_at is not null and c.account_id = :account
  and (c.met_at at time zone :tz)::date = :d
group by t.ticket_type;

-- reopen_rate: reopened within 14 days of a resolution stamped on :d
select count(*) filter (where exists (
         select 1 from acct.audit_events e
         where e.entity = 'ticket' and e.entity_id = t.id and e.field = 'state'
           and e.new_value not in ('resolved','closed')
           and e.created_at > t.resolved_at and e.created_at <= t.resolved_at + interval '14 days'))
       as numerator, count(*) as denominator
from acct.tickets t where t.account_id = :account and (t.resolved_at at time zone :tz)::date = :d;
```

Live measures (open tickets, backlog by age, at risk, breached now, consumption, forecast) are queries in the same folder run on request with the caller's RLS context; they are also snapshotted daily so trends exist.

### 2.8 Snapshot job logic

- Runs in the worker every 15 minutes; selects accounts whose local midnight has passed since their last `snapshot_date` (`FOR UPDATE SKIP LOCKED` on a `sys.job_leases` row per account).
- For each due day, computes every snapshot measure at every configured grain, inserts with `ON CONFLICT DO NOTHING` (idempotent), records `source = scheduled`.
- Backfill: an admin action or the same loop when a gap of more than one day is detected recomputes missing days from the ticket and audit tables with `source = backfill`; live-only measures are reconstructed from audit events where possible (open count from state transitions) and otherwise left null with a `backfilled_partial` note on the run.
- Portfolio rows are computed from the account rows after all accounts for the day are complete.
- Measures never read `acct.work_notes` or free text; `notable` rows in a pack carry key, title, state, next step (public comment excerpt) only.

## 3. Producers / core logic

| Logic | Where | Notes |
|---|---|---|
| Measure functions and period math | `backend/src/domain/reporting/*` | Pure; take row sets and a calendar; used by API (live), worker (snapshots), tests |
| Snapshot job | `backend/src/worker/jobs/snapshot.job.ts` | §2.8 |
| Schedule runner | `backend/src/worker/jobs/report-schedule.job.ts` | Claims due schedules like the harness routine engine, inserts the run row in the claim transaction, advances `next_run_at` on the account calendar, enqueues `report.generate` |
| Pack generator | `backend/src/worker/reports/pack-generator.ts` | Loads measures (snapshots for the period plus live notable rows), freezes them into `acct.report_packs.measures`, requests the narrative (§5.2), renders |
| Renderer | `backend/src/worker/reports/render-pptx.ts` (`pptxgenjs` from the template master and layout), `render-pdf.ts` (headless Chromium prints an HTML rendition of the same layout so the PDF matches the deck) | Chart images produced with a server-side chart library into PNG, embedded in both |
| Delivery | connector `reports` on the framework | Email with links and optional PDF attachment; outcome written to `report_runs.delivery` |
| Exports | `backend/reporting/export.service.ts` streams CSV directly; Excel over 5,000 rows enqueues `export.generate` to the worker (`exceljs` streaming writer), stores under `accounts/<id>/exports/`, notifies | DR-06 |
| Review | `backend/reporting/review.service.ts` | Narrative version append, regenerate, approve; state transitions on the run |

## 4. API routes

All under `/v1`, versioned with `enableVersioning({ type: URI })`, global auth and permission guard.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/reporting/measures` | `tickets:view` | Catalog metadata (keys, grains, definitions) for the UI and the NL query surface |
| GET | `/reporting/dashboard?accounts=&period=&group=&assignee=` | `tickets:view` | Live plus snapshot measures for the operational dashboard in one payload |
| GET | `/reporting/portfolio?period=` | `reports:view-portfolio` | Per-account roll-up |
| GET | `/reporting/series?measure=&grain=&from=&to=&accounts=` | `tickets:view` | Time series from snapshots |
| GET | `/portal/dashboard?period=` | `portal:view-org-tickets` | Client dashboard (portal role, single account) |
| GET | `/reporting/schedules?account=` | `reports:manage` | List |
| POST | `/reporting/schedules` | `reports:manage` | Create |
| PATCH | `/reporting/schedules/{id}` | `reports:manage` | Update, enable, disable |
| POST | `/reporting/schedules/{id}/run-now` | `reports:manage` | Off-cycle run for a period |
| GET | `/reporting/runs?account=&status=` | `reports:manage` | Runs with delivery outcome |
| GET | `/reporting/runs/{id}` | `reports:manage` | Run plus pack, slide images, narrative versions |
| POST | `/reporting/runs/{id}/narrative` | `reports:review` | Append a narrative version |
| POST | `/reporting/runs/{id}/regenerate` | `reports:review` | Re-render with the latest narrative |
| POST | `/reporting/runs/{id}/approve` | `reports:review` | Approve and send |
| GET | `/reporting/runs/{id}/files/{kind}` | `reports:review`, portal `portal:view-org-tickets` for sent packs | Presigned download |
| POST | `/reporting/exports` | route-specific view permission | Body names the view and filters; returns a stream or a job id |
| GET | `/reporting/exports/{id}` | same | Job status and presigned link |
| GET | `/reporting/templates` | `admin:config` | Operator templates |
| POST | `/reporting/templates` | `admin:config` | Upload a master and layout |

Recipient and account are always derived from the principal; `accounts=` is intersected with the grants, never trusted.

## 5. Cross-cutting concerns

### 5.1 Scoping and RLS

Every dashboard query runs inside the request transaction with `xms.account_ids` bound; the portal route binds `xms.account_id` and the portal role, so the whitelist policy applies even if a service bug requested a consumption measure. Portfolio rows in `rpt.portfolio_daily` carry no account content and are readable only with `reports:view-portfolio`.

### 5.2 Narrative through the Axel adapter

The pack generator sends the frozen measures and notable rows (no work notes, no attachments) to the adapter's batch face as capability `wsr_narrative`; the adapter enforces the account AI switch and returns a suggestion id and text, or `withheld`. On `withheld` or `unavailable` the generator uses the templated narrative (`narrative_source = template`) and continues; the review screen shows which source produced it. The suggestion is accepted when the reviewer approves (the adapter records the decision, [Axel AI Functionality §2](../ai-functionality/TECHNICAL-SPEC.md)).

### 5.3 Freezing

A pack's numbers are the rows in `report_packs.measures`, written once. Regeneration after a narrative edit re-renders from the frozen measures; it never re-queries, so the deck the reviewer approved is the deck the client receives.

### 5.4 Caching and refresh

The dashboard payload is cached per (principal grants, filters) for 30 seconds in the API process; the web polls at 60 seconds while the document is visible (`pollingInterval` set to 0 when hidden). Snapshot series are cached until the next snapshot day.

### 5.5 Time zones

Period boundaries and snapshot days use the account's default calendar zone from [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md); portfolio periods use the operator zone (`America/New_York`).

## 6. Web / client changes

- `frontend/app/(internal)/operations/page.tsx`: the dashboard, composed from `ScoreCard`, `Panel`, `InkBanner`, `PillarRail` in the XMS token package; RTK Query slice `reportingApi` with tag `Reporting:<scope hash>`; polling per §5.4; tiles link to the ticket list with the matching saved-view filter.
- `frontend/app/(internal)/portfolio/page.tsx`: SortableTable with attention sort; export button.
- `frontend/app/(portal)/dashboard/page.tsx`: portal layout; panels render conditionally on the measures present in the payload (no placeholder for absent consumption).
- `frontend/app/(internal)/reports/*`: schedules list and record form (admin grammar per [Design System §4](../../01-architecture/DESIGN-SYSTEM.md)), runs list, review screen (narrative editor left, slide images right, approve and regenerate actions), exports list.
- Charts: one chart component library for web and the worker's PNG rendering so the screen and the deck match (the worker renders the same specs headlessly).
- Export button component shared by every list: calls `/reporting/exports`, streams small results, otherwise shows a toast and a notification when ready.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/reporting-measures` (`backend/src/domain`, `backend/src/db`) | Measure catalog, snapshot tables, snapshot job, RLS, tests | Ticket, SLA, contract tables (Phase 1) |
| 2 | `feature/reporting-exports` (`backend`, `frontend`) | Export endpoints, streaming CSV, worker Excel job, shared button | 1 |
| 3 | `feature/reporting-dashboards` (`backend`, `frontend`) | Dashboard and portal payloads and screens | 1 |
| 4 | `feature/reporting-packs` (`backend/src/worker`, `backend`, `frontend`) | Templates, schedules, runs, generator, renderer, review, delivery | 1, report connector, Axel adapter batch face (optional) |
| 5 | `feature/reporting-portfolio` | Portfolio view, CSAT and utilisation measures | 3, Capacity and Portal surveys |
| 6 (Phase 4) | `feature/reporting-qbr`, `feature/reporting-health`, `feature/reporting-builder` | Later items | 4, 5 |

Deploy order within a release: db migration, worker, api, web.

## 8. Testing & verification

- **Domain unit (Jest):** every measure function against constructed row sets: attainment counts a breached-then-met resolution as missed; MTTR excludes paused minutes; reopen within 14 days counts, at 15 days does not; backlog buckets use business days on the account calendar; period boundaries at DST changes in Europe/London and Australia/Sydney.
- **Snapshot job (Testcontainers):** running the job twice for the same day inserts once (unique index and `ON CONFLICT`); a gap of three days is backfilled with `source = backfill`; an account created mid-day gets its first snapshot the next midnight; portfolio rows only after all accounts complete.
- **Isolation:** generated suite covers `rpt.daily_snapshots`, `acct.report_*`; a portal role query for a consumption measure with visibility off returns zero rows even when requested directly.
- **Schedule runner:** two worker instances claim one due schedule once; a run whose worker dies is marked failed by the watchdog and retried; `next_run_at` advances on the account calendar including holidays.
- **Generator and renderer:** golden test renders a pack from fixture measures and asserts slide count, titles, and that empty sections produce the "No activity" slide; PDF page count equals slide count; consumption slides absent when visibility is off.
- **Review flow (supertest):** approve without `reports:review` is 403; approve on `awaiting_review` after the grace period succeeds; regeneration uses frozen measures (a ticket edit between generate and regenerate does not change the numbers).
- **Delivery:** stubbed SES; bounced recipient recorded per recipient; failure after retries lands in the DLQ and raises the alarm metric.
- **Exports:** CSV stream of 20,000 rows completes; Excel over the threshold produces a job and a notification; the provenance sheet lists the filters.
- **Web (Vitest and Playwright):** dashboard polls only while visible; portal dashboard markup contains no consumption panel when off; e2e generates a pack for the seed account and downloads the PDF.

## 9. Risks / notes

- **Live measures over large grants.** A practice lead with 40 accounts and 500k tickets could make the dashboard payload slow; partial indexes on open tickets and the 30-second API cache cover the expected scale, and the portfolio view reads daily rows, not live tickets.
- **Chart parity between screen and deck.** Rendering the same chart spec in the browser and headlessly can drift in fonts; the worker image bundles the same fonts as the design tokens.
- **Narrative quality.** A weak narrative erodes trust in the whole pack; the review step is mandatory for client recipients until acceptance rates justify relaxing it (measured in the AI module).
- **Backfill fidelity.** Live-only measures reconstructed from audit events can differ from what a true snapshot would have shown; they are flagged as backfilled and excluded from attainment claims.
- **Template upgrades.** A new master version changes the look of future packs only; packs freeze the template version.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
