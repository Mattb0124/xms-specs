# Technical Spec: Capacity & Allocation

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md), [Axel AI Functionality](../ai-functionality/TECHNICAL-SPEC.md)
**Requirements covered:** CAP-01 to CAP-10, AI-16 (data only)
**Repos affected:** `backend/src/domain`, `backend/src/db`, `backend/src/contracts`, `backend`, `backend/src/worker`, `frontend`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Roster source in the POC | `web-ui/components/aix-v3/xms/store.tsx` `useTenantRoster()` (Clerk `organization.getMemberships`, keyed by lowercased email), verified 2026-09-04 | XMS persists the roster in `op.people` linked to `op.users`; Clerk is the import source, not the store |
| Profile fields and time zone picker | `web-ui/components/aix-v3/xms/XmsAdminPages.tsx` (`UserRow`, `ALL_TIME_ZONES`, `tzAbbrev`), studio `tenant_user_profiles`, verified 2026-09-04 | Screen grammar for the roster record |
| Operator schema and grants | [Data Model §2](../../01-architecture/DATA-MODEL.md): `op.*` readable by `xms_app` and `xms_worker`, portal role limited to a whitelist view | All tables here are `op.*` or `rpt.*`; no `account_id` on people, skills, PTO |
| Account calendars and holiday sets | [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md) `op.holiday_calendars`, `op.holidays`, `backend/src/domain/calendar` | Person calendars reuse the same holiday sets and the same business-day functions |
| Time entries (actuals) | [Time, Contracts & Budget §2.5](../time-and-budget/TECHNICAL-SPEC.md) `acct.time_entries` (`person_id`, `performed_on`, `minutes`) under RLS | Read by the worker only, into `rpt.capacity_periods` |
| Row claiming for jobs | studio `app/modules/agent_harness/scheduler/routine_engine.py` (`FOR UPDATE SKIP LOCKED`), verified 2026-09-04 | Recompute jobs |
| Notifications | `app-api/src/api/v3/notifications/*` design, verified 2026-09-04 | Certification expiry and overallocation notices |
| Assignment control | [Ticket Management](../ticket-management/TECHNICAL-SPEC.md) assignee picker | Consumes this module's capacity check endpoint |
| AIX pipeline data | `app-api` Salesforce nightly sync (`SALESFORCE_SYNC_*` in `.env.example`), verified 2026-09-04 | Not used; XMS demand is entered or imported (Functional §5.7) |

Cross-module rule: operator tables never carry `account_id` except `op.allocations` and `op.pipeline_demand`, which reference `op.accounts.id` as a plain foreign key to the operator's own account registry (not to `acct.*`). Actuals cross the boundary only inside the worker, which runs with `xms.account_ids` set to every active account when building `rpt.capacity_periods`, and the read model stores minutes per (person, account, period) with no ticket content. Portal principals have no grant on `op.*` capacity tables or `rpt.capacity_periods`.

## 2. Data model

### 2.1 `op.people`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | The `person_id` stored on time entries and assignments |
| `user_id` | uuid null unique | `op.users.id`; null for a person who has not signed in yet |
| `display_name`, `email` | text | Email lowercased, unique |
| `role` | text | Operator role code (rate cards key on it) |
| `fte_percent` | numeric(5,2) | 0 to 100 |
| `hours_base_per_week` | numeric(5,2) | Default 40 |
| `admin_overhead_percent` | numeric(5,2) null | Null means operator default |
| `cost_rate`, `bill_rate` | numeric(10,2) null | Per hour; column grants restrict to finance and admin |
| `currency` | char(3) | |
| `country` | char(2) | Selects the holiday calendar |
| `time_zone` | text | IANA |
| `holiday_calendar_id` | uuid | `op.holiday_calendars` |
| `assignment_group_ids` | uuid[] | Denormalised from `op.group_members` for the picker |
| `start_date`, `end_date` | date | Prorates capacity |
| `is_active` | boolean | |
| `created_at`, `updated_at`, `version` | | |

### 2.2 `op.person_calendars`

| Column | Type | Notes |
|---|---|---|
| `person_id` | uuid PK | |
| `working_days` | int[] | ISO weekday numbers |
| `day_start`, `day_end` | time | Local to `time_zone` |
| `hours_per_day` | numeric(4,2) | Derived, stored for speed |

### 2.3 `op.skills`, `op.person_skills`, `op.certifications`

