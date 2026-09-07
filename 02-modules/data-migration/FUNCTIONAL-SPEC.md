# Functional Spec: Data Migration & Cutover

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [ServiceNow Sync](../servicenow-integration/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Roadmap](../../03-delivery/ROADMAP.md), [Decision Log](../../00-overview/DECISION-LOG.md)
**Requirements covered:** DM-01, DM-02, DM-03, DM-04
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `infra`

---

## 1. Problem

The DMS practice has years of history in ServiceNow CSM: open and closed cases, the comment threads that explain them, attachments, and the time that was logged against them. Contract balances, consumed hours and current retainer positions live partly in ServiceNow and partly in finance spreadsheets. When ServiceNow is switched off in 2027, that history is the baseline every client conversation depends on: "how many tickets did we close for you last year", "how many hours are left on the block", "when did this problem last happen". Without it the new product starts blind (DM-01, DM-02).

Two things make this harder than a bulk copy. First, the numbers have to agree with finance before anyone trusts the product, so every import must produce a reconciliation that a person signs (DM-03). Second, the practice cannot stop working while the move happens, and the assessment's chosen approach is explicit: import, then shadow sync, then a short freeze, then cutover with rollback, instead of asking consultants to enter tickets twice (DM-04, assessment p.13).

This module covers the four distinct cases the workbook asks for:

1. **Historical ticket import**: cases, journal entries (split into public comments and internal work notes), attachments, and time records.
2. **Commercial history import**: contracts, consumed hours per period, and the balances carried forward, reconciled to finance.
3. **Reconciliation**: counts and hour totals, source against target, deltas explained, sign-off recorded.
4. **Parallel run and cutover**: the period where both systems run, the freeze, the switch, the rollback decision, and the decommission.

## 2. Current state (what exists today)

- **Nothing migration-shaped exists in AIX.** No import tooling, no reconciliation, no cutover runbook. The only precedent for loading ticket data is the studio's demo seed script `scripts/seed_xms_demo.py` on the `feature/xms-ticketing` branch, which creates a handful of fictional contracts and tickets for a demo and is not a migration tool.
- **ServiceNow read access exists once**: the `servicenow_ams_mcp` module in `aix-mcp` (source on another branch, only compiled files on the current checkout) has a ServiceNow client that the migration extractor can learn from but does not reuse.
- **The XMS model the data lands in** is defined in the [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md) and [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md) specs. The state and field maps the import uses are the same maps the [ServiceNow Sync](../servicenow-integration/FUNCTIONAL-SPEC.md) connector uses, so a state translated one way during import is translated the same way during the parallel run.
- **Migration facts are still undefined**: the assessment lists "migration scope undefined (period, files, reconciliation)" as a risk, with the mitigation "define with DMS; import + shadow sync + short freeze + cutover with rollback". Brookfield's documentation (Sofi, Vini) is due 2026-09-25.

## 3. Goals

1. **The baseline survives.** Every case XMS decides to keep, with its comments, work notes, attachments and time, is in XMS with its original dates, actors and ServiceNow number, searchable and reportable as if it had always been there.
2. **Finance agrees before cutover.** Contract balances and consumed hours in XMS match finance's records period by period, and the person who checked signs the reconciliation inside the product.
3. **Re-running is safe.** Any batch can be run again after a fix without creating duplicates; the second run only changes what the fix changed.
4. **Nobody enters anything twice.** During the parallel run, ServiceNow changes flow into XMS through the sync connector; consultants work in one system at a time.
5. **Cutover is a decision, not a hope.** Rollback criteria are written down before the freeze, checked during it, and the decision is recorded.
6. **The evidence is kept.** Batches, mappings, unmatched records, reconciliation reports and sign-offs are retained so a later dispute can be answered.

## 4. Non-goals / out of scope

