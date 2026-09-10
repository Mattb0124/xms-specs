# Functional Spec: Time Certification

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Configuration Governance](../configuration-governance/FUNCTIONAL-SPEC.md)
**Requirements covered:** TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `frontend`

---

## 1. Problem

Almost every number the practice wants to report has delivered hours in the denominator. Utilisation, profitability, burn, value against entitlement, the DR-15 scorecard: all of them are wrong in the same direction when time is under-captured, and under-captured is the normal state of professional services time entry.

The usual fix makes it worse. Mandatory minute-level entry against tickets produces either resentment or fiction, and fiction is more expensive than a gap because it cannot be seen.

## 2. Current state (what exists today)

`frontend` ships a timesheet over `/v1/timesheets/me`, per-day expected against logged with an unlogged highlight, a quick Log time form, and non-ticket buckets (TB-12). That is a good timesheet. It is still a timesheet: it asks a person to remember and to type into a blank field.

AI-06 currently covers both description normalisation and unlogged-time prompting. **Revision 3 narrows AI-06 to normalisation and gap detection only**, and this module takes the daily flow.

## 3. Goals

- A daily wrap-up that takes under a minute, for every role from agent to director.
- Nothing entered from a blank screen. The system proposes; the person confirms.
- Capture effort that never touched a ticket, without forcing it onto one.
- Fill the denominator honestly, and never turn the act of filling it into a performance measure.

## 4. Non-goals / out of scope

- Minute-level accounting. Deliberately not the aim, and designing for it would defeat the flow.
- Replacing ticket time entry (TB-01). Both write to the same store; either satisfies the TB-02 gate.
- Billing logic, rates, adjustments. That is [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md).
- Grading anyone on how much they logged. Explicitly forbidden by TC-07.

## 5. User-facing behaviour

### 5.1 The daily flow (TC-01)

A card-based end-of-day wrap-up, **under a minute**, available on any device, and it does not require opening a ticket. Every role completes it, director included, because a denominator that excludes leadership is not a denominator.

### 5.2 Proposed, not asked (TC-02)

The first card **proposes the day's activities** from ticket, comment, time-entry and calendar signals. The person confirms, removes or corrects. Nothing is entered from a blank screen.

This is the difference between a wrap-up and a timesheet. Recognition is fast; recall is slow and inaccurate.

### 5.3 Off-system capture (TC-03)

One prompt asks whether anything else happened, answerable by **typing or by speaking**. Spoken input is transcribed into a candidate entry the person confirms. The hallway conversation, the call that never became a ticket, the thirty minutes helping someone else's account: this is where they land.

### 5.4 Effort against placeholders (TC-04)

Each confirmed activity gets one card for effort. Duration fields show a **placeholder** and are **never pre-filled with a computed actual**. The person supplies the figure.

This is a deliberate constraint and it is easy to get wrong helpfully. Pre-filling a computed duration turns confirmation into acceptance, and the number stops being a person's own statement of effort. A placeholder suggests the shape of the answer; a pre-filled value supplies it.

### 5.5 The catch-all (TC-05)

An **other** bucket accepts effort without forcing a ticket, an account or an activity type. Nobody is ever blocked from finishing the wrap-up because they cannot classify something at 18:00.

### 5.6 The guardrail, weekly (TC-06)

The size of **other** is policed **weekly, never daily**. Crossing a role-configurable threshold raises to the person and their manager. The threshold and its owner appear in the CG-01 configuration register.

Weekly, because a daily check turns the escape hatch into a nag and people stop using it honestly. The bucket only works if using it feels free in the moment.

### 5.7 Completeness, not content (TC-07)

A missed evening is permitted. The next login shows outstanding wrap-ups. **Completeness** (submitted or not) is reportable per person and per period and may drive enforcement.

**No report, screen or export renders certification magnitude as a performance measure of a person, and this is enforced rather than conventional.** Hours logged is not a leaderboard, is not a column beside a name, and is not derivable by export. The moment it is, the flow produces fiction and every downstream number degrades. Treat this as a data-model constraint of the same kind as account isolation, not as a reporting guideline.

### 5.8 Empty and edge states

- A day with no detectable signal opens on the off-system prompt rather than an empty list.
- A person on PTO is not asked, and the absence is not an outstanding wrap-up.
- A failed transcription keeps the audio attached and asks for text, never discards.
- Certification for a locked billing period is refused with the period named, not silently written.

## 6. Rollout

1. **Flow with proposals.** TC-01, TC-02, TC-04, TC-05. This is the whole value; the guardrails follow.
2. **Voice.** TC-03 typing first, speech once transcription is available through the Axel adapter.
3. **Guardrail and completeness.** TC-06 and TC-07 once there is a few weeks of baseline to set a threshold against.
4. **Gate integration.** TB-02 accepting certification-sourced time as satisfying the resolution gate.

## 7. Success criteria

- A wrap-up with three proposed activities completes in under 60 seconds, measured.
- No duration field is ever pre-filled with a computed actual, proven by test.
- Certification magnitude cannot be resolved to a person on any screen or in any export, proven by test.
- The other bucket accepts an entry with no ticket, no account and no activity type.
- Capture rate is computable, since DR-16 gates the scorecard on it.

## 8. Open questions

- What is "the day" for someone working across time zones, and does the wrap-up follow the person's calendar or the account's?
- Does a director's wrap-up propose from calendar alone, given they may touch no tickets?
- TC-07 permits completeness to "drive enforcement". What enforcement, and who owns it? That is a people decision, and it needs an owner before it is built.
- Where does certified non-ticket effort land against TB-12 buckets: same store, or parallel?
