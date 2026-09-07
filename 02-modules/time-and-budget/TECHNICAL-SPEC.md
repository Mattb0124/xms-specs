# Technical Spec: Time, Contracts & Budget

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Capacity & Allocation](../capacity-and-allocation/TECHNICAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md), [Axel AI Functionality](../ai-functionality/TECHNICAL-SPEC.md)
**Requirements covered:** TB-01 to TB-16, INT-02, INT-03
**Repos affected:** `backend/src/domain`, `backend/src/db`, `backend/src/contracts`, `backend`, `backend/src/worker`, `frontend`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Burn-down aggregate and time entry shape | studio `feature/xms-ticketing` `app/modules/xms_ticketing/models_db.py` (`xms_contracts`, `xms_time_entries` with denormalised `contract_id`) and `service.py` (billable minutes per contract in the current month), verified 2026-09-04 | Ported: the denormalised contract id on the entry is kept so burn-down is one aggregate immune to later ticket edits |
| Contract admin grammar | `web-ui/components/aix-v3/xms/ContractsTab.tsx`, `ContractFormDialog.tsx` (`PolicyDraft` keeps hours as strings while typing), verified 2026-09-04 | Screen shape for the contract record and period list |
| Time widget on the ticket record | `web-ui/components/aix-v3/xms/TicketDrawer.tsx` related-info rail, verified 2026-09-04 | Kept as the primary logging surface |
| Vocabulary | `web-ui/components/aix-v3/xms/vocab.ts` (`ContractType`, `XmsTimeEntry`), verified 2026-09-04 | Extended with activity type, billable class, period, rate snapshot |
| Isolation and append-only rules | [Data Model §1, §3](../../01-architecture/DATA-MODEL.md): RLS on `acct.*`, append-only trigger on `time_entries`, `time_adjustments` | Every table here is `acct.*` and follows both |
| Period locking at the database | [Security & Tenancy §7](../../01-architecture/SECURITY-AND-TENANCY.md): trigger checks `billing_periods.locked` for the entry date | Defined in §2.8 below |
| Job claiming | studio `app/modules/agent_harness/scheduler/routine_engine.py` (`FOR UPDATE SKIP LOCKED`, watchdog), verified 2026-09-04 | Threshold, renewal and auto-lock jobs in the worker |
| Connector framework | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md): outbox, connector queue, DLQ, kill switch | Finance export delivery (INT-02) |
| Notifications | `app-api/src/api/v3/notifications/*` (recipient identity key, collapse key, copy in one file), verified 2026-09-04 | Threshold and renewal notifications reuse the XMS notification table shaped on this |
| No export utility in AIX | `app-api` has `xlsx` 0.18.5 import only, no generator (verified 2026-09-04) | XMS uses `exceljs` in the API for on-demand exports and in the worker for the finance file |
| Calendar engine | [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md) `backend/src/domain/calendar` (business minutes, business days, after-hours classification) | Forecast, after-hours flagging |

Cross-module dependency: Ticket Management calls this module's `TimeGate` before a Resolved or Closed transition (TB-02) and reads `ContractPosition` for the over-budget flag; Capacity reads `time_entries` through the worker read model only.

## 2. Data model

All tables are `acct.*` with `account_id uuid not null`, RLS policies per [Data Model §3](../../01-architecture/DATA-MODEL.md), `created_at`, and (mutable tables only) `updated_at`, `version`. Money is `numeric(14,2)` plus `currency char(3)`.

### 2.1 `acct.engagements`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | |
| `name` | text | |
| `owner_user_id` | text | Opaque internal user id (account owner) |
| `renewal_date` | date null | Drives INT-03 |
| `notice_period_days` | int null | |
| `status` | text | CHECK in (`active`, `expiring`, `ended`) |

