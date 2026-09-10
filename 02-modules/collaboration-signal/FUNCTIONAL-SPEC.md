# Functional Spec: Collaboration Signal

**Status:** Draft, blocked on [C-05](../../00-overview/CLARIFICATIONS-NEEDED.md)
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Account Health & Experience](../account-health/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md), [Measurement & Calibration](../measurement-and-calibration/FUNCTIONAL-SPEC.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Audit & Analytics](../../01-architecture/AUDIT-AND-ANALYTICS.md)
**Requirements covered:** CL-01, CL-02, CL-03, CL-04, CL-05
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `backend/src/worker`, `frontend`

---

## 1. Problem

Swarming is many minds around one credentialed pair of hands. The person who owns the ticket is often not the person who solved the hard part, and today none of that is recorded. The contribution is invisible, so it cannot be recognised, and the people who are quietly carrying others cannot be identified except by anecdote.

The second problem is that peer opinion and client opinion frequently disagree about the same person, and the disagreement is more informative than either alone. An engineer the team relies on and clients find abrasive is a specific, addressable situation. An average of the two is not.

## 2. Current state (what exists today)

Nothing. TM-21 (participant record) and TM-22 (invite a collaborator) are prerequisites and are themselves new in revision 3.

## 3. Goals

- Capture peer signal where the work happens, at closure, as the path of least resistance.
- Render peer signal **against** client satisfaction rather than blended into it.
- Make positive feedback attributable, and make concerns safe to give.
- Accept leakage rather than chase it with surveillance.

## 4. Non-goals / out of scope

- Performance management. This is signal for coaching and recognition; it is not an appraisal input, and it is not a rating.
- Chasing completion. CL-03 is explicitly skippable and never chases.
- Capturing collaboration that happens off platform. In-platform capture is designed to be easiest; what leaks, leaks.
- Client satisfaction capture. That is CP-07.

## 5. User-facing behaviour

### 5.1 Closure grading (CL-01)

At closure the ticket owner grades each TM-21 participant on a short scale, with an optional comment. **Skipping is permitted**, and the skip rate is reportable, because a collapsing skip rate says the prompt has become a chore.

### 5.2 Client-relayed feedback (CL-02)

A CSM records feedback about a named person as relayed from the client, attributed to the client source and dated. This feeds the **client side** of CL-04. It is second-hand by construction, and it is recorded as second-hand: attribution names the client contact and the CSM who relayed it.

### 5.3 The weekly digest (CL-03)

Once a week a person is shown who they worked with and is invited to comment. **Skippable, under a minute, never chases.** No reminder emails, no completion percentage on a dashboard, no manager notification for a skipped week.

### 5.4 The quadrant (CL-04)

Peer signal renders against client satisfaction in four quadrants, per person and per account:

| | Client positive | Client negative |
|---|---|---|
| **Peer positive** | Convergent positive | Peer-positive, client-negative |
| **Peer negative** | Peer-negative, client-positive | Convergent negative |

**Client satisfaction governs where the two disagree**, and the disagreement is itself the reported signal. The two off-diagonal quadrants are the whole point of the view; a blended score would erase them.

### 5.5 Asymmetric visibility (CL-05)

This is the row the module lives or dies on.

- **Positive feedback is attributable** and visible to its subject. Recognition that cannot be traced to a person who gave it is worth little.
- **Concerns are aggregated and anonymised**, never rendered attributably, and are **withheld from display until a configured minimum contributor count is reached** (the minimum lives in the CG-01 register).
- **No interface, export or audit view can resolve an anonymised concern to its author.**

That last clause conflicts with XA-01, which records an actor on every event. See [C-05](../../00-overview/CLARIFICATIONS-NEEDED.md). The resolution has to be designed before a single concern is written, because a concern captured with an actor id is unfixable afterwards: the mapping exists in the table and in every backup.

### 5.6 Empty and edge states

- Fewer contributors than the minimum: the view says signal is withheld pending more input, and does not hint at direction or count.
- A person with no collaboration in the window has no quadrant rather than an empty or neutral one.
- A single-participant ticket produces no grading prompt at all.

## 6. Rollout

1. **Prerequisites.** TM-21 and TM-22 in [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md).
2. **Resolve C-05 and design the anonymity mechanism.** Before any capture.
3. **Positive path first.** CL-01 with attributable positive signal and concerns disabled, which is safe under any resolution of C-05.
4. **Concerns.** Once the mechanism exists and the minimum contributor count is set.
5. **Quadrant.** CL-02 and CL-04 once both sides have enough volume.

## 7. Success criteria

- An anonymised concern cannot be resolved to its author through any screen, export, API response or audit query, proven by test written against the database and not only the API.
- Concerns below the minimum contributor count are not displayed, and the display does not leak the count.
- Positive feedback reaches its subject with its author named.
- The quadrant view never collapses to a single blended score.
- Skipping CL-01 and CL-03 produces no chase of any kind.

## 8. Open questions

- **C-05:** how anonymity coexists with the append-only audit trail. Blocking.
- Who may see a person's quadrant: the person, their manager, the practice leadership, or the person alone?
- What is the minimum contributor count's default, and who owns it in CG-01?
- CL-02 records client-relayed feedback about a named person. Is that disclosable to the person, and does it survive a client asking for their record?
- Does peer signal have a retention period, or does it accumulate for the life of the account?
