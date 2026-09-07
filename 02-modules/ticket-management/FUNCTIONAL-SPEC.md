# Functional Spec: Ticket Management

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Design System](../../01-architecture/DESIGN-SYSTEM.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md), [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md), [Email Intake & Outbound](../email-intake/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md)
**Requirements covered:** TM-02, TM-03, TM-04, TM-05, TM-07, TM-09, TM-10, TM-11, TM-12, TM-13, TM-14, TM-15, TM-16 (Nice to Have), TM-18 (Nice to Have)
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Problem

The DMS team runs incidents, requests, changes, problems and project tasks for several clients across five countries. ServiceNow gives them one generic lifecycle, wall-clock SLA timers, and a work-note model that leaks into client views when misconfigured. What the team needs is a ticket whose lifecycle depends on its type, whose SLA clocks respect the client's working hours and pause with a recorded reason, whose every change is evidence, and whose internal discussion can never reach the client by construction.

The cases this module must cover:

1. **Five ticket types with their own workflows** and billing treatment (TM-02), each a configurable state machine (TM-03).
2. **Priority from impact and urgency**, overridable per client (TM-04).
3. **SLA clocks** per type, priority and contract (TM-05), running on business calendars, pausing on Awaiting Client and Awaiting Third Party with the reason and duration stored (TM-07).
4. **Relationships:** parent and child, related, duplicate, blocks and blocked by (TM-09); grouping a tree under a project or change window (TM-10).
5. **Out-of-scope or over-budget work** flagged, visible to the client, and blocked until approved (TM-11).
6. **Immutable audit** of every field change (TM-12); **public comments distinct from work notes** (TM-13); **attachments** with limits and virus scanning (TM-14); **full-text search and saved views** (TM-15).
7. Later: bulk actions with per-record audit (TM-16) and a change calendar with freeze windows and conflict detection (TM-18).

## 2. Current state (what exists today)

- **XMS proof of concept, web** (`web-ui/components/aix-v3/xms/`): `QueueTab.tsx` (dense list, condition builder, breadcrumb filter trail), `NewTicketPage.tsx` (full-screen New record form with impact, urgency, live priority preview, SLA preview, attachments), `TicketDrawer.tsx` (record view with Conversation, Activity and Resolution tabs and a related-info rail), `DispatchTab.tsx`, `vocab.ts` (types, priorities, statuses, resolution codes, `derivePriority`, `ticketKey`), `slaTime.ts` with unit tests, `atoms.tsx` (pills, SLA badge and bar). Approved UI, runs against the studio in live mode.
- **XMS proof of concept, backend** (studio `feature/xms-ticketing`): `service.py` with wall-clock SLA stamping, pause and resume shifting, latch-before-pause ordering, response-met on first public reply, server-derived priority from impact and urgency, close discipline with resolution codes; `sweeper.py` breach sweeper; `xms_ticket_events` audit; `xms_comments` with a visibility column; `xms_attachments` with size and MIME checks and presigned upload; `notify.py` mirroring events into the AIX notification feed. Real but narrow: three ticket types with one shared status list, no business calendars, no state machine configuration, no links beyond parent, no groups, no out-of-scope flag, no saved views, no AV scanning.
- **POC audit findings** carried forward as requirements here: breach only latched on mutation (fixed by the sweeper), no attachments decision (now in scope with scanning), no notifications on assign or near-breach (now in scope), no concurrency control (now optimistic versions), no contract period check on create (now enforced).
- **Not built anywhere:** configurable state machines, calendar-aware SLA math, pause reasons as evidence, link types, groups, approval gates, saved views, attachment scanning, bulk actions, change calendar.

## 3. Goals

1. **The right lifecycle for each type.** An incident, a service request, a change, a problem and a project task each move through their own states, with their own required fields and billing treatment, and an administrator can adjust them per client.
2. **Honest clocks.** Response and resolution due times are computed on the client's calendar, pause with a stored reason, show remaining business time, and latch breaches that nothing can undo.
3. **Evidence for every conversation with the client.** Pause history, audit events and time entries together answer "where did the hours go" without reconstruction.
4. **Internal stays internal.** Work notes are a separate object; no screen, export, sync or email can present one as a public comment.
5. **A queue that consultants live in.** Dense, fast, filterable with a condition builder, saved as views, exported to Excel, with the SLA badge as the signature element.
6. **Safe attachments.** Uploads are limited, scanned, quarantined on detection, and never downloadable until clean.

## 4. Non-goals / out of scope

