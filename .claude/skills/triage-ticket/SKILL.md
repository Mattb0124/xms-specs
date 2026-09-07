---
name: 'triage-ticket'
description: 'Triage an incoming XMS ticket in ClickUp into one of four outcomes (ready, needs-spec, needs-info, deferred), then set the status, priority, tag, assignee and traceability comment. Use when a new XMS task lands in the current sprint list, when the user says "triage this", "is this ready to build", "should we spec this first", "what is the estimate", when clearing the Waiting for Triage or untriaged Backlog queue, or when sizing work for a sprint. Runs manually today through the ClickUp MCP tools; the same decision rules are what a pipeline would later automate.'
---

# Skill: Triage an XMS Ticket

Triage answers one question: **can someone start building this from the ticket alone, or does something have to happen first?** It is the gate between a request and the sprint. Getting it right is what stops half-specified work reaching a developer and stalling.

This skill is the decision procedure. `aibl-clickup` owns the conventions it writes into (naming, description template, the 13 states, Fibonacci, required fields). Read that skill for the mechanics; read this one for the judgement.

## Where XMS tickets live

Workspace `9015896416`, space **X Platforms** `901511370980`.

| Ticket | Destination |
|---|---|
| Development / enhancement | The **current sprint list** inside `X Platform Sprints` folder `901516703258`. Resolve it every time by the `Sprint N (M/D - M/D)` range containing today; it changes fortnightly |
| Bug | The `Bugs` folder `901516841378`, platform list. **There is no XMS list there yet**, see the gaps below |

**The XMS list `901525777420` is the home for the architecture docs only. Never create a ticket in it.** Sprint lists carry all 13 states plus a closed `complete`, so the workflow below applies unchanged.

Sprint lists as of 2026-09-04: Sprint 1 `901524338458`, Sprint 2 `901524755515`, Sprint 3 `901525034981`, Sprint 4 (8/24 - 9/6) `901525290760`. Do not hardcode one; resolve by date.

### Setup gaps to work around (verified 2026-09-04)

1. **The `Platform` dropdown has no XMS option.** Its options are the AIX family, XT, XDA, CSF, Spend Analysis, HLM, ALL, AIX ALL and AIBL. Until an XMS option is added, do not pick a wrong one to fill the field. Leave it unset and record `Platform: XMS` in the triage comment.
2. **There is no XMS list in the `Bugs` folder** (only XT, XDA, AIX), so an XMS defect has nowhere correct to go. Raise it rather than filing under another platform.
3. **No Sprint Points field exists** on the sprint lists (only `Platform` and `⚡ Next Release`). The estimate goes in the comment.

Field ids, when they are settable: `Platform` `b8bfb2b8-6ab6-4af4-898f-f911baf10263`, `⚡ Next Release` (checkbox) `10158a6b-7a0c-49ad-a249-92f83ed79dff`. Re-read them with `clickup_get_custom_fields` on the target list before writing.

What you can reliably set today: status, native priority, assignee, tags, name, description, comments, and Next Release.

## The four outcomes

Tags are the label mechanism, mirroring the GitHub-label pattern that a triage pipeline would later key off. Apply exactly one.

| Outcome | Tag | Status | Meaning |
|---|---|---|---|
| Ready | `triage:ready` | `backlog` | Documented well enough to start. A developer could pick it up and build it without asking a question |
| Needs spec | `triage:needs-spec` | `backlog` | Real, wanted work, but the approach has to be written down before anyone builds. Moves to `planning` when someone picks it up |
| Needs info | `triage:needs-info` | stays where it is | Cannot be judged yet. Reassign to the requester with the questions |
| Deferred | `triage:deferred` | `backlog`, priority `low` | Valid, not now. Out of the current phase or blocked by something unstarted |

A bug enters at `waiting for triage` and, once triaged, follows the bug path to `investigating` rather than `backlog`.

## How to decide

Work down this list. The first rule that fires wins.

### 1. Needs info, if the ticket cannot be judged

