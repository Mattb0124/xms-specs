# Technical Spec: Outcomes

**Status:** Draft, not yet verified in code
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Dashboards & Report Packs](../dashboard-and-reporting/TECHNICAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md)
**Requirements covered:** OC-01, OC-02, TM-10, TM-26 (association owned by Ticket Management)

---

## 1. What exists today

Change windows and ticket groups ship in `frontend` and the API. Revision 3 reframes TM-10 as an outcome of a particular type rather than a parallel concept, so this module absorbs an existing structure rather than adding one beside it.

That migration is the delicate part: change windows carry live data and are referenced by the transition gate (TM-18 freeze rules).

## 2. Data model

| Table | Holds |
|---|---|
| `acct.outcomes` | OC-01: name, stated business result, owner, period, status, type, client visibility, linked contract |
| `acct.outcome_types` | The per-account configurable taxonomy, each type carrying its default client visibility |
| `acct.outcome_tickets` | TM-26 association, with attached and detached timestamps so coverage is computable historically |
| `rpt.outcome_coverage_daily` | The TM-26 coverage measure per account, per engineer, per period |

Account scoped, `FORCE ROW LEVEL SECURITY`, policies in the same migration, picked up by the isolation suite.

`status` and `client_visibility` are `text` with `CHECK` constraints and matching TypeScript unions, not enums, so a new status does not need a type migration.

## 3. Visibility is defaulted by type, overridden per instance, always audited

The default lives on `acct.outcome_types`. An instance may override it. **Every override writes an audit event** naming actor, old and new value, in the same transaction as the write.

Change windows migrate to a type whose default visibility is not client visible, which preserves today's behaviour exactly.

The portal read path filters on the **effective** visibility of the instance, never the type default, and the filter is in the data layer. A portal role that could read a non-client-visible outcome through any join is the failure this module is most likely to produce.

## 4. Migrating TM-10

1. Create `acct.outcome_types` with a change-window type, default visibility internal.
2. Create an outcome per existing change window, preserving ids where the API contract exposes them.
3. Repoint the freeze and conflict rules (TM-18) at the outcome, in the same release.
4. Keep the change-window routes answering, backed by outcomes, until the frontend has moved.

Steps 3 and 4 are where a mistake breaks the transition gate, which is a live control. The `frontend` change calendar and `RightNow` read `/v1/change-calendar/at`, and that route must answer identically before and after.

## 5. Coverage (TM-26)

Coverage is the share of tickets **and of delivered hours** carrying an outcome. Hours-weighted coverage is the more honest of the two: a hundred trivial tickets with outcomes and one large unattributed project reads as excellent ticket coverage and poor hours coverage.

Both are computed and both are reported. The coverage floor is a CG-01 registered parameter.

## 6. Ordering

1. `acct.outcome_types` and `acct.outcomes`, with the TM-10 migration.
2. `acct.outcome_tickets` attach and detach.
3. Coverage computation and `rpt.outcome_coverage_daily`.
4. Coverage floor surfacing to the account owner and support director.
5. OC-02 client-facing report, last.

## 7. Testing

- A portal principal cannot read an outcome whose effective visibility is internal, through the list route, the detail route or any join. Isolation suite plus an explicit portal test.
- A per-instance visibility override writes an audit event in the same transaction.
- The change-window migration: `/v1/change-calendar/at` returns identical answers before and after, over a fixture set covering inside, frozen and outside a window.
- Coverage computed both by ticket count and by hours, and the two are reported separately.
- A retired outcome type stays readable on outcomes already carrying it.

## 8. Risks

- **The TM-10 migration touches a live control.** The transition gate refuses changes during a freeze. A migration error there blocks legitimate work or permits a change during a freeze, and the second is worse.
- **Coverage reported without the floor.** A result-led client report over thin coverage hides work. OC-02 shipping before the floor is the sequencing error to avoid.
- **Type taxonomy sprawl.** Per-account configurable types with no maintained default list produces twelve accounts with twelve vocabularies and no portfolio view. The default list needs an owner in CG-01.