| Table | Columns |
|---|---|
| `skills` | `id`, `kind` CHECK in (`technology`, `account`, `process`), `code`, `name`, `account_id null` (generated account familiarity skill), `is_active` |
| `person_skills` | `person_id`, `skill_id`, `level` CHECK 1..4, `assessed_on`, `assessed_by`; PK (`person_id`, `skill_id`) |
| `certifications` | `id`, `person_id`, `name`, `issuer`, `obtained_on`, `expires_on null`, `expiry_notified_at null` |

### 2.4 `op.pto`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `person_id` | uuid | |
| `starts_on`, `ends_on` | date | Inclusive |
| `kind` | text | CHECK in (`vacation`, `sick`, `other`) |
| `fraction` | numeric(3,2) | 1.00 full day, 0.50 half day |
| `entered_by` | text | |

### 2.5 `op.allocations`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `person_id` | uuid | |
| `account_id` | uuid | `op.accounts.id` |
| `period_month` | date | First day of the month; unique per (person, account, month) |
| `planned_minutes` | int | |
| `note` | text null | |
| `updated_by` | text | |
| `version` | int | Optimistic concurrency for the grid |

### 2.6 `op.pipeline_demand`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `source` | text | CHECK in (`pipeline`, `project`, `import`) |
| `account_id` | uuid null | Null for a prospect |
| `prospect_name` | text null | |
| `period_month` | date | |
| `hours` | numeric(8,2) | |
| `probability` | numeric(3,2) | 1.00 for project demand |
| `role` | text null | Optional role split |
| `skill_id` | uuid null | Optional technology hint |

### 2.7 `rpt.capacity_periods` (worker-built read model)

| Column | Type | Notes |
|---|---|---|
| `person_id` | uuid | |
| `period_month` | date | PK with `person_id` |
| `working_days` | int | Calendar working days in the month within employment dates |
| `contracted_minutes` | int | `working_days * hours_per_day * 60 * fte_percent / 100` |
| `pto_minutes`, `holiday_minutes`, `overhead_minutes` | int | |
| `available_minutes` | int | `contracted - pto - holiday - overhead` |
| `allocated_minutes` | int | Sum of allocations |
| `actual_minutes` | int | Sum of time entries (all classes) for the month |
| `pipeline_minutes_weighted`, `project_minutes` | int | |
| `status` | text | CHECK in (`available`, `warning`, `over`, `no_calendar`) |
| `computed_at` | timestamptz | |

Plus `rpt.capacity_actuals` with `person_id`, `account_id`, `period_month`, `planned_minutes`, `actual_minutes`, `variance_minutes` for the planned versus actual report (CAP-05), minutes only, no ticket references.

### 2.8 Constraints, indexes, grants

```sql
alter table op.allocations add constraint uq_allocations unique (person_id, account_id, period_month);
create index ix_pto_person_dates on op.pto (person_id, starts_on, ends_on);
create index ix_allocations_account_month on op.allocations (account_id, period_month);
create index ix_pipeline_demand_month on op.pipeline_demand (period_month);

-- operator-only: no portal access to anything in this module
revoke all on op.people, op.person_calendars, op.skills, op.person_skills, op.certifications,
  op.pto, op.allocations, op.pipeline_demand, rpt.capacity_periods, rpt.capacity_actuals from xms_portal;
-- cost and bill rates are column-restricted
revoke select (cost_rate, bill_rate) on op.people from xms_app;
grant select (cost_rate, bill_rate) on op.people to xms_app_finance;   -- role used only when the principal holds contracts:manage or admin:users

-- read model has account ids but no client content; RLS still applies so an internal user sees only granted accounts
alter table rpt.capacity_actuals enable row level security;
alter table rpt.capacity_actuals force row level security;
create policy acct_isolation_operator on rpt.capacity_actuals for select to xms_app
  using (account_id = any (current_setting('xms.account_ids')::uuid[]));
```

`rpt.capacity_periods` has no `account_id` (totals per person) and is readable by any principal with `capacity:view`.

### 2.9 Core math (`backend/src/domain/capacity`)