- **Migrating ServiceNow configuration** (forms, workflows, notifications, reports). XMS has its own configuration; only data moves.
- **Migrating ServiceNow knowledge articles automatically.** Articles are a curation job for the [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md); the import can attach a ServiceNow KB reference to a ticket but does not create articles. Decided so that the knowledge base starts clean.
- **Migrating every client instance.** The first migration is the DMS practice's own ServiceNow CSM. Client-owned instances such as Brookfield's are synced, not migrated ([ServiceNow Sync](../servicenow-integration/FUNCTIONAL-SPEC.md)).
- **Ongoing sync.** Owned by the ServiceNow Sync module; this module uses it during the parallel run.
- **A generic import framework for other sources** (Jira, spreadsheets). The batch and record model is generic on purpose, but only the ServiceNow extractor and the finance balance loader ship. Deferred to Phase 4 if a second source appears.
- **Rewriting history.** Imported audit events are marked as imported; XMS never pretends an import was a live action.

## 5. User-facing behavior

### 5.1 Vocabulary

| Set | Values | Notes |
|---|---|---|
| Object kind | account, contact, user, case, comment, work note, attachment, time record, contract, contract period balance | One batch imports one object kind for one account |
| Batch status | draft, extracting, extracted, mapping, mapped, loading, loaded, reconciling, reconciled, signed off, failed, superseded | A batch that is re-run supersedes the previous run of the same scope |
| Record status | pending, loaded, updated, skipped, unmatched, error | `updated` means a re-run changed an existing target row; `unmatched` means an identity or lookup could not be resolved |
| Reconciliation status | pending, matched, delta explained, delta open | A batch cannot be signed off with a `delta open` line |
| Cutover stage | not started, import, shadow sync, freeze, cutover, parallel run, decommissioned, rolled back | One stage record per account being migrated |

### 5.2 The migration console

An admin-only area of XMS Web (permission `admin:migration`) in the ServiceNow list grammar from the [Design System](../../01-architecture/DESIGN-SYSTEM.md): a dense list, a record view, a slim toolbar. Four views:

