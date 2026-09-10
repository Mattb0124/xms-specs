# Functional Spec: Account Health & Experience

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Resolution Ladder & Routing](../resolution-ladder/FUNCTIONAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Outcomes](../outcomes/FUNCTIONAL-SPEC.md)
**Requirements covered:** AH-01, AH-02, AH-03, AH-04, AH-05, AH-06, AH-07, AH-08, AH-09
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `backend/src/worker`, `frontend`

---

## 1. Problem

An account owner cannot see their own account. Work happens on it across shifts, across paths, and by people who do not report to them, and the only way to find out is to ask or to run a report. By the time a pattern is visible, it is a complaint.

There is a second problem underneath. Every measure of an account that gets built tends to be a measure of **our** efficiency: throughput, attainment, burn. An account can look healthy on all of them and still be quietly furious. Readiness and experience are different questions and they move independently.

## 2. Current state (what exists today)

`frontend` ships an account dashboard with SLA, consumption, CSAT and a Satisfaction tab, and DR-09 defines a composite customer health score. That is a periodic read of our delivery, not a continuous record of the relationship, and there is nothing that captures what a person knows about an account.

**See [C-06](../../00-overview/CLARIFICATIONS-NEEDED.md): whether DR-09 survives beside AH-03 and AH-04 is unresolved.**

## 3. Goals

- One continuous account truth, always on rather than a report someone runs.
- Visible to the account owner regardless of who did the work or on what shift.
- Two trajectories, never one: readiness and experience, always rendered together.
- Calibrate against the account's own history, not a global target.
- Land people on the accounts that need attention, not on an alphabetical list.

## 4. Non-goals / out of scope

- Replacing the client-facing report. That is DR-03 and OC-02.
- CSAT capture. That is CP-07; this module reads it.
- Scoring people. Nothing here is a measure of a person.
- Being a CRM. Perception capture is about service delivery, not pipeline.

## 5. User-facing behaviour

### 5.1 The continuous record (AH-01)

Every touch on an account lands in one account-level record: any path, any shift, any person, any reporting line. The account owner sees it **without running a report**, including work done by people who do not report to them.

That last clause is the requirement. A record that only shows an owner's own team reproduces the problem it exists to solve.

### 5.2 Patterns, not a feed (AH-02)

The account view surfaces recurring requests, repeated themes, commitments made to the client and precedents set, as patterns over a rolling window. A chronological list is available but it is not the view: a feed of 400 events is the same as no visibility.

### 5.3 The two trajectories (AH-03, AH-04)

| Trajectory | Composed of |
|---|---|
| **Readiness** (AH-03) | Front-desk share, path-0 volume and fallback rate, profile maturity, knowledge coverage |
| **Experience** (AH-04) | CSAT, responsiveness, expectation-management signal, perception notes |

Readiness is calibrated against **that account's own historical mix**, not a global target. An account that has moved from 10 to 25 percent front-desk share is improving even if another account sits at 60.

**Rising front-desk share reads as readiness, not as risk.** Written down because the opposite reading is the intuitive one: fewer engineer hours can look like disengagement, and it is the goal.

**No surface renders AH-03 without AH-04 beside it.** Readiness without experience is how a practice optimises itself into a client leaving happy with the numbers and unhappy with the service.

### 5.4 The ranked surface (AH-05)

The CSM, the technical manager, the CSM lead and the director land on accounts **ranked by attention need**, computed server-side from health movement, exposure, consumption position and open divergences. Never alphabetical, never portfolio order.

Open CAP-11 concentration alerts appear here, and accounts past their AH-09 touch interval surface here too.

### 5.5 Perception capture (AH-06)

Meeting transcripts, forwarded emails, typed notes and voice notes attach to the account record. Each is attributable and timestamped, is searchable, and feeds AH-04. Voice notes transcribe.

The point is that it takes whatever form the knowledge already has. A CSM will not retype a call into a form, but they will forward an email or record thirty seconds of voice.

### 5.6 The crystallised prior (AH-07)

An account can be seeded with a dated starting assessment: the owner's read of health, known fragility, key relationships, continuity risk. It is recorded as a **stated prior**, and later movement renders against it rather than against an empty history. The prior remains readable and attributable.

Without this, every account starts at launch with no history and the first quarter of trajectories is noise.

### 5.7 The service-line seam (AH-08)

The account-health object holds more than one service line. Support is the only line populated at launch. Adding a second requires **configuration, not schema change**, and no surface hard-codes support as the only line.

### 5.8 Touch cadence (AH-09)

Direct account conversations log against the account with date and participant. Rolling coverage per account is visible, a per-account target interval is configurable, and accounts past their interval surface on AH-05.

### 5.9 Empty and edge states

- A new account with no prior says the prior is missing rather than rendering a trajectory from nothing.
- An account with AH-03 data but no CSAT responses renders experience as unknown, and readiness is **still not shown alone**: the pair renders with experience explicitly unknown.
- A voice note that fails to transcribe stays attached and playable, flagged as untranscribed, never silently dropped.

## 6. Rollout

1. **The record.** AH-01 and AH-08's seam, populated from existing ticket, time and comment activity.
2. **The prior.** AH-07, so cutover accounts start with a stated baseline rather than an empty one.
3. **Experience first.** AH-04 from CSAT and perception capture AH-06. Experience is buildable today; readiness depends on the ladder.
4. **Readiness.** AH-03 once the ladder produces path data.
5. **Ranking and cadence.** AH-05 and AH-09 once there is enough signal to rank on.

## 7. Success criteria

- An account owner sees work done on their account by someone outside their reporting line, without running a report.
- No screen or export renders AH-03 without AH-04, proven by test.
- Readiness for an account is computed against that account's own history, demonstrable by two accounts with different baselines and the same movement scoring alike.
- The ranked surface never falls back to alphabetical order, including when ranking data is thin.
- A second service line can be added without a schema migration.

## 8. Open questions

- **C-06:** does DR-09 survive as its own number, or is it superseded by AH-03 and AH-04? Two competing health figures is worse than either.
- What is the "expectation-management signal" in AH-04, concretely? It is the only component with no obvious source.
- Who may read another owner's account health: the whole practice, the leadership line, or the account team plus leadership?
- Do perception notes attached under AH-06 fall inside the client-visible boundary if an account ever requests their record?
