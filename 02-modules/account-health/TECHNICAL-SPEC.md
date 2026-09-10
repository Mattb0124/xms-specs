# Technical Spec: Account Health & Experience

**Status:** Draft, not yet verified in code
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Dashboards & Report Packs](../dashboard-and-reporting/TECHNICAL-SPEC.md), [Resolution Ladder & Routing](../resolution-ladder/TECHNICAL-SPEC.md)
**Requirements covered:** AH-01 to AH-09

---

## 1. Why this is a draft

No code exists for this module. The account dashboard that ships today is a different thing: a periodic read of delivery, not a continuous relationship record.

## 2. Data model

| Table | Holds |
|---|---|
| `acct.account_activity` | AH-01. One row per touch, whatever its origin: ticket event, time entry, comment, call, report sent. Carries actor, path, shift and source. Append-only |
| `acct.account_patterns` | AH-02. Derived recurring requests, themes, commitments and precedents over a rolling window. Rebuildable |
| `acct.perception_notes` | AH-06. Transcript, forwarded email, typed note or voice note, with attribution, timestamp and transcription state. Attachments follow the standard scan pipeline |
| `acct.account_priors` | AH-07. The dated starting assessment, immutable once written, with author |
| `acct.account_touches` | AH-09. Direct conversations with date and participants |
| `rpt.account_trajectory_daily` | AH-03 and AH-04 components snapshotted daily, per account, per service line |

`service_line` sits on the trajectory and pattern tables from the first migration (AH-08), defaulted to support. Adding a second line is configuration; no surface hard-codes the default.

## 3. The pairing rule (AH-04)

"No surface renders AH-03 without AH-04 beside it" is enforced in the read model, not in each screen. The API returns readiness and experience as **one object** that cannot be requested separately, with experience carrying an explicit unknown state where there is no CSAT. A screen that wants only readiness has nothing to call.

That is the only way the rule survives the third screen someone adds.

## 4. Domain rules

- **Readiness calibration** is per account against its own history, so the function takes the account baseline as an argument rather than a global target. Two accounts with different baselines and identical movement must score alike, and that is the unit test.
- **Ranking** (AH-05) is computed server-side from health movement, exposure, consumption position and open divergences. The browser sorts nothing. With thin data the rank degrades to a stated insufficient-signal bucket, never to alphabetical.
- Voice transcription goes through the Axel adapter, subject to the account AI switch. With AI off the note is stored and playable, flagged untranscribed, and no call is made.

## 5. Ordering

1. `acct.account_activity` populated from existing ticket, time and comment events, with the service-line seam present from the first migration.
2. AH-07 priors, before cutover, so accounts start with a baseline.
3. AH-06 perception capture, typed and forwarded first, voice once transcription is wired.
4. AH-04 experience trajectory from CSAT plus perception.
5. AH-03 readiness, once the ladder produces path data.
6. AH-05 ranking and AH-09 cadence.

## 6. Testing

- A test that no endpoint returns readiness without experience.
- Calibration test: two accounts, different baselines, same movement, same score.
- A test that the ranked surface never returns alphabetical order, including on empty ranking inputs.
- A test that a second service line can be added with configuration and no migration.
- Isolation suite coverage on every table above, both roles. Perception notes carry client-relayed content and must never be portal readable.
- Voice note with AI disabled: stored, flagged, no HTTP call.

## 7. Risks

- **Volume.** `acct.account_activity` is one row per touch across the whole practice. Partitioning and retention need deciding with the rest of the append-only family.
- **Perception notes are sensitive.** They hold opinions about clients and are attributable. Read scope is an open question in the functional spec and needs answering before capture is switched on.
- **Trajectory noise.** Daily snapshots on a low-volume account produce a jagged line that reads as instability. Smoothing is a presentation decision, and it must not be applied silently.
