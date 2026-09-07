# Functional Spec: Time, Contracts & Budget

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Capacity & Allocation](../capacity-and-allocation/FUNCTIONAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Platform Integrations](../integrations/FUNCTIONAL-SPEC.md)
**Requirements covered:** TB-01, TB-02, TB-03, TB-04, TB-05, TB-06, TB-07, TB-08, TB-09, TB-10, TB-11, TB-12, TB-13, TB-14, TB-15 (nice), TB-16 (nice), INT-02, INT-03
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Problem

The managed-services business is sold in hours and value against contracts, but ServiceNow only knows tickets. Today time is logged in a separate tool, reconciled by hand, and the answer to "where did the hours go" on a client call is reconstructed from memory. Budget burn is discovered late, threshold conversations happen after the overage, historical entries lose the rate that applied when they were performed, and finance receives spreadsheets whose numbers can change after they were sent.

The workbook names the distinct cases this module must cover: time at ticket level (TB-01), time as a precondition of resolution (TB-02), an activity taxonomy that answers "what kind of work" (TB-03), a billable classification that answers "who pays" (TB-04), effective-dated rate cards (TB-05), several commercial models under one contract object with rollover and overage rules (TB-06), burn-down by client and period with drill-through (TB-07), a forecast to period end (TB-08), threshold alerts (TB-09), a per-ticket hours breakdown (TB-10), adjustments and write-offs that preserve the original (TB-11), non-ticket time so utilisation is honest (TB-12), after-hours flagging on the client calendar (TB-13), a billing export with a locked period (TB-14), and a structured finance interface plus renewal alerts (INT-02, INT-03).

## 2. Current state (what exists today)

- **XMS proof of concept (web-ui `components/aix-v3/xms/`)**: `ContractsTab.tsx` lists contracts with a `BurnBar` burn-down and queue management; `ContractFormDialog.tsx` edits a contract (name, type, dates, monthly hours, rollover policy, scope notes, active flag) and a per-priority SLA grid; `TicketDrawer.tsx` carries a time-entry widget (minutes, date, billable toggle, note) and lists the ticket's entries with per-user totals; `vocab.ts` fixes `ContractType = retainer | tm | fixed` and `XmsTimeEntry` with `minutes`, `entryDate`, `billable`, `note`. Approved UI on mock data with a live seam.
- **Studio `xms_ticketing` module (branch `feature/xms-ticketing`)**: tables `xms_contracts` (contract type, monthly hours, rollover policy stored but not applied) and `xms_time_entries` (minutes, entry date, billable, note, denormalised `contract_id`), and a burn-down aggregate of billable minutes in the current month per contract. Real but narrow: one bucket per calendar month, no periods, no rates, no locking.
- **Not built anywhere**: activity types, billable classes beyond a boolean, rate cards, contract periods, prepaid blocks, rollover application, overage rules, forecast, threshold alerts, adjustments and write-offs, non-ticket buckets, after-hours flagging, billing periods and locking, exports, a finance interface, renewal alerts. AIX has no XLSX or CSV export utility at all (verified in [AIX Pattern Reuse §2](../../01-architecture/AIX-PATTERN-REUSE.md)).

## 3. Goals

1. **Every hour lands on a ticket or a named bucket, once, with a reason.** Logging is fast enough to happen as the work happens, and a ticket cannot resolve with zero time unless someone says why.
2. **Every hour carries its commercial meaning at the moment it was performed.** Activity type, billable class, and the rate in force that day are frozen on the entry.
3. **The contract knows where it stands, today and at period end.** Consumed against contracted, in hours and value, with a run-rate forecast and alerts before the line is crossed.
4. **The history is evidence, not opinion.** Originals are never edited; adjustments and write-offs are separate linked records; a locked period cannot change after finance has consumed it.
5. **Finance gets a file they can trust, without asking.** A structured export in the THG finance format, produced from a locked period, delivered through the connector framework.
6. **Utilisation is honest.** Governance, QBR preparation, account management and escalation time are captured per account so budget burn and utilisation read true.