- **Time entry, contracts and burn-down.** Owned by [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md); this module only enforces "time logged before resolution" as a transition rule using that module's data.
- **Resolution records and articles.** The close discipline requires a solution link; the article itself is owned by the [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md).
- **Portal submission forms and CSAT.** Owned by [Client Portal](../client-portal/FUNCTIONAL-SPEC.md); the portal creates tickets through the same lifecycle.
- **Email parsing.** Owned by [Email Intake](../email-intake/FUNCTIONAL-SPEC.md); this module receives a ticket or a comment with origin `email`.
- **AI suggestions.** Owned by [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md); this module shows suggestion chips where they apply.
- **Approval workflows beyond the out-of-scope gate and change approval.** Multi-step approvals with delegation are later.
- **Ticket deletion.** Never offered; Cancelled is the escape hatch.
- **Auto-close after resolution.** Deferred; the pilot closes tickets explicitly. Default timer is an open question.

## 5. User-facing behavior

### 5.1 Vocabulary

| Set | Values | Notes |
|---|---|---|
| Ticket type | Incident, Service Request, Change, Problem, Project Task | Each has its own state machine and billing treatment (§5.2) |
| Priority | P1 Critical, P2 High, P3 Medium, P4 Low | Derived from impact and urgency (§5.3); P1 and P2 light up in the list, P3 and P4 stay quiet |
| Impact, Urgency | High, Medium, Low | ITIL inputs, captured at intake, editable with audit |
| Source | portal, email, internal, api, sync, import | Stamped by the creator, never editable |
| Comment kind | Public comment, Work note | Two objects; the composer has a two-way toggle with a distinct tint for work notes |
| Link type | parent of, child of, related to, duplicate of, blocks, blocked by | Directional; the inverse is shown on the other ticket |
| Pause reason | Awaiting client, Awaiting third party, Scheduled window | Stored with start, end and business minutes excluded |
| Resolution code | Solution provided, Workaround provided, Known error, Configuration change, User education, No fault found, Duplicate, Cancelled by client | From the POC; Duplicate and Cancelled by client are "no-solution" codes |
| Attachment scan state | Pending, Clean, Quarantined | Download only when Clean |
| Out-of-scope flag | none, flagged, approved, declined | Visible to the client when flagged |

### 5.2 Ticket types and default state machines

Every type shares four conventions: `New` is the intake state; `Awaiting Client` and `Awaiting Third Party` pause SLA clocks with a mandatory reason; `Resolved` stops the resolution clock and requires the close discipline; `Closed` and `Cancelled` are terminal. Beyond that each type differs.

| Type | States (in order) | Distinctive rules | Billing treatment (default) |
|---|---|---|---|
| Incident | New, Assigned, In Progress, Awaiting Client, Awaiting Third Party, Resolved, Closed, Cancelled | Response and resolution clocks; reopen from Resolved returns to In Progress and keeps the latch | Billable against the contract's support allowance |
| Service Request | New, Triage, Approved, In Progress, Awaiting Client, Awaiting Third Party, Fulfilled, Closed, Cancelled | Triage may require a form; Approved needed when the request type says so; response clock only until Approved, then fulfilment clock | Billable per activity type default |
| Change | New, Assessment, Approved, Scheduled, Implementing, Awaiting Client, Validation, Completed, Closed, Cancelled, Rejected | Must belong to a change window (group) before Scheduled; implementation plan, backout plan and validation notes required before Approved; change approval gate | Billable or fixed per contract clause |
| Problem | New, Investigating, Known Error, Awaiting Third Party, Resolved, Closed, Cancelled | No response clock; resolution target optional; Known Error requires a workaround article link | Non-billable by default (absorbed), overridable per account |
| Project Task | New, Planned, In Progress, Blocked, Done, Closed, Cancelled | No SLA clocks by default; belongs to a project group; effort estimate field | Billable against the project contract |

Transition rules include required fields (for example Resolved requires resolution code, notes and a solution link unless a no-solution code is chosen), who may transition (a portal user may only move to Cancelled and, for their own tickets, confirm Resolved to Closed), and SLA effects. An administrator edits the machine per type and per account in [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md); the validation refuses machines with unreachable terminal states.

### 5.3 Priority matrix

| Impact \ Urgency | High | Medium | Low |
|---|---|---|---|
| High | P1 | P2 | P3 |
| Medium | P2 | P3 | P4 |
| Low | P3 | P4 | P4 |

The server derives priority whenever both inputs are present; a user with the right permission may override priority directly, and the override is audited with the matrix value it replaced. Accounts may override the matrix (TM-04).

### 5.4 SLA behavior

