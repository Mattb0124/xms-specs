# Technical Spec: Time Certification

**Status:** Draft, not yet verified in code
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Configuration Governance](../configuration-governance/TECHNICAL-SPEC.md)
**Requirements covered:** TC-01 to TC-07

---

## 1. Why this is a draft

No code exists for this module. The timesheet that ships today (`/v1/timesheets/me`, the quick Log time form, the TB-12 buckets) is the surface this replaces as the daily mechanism, and it stays as the corrective one.

## 2. Where certified time lands

Certified effort writes to the **same time-entry store** as ticket-level entry (TB-01). There is not a second ledger. An entry carries its origin (`ticket` or `certification`) so capture rate is computable, but every downstream consumer, burn, utilisation, profitability, billing export, reads one table.

This is what lets TB-02 accept either source as satisfying the resolution gate without special-casing.

## 3. Data model

| Table | Holds |
|---|---|
| `acct.certifications` | One row per person per day: submitted state, submitted at, device. Completeness (TC-07) is computed from presence, not from magnitude |
| `acct.certification_activities` | The confirmed activities on a certification: proposed or added, source signal, ticket or bucket or other, effort, and whether the person edited the proposal |
| `op.certification_thresholds` | The TC-06 role-configurable other-bucket threshold, its owner and its review cadence. Registered in CG-01 |

`acct.certifications` is account scoped where the activity is; the certification header itself is operator scoped by person, since a person crosses accounts in one day. That split needs care: the header carries no account data, and every activity row carries `account_id` and is RLS protected.

## 4. Domain rules

- **Proposal generation** is pure over the day's signals (ticket events, comments, existing entries, calendar), so it is unit-testable without a database and produces the same proposals for the same day.
- **No computed pre-fill.** TC-04 forbids a duration field pre-filled with a computed actual. The proposal carries a suggested **shape** (which activity, which ticket) and never a duration value. The API response must not include a duration for an unconfirmed activity, so the client has nothing to pre-fill with even by accident.
- **Other-bucket policing is weekly.** The evaluation runs on a weekly cadence in the worker, never per submission.
- **Locked periods.** A certification writing into a locked billing period is refused with the period named, using the same trigger that guards TB-14.

## 5. The TC-07 enforcement

"No report, screen or export renders certification magnitude as a performance measure of a person, and this is enforced rather than conventional."

Implementation: completeness (a boolean per person per period) is exposed; magnitude per person is not. There is no endpoint returning hours certified grouped by person, and the export surfaces carry completeness only. Capture rate for DR-16 is computed at account and practice level from the entry store, never as a per-person column.

Treat this as an isolation-class constraint: the test asserts the absence of the shape, not the styling of a screen.

## 6. Ordering

1. `acct.certifications` and `acct.certification_activities`, with proposal generation and the confirm flow (TC-01, TC-02, TC-04, TC-05).
2. TC-03 typed capture, then voice through the Axel adapter.
3. TC-06 threshold and weekly evaluation, with the CG-01 registration.
4. TC-07 completeness reporting.
5. TB-02 gate integration, accepting certification-sourced time.

## 7. Testing

- A test that no API response carries a duration for an unconfirmed proposed activity.
- A test that no endpoint or export returns certified magnitude grouped by person.
- Proposal determinism: same day signals, same proposals.
- The other bucket accepts an entry with no ticket, no account and no activity type.
- A certification into a locked period is refused, naming the period.
- Isolation suite coverage on `acct.certification_activities`; a test that the operator-scoped header carries no account data.
- AI off: TC-03 accepts typed input and makes no transcription call.

## 8. Risks

- **The flow becomes a timesheet.** Any pre-fill, any required field, any daily nag and the value is gone. The constraints in TC-04 and TC-06 are the mitigation and they should not be relaxed for convenience.
- **Header scoping.** A person-scoped header with account-scoped children is the one place in this module where the isolation model is not the default shape, and it needs review.
- **Capture rate gates the scorecard.** DR-16 makes every value-derived line provisional until capture rate passes a threshold, so this module is on the critical path for the scorecard being trustworthy at all.