### 2.2 `acct.contracts`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id`, `engagement_id` | uuid | |
| `display_key` | text unique | `CT00001` from an operator sequence |
| `name` | text | |
| `model` | text | CHECK in (`retainer`, `prepaid_block`, `tm`, `fixed_fee`) |
| `cadence` | text | CHECK in (`monthly`, `quarterly`, `term`) |
| `contracted_hours` | numeric(8,2) null | Per period; null for `tm` |
| `contracted_value` | numeric(14,2) null | Per period; fixed fee total for `fixed_fee` |
| `currency` | char(3) | |
| `rollover_rule` | text | CHECK in (`none`, `carry_month`, `carry_term`, `cap`) |
| `rollover_cap_hours` | numeric(8,2) null | Required when `cap` |
| `overage_rule` | text | CHECK in (`block`, `allow_flag`, `allow_rate`) |
| `overage_multiplier` | numeric(5,3) null | Required when `allow_rate` |
| `after_hours_handling` | text | CHECK in (`premium_rate`, `comp_time`, `none`) |
| `after_hours_multiplier` | numeric(5,3) null | |
| `sla_policy_id` | uuid null | Ticket Management |
| `start_date`, `end_date` | date | |
| `scope_notes` | text null | |
| `is_active` | boolean | Deactivate, never delete |
| `threshold_percents` | int[] | default `{50,75,90,100}` (TB-09) |
| `threshold_notify_client` | boolean | default false |

### 2.3 `acct.contract_periods`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id`, `contract_id` | uuid | |
| `period_start`, `period_end` | date | Unique per contract |
| `contracted_hours` | numeric(8,2) null | Copied from the contract at generation; editable for off-cycle blocks |
| `carried_over_hours` | numeric(8,2) | Computed at period open from the rollover rule |
| `overage_allowance_hours` | numeric(8,2) | Added by out-of-scope or over-budget approvals |
| `consumed_minutes` | int | Maintained by the service in the same transaction as entries and adjustments (derived, verifiable by aggregate) |
| `thresholds_fired` | int[] | Which percentages fired this period |
| `state` | text | CHECK in (`future`, `open`, `closed`) |

### 2.4 `acct.rate_cards` and `acct.rate_card_entries`

| Column | Type | Notes |
|---|---|---|
| `rate_cards.id` | uuid PK | |
| `rate_cards.account_id` | uuid | |
| `rate_cards.contract_id` | uuid null | Null means account default |
| `rate_cards.effective_from` | date | A new version is a new row; `effective_to` derived as the next version's `effective_from` |
| `rate_cards.currency` | char(3) | |
| `rate_card_entries.rate_card_id` | uuid | |
| `rate_card_entries.role` | text | Operator role code from the roster |
| `rate_card_entries.bill_rate` | numeric(10,2) | Per hour |
| `rate_card_entries.overage_rate` | numeric(10,2) null | Defaults to `bill_rate * contract.overage_multiplier` |

### 2.5 `acct.time_entries` (append-only)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | |
| `ticket_id` | uuid null | Exactly one of `ticket_id`, `bucket_id` |
| `bucket_id` | uuid null | Non-ticket bucket (TB-12) |
| `contract_id` | uuid null | Denormalised from the ticket at log time; null when the account has no contract (classed Internal) |
| `contract_period_id` | uuid null | Resolved by `performed_on` |
| `billing_period_id` | uuid | Resolved by `performed_on`; the lock check target |
| `person_id` | text | Opaque roster id |
| `role` | text | Role at time of logging |
| `performed_on` | date | |
| `performed_start` | time null | Optional; enables after-hours classification finer than the day |
| `minutes` | int | CHECK 1..1440 |
| `activity_type` | text | CHECK in the six values (TB-03) |
| `billable_class` | text | CHECK in (`billable`, `non_billable`, `internal`, `pre_sales`) |
| `override_note` | text null | Required when class differs from the activity default |
| `after_hours_class` | text | CHECK in (`standard`, `after_hours`, `weekend`, `holiday`) |
| `rate_snapshot` | numeric(10,2) null | Rate in force on `performed_on` for the role |
| `rate_multiplier` | numeric(5,3) | 1.000, overage or premium multiplier applied |
| `amount` | numeric(14,2) null | `minutes / 60 * rate_snapshot * rate_multiplier` |
| `currency` | char(3) null | |
| `description` | text | |
| `description_normalised` | text null | Accepted Axel normalisation (AI-06) |
| `source` | text | CHECK in (`ticket_widget`, `timesheet`, `import`, `sync`, `api`) |
| `created_by` | text | |