## 4. Non-goals / out of scope

- **Invoicing.** XMS produces the locked, exportable truth; finance produces invoices (Product Vision §7).
- **Expense capture.** Hours only; expenses stay in the finance system.
- **Timesheet approval workflows beyond period submission.** A person's entries are trusted; the period-level submit, approve and lock is the control. Per-entry manager approval is not built.
- **Automatic timers.** No start and stop clocks on tickets; entries are minutes on a date.
- **Multi-currency and profitability (TB-15, TB-16).** Nice to Have; deferred to Phase 4. The model stores a currency on every money column from day one so this is additive.
- **Payroll or comp-time balance management.** After-hours flagging records the fact and the handling rule; comp-time balances live in HR systems.
- **Rate cards by individual person.** Rates are by role. A person-specific rate is a role with one member.

## 5. User-facing behavior

### 5.1 Vocabulary (fixed sets)

| Set | Values | Notes |
|---|---|---|
| Activity type (TB-03) | Analysis, Development, Testing, Client Communication, Documentation, Meeting | Operator-defined list; each carries a default billable class; accounts cannot add types (consistency for reporting) |
| Billable class (TB-04) | Billable, Non-billable, Internal, Pre-sales | Set per entry, defaulted from the activity type, overridable with a required note when the override moves work off Billable |
| Contract model (TB-06) | Retainer hours, Prepaid block, Time and materials, Fixed fee | Retainer and prepaid have a bucket; T&M has no cap; fixed fee tracks hours for profitability only |
| Rollover rule | None, Carry month, Carry term, Cap | Applies to retainers; see 5.4 |
| Overage rule | Block, Allow with flag, Allow at overage rate | Applies to retainers and prepaid blocks; see 5.4 |
| Period cadence | Monthly, Quarterly, Contract term | Retainers are monthly by default; prepaid blocks are one period for the term |
| Billing period state | Open, Submitted, Approved, Locked, Exported | See 5.7 |
| Time exemption reason (TB-02) | Duplicate, Cancelled by client, Resolved by client, Administrative close, Merged | Only these allow resolution with zero time; each is an audit event |
| Non-ticket bucket (TB-12) | Governance, QBR preparation, Account management, Escalation handling | Per account; operator may add buckets per account |
| After-hours class (TB-13) | Standard, After hours, Weekend, Holiday | Derived from the account calendar; handling per contract: premium rate multiplier or comp-time flag |

### 5.2 Logging time on a ticket

The ticket record's related-information rail (the POC `TicketDrawer` time widget, kept) carries a compact "Log time" form: minutes (or hours with a decimal), date performed (defaults to today in the user's time zone), activity type, billable class (defaulted from the activity type), description. Submitting appends the entry to the ticket's time list, which shows per-person totals and the ticket total, and updates the contract card in the same rail ("Hours this period: 12.5 of 40").

- A person may log several entries on one ticket on one day (TB-01).
- Description is free text; Axel normalisation (AI-06) offers a cleaned description the user accepts or ignores.
- The entry shows an after-hours badge when the date and the user's stated time fall outside the account calendar (TB-13); the badge explains the handling rule ("Premium 1.5x per contract" or "Comp time").
- If the ticket's contract is over its bucket and the overage rule is Block, the form refuses with the reason and links to the contract; with Allow with flag, the entry saves and the ticket is flagged over budget (see Ticket Management for the block-until-approved behaviour); with Allow at overage rate, the entry saves at the overage rate and says so.
- If the ticket is flagged out-of-scope and not yet approved, entries save but are classed Non-billable until approval, and the widget says why.
- An entry cannot be dated inside a locked billing period; the form explains and suggests logging in the open period with a reference.

### 5.3 Resolution gate (TB-02)