- No Success Criteria, or criteria that are not observable ("works properly", "is fast").
- Scope open to more than one reading, so two developers would build different things.
- A bug with no reproduction steps, no environment, and no expected-versus-actual.
- It is unclear which module it belongs to, or which account or realm (internal versus portal) it affects.
- It contradicts a decision in `00-overview/DECISION-LOG.md` without saying it is revisiting it.

Ask the questions in a comment, reassign to the requester, and stop. Do not guess the intent and do not rewrite the description to what you assume was meant, per the traceability rule.

### 2. Needs spec, if the approach is not settled

Any one of these forces a spec, **regardless of how small the ticket looks**:

- Estimated at **8 points or more**. At 13, decomposition is mandatory: either break it into subtasks of 8 or less, or open a spike capped at 3 points to produce the decomposition.
- It changes a **shared contract**: the data model, the permission catalog in `backend/src/contracts`, the OpenAPI document, or a DTO the web client generates from.
- It **adds or alters an account-scoped table**, which pulls in RLS policy and the generated isolation suite.
- It touches the **branch-critical domain**: the state machine, the SLA engine, period locking, or loop prevention. These carry 100 percent branch coverage for a reason, and a miss there is a client-visible incident.
- It changes **anything that egresses to a model**: the Axel adapter, redaction, per-account AI switches, or residency.
- It changes **ServiceNow sync semantics**: mapping, state translation, loop prevention, conflict policy.
- It needs a decision that belongs in the **decision log or an ADR**.
- The module has **no spec pair yet** in `02-modules/<module>/`.

Name in the comment exactly what the spec must resolve. Use `xms-write-spec` to write it.

### 3. Deferred, if it is real but not now

- Outside the current phase in `03-delivery/ROADMAP.md` or `IMPLEMENTATION-PLAN.md`.
- Blocked by a dependency that has not started. Name the blocker.
- Worth doing but nothing breaks if it waits.

### 4. Otherwise ready

All three required description sections present (Context, Scope / User Story, Success Criteria), success criteria observable and testable, estimable at **5 points or less**, inside a module that already has a spec, and no open decision. Set the priority from urgency and impact.

## Estimating during triage

Use the Fibonacci scale in `aibl-clickup` §5, satisfying the **majority** of a level's criteria rather than all. The estimate is a triage output, not an afterthought: it is what decides ready versus needs-spec at the 8-point line. Record it in the comment until a Sprint Points field exists.

Remember what carries hidden cost in this codebase, so you do not under-estimate: a new account-scoped table drags RLS policy plus isolation coverage; a new endpoint drags the permission catalog entry plus four auth tests; anything user-facing drags tokens, dark mode and the density scale.

## The comment (mandatory)

Every triage leaves one comment. It is the traceability record and, later, the thing that tells you whether the automated version is any good.

```markdown
**Triage: <ready | needs-spec | needs-info | deferred>**

**Estimate:** <n> points, <one line of reasoning>
**Platform:** XMS
**Next Release:** <yes | no>
**Module:** 02-modules/<module>/

**Why:** <the rule that fired, in one or two sentences>
**Before this can start:** <questions, the spec to write, or the blocker. Omit when ready>
```

## Steps

1. Read the task in full, including the description and any existing comments.
2. Work the decision list top down and take the first rule that fires.
3. Estimate in points.
4. Set the status, the priority, and exactly one `triage:*` tag.
5. Reassign: to the requester for needs-info, otherwise leave or set the owner.
6. Post the triage comment.
7. Never invent an id. Resolve the current sprint list and any field ids first, and if the X Platforms space is not reachable, stop and say so rather than writing to the wrong place.

## Checkpoints

- Exactly one `triage:*` tag, and a status consistent with it?
- Did an 8-point-or-more estimate, a shared-contract change, an account-scoped table, a branch-critical or AI-egress change force needs-spec even though the ticket looked small?
- Is the estimate recorded in the comment, given there is no Sprint Points field to hold it, along with Platform since there is no XMS option?
- For needs-info, are the questions specific enough to answer, and is it assigned to someone who can answer them?
- Is the description unedited, with clarifications in comments instead?
- Did you leave the comment?