### 2.6 `acct.time_adjustments` (append-only)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id`, `original_entry_id` | uuid | |
| `billing_period_id` | uuid | The open period the adjustment is dated in |
| `kind` | text | CHECK in (`correction`, `write_off`, `reclassification`) |
| `delta_minutes` | int | Signed; 0 for reclassification |
| `new_billable_class` | text null | For reclassification |
| `reason` | text | |
| `approved_by` | text | |
| `performed_on` | date | Today, in the open period |

### 2.7 `acct.non_ticket_buckets`, `acct.billing_periods`, `acct.billing_exports`, `acct.threshold_alerts`, `acct.threshold_alert_events`

| Table | Columns (beyond id, account_id) |
|---|---|
| `non_ticket_buckets` | `name`, `code` CHECK in (`governance`, `qbr_prep`, `account_mgmt`, `escalation`, `custom`), `contract_id null`, `is_active` |
| `billing_periods` | `period_start`, `period_end` (calendar month, unique per account), `state` CHECK in (`open`, `submitted`, `approved`, `locked`, `exported`), `submitted_by/at`, `approved_by/at`, `locked_by/at`, `auto_lock_at`, `summary_json`, `checksum text null` |
| `billing_exports` | `billing_period_id`, `format` (`xlsx`, `csv`), `template_version`, `s3_key`, `checksum`, `row_count`, `produced_by`, `delivered_at null`, `delivery_ref null` |
| `threshold_alerts` | `contract_id`, `percent`, `recipient_user_ids text[]`, `notify_client boolean` (materialised from the contract for editing per threshold) |
| `threshold_alert_events` (append-only) | `contract_period_id`, `percent`, `consumed_minutes_at_fire`, `fired_at`, `notification_ids` |

### 2.8 Constraints, indexes, policies

```sql
-- entries: one target, period resolution, lock guard
alter table acct.time_entries add constraint ck_time_entries_target
  check ((ticket_id is null) <> (bucket_id is null));
create index ix_time_entries_contract_period on acct.time_entries (contract_id, contract_period_id);
create index ix_time_entries_person_date on acct.time_entries (person_id, performed_on);
create index ix_time_entries_ticket on acct.time_entries (ticket_id) where ticket_id is not null;
create index ix_time_entries_billing_period on acct.time_entries (billing_period_id);

-- append-only
create trigger trg_time_entries_append_only before update or delete on acct.time_entries
  for each row execute function sys.raise_append_only();
create trigger trg_time_adjustments_append_only before update or delete on acct.time_adjustments
  for each row execute function sys.raise_append_only();

-- locked period guard (TB-14): rejects any entry or adjustment whose billing period is approved or later
create or replace function acct.assert_billing_period_open() returns trigger language plpgsql as $$
declare st text;
begin
  select state into st from acct.billing_periods where id = new.billing_period_id;
  if st is null or st not in ('open','submitted') then
    raise exception 'billing period % is % and rejects writes', new.billing_period_id, coalesce(st,'missing')
      using errcode = 'check_violation';
  end if;
  return new;
end $$;
create trigger trg_time_entries_period_open before insert on acct.time_entries
  for each row execute function acct.assert_billing_period_open();
create trigger trg_time_adjustments_period_open before insert on acct.time_adjustments
  for each row execute function acct.assert_billing_period_open();

-- rate card versions never overlap per (account, contract)
alter table acct.rate_cards add constraint uq_rate_cards_version unique (account_id, contract_id, effective_from);

-- RLS (same shape on every table in this module)
alter table acct.time_entries enable row level security;
alter table acct.time_entries force row level security;
create policy acct_isolation_operator on acct.time_entries for all to xms_app, xms_worker
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[]));
revoke all on acct.time_entries, acct.time_adjustments, acct.rate_cards, acct.rate_card_entries,
  acct.billing_periods, acct.billing_exports from xms_portal;
-- portal consumption view (CP-06) reads only aggregated minutes through acct.contract_position_public
```

### 2.9 Core math (`backend/src/domain/commercial`)

Pure functions, unit-tested with constructed data.