Moving a ticket to Resolved or Closed with zero logged time is refused unless the user picks a time exemption reason. The transition dialog shows the ticket's total time and, when it is zero, the exemption picker. The exemption is recorded in the audit trail and reported.

### 5.4 Contracts and periods

Contracts live under an engagement on the account record and follow the POC `ContractsTab` and `ContractFormDialog` grammar (list, then a full-screen record): name, model, start and end, cadence, contracted hours or value per period, rollover rule, overage rule, overage rate multiplier, currency, SLA policy reference, scope notes, active flag, renewal date and notice period.

Rollover semantics (retainers):

| Rule | Behaviour |
|---|---|
| None | Unused hours expire at period end |
| Carry month | Unused hours from period N are added to period N+1 only, then expire |
| Carry term | Unused hours accumulate until the contract end |
| Cap | Carry term, but the carried balance never exceeds a configured number of hours |

Overage semantics (retainers and prepaid blocks):

| Rule | Behaviour when consumed reaches contracted plus carry-over |
|---|---|
| Block | New billable entries are refused; the ticket can be flagged over budget for approval; approval creates an overage allowance on the period |
| Allow with flag | Entries save; the period shows an overage; the ticket gets the over-budget flag for client-visible approval per Ticket Management |
| Allow at overage rate | Entries save at the overage rate; the period shows overage hours and value separately |

Periods are generated ahead from the cadence and shown as a list under the contract with contracted, carried over, consumed, remaining, forecast and state. A period can be created manually for an off-cycle block.

### 5.5 Burn-down and forecast (TB-07, TB-08)

The account's Budget view (also the one budget dashboard of the pilot) shows per contract per current period: consumed hours and value against contracted plus carry-over, a burn bar that turns amber at the first configured threshold and red past 100 percent, and a forecast to period end. Every number drills through: clicking consumed opens the list of time entries behind it, filterable by person, ticket, activity type and billable class, exportable.

Forecast wording is fixed so the client-facing view (when enabled) and the internal view agree: "At the current rate (X hours per business day over the last N business days), this period will finish at Y hours (Z percent of contracted)." N defaults to 10 business days on the account calendar, configurable per account.

### 5.6 Threshold alerts and renewal alerts (TB-09, INT-03)

Per contract: thresholds as percentages (default 50, 75, 90, 100), internal recipients (defaults to the account owner), and an optional client contact. When consumed crosses a threshold within a period the recipients get a notification and an email, once per threshold per period. The alert text carries the numbers from 5.5 and a link to the Budget view. Renewal alerts fire at configurable lead times before the contract end (default 90, 60, 30 days) to the account owner, and the account record shows an "Expiring" chip.

### 5.7 Billing periods, adjustments and exports (TB-11, TB-14, INT-02)

Each account has one billing period per calendar month (independent of contract periods, which may be quarterly). Its states:

| State | Who moves it | Effect |
|---|---|---|
| Open | System, at month start | Entries accepted |
| Submitted | Account owner | Entries still accepted but the owner is signalling readiness; a summary is produced |
| Approved | Finance role | Entries dated in the period are refused; only adjustments dated in the current open period may reference them |
| Locked | Finance role, or automatically N days after approval | Nothing referencing the period changes; the export is produced from this state |
| Exported | System, when the finance connector delivered the file | The file, checksum and delivery record are kept |

A period can move back from Submitted to Open; from Approved or later it cannot; corrections are adjustments. An adjustment is a separate record linked to the original entry: type (correction, write-off, reclassification), signed minutes or a new billable class, reason, approver. The original is never edited (TB-11). The ticket's time list shows the original struck through with the adjustment beneath it and the net.

Exports: any time list, the per-ticket hours breakdown (TB-10: by person, role, date, activity type), the period summary and the finance export are downloadable as Excel or CSV. The finance export uses the THG finance layout (one row per entry or adjustment with account, contract, period, person, role, date, minutes, activity, billable class, rate, currency, amount, ticket key, after-hours class) and is also delivered automatically through the finance connector when a period locks (INT-02).

