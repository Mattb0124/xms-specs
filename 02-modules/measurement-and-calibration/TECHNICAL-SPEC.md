# Technical Spec: Measurement & Calibration

**Status:** Draft, not yet verified in code. Blocked on [C-01](../../00-overview/CLARIFICATIONS-NEEDED.md) through the ladder
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Resolution Ladder & Routing](../resolution-ladder/TECHNICAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Audit & Analytics](../../01-architecture/AUDIT-AND-ANALYTICS.md), [Dashboards & Report Packs](../dashboard-and-reporting/TECHNICAL-SPEC.md)
**Requirements covered:** MC-01 to MC-10

---

## 1. Why this is a draft

No code exists, and the data this module reads comes from a module that does not exist either. Nothing here is verified in code.

## 2. The constraint that shapes the design

MC-02 and MC-03 must never resolve to an individual, and MC-02's denominator must not be movable by configuration. Both are structural, not reporting filters.

The consequence: the two resolution rates are computed into **pre-aggregated rows keyed by team and account** (MC-02) and by **account and practice** (MC-03), and the per-ticket detail behind them is not exposed through any read model that carries a person. A query surface that joins the detail back to an assignee would satisfy the letter and break the intent, so the aggregate is the only artefact these measures produce.

The denominator comes from `acct.ticket_paths.classified_path` and nothing else. No settings table participates, so there is no configuration that could move a path-3 ticket into the front desk's figure.

## 3. Data model

| Table | Holds |
|---|---|
| `acct.misroutes` | One row per detected disagreement: ticket, classified path, actual path, direction (under or over), detected at. Direction derived, never entered |
| `acct.misroute_reviews` | The MC-07 tag: cause (`model_wrong` or `person_wrong`), reason, reviewer, reviewed at. Append-only |
| `acct.review_samples` | MC-09: the sampled review, the director's agreement or disagreement, and the note. Visible to the manager by design |
| `rpt.ladder_daily` | Daily snapshot per account of intake mix, the two rates and the misroute rates. Snapshotted so DR-07 trends survive later reclassification |

Direction is `text` with a `CHECK`, not a Postgres enum. Cause tags likewise.

## 4. Domain rules

- **Misroute detection** is a pure comparison of classified against actual path, run by the worker at close. A ticket with an underived actual path produces no misroute, and is not counted as agreement.
- **Rate computation** takes the classified path as denominator input. Written as a pure function so the exclusion rule is unit-testable without a database.
- **First move to resolver** (MC-06) is derived from the ownership trail: did the ticket reach its final resolver on the first move. The legacy first-level figure is computed separately and carries a `legacy` label in its own field, so no caller can render it unlabelled.

## 5. Ordering

1. `acct.misroutes` and detection in the worker, silent.
2. `rpt.ladder_daily` snapshots and MC-01.
3. MC-02 and MC-03 aggregates, internal only.
4. MC-07 review queue, then MC-08 reporting over tags.
5. MC-06 published alongside the legacy figure.
6. MC-09 and MC-10.

## 6. Testing

Per [Test Strategy](../../03-delivery/TEST-STRATEGY.md):

- A test asserting no API response, export or report pack resolves MC-02 or MC-03 to a person. Written against the response shape, not the UI.
- A test that no configuration change moves a path-3 ticket into the front-desk denominator.
- Under-routing and over-routing never returned as a single combined field.
- A ticket with no derived actual path produces no misroute row.
- Isolation suite coverage on every account-scoped table, `rpt.ladder_daily` included.
- Suppression test: an account below the minimum ticket count returns suppressed rather than a percentage.

## 7. Risks

- **Aggregate reverse-engineering.** A team of one makes a team-level rate an individual rate. A minimum team size for publication is needed and is currently an open question in the functional spec.
- **Tag drift.** "Person was wrong" meaning different things to two managers is what MC-09 and MC-10 exist to detect, and neither works until tag volume is meaningful.
- **Snapshot cost.** Daily snapshots per account per measure grow quickly; retention needs setting alongside the rest of `rpt`.