- **Period consumption.** `consumed(period) = sum(entries.minutes where billable_class = billable and contract_period_id = period) + sum(adjustments.delta_minutes for originals in the period where kind != reclassification) - reclassified-away minutes`. The service maintains `contract_periods.consumed_minutes` transactionally and a nightly job asserts it equals the aggregate.
- **Available.** `available = contracted_hours * 60 + carried_over_minutes + overage_allowance_minutes`.
- **Carry-over at period open.** `none`: 0. `carry_month`: `max(previous.available - previous.consumed, 0)` only if the previous period is the immediately preceding one, and the previous period's own carry-over is not carried again. `carry_term`: `max(previous.available - previous.consumed, 0)` cumulatively. `cap`: `min(carry_term value, cap_hours * 60)`.
- **Overage check at log time.** `projected = consumed + new_minutes`; if `projected > available`: `block` rejects with `OverageBlockedError`; `allow_flag` saves and returns `flagOverBudget = true` for Ticket Management; `allow_rate` splits the entry at the boundary into two rows when the boundary falls inside it (one at multiplier 1.000, one at the overage multiplier) so amounts are exact.
- **Rate snapshot.** Rate card selection: contract-specific card with the greatest `effective_from <= performed_on`, else the account default card with the same rule; entry for the person's role; missing rate leaves `rate_snapshot` null and marks the period summary `unrated`.
- **After-hours class.** From the account calendar for `performed_on` and `performed_start` (if absent, the day's class: weekday standard, weekend, holiday). `premium_rate` handling sets `rate_multiplier` to the after-hours multiplier for non-standard classes; `comp_time` records the class only and the entry is included in a comp-time report.
- **Forecast (TB-08).** With the account calendar: `bd_elapsed = business days from period_start to today inclusive`, `bd_total`, `window = min(N, bd_elapsed)`, `run_rate = minutes consumed in the last window business days / window`, `forecast = consumed + run_rate * (bd_total - bd_elapsed)`. Percent of contracted uses `available`. N is `account_settings.forecast_window_days` (default 10).
- **Thresholds (TB-09).** After every consumption change, for each `percent` in `contract.threshold_percents` not in `period.thresholds_fired`: if `consumed >= available * percent / 100`, append to `thresholds_fired` in the same transaction and write an outbox event `threshold.crossed`. The worker turns the outbox event into notifications and email; because `thresholds_fired` is updated transactionally, concurrent entries cannot fire a threshold twice.
- **Time gate (TB-02).** `canResolve(ticket) = totalMinutes(ticket) > 0 or exemptionReason in allowed`.

## 3. Producers / core logic

- `TimeEntryService.log(principal, input)`: resolves contract and periods from the ticket or bucket and `performed_on`, computes after-hours class, rate snapshot and amount, runs the overage check, inserts the entry (the database trigger enforces the lock), updates `contract_periods.consumed_minutes`, evaluates thresholds, writes the audit event and an outbox row `time.logged` (consumed by Capacity's read model, Reporting snapshots, ServiceNow if the instance subscribes). One transaction.
- `TimeAdjustmentService.adjust(...)`: validates the original exists and its period state, inserts the adjustment dated today in the open billing period, updates consumption, audit and outbox `time.adjusted`.
- `ContractService`: CRUD, period generation on create and by a nightly job that keeps two periods ahead, carry-over computation at period open (worker job, `SKIP LOCKED` on `contract_periods` in state `future` whose `period_start <= today`).
- `BillingPeriodService`: state transitions with permission checks (`time:lock-period` for approve and lock), summary generation, checksum; `auto_lock_at` job in the worker.
- `ExportService` (API, on demand): builds workbooks with `exceljs` from the same query the screen used; streams to the client; the finance layout is a versioned template in `backend/src/domain/commercial/finance-template`.
- Finance connector (worker): on `billing_period.locked` outbox event, produces the export, stores it in S3 under `accounts/<id>/exports/`, records `billing_exports`, and delivers through the finance connector instance (SFTP or HTTPS per Platform Integrations) with idempotency on `billing_period_id + template_version`; on success moves the period to `exported`.
- Renewal job (worker, daily): for engagements with `renewal_date - today` in the configured lead times, write a notification and email to the owner once per lead time (tracked in a `renewal_alerts_fired` array on the engagement).
- Axel hooks: `description_normalised` is written by accepting an AI suggestion (owned by AI Functionality). `GET /v1/timesheets/me/unlogged` provides the data the nudge uses: per day, calendar minutes minus logged minutes.

## 4. API routes

All under `/v1`, authenticated, operator principals unless noted. Account context comes from the token's grants; `account_id` in a path is validated against them (404 when not granted).

| Method | Path | Permission | Purpose |
|---|---|---|---|
| POST | `/tickets/{id}/time-entries` | `time:log` | Log time on a ticket (TB-01) |
| POST | `/accounts/{id}/buckets/{bucketId}/time-entries` | `time:log` | Non-ticket time (TB-12) |
| GET | `/tickets/{id}/time` | `tickets:view` | Entries, adjustments, totals by person, role, date, activity (TB-10) |
| GET | `/tickets/{id}/time/export?format=xlsx` | `tickets:view` | Per-ticket breakdown export |
| GET | `/tickets/{id}/time-gate` | `tickets:view` | Can resolve, total minutes, allowed exemptions (TB-02) |
| POST | `/time-entries/{id}/adjustments` | `time:adjust` | Correction, write-off, reclassification (TB-11) |
| GET | `/timesheets/me?week=` | `time:log` | Personal week view |
| GET | `/timesheets/me/unlogged?from=&to=` | `time:log` | Data for AI-06 nudges |
| GET/POST | `/accounts/{id}/engagements` | `contracts:manage` | Engagements, renewal dates (INT-03) |
| GET/POST | `/accounts/{id}/contracts` | `contracts:manage` (GET: `tickets:view`) | Contracts |
| PATCH | `/contracts/{id}` | `contracts:manage` | Edit, deactivate |
| GET | `/contracts/{id}/periods` | `tickets:view` | Periods with consumed, available, forecast |
| POST | `/contracts/{id}/periods` | `contracts:manage` | Off-cycle block |
| PUT | `/contracts/{id}/rate-cards` | `contracts:manage` | New rate card version (never edits an old one) |
| GET | `/accounts/{id}/budget` | `tickets:view` | Budget view payload: per contract current period position and forecast (TB-07, TB-08) |
| GET | `/accounts/{id}/budget/entries?contract=&period=&person=&activity=&class=` | `tickets:view` | Drill-through list, exportable |
| GET | `/accounts/{id}/billing-periods` | `time:lock-period` or `contracts:manage` | Period list and summaries |
| POST | `/billing-periods/{id}/transitions` | `contracts:manage` (submit), `time:lock-period` (approve, lock) | State machine |
| GET | `/billing-periods/{id}/export?format=` | `time:lock-period` | Finance file on demand (TB-14) |
| GET | `/portal/consumption` | `portal:view-consumption` (portal principal) | Aggregated position only, gated by the account setting (CP-06) |

Every POST accepts an `Idempotency-Key` header per [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md).

## 5. Cross-cutting concerns

### 5.1 Isolation

Every table is account-scoped under RLS. The portal role has no grant on the raw tables; the consumption view is a `security definer` function returning only aggregates for the principal's single account and only when `account_settings.consumption_visible` is true.

### 5.2 Locking is a database property

The lock trigger in §2.8 is the authority; the API's friendlier refusal is a pre-check. The isolation and append-only test suites include the lock case.

### 5.3 Concurrency

`contract_periods.consumed_minutes` is updated with `UPDATE ... SET consumed_minutes = consumed_minutes + $delta` under the row lock the transaction already holds, and threshold evaluation reads the updated value in the same transaction, so two simultaneous entries cannot both fire the same threshold.

### 5.4 Out-of-scope and over-budget flags

Ticket Management owns the flag and its approval; this module reads `ticket.scope_state`. Entries on a ticket in `out_of_scope_pending` are classed `non_billable` with `override_note = 'out of scope pending approval'`; approval writes reclassification adjustments for those entries in the open period and adds `overage_allowance_hours` to the period when the approval carries hours.

### 5.5 Currency

Stored on every money column now; a single currency per account is enforced by the service until TB-15 ships (a `CHECK` is not used so the migration is additive).

## 6. Web / client changes

- **Ticket record rail**: "Log time" form and the time list with strike-through originals and adjustments beneath (POC widget extended), contract card with burn bar and forecast line.
- **Transition dialog**: time gate check and exemption picker (owned by Ticket Management, consumes `/time-gate`).
- **Timesheet** (`/timesheet`): week grid, direct logging, unlogged highlight, bucket rows per account.
- **Account Budget view** (`/accounts/{id}/budget`): per-contract cards with burn bars, forecast sentence, threshold markers, drill-through list with filters and export button.
- **Contracts admin** (`/accounts/{id}/contracts`, record view): contract form, period list, rate card versions (new version form, history read-only), threshold and renewal settings.
- **Billing periods** (`/accounts/{id}/billing`): period list with state chips, summary, transitions, export download, export history with checksum.
- Data layer: RTK Query slice `commercialApi` with tags `Contracts`, `Periods`, `TicketTime`, `Budget`, `BillingPeriods`; optimistic append on log time with rollback on 409 or 422 (pattern from `web-ui/redux/services/xmsApi.ts:606-667`).
- Exports: the browser requests the file from the API (server-side `exceljs`), never builds it client-side, so the export and the screen share one query.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/time-and-budget-core` (db, domain) | Migrations for engagements, contracts, periods, time entries, buckets, billing periods (open state only), domain math, unit tests | Accounts calendars |
| 2 | `feature/time-and-budget-api` (api) | Routes in §4 for Phase 2, time gate, exports | 1 |
| 3 | `feature/time-and-budget-web` (web) | Ticket rail, Budget view, contracts admin | 2 |
| 4 | `feature/time-and-budget-rates` (db, domain, api, web) | Rate cards, snapshots, overage rules, after-hours | 1 to 3, calendar engine |
| 5 | `feature/time-and-budget-periods` (db, worker, api, web) | Billing period state machine, lock trigger, adjustments, thresholds, renewal job, timesheet | 4, connector framework |
| 6 | `feature/time-and-budget-finance` (worker) | Finance export template and connector delivery | 5 |

Deploy order within each release: db migration, worker, api, web.

## 8. Testing & verification

- **Domain (Jest, `backend/src/domain/commercial/*.spec.ts`)**: carry-over for each rollover rule across three periods; overage split at the boundary produces exact amounts; rate selection by effective date and contract precedence; forecast with constructed calendars (holidays inside the window); threshold firing set semantics; time gate with each exemption; after-hours class for a Brazil calendar entry at 22:00 and a UK Saturday.
- **Data layer (Testcontainers)**: append-only triggers reject update and delete; lock trigger rejects an entry dated in an approved period and accepts an adjustment dated in the open period; RLS isolation for every table in this module (generated suite); `consumed_minutes` equals the aggregate after a randomised sequence of entries and adjustments.
- **HTTP (supertest)**: anonymous and garbage tokens rejected on every route; portal token gets 403 on operator routes and only aggregates on `/portal/consumption`; `Idempotency-Key` replay returns the stored response; export endpoint streams a workbook whose totals match the JSON payload.
- **Worker**: threshold event produces one notification per recipient per threshold; finance connector is idempotent on retry (one `billing_exports` row); renewal job fires once per lead time.
- **E2E (Playwright)**: log 90 minutes from the ticket record and see the contract card update; lock a period and see the refusal message on a back-dated entry; download the finance export and compare the total to the period summary.
- Manual smoke maps to Functional §7.

## 9. Risks / notes

- **Finance layout unknown.** The template is versioned so a late change is a new version, not a rewrite; periods record `template_version`.
- **Derived `consumed_minutes`.** Kept for cheap reads; the nightly assertion job and the transactional update keep it honest. If it ever drifts, the aggregate is the truth and the job repairs the column with an audit event.
- **Overage split rows.** Two rows for one logged action is unusual for users; the ticket time list groups them under one action id (`action_id` column on entries) so the UI shows one line with two rates.
- **Quarterly contract periods vs monthly billing periods.** Deliberately independent; the export is by billing period and carries the contract period reference per row.
- **Comp time** is recorded, never balanced; stated in the functional non-goals.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