- **Which targets apply:** the contract's SLA policy for the ticket's type and priority; if the contract has none, the account's policy default; if neither, "No SLA" (badge muted, nothing breaks).
- **Which calendar applies:** the policy's calendar, else the account default calendar; the clock remembers the calendar it started on.
- **Business-minute math:** due time is start plus target business minutes on that calendar; the badge shows remaining business time ("Resp 1h 40m"), not wall-clock.
- **Response met** on the first public comment by an operator user or the first transition to an in-progress state, whichever comes first; never changes afterwards.
- **Pause:** entering Awaiting Client, Awaiting Third Party or a Scheduled window requires a reason (the state implies the reason category; a note is optional) and freezes both clocks; the badge shows "Paused" with the reason. **Resume** on leaving the state closes the pause interval, records the business minutes excluded, and shifts due times forward by that amount.
- **Breach latch:** when a clock passes due, the ticket is marked breached for that clock, an audit event is written, and notifications go out. Idle tickets are caught by a sweeper every five minutes, so a breach is never more than five minutes late. A latch is never cleared by a later pause, priority change or reopen.
- **Priority change** restamps targets from the moment of change for the remaining window (the POC restamped from creation; the stricter rule applies here) and records the old and new targets.
- **Pause evidence:** the record view shows every pause with reason, start, end and excluded minutes; the same list appears in the Time and Budget hours breakdown and in exports.

### 5.5 The queue (list) screen

Per [Design System §4](../../01-architecture/DESIGN-SYSTEM.md) and the POC `QueueTab.tsx`:

- Slim toolbar: funnel (opens the condition builder), "Show" dimension dropdowns (Account, Type, Priority, State, Group, Assignee, SLA), search, saved-view selector, Export, New.
- Condition builder: rows of field, operator, value joined with AND, plus a breadcrumb trail of active criteria where clicking a segment removes it; "Save as view" names the filter with columns and sort, private by default, shareable to a group or made an account view.
- Columns (default): Key, Short description, Account, Type, Priority, State, Group, Assignee, SLA, Updated. Edge to edge, sticky header, zebra rows, row and cell hover.
- The SLA column shows the nearest live clock with tone: green with more than 25 percent of the window left, amber below, red "Breached 2h", gray "Paused (client)", muted "No SLA", "Responded" or "Resolved in SLA" once met.
- Default sort: breached first, then soonest due. Stat strip above the list: Open, Due today, Breached, Unassigned; each filters the list.
- Chips: My tickets, My groups, Unassigned, Breached, Flagged out of scope, All open.
- Empty states: no accounts granted ("Ask an administrator for access"); accounts but no tickets ("No tickets yet" with New).
- Full-text search covers key, description, comments, work notes (internal only), attachment names and requester (TM-15).

### 5.6 Dispatch

The same list, pre-filtered to tickets with no group or no assignee, oldest first, with an inline Assign control (group then member) and a count badge on the navigation item. Overallocation warnings from Capacity appear inline when assigning (Phase 3).

### 5.7 New record

Full-screen form per the POC `NewTicketPage.tsx`: Account (required, from granted accounts), Requester (contact search with suggestions from contacts seen on that account), Type, Category, Configuration item, Group, Assigned to (searchable roster), Contract (preselected when the account has one active contract; required), Impact, Urgency, Priority (read-only preview from the matrix, override with permission), SLA preview (targets and calendar from the resolved policy), Short description, Description, Attachments (upload starts immediately; the form cannot submit while a scan is Pending unless the user acknowledges the placeholder), Template picker (fills fields from a ticket template). On submit: toast "CS0001235 created", record opens. Creating against an expired contract period is refused with a link to Contracts.

### 5.8 Record view

Per the POC `TicketDrawer.tsx`, full screen:

- **Record bar:** key, short description (inline edit), state pill, priority pill, SLA bar with both meters and pause segments, out-of-scope banner when flagged.
- **Properties (label-left, commit on blur):** account, requester, type, category, configuration item, group, assignee, contract, impact, urgency, priority, source, group membership (project or change window), external references (ServiceNow key), created, resolved, closed.
- **Work area tabs:** Conversation (composer with Public comment or Work note toggle; work notes tinted and chipped "Internal"; first public reply marked "First response"; attachments per message; Axel draft-reply chip when enabled), Activity (audit events interleaved with pauses and time entries, filterable), Resolution (code, notes, solution link or "create article from this ticket", exemption reason for time).
- **Related-info rail:** contract position (hours this period), time logged (from Time & Budget), attachments with scan state, links (add link by key with type), group, watchers, similar solutions (from the knowledge base, when AI is enabled).
- **Footer actions:** the transitions the state machine allows for this user; Resolve opens the close discipline dialog; Cancel needs a reason; Flag out of scope opens the flag dialog (reason, estimated hours, client-visible note) and the Approve or Decline actions appear for account owners; while flagged, the ticket cannot leave its current state except to Cancelled.
- **Concurrency:** saving a property that someone else changed since the record loaded shows "This ticket changed" with a reload; the last change is never silently clobbered.

### 5.9 Links and groups