- **Working days in month.** `calendar.businessDays(person_calendar, holiday_calendar, monthStart, monthEnd) ∩ [start_date, end_date]`.
- **Contracted minutes.** `working_days * hours_per_day * 60 * fte_percent / 100`.
- **PTO minutes.** For each PTO row overlapping the month: `sum(fraction * hours_per_day * 60)` over working days in the overlap (holidays inside a PTO range are not double-counted: a day is holiday first, then PTO).
- **Holiday minutes.** Holidays on working days within employment dates, times `hours_per_day * 60`.
- **Overhead minutes.** `(contracted - pto - holiday) * overhead_percent / 100`, overhead percent from the person or the operator default.
- **Available.** `contracted - pto - holiday - overhead`, floored at zero.
- **Status.** `allocated / available` above the warning threshold (default 0.90) is `warning`, above 1.00 is `over`; missing calendar is `no_calendar`.
- **Single point of failure (CAP-07).** For each account, required skills come from the technologies on its active contracts (Time & Budget contract `technology_codes`, or the account's configured list); qualified people are those with `level >= spof_level` (default 3) and `is_active`; count 1 is `spof`, count 0 is `gap`.
- **Variance (CAP-05).** `actual - planned` in minutes and `variance / planned` when planned is positive, else null.
- **Proration.** A person starting or ending mid-month contributes only the working days inside their employment dates.

The functions are pure and take constructed calendars; the worker and the API's inline preview call the same code.

## 3. Producers / core logic

- `RosterService`: CRUD on people, skills, certifications, calendars; `importFromDirectory()` creates people for `op.users` of kind `internal` without a person row. Writes audit events into an operator audit table (`op.audit_events`, same shape as `acct.audit_events`).
- `PtoService`: CRUD; every change enqueues a recompute for the affected (person, months).
- `AllocationService`: upsert cells with version check; enqueue recompute; the account grid reads `op.allocations` joined to `rpt.capacity_periods` for the remaining column.
- `DemandService`: CRUD and spreadsheet import (`exceljs` parse of the template; rows validated with the same DTO as the API).
- `CapacityRecomputeJob` (worker): a `sys.job_leases` row per (person, month) claimed with `SKIP LOCKED`; recomputes `rpt.capacity_periods` and `rpt.capacity_actuals` for that pair. Triggers: PTO, calendar, roster, allocation, holiday changes (outbox events `capacity.recompute`), time entry outbox events `time.logged` and `time.adjusted` (from Time & Budget), and a nightly full recompute of the current and next six months. The job sets `xms.account_ids` to all active account ids for the actuals aggregation and writes only minutes.
- `CertificationExpiryJob` (worker, daily): notifications at 60 days before `expires_on`, once, tracked by `expiry_notified_at`.
- `CapacityCheckService.check(personIds, month)`: returns per person available, allocated, actual-to-date, remaining, status; used by the assignment control (CAP-06) and exposed to Axel via the XMS MCP tool `get_capacity` for AI-16 (Phase 4).

## 4. API routes

All under `/v1`, operator principals only; portal tokens receive 403 on every route here.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET/POST | `/roster/people` | `capacity:view` (GET), `admin:users` (POST) | Roster list and create (CAP-01) |
| GET/PATCH | `/roster/people/{id}` | `capacity:view`, `admin:users` | Record; rates only returned to `contracts:manage` or `admin:users` |
| POST | `/roster/import` | `admin:users` | Create people from the sign-in directory |
| PUT | `/roster/people/{id}/calendar` | `admin:users` or `capacity:manage` | Working calendar |
| GET/PUT | `/roster/people/{id}/skills` | `capacity:view`, `capacity:manage` | Skill levels |
| GET/POST/DELETE | `/roster/people/{id}/certifications` | `capacity:view`, `capacity:manage` | Certifications |
| GET/POST/DELETE | `/roster/people/{id}/pto` | self or `capacity:manage` | PTO (CAP-02) |
| GET | `/capacity?month=&group=&role=&skill=&account=` | `capacity:view` | Capacity view rows with overlays (CAP-03, CAP-08) |
| GET | `/capacity/check?person_ids=&month=` | `tickets:work` | Assignment-time check (CAP-06) |
| GET | `/capacity/skills-matrix?lens=people\|account` | `capacity:view` | Heat map and single-point-of-failure flags (CAP-07) |
| GET/PUT | `/allocations?account=&from=&to=` | `capacity:view`, `capacity:manage` | Grid read and bulk cell upsert (CAP-04) |
| GET | `/capacity/variance?month=&account=&person=` | `capacity:view` | Planned vs actual (CAP-05), exportable with `?format=xlsx` |
| GET/POST/DELETE | `/demand` | `capacity:view`, `capacity:manage` | Pipeline and project demand (CAP-08) |
| POST | `/demand/import` | `capacity:manage` | Spreadsheet import |

## 5. Cross-cutting concerns

### 5.1 The account boundary

Actuals join operator allocation to account-scoped time entries only inside the worker recompute, which runs as `xms_worker` with all active accounts in `xms.account_ids`. The read model stores minutes per (person, account, month) with no ticket id, no description, no rate. An internal user then reads `rpt.capacity_actuals` under RLS with their own grants, so a consultant with no grant on account X never sees X's row even in aggregate. `rpt.capacity_periods` (per person totals) has no account dimension and is safe to show to anyone with `capacity:view`.

### 5.2 Cost rates

Column-level grants plus a service check: the DTO omits `cost_rate` and `bill_rate` unless the principal holds `contracts:manage` or `admin:users`. Rates never enter `rpt.*`.

### 5.3 Freshness

Recompute is event-driven with a nightly sweep; the capacity view shows `computed_at` and offers a manual recompute for the visible month (enqueues jobs, does not compute inline). The inline remaining-capacity preview in the allocation grid uses the domain function on the client with the row's current numbers, so the lead sees an immediate figure that the worker confirms.

### 5.4 Holiday calendars

Shared `op.holiday_calendars` with Accounts & Administration; adding a holiday enqueues recompute for every person on that calendar.

## 6. Web / client changes

- **Roster** (`/admin/roster`, record view): list in the admin grammar; record with sections Profile, Calendar, Skills, Certifications, Rates (permission-gated), PTO.
- **Capacity** (`/capacity`): month picker, filters, the grid from Functional §5.4 with stacked overlay bars for allocated, weighted pipeline and project demand; status chips on the `--state-*` trios.
- **Allocation grid** (`/accounts/{id}/allocation` and `/capacity/allocation?month=`): editable cells with debounced bulk `PUT`, version conflicts surfaced as a toast with reload; remaining column computed client-side from `backend/src/domain/capacity` (shared code via the contracts package build).
- **Skills matrix** (`/capacity/skills`): heat map with a people lens and an account lens; single-point-of-failure and gap cells flagged; export.
- **Planned vs actual** (`/capacity/variance`): sortable table, drill-through links to the Time & Budget entry list and to the allocation cell, export.
- **Assignment control** (Ticket Management): the picker calls `/capacity/check` for the visible candidates and renders remaining hours and the inline notice with "Assign anyway".
- Data layer: `capacityApi` slice with tags `Roster`, `Capacity`, `Allocations`, `SkillsMatrix`, `Variance`, `Demand`; the check endpoint is not cached beyond the picker's open state.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/capacity-roster` (db, api, web) | `op.people`, calendars, skills, certifications, import, roster screens, picker data | Accounts & Administration holiday calendars |
| 2 | `feature/capacity-engine` (domain, db, worker) | PTO, allocations, demand tables, capacity math, recompute job, read models | 1, Time & Budget entries |
| 3 | `feature/capacity-views` (api, web) | Capacity view, allocation grid, variance, skills matrix, check endpoint and picker integration | 2 |
| 4 | `feature/capacity-later` | Rota, scenarios, Salesforce import, MCP `get_capacity` tool | 3, Phase 4 |

Deploy order within each release: db migration, worker, api, web.

## 8. Testing & verification

- **Domain (Jest, `backend/src/domain/capacity/*.spec.ts`)**: the Functional §7 Brazil example computes to the stated number; holiday inside PTO counted once; proration for a mid-month start; status thresholds at exactly 90 and 100 percent; single-point-of-failure with 0, 1 and 2 qualified people; variance with zero planned returns null percent.
- **Data layer (Testcontainers)**: portal role has no access to any table here (generated grant suite); `rpt.capacity_actuals` RLS hides ungranted accounts; column grants hide rates from `xms_app`; allocation unique constraint and version conflict.
- **Worker**: a `time.logged` outbox event recomputes only the affected (person, month); nightly sweep is idempotent; certification expiry fires once.
- **HTTP (supertest)**: every route rejects anonymous, garbage and portal tokens; `/roster/people/{id}` omits rates without the permission; `/capacity/check` returns the inline-notice payload for an over person.
- **E2E (Playwright)**: add PTO and watch the capacity row change; allocate over capacity and see the red cell and the assignment notice; export the variance report.

## 9. Risks / notes

- **Read model lag** between a time entry and the variance report is seconds to a minute; the screens show `computed_at`. Accepted.
- **Rates in `op.people`** are the only cost data in XMS; the column grants are tested, and profitability (TB-16) will read them only in the worker.
- **Skill taxonomy drift** (free-form skill codes) is prevented by an operator-managed list; account familiarity skills are generated, not typed.
- **Pipeline probability** is entered by hand until a Salesforce feed exists; the weighted overlay is labelled as an estimate.
- **Forty-hour base** assumption is stated in Functional §8; per-person override covers exceptions.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
