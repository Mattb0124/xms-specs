# Functional Spec: Measurement & Calibration

**Status:** Draft, blocked on [C-01](../../00-overview/CLARIFICATIONS-NEEDED.md)
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Resolution Ladder & Routing](../resolution-ladder/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Time Certification](../time-certification/FUNCTIONAL-SPEC.md), [Collaboration Signal](../collaboration-signal/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md), [Audit & Analytics](../../01-architecture/AUDIT-AND-ANALYTICS.md)
**Requirements covered:** MC-01, MC-02, MC-03, MC-04, MC-05, MC-06, MC-07, MC-08, MC-09, MC-10
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `backend/src/worker`, `frontend`

---

## 1. Problem

Once the ladder exists, the obvious next mistake is to measure it badly. Two failures are easy and both are expensive.

The first is a single "routing accuracy" number. Under-routing (classified low, then escalated) and over-routing (classified high, when the desk could have closed it) have opposite causes and opposite fixes, and averaging them hides both.

The second is publishing a resolution rate per person. The moment an individual's rate is visible, the rate is what gets managed: tickets get classified to protect it, and the number stops describing reality. The measure has to be useful to a manager without being usable against a person.

## 2. Current state (what exists today)

Nothing. `frontend` ships operational and usage dashboards, but none of them know about paths, misroutes or calibration. The data this module reads comes from [Resolution Ladder & Routing](../resolution-ladder/FUNCTIONAL-SPEC.md), which does not exist yet either.

## 3. Goals

- Four numbers, split on the ownership line, plus the path-0 fallback signal.
- Denominators set by the **classified** path, so a path-3 ticket never enters the front desk's figure.
- Misroutes detected by the system, not reported by people.
- A calibration loop that turns disagreement into labelled training signal.
- A second loop that checks the people doing the calibrating.

## 4. Non-goals / out of scope

- Producing the path data. That is the resolution ladder module.
- Individual performance measurement. Explicitly forbidden below, and this is a constraint on the data model rather than on the reports.
- Replacing the operational dashboard. DR-02 keeps its job; these are different numbers for a different question.
- MTTR and ticket volume. DR-15 states they cannot be added to the scorecard, and nothing here reintroduces them.

## 5. User-facing behaviour

### 5.1 Intake mix (MC-01)

The share of intake landing at each of the four paths, per account, per period, with trend, rolling up to the portfolio. This is the headline: it says whether resolution is moving toward the client.

### 5.2 The two resolution rates (MC-02, MC-03)

| Measure | Denominator | Reported at |
|---|---|---|
| Front-desk resolution rate | Tickets whose **classified** path was 1 or 2 | Team and account only |
| Engineer resolution rate | Tickets whose **classified** path was 3 | Account and practice only |

A ticket classified 3 is absent from the front desk's denominator **regardless of outcome**, and no configuration can move it in. That sentence is a build instruction: the exclusion is structural, not a filter someone can change in settings.

**Neither rate resolves to an individual.** No screen, no export, no report pack, no ad-hoc query surface. Individual coaching signal comes from MC-07 cause tags and CL-04, which are designed for it.

### 5.3 First move to resolver (MC-06)

First-contact resolution is redefined: the ticket reached its **final resolver on the first move**, not the service desk having solved it. Under the ladder, a correct immediate escalation is a success, and the legacy definition would score it as a failure.

The legacy first-level figure stays available during transition, labelled as legacy wherever it appears, so a number in a client deck does not silently change meaning mid-quarter.

### 5.4 Misroute detection (MC-04, MC-05)

Where classified path and actual path disagree, a misroute is raised automatically. Nobody reports it. Direction comes from the ownership trail:

- **Under-routing**: classified low, escalated. The desk could not do it.
- **Over-routing**: classified high, resolvable at the front desk. An engineer did work the desk could have done.

They report as **distinct rates, never as one accuracy figure**. Over-routing reports beside DR-13's principal-engineer first-touch measure, since over-routing is its mechanism.

### 5.5 The review queue (MC-07)

Misroutes queue for the technical manager weekly. Each is tagged **model was wrong** or **person was wrong**, with a short reason. Unreviewed misroutes age visibly and surface to the support director past a configured age.

The weekly cadence is deliberate. Daily makes it a chore that gets skipped; monthly makes the ticket too cold to judge.

### 5.6 Tags as training signal (MC-08)

Cause tags are retained as labelled training signal, reportable by cause, account and manager. A **model was wrong** volume trend is visible beside the classifier's accuracy, so the two can be read together: a classifier improving while "model was wrong" rises means the tagging is drifting, not the model.

### 5.7 Calibrating the calibrators (MC-09, MC-10)

The support director samples a manager's tags, records agreement or disagreement per sampled item, and sees disagreement rate per manager. **Sampling is visible to the manager**; it is a calibration loop, not surveillance.

MC-10 compares calibration quality, ladder mix, misroute rate and certification completeness **between** managers and between service desk teams, not only within accounts, on a surface the support director and service desk lead own. Variance between managers is the thing that says whether "person was wrong" means the same thing in two places.

### 5.8 Empty and edge states

- A period with no misroutes shows nothing to review rather than an empty queue chrome.
- An account with too few tickets for a stable rate says so instead of rendering a percentage from four tickets.
- A ticket with no derived actual path is absent from misroute detection, not counted as agreement.

## 6. Rollout

1. **Silent measurement.** MC-01 to MC-03 computed and inspectable internally while the classifier runs silently (ladder rollout step 2). Nothing published.
2. **Misroute detection.** MC-04 and MC-05 with the review queue MC-07. This is the loop that earns the right to let classification drive routing.
3. **Publication.** MC-06 alongside the legacy figure, and the team surfaces.
4. **Second loop.** MC-08, MC-09, MC-10 once there is enough tag volume to be worth sampling.

## 7. Success criteria

- A ticket classified path 3 cannot be made to appear in the front-desk denominator by any configuration change, proven by test.
- No screen, export or report resolves MC-02 or MC-03 to a named person, proven by test.
- Under-routing and over-routing never render as a single combined accuracy figure.
- A misroute is raised without any human reporting it.
- The legacy first-contact figure is labelled as legacy everywhere it appears.

## 8. Open questions

- **C-01 blocks this module** through the ladder: without settled routing, misroute direction has no stable meaning.
- What is the minimum ticket count before a rate is published rather than suppressed?
- Does "team" in MC-02 mean the service desk team, the account team, or the shift? Three different denominators.
- MC-09 samples a manager's tags. Who samples the director's sampling, or is that where the loop deliberately stops?