### 5.8 Non-ticket time and the personal timesheet (TB-12)

A personal Timesheet view shows the signed-in person's week: one column per day, rows for each ticket and each non-ticket bucket they logged against, a daily total against their working calendar, and empty cells to log directly. Non-ticket buckets appear per account as rows the person can pick. Unlogged hours against the calendar are highlighted; Axel's unlogged-time nudge (AI-06) reads the same numbers.

### 5.9 Empty and edge states

- Account with no contract: the Budget view and the time widget say "No contract yet" and link to the contract record; time can still be logged (classed Internal) so onboarding weeks are not lost.
- Contract without a rate card: entries save with no rate and a warning on the period summary; the export refuses to lock a period containing unrated billable entries.
- Rate card change mid-period: entries keep the rate of their performed date; the period summary shows both rates.
- Deleting is never offered for entries; a mistaken entry is written off by an adjustment.
- Time on a cancelled ticket stays and remains reportable.

## 6. Rollout

1. **Phase 2 (Focused pilot):** time entries on tickets with activity type and billable class, the resolution gate, contracts with periods and rollover for retainers and T&M, burn-down with drill-through, per-ticket breakdown, Excel and CSV exports of lists. Depends on Ticket Management transitions and Accounts & Administration calendars (for date defaults only). Independently demoable: one account, one retainer, logged hours, a burn bar.
2. **Phase 3 (Operational replacement):** rate cards with snapshots, prepaid blocks and fixed fee, overage rules, forecast, threshold alerts, adjustments and write-offs, billing periods with locking, finance export and connector, after-hours flagging on the account calendar, renewal alerts, personal timesheet with non-ticket buckets. Depends on the connector framework and the calendar engine.
3. **Phase 4 (Later):** multi-currency (TB-15), profitability view with cost rates (TB-16), any additional buckets or approval flows XMS asks for.

## 7. Success criteria

- A consultant logs 90 minutes of Development on a ticket in under 20 seconds from the ticket record, and the contract card shows the new total without a page reload.
- Resolving a ticket with zero time is refused; choosing "Resolved by client" allows it and the audit trail shows the exemption.
- A retainer of 40 hours per month with Carry month and 10 unused hours shows 50 available next month and 40 the month after.
- With consumed at 38 of 40 hours and Block overage, a billable entry of 3 hours is refused with a reason; changing the rule to Allow at overage rate saves it and shows 1 hour at the overage rate.
- Changing a role's rate on 2026-11-01 leaves entries dated 2026-10-31 at the old rate and shows both rates on the November summary if October entries are adjusted in November.
- Locking October refuses a new entry dated 2026-10-15 with a clear message, at the database level as well as in the form.
- The finance export for a locked period matches the period summary to the cent and carries a checksum recorded on the period.
- A threshold of 75 percent fires exactly once for a period even when three entries cross it in the same minute.
- The Budget view forecast for an account with 20 hours consumed over 10 business days and 12 business days left reads 44 hours at period end.

## 8. Open questions

- **Finance export layout.** The exact THG finance column set is not documented. Default assumption: the column list in 5.7; finance confirms in Phase 3 week one and the layout is a versioned template.
- **Auto-lock delay.** Default assumption: periods lock automatically 5 business days after approval unless finance locks earlier.
- **Premium rate vs comp time.** Whether after-hours handling is per contract or per account. Default assumption: per contract, defaulting from the account.
- **Pre-sales time.** Whether pre-sales hours belong under a prospective account or an operator bucket. Default assumption: an account can exist in `prospect` status with a Pre-sales bucket and no contract.
- **Time granularity.** Default assumption: 15-minute rounding is off; entries are stored as entered and finance rounding, if any, is applied in the export template.