- Add link: choose type, enter key; the inverse appears on the other ticket; duplicate-of moves the ticket to Cancelled with code Duplicate on confirmation and copies the requester as a watcher of the original.
- Blocks and blocked by: a blocked ticket shows the blocker in its bar; resolving a blocker notifies the assignees of blocked tickets.
- Groups: a project or change window has a name, type, schedule (start, end, freeze windows), account, owner and a ticket tree; the group page lists its tickets by state with an aggregated SLA and hours position; a Change must belong to a change window before it can be Scheduled (TM-10).

### 5.10 Attachments

Limits: 25 MB per file by default (per-account override), an allowlist of document, image, archive, log and spreadsheet types. Every upload shows Pending until scanned; a Quarantined file shows a warning placeholder, the uploader and an administrator are notified, and the file is never downloadable (TM-14). Inline images from email are re-encoded and shown in the comment body.

### 5.11 Notifications and watchers

Notifications (in-app bell and email per user preference): assigned to you, assigned to your group, mentioned, public comment on a watched ticket, SLA at risk (25 percent remaining), SLA breached, blocker resolved, out-of-scope flag needs approval, attachment quarantined. Repeated events on one ticket collapse into one unread item with a count; mentions never collapse. Watchers are added automatically (creator, assignee, commenters) and can unfollow, and unfollowing is remembered so an automatic follow never re-subscribes them.

### 5.12 Bulk actions (Phase 4)

Select rows in the queue, then reassign, change state (only transitions valid for every selected ticket), or tag; each affected ticket gets its own audit event and the result dialog lists failures per ticket (TM-16).

### 5.13 Change calendar (Phase 4)

A calendar of change windows across accounts with freeze windows; scheduling a change inside a freeze window or overlapping another change on the same configuration item raises a warning that must be acknowledged with a reason (TM-18).

### 5.14 Edge cases

- A ticket created without a contract is refused (the contract is the entitlement anchor).
- Changing a ticket's type after creation is allowed only from New and re-derives the state machine.
- A portal user cannot see work notes, pause reasons in detail (they see "Waiting on you since Tuesday 14:02"), or internal attachments.
- Reopening a Resolved incident within seven days returns it to In Progress and increments the reopen counter used by reporting; after that a new ticket is created linked as related.

## 6. Rollout

1. **Phase 1 (Foundations):** tickets, comments, work notes, attachments with scanning, audit events, the five types with their default machines, matrix, wall-clock SLA fallback where no calendar exists, queue and record screens. Depends on Accounts & Administration Phase 1 and the S3 and GuardDuty setup.
2. **Phase 2 (Focused pilot):** calendar-aware SLA engine with pauses as evidence and the sweeper, links, saved views and the condition builder, dispatch, notifications and watchers, close discipline with resolution codes and solution links, templates. Depends on Knowledge Base Phase 2 (articles) and Time & Budget Phase 2 (time before resolution).
3. **Phase 3 (Operational replacement):** groups (projects, change windows), change type approval gate, out-of-scope flag with approval, priority override permission, reopen rules, contract period enforcement, external references for migrated tickets.
4. **Phase 4 (Later):** bulk actions, change calendar with freeze windows and conflict detection, auto-close timer.

## 7. Success criteria

- Create a P2 incident against a UK account at Friday 17:30 Europe/London with a 4-hour response target; the badge shows the due time as Monday 12:00 and remaining business time, not wall-clock.
- Move a ticket to Awaiting Client for a constructed 90 business minutes and back; both due times shift by exactly 90 business minutes, the pause row shows the reason and the excluded minutes, and the Activity tab shows both events.
- Leave a ticket untouched past its due time; within five minutes it shows Breached, an audit event exists, and the assignee has a notification.
- Try to resolve a ticket with no time logged and no exemption; the transition is refused with the reason.
- A portal user viewing a ticket with three work notes and two public comments sees exactly two messages, and the API returns no work-note fields to that principal.
- Upload a test malware file; it shows Quarantined, the download route refuses, and the administrator has a notification.
- Two users edit the same ticket; the second save is refused with a reload prompt and no field is lost.
- Save a condition-builder filter as a view, share it with a group, and see it in a colleague's view list.

## 8. Open questions

- **Auto-close timer:** should Resolved tickets close automatically after N days without a reply? Default assumption: no auto-close in Phases 1 to 3; Phase 4 adds a per-account timer defaulting to 5 business days.
- **Who may override priority:** dispatchers and account owners, or any consultant? Default assumption: a dedicated permission granted to Dispatcher and Account Owner roles.
- **Response-met on work notes:** does an internal note count as a response? Default assumption: no; only public replies and in-progress transitions.
- **Change approval by the client:** must a client approve a Change before Scheduled? Default assumption: configurable per account; default is internal approval only.
- **Reopen window:** seven days as assumed, or per account? Default assumption: per-account setting defaulting to seven calendar days.
