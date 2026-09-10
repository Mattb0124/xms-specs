# Functional Spec: Outcomes

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Account Health & Experience](../account-health/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md)
**Requirements covered:** OC-01, OC-02, TM-10 (as an outcome type), TM-26 (association and coverage, owned by Ticket Management)
**Repos affected:** `backend`, `backend/src/domain`, `backend/src/db`, `frontend`

---

## 1. Problem

The client conversation is about hours. Hours consumed, hours remaining, hours against entitlement. That conversation makes the practice a supplier of effort, and effort is the thing a client is always trying to reduce.

Nothing in the system holds the business result the work was for. A ticket tree exists, hours attach to it, and a report can total them, but no object says "this was the Azure Files cutover, this is what it was supposed to achieve, and here is where it got to." Without that object, no report can lead on result, because the result is not recorded anywhere.

## 2. Current state (what exists today)

TM-10 exists as "grouping under a project or change window", and `frontend` ships change windows and ticket groups. That is a container for tickets. It carries no stated business result, no owner, no period, no client visibility rule, and nothing reports from it.

Revision 3 reframes TM-10 as **an outcome of a particular type**, rather than a parallel concept.

## 3. Goals

- One object above the ticket that holds the business result.
- A configurable type taxonomy, because "change window" and "quarterly initiative" are not the same shape.
- Client visibility decided by type, overridable per instance, audited when overridden.
- A client-facing report that leads on result with tickets and hours as evidence.

## 4. Non-goals / out of scope

- Project management. No task breakdown, no dependencies, no Gantt. An outcome groups tickets and states a result.
- Ticket-to-outcome association and coverage measurement. That is TM-26, owned by [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md).
- Replacing contracts. An outcome links to a contract; it is not a commercial object.
- Time capture. Hours arrive through the tickets and through certification.

## 5. User-facing behaviour

### 5.1 The outcome object (OC-01)

An outcome carries:

| Field | Notes |
|---|---|
| Name | Short, client-legible |
| Stated business result | What this was for, in the client's terms, not ours |
| Owner | A named person |
| Period | The window it belongs to |
| Status | Where it got to |
| Type | From the configurable taxonomy |
| Client visibility | Defaulted by type, overridable per instance, **audited when overridden** |
| Linked tickets | Through TM-26 |
| Linked contract | Which entitlement it consumed |

The **type taxonomy is configurable per client** from a maintained default list. Each type carries a **default client-visibility setting**. An override on a single outcome is allowed and is audited, because changing whether a client can see something is exactly the kind of change that needs a trail.

### 5.2 Change windows are outcomes (TM-10)

A ticket tree grouped under a change window is an outcome of that type, and it is **not client-visible by default**. This is why visibility defaults live on the type: an internal change window and a client-facing initiative are both outcomes and want opposite defaults.

### 5.3 Outcome-framed client reporting (OC-02)

The client-facing report **leads on business result**, with tickets and hours as supporting evidence beneath it. It shows **only client-visible outcome types**.

The ordering is the requirement. Hours first with a result appended is the report we already produce; result first with hours as evidence is a different conversation.

### 5.4 Coverage is the honest counterweight (TM-26)

Outcome-framed reporting is only as good as the share of work actually attached to an outcome. TM-26 makes linkage coverage reportable per account, per engineer and per period, and surfaces accounts below a configured coverage floor to the account owner and the support director.

A report leading on outcomes while 30 percent of hours carry no outcome is a report that hides a third of the work. The coverage floor is what stops that shipping quietly.

### 5.5 Empty and edge states

- An outcome with no linked tickets is valid (it was just created) and renders as having no delivery yet, not as empty.
- An account below the coverage floor still gets its report, with the uncovered share stated rather than omitted.
- An outcome whose type is retired keeps its type and stays readable; retirement removes it from the picker only.

## 6. Rollout

1. **The object and the taxonomy.** OC-01 with default types, and TM-10 migrated onto it so change windows stop being a parallel concept.
2. **Association.** TM-26 attach and detach, plus coverage measurement.
3. **Coverage floor.** Surfacing to owners once there is enough linkage to have a meaningful floor.
4. **Reporting.** OC-02, last, because a result-led report over thin coverage is worse than the hours-led one it replaces.

## 7. Success criteria

- A change window created today is an outcome of type change window and is not client-visible.
- A per-instance visibility override writes an audit event naming who changed it and when.
- The client-facing report renders business result above tickets and hours, and omits non-client-visible types entirely rather than showing them empty.
- Linkage coverage is reportable per account, per engineer and per period.
- A client report over an account below the coverage floor states the uncovered share.

## 8. Open questions

- What is the default type list, and who maintains it? It needs an owner in the CG-01 register.
- Does an outcome belong to exactly one account, or can one span accounts (a shared platform upgrade across two clients)?
- Can a ticket belong to more than one outcome? Coverage arithmetic differs sharply depending on the answer.
- What is the default coverage floor, and is it per account or operator wide?
- Does an outcome have its own consumption view, or does entitlement stay purely at contract level?
