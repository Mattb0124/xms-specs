# Functional Spec: Configuration Governance

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md), [Measurement & Calibration](../measurement-and-calibration/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Resolution Ladder & Routing](../resolution-ladder/FUNCTIONAL-SPEC.md), [Audit & Analytics](../../01-architecture/AUDIT-AND-ANALYTICS.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md)
**Requirements covered:** CG-01, CG-02, CG-03, CG-04
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `frontend`

---

## 1. Problem

The operating model multiplied the number of configurable parameters. Path rules and credential markings, classifier and queue weights, every threshold, the TC-06 guardrail, activity and outcome taxonomies, auto-resolution allowlists, consent flags, CL-05 aggregation minimums, coverage floors. Each was added for a good reason by someone who understood it.

Without ownership they rot within two quarters. Nobody remembers why a threshold is 80, whether it was ever reviewed, or who is allowed to change it. Worse, a number moves on a trend chart and everyone reads it as behaviour when it was a setting.

## 2. Current state (what exists today)

`frontend` ships an account Configuration tab over six catalogs with effective source, version history, a JSON body editor, and override or remove under `admin:config`. That is configuration **storage** with versioning, and it is a good base. What it has no notion of is **ownership**, **why a value changed**, **when it takes effect**, or **whether it is stale**.

## 3. Goals

- One register of every configurable parameter, with a named owner and a plain-language description.
- A parameter with no owner is visible as unowned rather than invisible.
- Every change carries a reason and an effective date, and the history is immutable.
- A configuration change is visible on the chart it moved.
- Parameters go stale, and staleness surfaces.

## 4. Non-goals / out of scope

- Being the configuration store. The existing catalog and override mechanism stays; this module governs it.
- Access control. Who may change a parameter is a permission (`admin:config` and its relatives), not a governance record.
- Infrastructure configuration. Terraform owns that, and it has its own review.

## 5. User-facing behaviour

### 5.1 The register (CG-01)

Every configurable parameter appears in one register with:

- A **named owner**, a person and not a team.
- A **plain-language description of what it affects**, written for someone who did not build it.
- Its current effective value and scope (operator wide, or per account).
- Its review cadence (CG-04).

A parameter with **no owner is visible as unowned**. Unowned is a state the register displays, not a gap it hides, and the count of unowned parameters is itself worth watching.

The register is populated from the parameters themselves rather than maintained by hand, otherwise it drifts from what the system actually reads.

### 5.2 Audited change (CG-02)

Changing a parameter records who, when, old value, new value, **a reason** and an **effective date**. Prior values remain readable, and no interface edits or deletes the history.

The effective date is what distinguishes this from the version history that exists today. A threshold changed on the 9th but effective from the 1st changes how the whole period reads, and CG-03 cannot mark the chart correctly without knowing which date matters.

### 5.3 Change markers on trends (CG-03)

A trend or scorecard line spanning a configuration change **renders a marker for that change**, so a step is never read as behaviour when it was a setting.

This is the requirement that pays for the module. Without it, someone lowers a threshold, the alert count halves, and a quarterly review concludes the practice improved.

Markers appear on DR-15 scorecard lines, on measurement trends (MC-01 to MC-05), and on any account-health trajectory whose inputs are configured.

### 5.4 Review cadence and staleness (CG-04)

Each parameter carries a review cadence. Parameters past it surface to their owner and, unactioned, to the support director. Reviewing a parameter without changing it is a valid outcome and is recorded, so "still correct" is distinguishable from "never looked at".

### 5.5 Empty and edge states

- A parameter added by a deploy with no owner appears immediately as unowned rather than waiting for someone to register it.
- A change with no reason is refused, not saved with an empty reason.
- A trend rendered over a window with no configuration change shows no markers and no marker chrome.

## 6. Rollout

1. **Register over what exists.** CG-01 across the six catalogs already in the product, populated automatically, most of it unowned on day one. That list is the useful output.
2. **Ownership pass.** Assign owners, which is a people exercise the register makes possible rather than a build step.
3. **Audited change.** CG-02, extending the existing version history with reason and effective date.
4. **Markers.** CG-03 once there is change history worth marking.
5. **Cadence.** CG-04 last.

## 7. Success criteria

- Every parameter the system reads appears in the register, proven by a test that fails when a new configurable parameter is added without registration. This is the same shape as the isolation-suite check: the build catches the omission, not a reviewer.
- A parameter with no owner renders as unowned.
- No change can be saved without a reason.
- A scorecard line spanning a change renders its marker, proven by test.
- Configuration history cannot be edited or deleted through any interface.

## 8. Open questions

- Is the register operator wide, or per account for per-account parameters? A threshold overridden on twelve accounts is either one register row with twelve values or twelve rows.
- Does an effective date in the past trigger recomputation of anything already reported, or is it forward only with the marker explaining the discontinuity?
- Who is the default owner for a parameter whose owner leaves, and does the register block a leaver's offboarding?
- Does CG-03 mark client-facing report packs, or internal surfaces only? A marker in a client deck invites a question that may be better asked internally first.