1. **Batches.** One row per batch: account, object kind, source range (for example cases opened 2021-01-01 to 2026-12-31), status, counts (extracted, loaded, updated, skipped, unmatched, errors), started, finished, run by. Click opens the batch record. New batch is a full-screen form: account, object kind, source (ServiceNow instance profile or uploaded export files), range, mapping version, dry run toggle.
2. **Batch record.** Properties, progress bar while running, then three tabs: **Records** (per-record list with source id, target key, status, message; filter to unmatched or error; each row opens the source payload and the target record side by side), **Mapping** (the state map, priority map, group map and identity map versions used, with a link to edit them in the [ServiceNow Sync](../servicenow-integration/FUNCTIONAL-SPEC.md) mapping screens), **Log** (the batch's run history: dry runs, real runs, who ran them, superseded runs).
3. **Reconciliation.** One row per reconciliation line: account, object kind or contract and period, source figure, target figure, delta, status, explanation, explained by. Lines with a delta are highlighted with the `overdue` signal colour until explained. A **Sign off** button at the top of the account's reconciliation becomes available only when every line is `matched` or `delta explained`; signing records who, when, and the report snapshot.
4. **Cutover.** One card per account being migrated showing the current stage, the dates of each stage, the rollback criteria checklist with pass/fail per item, and the stage transition button. Advancing to `cutover` requires a signed reconciliation and all rollback criteria checked.

Empty states: no batches yet shows "Create the first batch for an account; start with accounts and contacts, then cases". A batch with zero unmatched records shows "All records resolved".

### 5.3 What gets imported and how it looks afterwards

| ServiceNow object | Lands as | What a user sees on the ticket |
|---|---|---|
| Customer account | XMS account (matched by name and account key to an existing account; never created silently) | Nothing new; the account already exists in XMS |
| Contact and user | XMS contact (portal user if the email matches an invited user) or internal user by email; unmatched people become a placeholder contact named from the source | Requester and actor names as they were |
| Case | Ticket with its original number in **External ref** (`CS0012345` from ServiceNow stays searchable), original opened, resolved and closed dates, the XMS state translated by the same state map the sync connector uses, priority from the source or re-derived from impact and urgency when the account's matrix says so, assignment group and assignee mapped | The ticket reads as history: a grey "Imported from ServiceNow on 2026-11-14" line at the top of the activity tab |
| Journal entry, comments field | Public comment | In the conversation, dated as the source |
| Journal entry, work notes field | Work note | In the internal thread only; never public |
| Attachment | Attachment with scan pending until the malware scan clears it | Downloadable once clean; quarantined ones show a placeholder |
| Time card or time worked | Time entry dated as performed, with the activity type defaulted to `Analysis` and the billable class from the source or the contract default, and an `imported` marker | Counted in per-ticket hours and, when the period is loaded, in consumption |
| Resolution code and notes | Resolution record; where the account's resolution codes differ, mapped through the resolution code map; the solution link is `none (imported)` | Resolution tab populated; the knowledge base is not touched |
| SLA definitions and breach flags | Not replayed. Imported tickets carry the source's breached flags as read-only facts; clocks are not created for closed tickets | SLA badge shows "Imported" instead of a countdown on closed tickets |

Audit: every imported row gets one `imported` audit event carrying the source timestamp, the batch id and the source id. Dates on the ticket are the source dates, not the import date, so trend reports are correct.

### 5.4 Commercial history

Contracts are created in XMS by an administrator from the finance records before the balance load; the import matches them by contract number. The balance loader takes one row per contract per period: contracted hours or value, consumed hours, carried-over hours, and the closing balance, straight from the finance workbook. After loading, the consumption view for a past period shows the finance figure as the period's locked total, and any imported time entries in that period are reconciled against it. Where the sum of imported time entries does not equal the finance figure, the reconciliation line shows the delta and the operator chooses: trust finance (the period is locked at the finance figure with a balancing adjustment entry marked `migration adjustment`), or trust the entries (finance updates its record). Either choice is written into the explanation.

### 5.5 Identity mapping

Before the case import, a **people map** batch lists every ServiceNow user and contact seen in the extract with the XMS match found by email, the match confidence, and an editable target. Unmatched rows default to a placeholder contact (`Unknown person (ServiceNow: J. Smith)`) so the import never blocks on a person; the admin can merge the placeholder into a real contact later and every imported reference follows.

### 5.6 Re-runs and dry runs

Every batch can run as a dry run first: it extracts, maps and reconciles but writes nothing except the batch record and its report. A real run after a dry run loads. A re-run of a loaded batch uses the source id as the identity: existing targets are updated where the source changed, new source rows are added, nothing is duplicated, and the batch record shows `updated` counts. Deleting a batch is not offered; a superseded batch is kept as evidence.

### 5.7 Parallel run, freeze, cutover, rollback

1. **Import** the closed history and the open cases into the isolated migration environment; reconcile; fix mappings; re-run until signed off.
2. **Shadow sync**: promote the signed batches into production XMS, then switch the ServiceNow Sync connector for the XMS instance to `ingest only`. ServiceNow stays the working system; every change flows into XMS within minutes. Consultants can read XMS but the desk banner says "ServiceNow is the system of record until <date>".
3. **Freeze**: a short window (target 4 hours, weekend) where ServiceNow is set read-only for the practice, a final delta batch runs, reconciliation runs again on the delta, and the rollback criteria are checked.
4. **Cutover**: XMS becomes the system of record; the banner changes; the ServiceNow connector switches to `bidirectional` only if a client instance needs it, otherwise `off`; the inbound email aliases are repointed to XMS.
5. **Parallel run**: an agreed period (default 30 days) where ServiceNow stays available read-only for lookups and as a rollback target, and the cutover card tracks the exit checks.
6. **Rollback** (at any point before the parallel run ends): ServiceNow returns to read-write, XMS goes to `ingest only`, and tickets created in XMS during the window are exported back through the connector. The criteria that trigger rollback are on the cutover card and written before the freeze: reconciliation delta open, email intake failing for more than one hour, SLA clocks disagreeing with ServiceNow on more than one percent of open tickets, or a client-facing defect with no workaround.
7. **Decommission**: after the parallel run, a checklist on the cutover card (final ServiceNow export archived, aliases confirmed, connector off, licences cancelled, access revoked) closes the stage as `decommissioned`.

### 5.8 Evidence retention

Batches, per-record results, the mapping versions used, reconciliation reports and sign-offs are kept for the account's retention period, and the final ServiceNow export files are archived in S3 under the account prefix. The console can export any reconciliation report to Excel.

## 6. Rollout

1. **Phase 2 (Focused pilot): representative import.** ServiceNow extractor and case, comment, work note, attachment and people-map batches for one account over a limited range into the migration environment; dry runs; the reconciliation view for counts. Depends on the Ticket Management core, the ServiceNow Sync mapping screens and the attachment scanning pipeline from Phase 1. This is the "representative import plus one integration scenario" item on the assessment's pilot list.
2. **Phase 3 (Operational replacement), first half: full history and commercial history.** All accounts, all objects, time records, contract period balances, hour reconciliation, sign-off, and promotion from the migration environment into production. Depends on the Time, Contracts & Budget module's billing periods.
3. **Phase 3, second half: parallel run and cutover.** Shadow sync in `ingest only`, the freeze runbook, the cutover card with rollback criteria, the decommission checklist. Depends on the ServiceNow Sync connector being production grade and on the email alias repoint.
4. **Phase 4: second-source extractor** only if a non-ServiceNow source appears.

## 7. Success criteria

- A closed 2023 case with three public comments, two work notes, one attachment and 4.5 hours of time appears in XMS with its ServiceNow number in External ref, the same dates and authors, the work notes hidden from the portal, the attachment downloadable after scanning, and 4.5 hours on the ticket's hours breakdown.
- Running the same case batch twice yields identical counts on the second run with zero new tickets and zero duplicate comments.
- For every migrated account, the reconciliation view shows ticket counts by state and hour totals by contract and period with zero `delta open` lines before the Sign off button is enabled, and the signed report is downloadable as Excel with the signer's name and time.
- A contract period whose finance balance differs from the imported entries by 2.0 hours shows the delta, records the operator's choice, and the period's consumption in Time & Budget reflects that choice.
- During shadow sync, a case updated in ServiceNow appears updated in XMS within five minutes with no duplicate.
- The cutover card refuses to advance to `cutover` while any rollback criterion is unchecked or the reconciliation is unsigned, and a rollback executed in the parallel run restores ServiceNow as the working system with XMS-created tickets exported back.
- Imported tickets never create SLA clocks, never send notifications, and never appear as live activity in the operator feed.

## 8. Open questions

- **Which cases to keep.** All history, or a cut-off (for example closed cases from the last three years)? Default assumption: all cases for active accounts; closed cases older than five years for inactive accounts are archived as an export only.
- **Where time lives in ServiceNow.** Time cards, a custom time-worked field, or a separate spreadsheet? Default assumption: a custom time-worked table on the case, confirmed by Vini by 2026-09-25; the loader accepts a CSV shape as the fallback.
- **Finance's period granularity.** Monthly per contract? Default assumption: monthly, matching the default contract period cadence in Time & Budget.
- **Attachment volume and size.** Unknown. Default assumption: under 50 GB total; anything over the 25 MB per-file cap is imported as a reference row with a download link to the archived export rather than a live attachment.
- **Freeze window length and day.** Default assumption: a Saturday, 4 hours, agreed with the client-facing leads two weeks ahead.
- **Parallel run length.** Default assumption: 30 days, extendable once by 30 days.
- **Access to a ServiceNow export API versus file exports.** Default assumption: Table API with a read-only integration user for the XMS instance; CSV/XML export files as the fallback for the same object kinds.
