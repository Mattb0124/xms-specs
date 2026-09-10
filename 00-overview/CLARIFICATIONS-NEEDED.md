# Clarifications needed

**Status:** Open
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Why this file exists:** One place for every question that blocks a spec or contradicts something already built. If a question is answered, move the answer into the spec it belongs to, record it in the [Decision Log](./DECISION-LOG.md) if it is a decision, and delete the row here. This file should shrink.

**Read this before starting work in `02-modules/resolution-ladder`, `measurement-and-calibration`, `account-health`, `time-certification`, `collaboration-signal`, `configuration-governance` or `outcomes`. Every one of them is blocked on something below.**

---

## The one that is costing money right now

### C-01 Do assignment groups route, or not? (TM-08)

**This contradicts shipped code.** It is the only item here where the answer changes something already built, so it is first.

| | Says |
|---|---|
| Our register (workbook) | TM-08 "Assignment groups", with "support for group-level and individual assignment" |
| Functional RTM revision 3 | TM-08 groups "are searchable when inviting a collaborator, and **carry no routing behaviour of their own**" |
| What is built | `frontend` ships the group queue (`my_groups` and `group_id` dimensions), the group picker, and a **Routing defaults** panel saving type/category/group rules under `admin:config` |

Under revision 3, routing moves to two other rows: **TM-23** (account ownership drives default routing) and **CAP-09** (the triage rota drives routing for unowned intake). Groups become a skill-lookup directory for inviting collaborators, nothing more.

**What we need decided:**

1. Is revision 3 right that groups do not route?
2. If yes, what happens to the Routing defaults panel and the group queue dimensions already in `frontend`? Removed, or kept as a transitional mechanism until TM-23 and CAP-09 exist?
3. If no, revision 3's TM-08, TM-23 and CAP-09 all need amending, because they are written as one coherent change.

**Until this is answered:** `02-modules/resolution-ladder/` cannot be specced. RL-03 says the proposed path drives routing, and that sentence means nothing until we know what routing is. Do not build more on the group-routing model in the meantime.

---

## Blocking the new module specs

### C-02 Every revision 3 row is unscoped

The functional RTM carries no phases and no priorities, deliberately ("no phases, no priorities"). Our register carries both, and delivery planning depends on them. So all **75** new rows landed in a holding pen: phase `0 Unscoped (revision 3 intake)`, priority `Unassessed`.

That is honest but it is not a plan. Nothing in the roadmap covers them, so today they are invisible to delivery.

**What we need:** a triage pass assigning a phase and a priority to each of the 75. The seven new modules are the bulk (47 rows) and can be triaged as blocks; the 28 rows landing in existing modules need individual calls.

### C-03 Which register is the authority?

Two registers now exist: ours (generated, phased, prioritised, 190 rows) and the functional RTM (176 functional rows, no phases, richer "Done when" statements).

**What we need:** either the RTM becomes the upstream source and our generator reads it, or our register stays authoritative and the RTM is a one-time intake. Right now the RTM's "Done when" text is better than our acceptance notes and is not being used. Left alone, the two will diverge within a sprint.

### C-04 Is there a home for the seven new modules in the roadmap?

`03-delivery/ROADMAP.md` and `IMPLEMENTATION-PLAN.md` predate revision 3 and know nothing about the resolution ladder, calibration, account health, time certification, collaboration signal, configuration governance or outcomes. 47 requirements have specs coming but no delivery slot.

---

## Design conflicts to resolve before building

### C-05 Anonymised concerns versus the audit trail (CL-05 against XA-01)

CL-05 says no interface, export **or audit view** can resolve an anonymised concern to its author. XA-01 says every action is recorded as an append-only security event with actor and principal kind.

These are in direct tension. Either concern-authoring is exempt from actor capture (and we accept the audit gap deliberately, in writing), or concerns are pseudonymised at write time with the mapping held somewhere no interface reads. The second is the only one that satisfies both, and it needs designing rather than assuming.

**Same family, same question:** MC-02, MC-03 and TC-07 all say a figure must never resolve to an individual. TC-07 goes further: "enforced rather than conventional". These are data-model constraints, not reporting conventions, and they need to be designed in from the first migration, not filtered at the query.

### C-06 DR-09 and AH-03 / AH-04 overlap

DR-09 "Customer health score" (composite of CSAT, SLA attainment, budget position, engagement) already exists in our register and survives in revision 3. AH-03 (readiness trajectory) and AH-04 (experience trajectory) cover much the same ground with a different philosophy: two trajectories that must always render together, calibrated per account rather than against a global target.

**What we need:** does DR-09 survive as its own number, or is it superseded by the AH pair? Building both produces two competing health figures, which is how a client conversation goes wrong.

### C-07 AI-17 changed meaning

Ours: "Allocation suggestions: recommend assignee based on skills, current capacity and account familiarity."
Revision 3: "Collaborator recommendation: who to pull in, **not who to reassign to**, and never someone recorded absent."

That is close to an inversion. If AI-17 is now about swarming rather than assignment, it belongs with TM-21/TM-22 and the collaboration module, and the "recommend an assignee" behaviour either disappears or becomes a separate row.

### C-08 TB-02 grew from one rule to four

Ours: a ticket cannot resolve with zero logged time unless an exemption is selected.
Revision 3: logged time **or** exemption, **plus** a resolution code, **plus** resolution notes meeting a completeness rule, **plus** a knowledge article prompted then warned on then required, with time optionally arriving from the TC-01 certification flow instead of the ticket.

The composite gate is a much larger piece of work than the row it replaces, and it now depends on a module (time certification) that does not exist. Worth confirming it is wanted in full before it is specced that way.

---

## Carried from the RTM itself

Revision 3 lists these as still open (§21). They are repeated here so there is one list, not two.

| Ref | Question | Blocks |
|---|---|---|
| C-09 | What "a workflow" means for AI-04. Working answer: one request category on one consenting account. Not confirmed | `ai-functionality` |
| C-10 | TM-11 disposition on decline: out of scope, converted to a quote, or held pending contract change. A commercial decision | `ticket-management` |
| C-11 | TM-28 handover boundary. Working answer: per-rota-slot, dependent on how CAP-09 is configured | `ticket-management`, and C-01 |
| C-12 | CAP-11 closure condition: does a concentration alert close on a recorded state, or does it require a moved concentration figure? | `capacity-and-allocation` |

---

## Noted, not blocking

- **C-13 XA-03 split.** Revision 3 splits our XA-03 into XA-03a (audit search, security dashboard, SQL surface, excluded as security tooling) and XA-03b (usage and knowledge dashboard, functional). Our register still carries one XA-03. Harmless today; worth aligning when XA is next touched.
- **C-14 Fifteen of our rows are reclassified.** TM-01, CP-01, CP-02, INT-01, AI-12, XA-01 to XA-05 and DM-01 to DM-05 become "excluded" in the RTM as architectural, platform, contractual or cutover. They are still real work and mostly built. It only means the two registers count different things, so their totals are not comparable.
- **C-15 TM-15 gains a UI constraint.** A saved view "appears as a secondary tab, never as the landing surface". The Queue already ships saved views; worth checking the built behaviour against this before it is called done.
- **C-16 Subcontractor versus employee capacity** was deliberately dropped from the RTM as a commercial question rather than a functional one. Recorded here so it is not silently lost.

---

## How to close a row here

1. Get the answer from the person who owns the decision.
2. Write it into the spec that needed it, in the spec's own words.
3. If it is a decision rather than a clarification, add an ADR to the [Decision Log](./DECISION-LOG.md).
4. Delete the row from this file in the same commit.
