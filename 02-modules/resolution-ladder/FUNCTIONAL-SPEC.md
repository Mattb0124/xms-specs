# Functional Spec: Resolution Ladder & Routing

**Status:** Draft, blocked on [C-01](../../00-overview/CLARIFICATIONS-NEEDED.md)
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Measurement & Calibration](../measurement-and-calibration/FUNCTIONAL-SPEC.md), [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md), [Account Health & Experience](../account-health/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md)
**Requirements covered:** RL-01, RL-02, RL-03, RL-04, RL-05, RL-06, RL-07, RL-08, RL-09
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `backend/src/worker`, `frontend`

---

## 1. Problem

Today a request lands and a person decides who deals with it, using judgement that lives in their head. Nothing records what kind of resolution the request needed, so nothing can be said about whether the right person handled it. Work that a service desk agent could have closed reaches an engineer, and nobody finds out. Work that genuinely needed credentialed access sits with an agent who cannot progress it, and the client waits.

The practice cannot answer its own central question: is resolution moving toward the client, or away from it?

## 2. Current state (what exists today)

Nothing. This is a new module. The ticket record has an assignee and an assignment group, and the frontend ships a group queue and routing defaults, but there is no notion of what kind of resolution a ticket needed, and no record of what kind it actually got.

The historical corpus that RL-02 profiles arrives through [Data Migration](../data-migration/FUNCTIONAL-SPEC.md) (DM-01).

## 3. Goals

- Make the ladder explicit: every ticket carries the path it was classified to and the path it actually took.
- Let the two disagree, and keep both, because the disagreement is the signal ([Measurement & Calibration](../measurement-and-calibration/FUNCTIONAL-SPEC.md) MC-04).
- Give the front desk what it needs to resolve more: a profile of what has worked before, and step-by-step guidance against the current corpus.
- Never send an agent at work they cannot do. Access, not difficulty, is what separates path 1 from path 3.
- Surface what should stop being a ticket at all.

## 4. Non-goals / out of scope

- Measuring the ladder. That is [Measurement & Calibration](../measurement-and-calibration/FUNCTIONAL-SPEC.md); this module produces the data it reads.
- Deciding who a ticket is assigned to. Routing is TM-23 and CAP-09, and this module supplies the path that informs it.
- Grading people. No figure here resolves to an individual.
- Building the self-service surface itself. Path 0 lives in the [Client Portal](../client-portal/FUNCTIONAL-SPEC.md); this module records what happened there.

## 5. User-facing behaviour

### 5.1 The four paths (fixed set)

| Path | Name | Meaning |
|---|---|---|
| 0 | Client self-service | The client resolved it without a Hackett touch |
| 1 | Front-desk resolved | The service desk closed it alone |
| 2 | Front-desk owned, engineer-validated | The desk owned it throughout; an engineer validated, certified or coordinated |
| 3 | Engineer-owned | An engineer owned the resolution |

The ladder ascends in cost, skill and client-perceived turnaround. Paths 1 and 2 are separated from 3 by an **access and authorisation limit**, not a difficulty one: the agent will never hold client credentials. That is why path 3 and path 0 connect directly, and why a request the agent cannot authenticate into can never be a path 1 no matter how simple it is (RL-04).

### 5.2 Classified path and actual path (RL-01)

Every ticket carries two values. **Classified path** is stamped at intake. **Actual path** is derived at close from the ownership and participant trail. Neither overwrites the other; both are reportable. A ticket closed without enough trail to derive an actual path reports as underived rather than defaulting to its classified value.

### 5.3 Classification at intake (RL-03)

Axel proposes a path from the RL-02 profile and the request content, with a confidence, subject to AI-08 (human in the loop) and AI-09 (confidence thresholds). Below threshold the proposal is withheld and the ticket routes to a human.

A human can override the proposal. The override is recorded **against the proposal**, not instead of it, so MC-08 can read what the model said and what the person did.

### 5.4 The profile (RL-02)

Closed historical records are profiled by client, request type, complexity, who resolved them, and whether resolution required credentialed access or genuine expertise. The profile is queryable per client and per request type, and is the classifier's prior from day one rather than something that warms up over months.

### 5.5 Credential-blocked types (RL-04)

Request types are marked where resolution requires client-side access or elevated permission. A marked type **cannot** classify to path 1: it routes to path 3, or to path 0 where the client can do it themselves. The marking is per client, because access varies by account. The same request type can be path 1 on one account and path 3 on another, and that is expected rather than an inconsistency.

### 5.6 The validation touch (RL-05)

An engineer records a validation, certification or coordination touch on a ticket the agent still owns. The touch is a TM-21 participant event carrying a touch type. **The assignee does not change.** The ticket's actual path resolves to 2 rather than 3.

This is the row that makes path 2 real. Without it, any engineer involvement looks like escalation and the front desk loses credit for work it did.

### 5.7 Guided resolution (RL-08)

Where the profile holds a known-good path, Axel walks a non-technical resolver through it step by step against the current corpus. Where the profile says expertise or access is required, Axel proposes path 2 or path 3 **instead of** guidance. It does not walk someone toward a wall.

Guidance reads the knowledge corpus subject to the AI-23 two-scope consent rules: an account that has not opted in to cross-account contribution never has its content surfaced to another account's resolver.

### 5.8 Path 0 on platform (RL-06, RL-07)

A client resolving through self-service produces a record: what was asked, what was returned, and whether the experience satisfied. It attaches to the account and feeds AH-03. A self-service attempt **abandoned into a raised ticket** links to that attempt, and fallback rate is reportable by request type and account.

Fallback rate is the honest counterweight to path-0 volume. Deflection that fails and becomes a ticket anyway is worse than no deflection, because the client tried twice.

### 5.9 Self-service candidates (RL-09)

Request types resolved repeatedly at path 1 without engineer involvement surface as path-0 candidates, ranked by volume and consistency of resolution, on a surface the service desk lead owns.

### 5.10 Empty and edge states

- No profile for a client and request type: the classifier says so and routes to a human rather than guessing.
- A ticket that never closes has no actual path, and is absent from ladder measures rather than counted as a failure.
- A path-0 record with no linked ticket is complete, not orphaned.

## 6. Rollout

1. **Profile first.** RL-02 over the migrated corpus, with no classification and no UI. The profile is inspectable before anything depends on it.
2. **Classify silently.** RL-01 and RL-03 stamping paths with no routing effect, so classifier accuracy can be measured against human behaviour before it influences anything.
3. **Turn on routing.** Only once C-01 is answered and MC-04/MC-05 report an accuracy anyone is willing to stand behind.
4. **Guidance and candidates.** RL-08, then RL-09.

## 7. Success criteria

- Every closed ticket carries both a classified and an actual path, or an explicit reason why the actual path could not be derived.
- A credential-blocked type never classifies to path 1 on an account where access is not held, proven by test.
- An override always has its original proposal readable beside it.
- A path-2 ticket is distinguishable from a path-3 ticket without reading the comment thread.
- Path-0 fallback rate reports beside path-0 volume everywhere path-0 volume appears.

## 8. Open questions

- **C-01 blocks this module.** RL-03 says the proposed path drives routing. Until the TM-08 versus TM-23/CAP-09 conflict is settled, "drives routing" has no defined meaning.
- What counts as "complexity" in the RL-02 profile, and is it derived or recorded?
- Who owns the per-client credential markings in RL-04, and does that owner sit in the CG-01 register? (The register says configuration owners exist; this is one of the first parameters that needs one.)
- Does a path-2 touch have a minimum, or does any engineer comment count? An overly generous definition inflates the front-desk figure MC-02 depends on.
