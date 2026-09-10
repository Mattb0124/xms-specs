# Requirements Traceability Matrix: XMS Ticketing

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Sources:** `Copy of DMS_Ticketing_System_Requirements.xlsx` (sheet `Requirements`, 110 rows); five XMS-added rows (prefix `XA`) covering the audit log, user analytics and assurance capability; and the functional RTM revision 3 of 2026-09-09, which folds in the gap analysis, the day-in-the-life analysis and the operating model session. The `source` column on every row says which. Machine-readable copies: [requirements.csv](./requirements.csv), [requirements.json](./requirements.json).
**Open items:** [Clarifications needed](./CLARIFICATIONS-NEEDED.md) carries the questions that block rows in this register, including the TM-08 routing conflict and the triage of every revision 3 row.
**Related:** [Product Vision](./PRODUCT-VISION.md), [Roadmap](../03-delivery/ROADMAP.md), [Architecture](../01-architecture/ARCHITECTURE.md)

---

## 1. How to read this matrix

Every workbook row has a stable ID (`<category prefix>-<nn>`, numbered in workbook order within its category). Each row maps to exactly one primary module spec under `02-modules/` and to one delivery phase from the [Roadmap](../03-delivery/ROADMAP.md). Secondary modules are named in the module specs themselves. The workbook this matrix was generated from carries 110 rows (90 Must Have, 20 Nice to Have); the assessment deck of 2026-09-03 cites 111 items and 75 Must Have after a reprioritisation pass that is not in this copy. Treat the deck's 75 as the pilot-scoping source and this matrix as the full target register; the reconciliation is an open item in the [Decision Log](./DECISION-LOG.md).

Phases: **1 Foundations** (auth, isolation, pipeline, monitoring, email infrastructure), **2 Focused pilot** (internal beta, no external clients, no Brookfield production traffic), **3 Operational replacement** (ServiceNow can be switched off), **4 Later releases** (incremental).

**0 Unscoped (revision 3 intake)** is not a phase, it is a holding pen. The functional RTM carries no phases and no priorities by design, so every row it introduced sits there as Unassessed until it is triaged into a real phase. A row left there is not scheduled and is not in anyone's plan, which is the point: see [Clarifications needed](./CLARIFICATIONS-NEEDED.md) item C-02.

## 2. Summary

| Phase | Must Have | Nice to Have | Unassessed |
|---|---|---|---|
| 0 Unscoped (revision 3 intake) | 0 | 0 | 75 |
| 1 Foundations | 14 | 0 | 0 |
| 2 Focused pilot | 42 | 0 | 0 |
| 3 Operational replacement | 36 | 0 | 0 |
| 4 Later releases | 3 | 20 | 0 |
| **Total** | **95** | **20** | **75** |

| Module spec | Rows | Must Have | Unassessed |
|---|---|---|---|
| [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 5 | 4 | 1 |
| [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 21 | 12 | 7 |
| [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 11 | 2 | 6 |
| [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 19 | 16 | 1 |
| [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 12 | 8 | 2 |
| [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 7 | 7 | 0 |
| [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 8 | 8 | 0 |
| [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 17 | 7 | 7 |
| [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 9 | 9 | 0 |
| [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 23 | 13 | 4 |
| [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 5 | 4 | 1 |
| [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 2 | 0 | 0 |
| [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 5 | 5 | 0 |
| [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 9 | 0 | 9 |
| [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 10 | 0 | 10 |
| [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 9 | 0 | 9 |
| [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 7 | 0 | 7 |
| [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 5 | 0 | 5 |
| [Configuration Governance](../02-modules/configuration-governance/FUNCTIONAL-SPEC.md) | 4 | 0 | 4 |
| [Outcomes](../02-modules/outcomes/FUNCTIONAL-SPEC.md) | 2 | 0 | 2 |

### Build status

Established by inspecting `frontend` and `backend` on 2026-09-09: requirement-id references in source, the feature modules and migrations present, the AI capability builders, and the as-built notes in each application's `CLAUDE.md`. **This is a read of the code, not an acceptance result.** Built means the capability is present and wired, not that it has been signed off against its acceptance note, and not that it satisfies the revision 3 wording where revision 3 widened the row. Every Partial names its gap.

| Status | Rows |
|---|---|
| Built | 96 |
| Partial | 11 |
| Not started | 83 |
| **Total** | **190** |

| Module spec | Built | Partial | Not started |
|---|---|---|---|
| [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 4 | 0 | 1 |
| [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 13 | 1 | 7 |
| [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 5 | 5 | 1 |
| [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 15 | 3 | 1 |
| [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 8 | 1 | 3 |
| [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 6 | 0 | 1 |
| [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 8 | 0 | 0 |
| [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 9 | 0 | 8 |
| [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 9 | 0 | 0 |
| [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 10 | 1 | 12 |
| [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 | 0 | 2 |
| [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 1 | 0 | 1 |
| [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 5 | 0 | 0 |
| [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 | 0 | 9 |
| [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 | 0 | 10 |
| [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 | 0 | 9 |
| [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 | 0 | 7 |
| [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 0 | 0 | 5 |
| [Configuration Governance](../02-modules/configuration-governance/FUNCTIONAL-SPEC.md) | 0 | 0 | 4 |
| [Outcomes](../02-modules/outcomes/FUNCTIONAL-SPEC.md) | 0 | 0 | 2 |

**Partly built, with the gap named:**

| ID | Requirement | What is missing |
|---|---|---|
| TM-11 | Ability to flag out-of-scope / over-budget work | The flag, the decision and the allowance ship. Revision 3 adds an immutable, client-visible, exportable decision record, which does not exist |
| TM-17 | Ticket templates | Schema only; one reference in the backend and no authoring or apply surface |
| TB-02 | Mandatory time entry before resolution | The time-or-exemption gate ships. Revision 3 makes it composite (resolution code, notes completeness, article prompt, certification-sourced time), and that is not built |
| TB-15 | Multi-currency support | Currency is carried on rate cards and amounts; no FX conversion for consolidated views |
| TB-16 | Profitability view per account | Cost rates and revenue exist; the profitability view and the revision 3 rule that margin never renders without delivered value do not |
| CAP-09 | On-call / shift rota | A rota exists in the backend; no desk surface, no coverage-gap detection, and it drives no routing |
| EM-09 | Priority detection from email content | The prioritise capability exists and is wired to tickets, not to email intake |
| AI-18 | Auto-resolution of allowlisted request types | The allowlist configuration exists; no end-to-end auto-resolution path |
| KB-03 | Client-to-global promotion with sanitisation | The generalise flow with its findings sheet ships; the AI-23 cross-account consent gate that must block it does not exist |
| KB-04 | Article health and coverage | Staleness and reuse signals exist on articles; the coverage report listing high-volume patterns with no article does not |
| KB-05 | Contribution attribution | Author and improver are recorded per version; the per-person and per-account aggregation is not built |

## 3. Matrix by category


### Ticket Management

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| TM-01 | Multi-tenant data isolation | Built | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Hard isolation per client at the data layer, not row-level filtering. |
| TM-02 | Ticket types with distinct workflows | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Incident, Service Request, Change, Problem, Project Task. Each with its own workflow and billing treatment. |
| TM-03 | Configurable state machine | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | States and transitions aligned to the existing DMS ticket lifecycle procedure. Configurable per ticket type. |
| TM-04 | Priority / impact matrix | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Standard impact x urgency matrix producing priority, with per-client override capability. |
| TM-05 | SLA engine | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Response and resolution targets per ticket type, priority and client contract. |
| TM-06 | Per-client business calendars and timezones | Built | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Required for UK, Brazil, Australia, Canada and US coverage. SLA clocks must respect local working hours and holidays. |
| TM-07 | SLA clock pause with reason logging | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Pause on 'Awaiting Client' / 'Awaiting Third Party'. Pause reason and duration stored - this is the evidence used in hour-justification discussions. |
| TM-08 | Assignment groups | Built | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Groups mapped to CSM, OneStream Technical and Infrastructure teams. Support for group-level and individual assignment. |
| TM-09 | Parent / child and related ticket linking | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Link types: parent-child, related, duplicate, blocks/blocked-by. |
| TM-10 | Grouping under project or change window | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Ability to group a ticket tree under a project or scheduled window (e.g. one tree per Azure Files cutover weekend). |
| TM-11 | Ability to flag out-of-scope / over-budget work | Partial | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Configurable flag with client-side visibility. Ticket blocked from progressing until approved. |
| TM-12 | Immutable audit trail | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Every field change recorded with user, timestamp, old value, new value. Non-editable, non-deletable. |
| TM-13 | Public comments vs internal work notes | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Two distinct objects. Internal notes must never be exposed through the portal or ServiceNow public sync. |
| TM-14 | Attachments with virus scanning | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Size limits, allowed file types, AV scan on upload, quarantine on detection. |
| TM-15 | Full-text search and saved filters | Built | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Search across ticket fields, comments and attachments metadata. User-defined saved views. |
| TM-16 | Bulk actions | Built | Nice to Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Bulk reassign, bulk state change, bulk tag - with audit entries per affected record. |
| TM-17 | Ticket templates | Partial | Nice to Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Pre-filled templates for recurring request types to reduce intake time. |
| TM-18 | Change calendar with conflict detection | Built | Nice to Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Visual change calendar with freeze windows and overlap warnings across clients. |
| TM-19 | CMDB / lightweight asset register | Built | Nice to Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Per-client configuration item register, linkable to tickets. |
| TM-21 | Ticket participant record | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | People appear on a ticket in roles other than assignee, with joined and left timestamps and who invited them; contributor count is queryable. |
| TM-22 | Invite a collaborator without transferring ownership | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A named person or skill group is invited, accepts or declines, is notified, and the assignee is unchanged throughout. |
| TM-23 | Account ownership and team construct | Not started | Unassessed | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Every account has exactly one named primary owner; changing it is audited; teams group accounts and people; ownership drives default routing and report authorship. |
| TM-24 | Ranked work queue with stall weighting | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The landing queue orders by a server-computed score over client priority, severity, breach proximity, shift context and, weighted at least as heavily, time since last movement, age against expected duration for that ticket type, and time since last client contact. An administrator changes a weight and the order changes. |
| TM-25 | Default active-work view | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Resolved, closed and transferred tickets are absent from the default view and require a deliberate action to reach. |
| TM-26 | Ticket-to-outcome association with coverage measure | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A ticket can be attached to and detached from an outcome, and the outcome lists it. Linkage coverage, the share of tickets and of delivered hours carrying an outcome, is reportable per account, per engineer and per period, and accounts below a configured coverage floor surface to the account owner and the support director. |
| TM-27 | Container-case detection | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A ticket crossing the configured time-entry, elapsed-day or effort threshold raises TM-11 and notifies the account owner. |
| TM-28 | Shift handover | Not started | Unassessed | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | At the close of a coverage window the outgoing owner produces a handover for the incoming one covering open work, items at risk of breach, commitments made to clients, and anything awaiting a third party. The incoming owner acknowledges it. Unacknowledged handovers are visible to the technical manager. Drafted by Axel (AI-25) and editable before it is passed; retained and searchable against the ticket. |

### Time Tracking & Budget

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| TB-01 | Time entry at ticket level | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Fields: duration, date performed, activity type, billable flag, description. Multiple entries per ticket per user. |
| TB-02 | Mandatory time entry before resolution | Partial | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | A ticket cannot move to Resolved/Closed with zero logged time unless an exemption reason is selected. |
| TB-03 | Activity type taxonomy | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Analysis, Development, Testing, Client Communication, Documentation, Meeting. This is what makes 'where did the hours go' answerable. |
| TB-04 | Billable classification | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Billable / Non-billable / Internal / Pre-sales, set per time entry with a default per activity type. |
| TB-05 | Rate cards by client, contract and role | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Effective-dated versions so historical entries retain the rate in force at the time performed. |
| TB-06 | Contract object with multiple commercial models | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Retainer hours, prepaid blocks, T&M, fixed fee. Includes rollover rules and overage rules. |
| TB-07 | Budget burn-down per client per period | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Consumed vs contracted hours and value, by period, with drill-through to source entries. |
| TB-08 | Forecast to period end | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Projected consumption at period end based on current run rate. |
| TB-09 | Threshold alerts | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Configurable percentage thresholds (e.g. 50/75/90/100%) alerting internal owner and optionally the client contact. |
| TB-10 | Per-ticket hours breakdown | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Hours by person, role, date and activity type for any single ticket. Exportable to Excel/CSV. |
| TB-11 | Adjustment and write-off workflow | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Original entry preserved; adjustment recorded as a separate linked record. |
| TB-12 | Non-ticket time capture | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Per-client buckets for governance, QBR prep, account management and escalation handling. Without this, utilisation reads artificially low and budget burn reads artificially favourable. |
| TB-13 | After-hours and weekend flagging | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Automatic flagging based on the client business calendar, with premium rate or comp-time handling. Needed across the cutover weekend programme. |
| TB-14 | Billing export | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Export in the format THG finance consumes, with a locked/approved period concept so exported data cannot be silently altered. |
| TB-15 | Multi-currency support | Partial | Nice to Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Rate cards and reporting in local currency with FX conversion for consolidated views. |
| TB-16 | Profitability view per account | Partial | Nice to Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Revenue vs delivery cost using cost rates, at account and engagement level. |
| TB-17 | Commercial model as a configurable type | Not started | Unassessed | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A new model type is added with its own consumption rules and the finance export still resolves it to hours and value with no interface change. |

### Team Allocation & Capacity

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| CAP-01 | Resource roster | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Role, FTE %, cost rate, bill rate, skills, certifications, timezone and working calendar per person. |
| CAP-02 | PTO and holiday calendar | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Per-country holiday calendars and individual PTO, feeding the capacity calculation. |
| CAP-03 | Available capacity calculation | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Contracted hours minus PTO minus holidays minus a configurable admin overhead factor. |
| CAP-04 | Planned allocation per person per client per period | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Forward-looking allocation grid, editable by team lead. |
| CAP-05 | Planned vs actual variance reporting | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Planned allocation compared against logged time. This is the report that actually changes behaviour. |
| CAP-06 | Overallocation detection | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Warning raised at assignment time when a person exceeds available capacity in a period. |
| CAP-07 | Skills matrix with single-point-of-failure flagging | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Identify where only one person can service a given client or technology. |
| CAP-08 | Forward demand from pipeline | Built | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Pipeline and project demand included in capacity view, not only current ticket load. |
| CAP-09 | On-call / shift rota | Partial | Nice to Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Rota management with coverage gap detection, linked to after-hours flagging. |
| CAP-10 | Scenario planning | Not started | Nice to Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Model the capacity impact of a prospective win before it is booked. |
| CAP-11 | Account concentration detection with owned response | Not started | Unassessed | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Any account where one person holds more than the configured share of delivered hours in a rolling window raises an alert to the technical manager, escalating to the support director if unactioned within a configured period. The alert carries a state (acknowledged, mitigation planned, accepted as risk, resolved) with the reason recorded, and open alerts are visible on the portfolio and AH-05 views. |
| CAP-12 | Absence-aware routing | Not started | Unassessed | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A person recorded as absent cannot be assigned a ticket, invited as a collaborator, or placed on the triage rota for that period without an explicit recorded override. Work already assigned at the point absence begins is surfaced for reassignment, and the ranked queue excludes them from scoring. |

### Client Portal

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| CP-01 | SSO via SAML / OIDC | Not started | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Authenticate against the client IdP, with local account fallback for clients without federation. |
| CP-02 | Strict data scoping | Built | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | A client user sees only their own organisation's tickets and data. Enforced server-side, verified by automated test. |
| CP-03 | Ticket submission with dynamic forms | Built | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Form fields vary by request type; required fields enforced at submission. |
| CP-04 | Ticket status tracking and comment threads | Built | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Client can view status, add comments and see public updates only. |
| CP-05 | Attachment upload from portal | Built | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Same AV scanning and size limits as internal upload. |
| CP-06 | Budget / consumption visibility toggle | Built | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Per-client switch controlling whether consumption data is exposed in the portal. |
| CP-07 | CSAT survey on ticket close and every quarter end | Built | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Triggered on closure, plus a periodic relationship survey. Results feed reporting. |
| CP-08 | Knowledge base with per-client article visibility | Built | Must Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Articles scoped to global or specific clients. |

### Email Intake

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| EM-01 | Dedicated inbound address | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | With alias support so existing client-facing addresses can be retained. |
| EM-02 | Thread matching on message headers | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Match on Message-ID / References / In-Reply-To. |
| EM-03 | Reply-to-update on existing tickets | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | A reply to a ticket notification appends a comment rather than creating a duplicate. |
| EM-04 | Attachment and inline image extraction | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Attachments stored on the ticket; inline images preserved in the comment body. |
| EM-05 | Signature and quoted-reply stripping | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Strip signatures, disclaimers and quoted history so comments stay readable. |
| EM-06 | Loop protection and auto-responder suppression | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Detect and suppress mail loops and out-of-office auto-replies. A loop with a client mail system is a severity-1 event. |
| EM-07 | Unknown-sender quarantine queue | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Unrecognised senders go to a review queue rather than auto-creating tickets. |
| EM-08 | Outbound email threading and branding | Built | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Outbound notifications correctly threaded and branded per client. |
| EM-09 | Priority detection from email content | Partial | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Suggest priority based on message content, subject to human confirmation. |

### Dashboard & Reporting

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| DR-01 | Near-real-time dashboard refresh | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Defined refresh interval / push updates. Role-scoped and client-scoped. |
| DR-02 | Internal operational view | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Backlog by age, SLA attainment and at-risk, MTTR by type, reopen rate, volume trend, team utilisation, portfolio budget burn. |
| DR-03 | Client-facing view | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Their tickets, their SLA performance, their consumption, their CSAT. Nothing else. |
| DR-04 | Auto-generated weekly report pack (PPTX / PDF) | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Generated from live data on a schedule. Highest-ROI item in the build - it replaces the manual WSR cycle. We would present on a call from a dashboard that can be exported and sent via email for client review |
| DR-05 | Scheduled email delivery of report packs | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Per-client schedule and distribution list. |
| DR-06 | Export to Excel / CSV on all views | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Raw data export for ad-hoc analysis and finance reconciliation. |
| DR-07 | Historical trend retention | Built | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Point-in-time snapshots so trends survive record edits and reclassification. |
| DR-08 | Automated QBR deck generation | Built | Nice to Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Quarterly pack assembled from the period's data, following the standard QBR structure. |
| DR-09 | Customer health score | Built | Nice to Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Composite of CSAT, SLA attainment, budget position and engagement signals. |
| DR-10 | Custom report builder | Not started | Nice to Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Self-service report definition for power users without developer involvement. |
| DR-12 | Client self-service measure | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The client sees how many issues they resolved without raising a ticket, and which articles they used. |
| DR-13 | Collaboration and contribution measures | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Median time to first response, contributors per ticket, and share of tickets first touched by a principal engineer. The first-touch figure reports beside MC-05 over-routing, since over-routing is its mechanism. |
| DR-14 | Renewal exposure view | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | For every contract approaching expiry, one view shows contracted value, delivered value, forecast consumption at expiry, the resulting undelivered exposure, and the account's health score, sortable by exposure and filterable by expiry window. Exposure totals roll up to the portfolio. |
| DR-15 | Portfolio scorecard surface | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The scorecard exists in the product, read quarterly, organised as four movements: is the ladder shifting downward, is the classifier getting braver safely, is knowledge compounding, is the conversation flipping from effort to value. Each line carries baseline, current, direction and target, and names the decision it informs. Ticket volume and MTTR cannot be added to it. |
| DR-16 | Capture-rate gate on the scorecard | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Time-capture rate renders at the top of DR-15. Every value-derived line displays as provisional, and is labelled as such on screen and in export, until capture rate passes its configured threshold. |
| DR-17 | Two pillar scorecards from one dataset | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | An operational scoping for the support director and a commercial scoping for the customer experience lead render from the same underlying data with no divergent figures; a number appearing on both is identical. |
| DR-18 | Service desk team view | Not started | Unassessed | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Team resolution rate within paths 1 and 2, early-escalation pattern, path mix and certification completeness, on a surface the service desk lead owns. Per-person detail is limited to MC-07 cause tags and CL-04; the team rate does not decompose to an individual figure. |

### ServiceNow Integration

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| SN-01 | Bidirectional sync with configurable field mapping | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Per-client-instance mapping configuration, maintainable without a code change. |
| SN-02 | State machine translation | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Translate between the internal state model and each client's. They will not match out of the box. |
| SN-03 | Loop prevention | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Correlation IDs and update watermarking to prevent infinite update ping-pong. |
| SN-04 | Conflict resolution policy | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Defined system of record per field. Last-write-wins is not acceptable as a blanket rule. |
| SN-05 | Comment and work note sync | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Respecting the public vs internal distinction in both directions. |
| SN-06 | Attachment sync | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Two-way attachment transfer with size limit handling. |
| SN-07 | Sync health monitoring and dead-letter queue | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Failed messages retained, alerting on failure, manual replay capability. |
| SN-08 | Multiple concurrent client instances | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Different schemas, different auth, different versions - running simultaneously. |
| SN-09 | One-way ingest mode | Built | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Read-only ingest as a lower-risk starting configuration and as a fallback if write-back is suspended. |

### AI Functionality

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| AI-01 | Auto-categorisation and priority suggestion | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Category, priority, account and CI tagging suggested on intake, human-confirmed. |
| AI-02 | Duplicate detection with merge suggestion | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Flag likely duplicates at creation and propose a merge. |
| AI-03 | Long-thread summarisation | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Summarise ticket history for handover, shift change and escalation briefing. |
| AI-04 | Draft response generation | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Generate a suggested reply; a human always reviews and sends. |
| AI-05 | Weekly report narrative generation | Not started | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Convert dashboard figures into the written talk track for the WSR. |
| AI-06 | Time entry assistance | Not started | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Normalise work descriptions and prompt on unlogged time (e.g. 'you have 6 unlogged hours on Tuesday'). |
| AI-07 | Similar-ticket retrieval and KB suggestion | Built | Must Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Surface comparable resolved tickets and relevant knowledge articles to the assignee. |
| AI-08 | Human-in-the-loop by default | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | No AI action takes effect without human confirmation unless explicitly opted in per client. |
| AI-09 | Confidence thresholds with human fallback | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Below threshold, the suggestion is withheld and the item routes to a human. |
| AI-10 | AI actions logged and attributable | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Every AI suggestion and action recorded in the audit trail, distinguishable from human actions. |
| AI-11 | Per-client AI disable switch | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Some clients will contractually prohibit AI processing of their data. Must be enforceable at the data layer. |
| AI-12 | No training on client data; DPA and residency compliance | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Contractual and technical guarantee before any client data reaches a model provider. |
| AI-13 | Feedback capture on AI suggestions | Built | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Accept/reject captured to measure accuracy and drive tuning. |
| AI-14 | Budget burn anomaly detection | Not started | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Flag accounts tracking materially above or below expected run rate. |
| AI-15 | Escalation risk and sentiment detection | Not started | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Early warning on threads trending negative, before a formal escalation occurs. |
| AI-16 | Effort estimation from historical similar work | Not started | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Suggested effort range on new tickets based on comparable closed work. |
| AI-17 | Allocation suggestions | Not started | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Recommend assignee based on skills, current capacity and account familiarity. |
| AI-18 | Auto-resolution of allowlisted request types | Partial | Nice to Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Fully automated handling of simple, explicitly allowlisted requests. Requires strong guardrails and per-client opt-in. |
| AI-19 | Agentic triage and routing without human review | Not started | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Autonomous triage. Only after measured accuracy on the human-in-the-loop version. |
| AI-20 | Natural language query over reporting data | Not started | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Ask questions of the dataset in plain language and get a chart or table back. |
| AI-21 | Confidence persisted and calibratable | Not started | Unassessed | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The confidence value is stored, and a calibration report compares stated confidence against realised outcome. |
| AI-22 | Draft outcome capture | Not started | Unassessed | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Within the AI-13 stream, a draft records sent unchanged, light edit, heavy edit or discarded, with edit distance. |
| AI-24 | Resolution note drafting | Not started | Unassessed | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | On close, Axel drafts resolution notes from the thread, work notes and time entries, and proposes a resolution code. The draft satisfies the TB-02 completeness rule only once a human confirms it. Confirmation without edit is recorded distinctly from edited confirmation, and the unedited rate is reported. |
| AI-25 | Shift handover summary | Not started | Unassessed | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | At the end of a coverage window Axel drafts the TM-28 handover (open work, breach risk, client commitments, third-party waits) from ticket state and activity, editable before it is passed. |

### Data Migration

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| DM-01 | Historical import from ServiceNow CSM | Built | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Workbook | Open and closed tickets, comments, attachments and time entries. Without history the baseline is lost. |
| DM-02 | Contract and budget history import | Built | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Existing contracts, consumed hours and current balances, reconciled to finance records. |
| DM-03 | Reconciliation report post-migration | Built | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Record counts and hour totals reconciled source vs target, signed off before cutover. |
| DM-04 | Parallel run period | Not started | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Both systems operating concurrently for an agreed period before decommissioning the old one. |
| DM-05 | Knowledge corpus backfill | Not started | Unassessed | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The existing knowledge corpus is imported and is governed by the AI-23 two-scope contribution rule; nothing crosses an account boundary without recorded opt-in. |

### Integrations

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| INT-01 | Identity provider integration (internal) | Built | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 1 Foundations | Workbook | Internal users authenticate via the THG IdP. |
| INT-02 | Finance / billing system export interface | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Structured interface to the billing system rather than manual file handling. |
| INT-03 | Renewal and contract expiry alerting | Built | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Workbook | Alerts ahead of contract end dates, surfaced to the account owner. |
| INT-04 | Slack / Teams integration | Not started | Nice to Have | [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Ticket notifications, create-from-message, and time logging via command. |
| INT-05 | Calendar integration | Built | Nice to Have | [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 4 Later releases | Workbook | Push change windows and scheduled work to Outlook calendars. |

### XMS additions

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| XA-01 | Security audit log | Built | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 1 Foundations | XMS addition | Every authentication, authorisation, administration, data-movement, abuse and AI decision is recorded as an append-only security event with actor, principal kind, request and trace ids; searchable and exportable. |
| XA-02 | User analytics | Built | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 1 Foundations | XMS addition | Screen views, named actions, searches, Axel decisions and API requests are captured as usage events (no ticket, email or article content), per role and per account, with portal capture governed by an account setting. |
| XA-03 | Audit and usage reporting | Built | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 2 Focused pilot | XMS addition | Admin screens for audit search over all three streams, a security dashboard and a usage dashboard (active users, feature adoption, core-loop funnel, knowledge gaps, Axel acceptance, portal deflection), with exports and an analyst SQL surface. |
| XA-04 | Security assurance and audit readiness | Built | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 1 Foundations | XMS addition | Every change passes the security definition of done (isolation, visibility, realm, evidence, egress) with the required tests and a completed checklist; controls are mapped to ISO 27001, SOC 2 and OWASP ASVS with evidence produced automatically; monthly access reviews, quarterly runbook rehearsals, annual penetration test. |
| XA-05 | Tamper evidence and retention | Built | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 3 Operational replacement | XMS addition | Append-only event tables, nightly Parquet archive to an Object Lock bucket, chained daily digests with weekly verification, retention per stream and per account DPA, pseudonymisation for erasure requests. |

### Resolution Ladder & Routing

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| RL-01 | Path as a first-class ticket attribute | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Every ticket carries a classified path (0 client self-service, 1 front-desk resolved, 2 front-desk owned and engineer-validated, 3 engineer-owned) stamped at intake, and an actual path derived from the ownership and participant trail at close. Both are stored, neither overwrites the other, and both are reportable. |
| RL-02 | Historical profiling layer | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Closed historical records are profiled by client, request type, complexity, who resolved them, and whether resolution required credentialed access or genuine expertise. Queryable per client and per request type, and the classifier's prior from day one. |
| RL-03 | Path classification at intake | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Axel proposes a path from the profile and the request content, with confidence, subject to AI-08 and AI-09. The proposed path drives routing. A human can override, and the override is recorded against the proposal. |
| RL-04 | Credential-blocked action taxonomy | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Request types are marked where resolution requires client-side access or elevated permission. A marked type cannot classify to path 1 and routes to path 3 or path 0. The marking is maintained per client, since access varies by account. |
| RL-05 | Path 2 validation touch | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | An engineer records a validation, certification or coordination touch on a ticket the agent still owns. The touch is a TM-21 participant event carrying a touch type, the assignee is unchanged, and the actual path resolves to 2 rather than 3. |
| RL-06 | Path 0 stays on platform | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A client resolving through self-service produces a record without a Hackett touch: what was asked, what was returned, and whether the experience satisfied. The record attaches to the account and feeds AH-03. |
| RL-07 | Path 0 fallback capture | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A self-service attempt abandoned into a raised ticket links to that attempt, and fallback rate is reportable by request type and account. |
| RL-08 | Guided resolution for the front desk | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Where the profile holds a known-good path, Axel walks a non-technical resolver through it step by step against the current corpus. Where the profile says expertise or access is required, Axel proposes path 2 or path 3 instead of guidance. |
| RL-09 | Self-service candidate surfacing | Not started | Unassessed | [Resolution Ladder & Routing](../02-modules/resolution-ladder/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Request types resolved repeatedly at path 1 without engineer involvement surface as path-0 candidates, ranked by volume and consistency of resolution, on a surface the service desk lead owns. |

### Measurement & Calibration

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| MC-01 | Intake mix by path | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The share of intake landing at each of the four paths reports per account, per period, with trend, and rolls up to the portfolio. |
| MC-02 | Front-desk resolution rate, paths 1 and 2 | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Computed over tickets whose classified path was 1 or 2. A ticket classified 3 is absent from the denominator regardless of outcome, and no configuration can move it in. Reported at team and account level only; no screen, export or report resolves it to an individual. |
| MC-03 | Engineer resolution rate, path 3 | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Computed over tickets whose classified path was 3, reported at account and practice level only; no screen, export or report resolves it to an individual. Individual coaching signal comes from MC-07 cause tags and CL-04. |
| MC-04 | Automatic misroute detection | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Where classified path and actual path disagree, a misroute is raised without anyone reporting it, and its direction is derived from the ownership trail. |
| MC-05 | Under-routing and over-routing reported separately | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Under-routing (classified low, escalated) and over-routing (classified high, resolvable at the front desk) report as distinct rates, never as one accuracy figure. |
| MC-06 | First-move-to-resolver measure | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | First-contact resolution is defined and computed as the ticket reaching its final resolver on the first move, not as the service desk having solved it. The legacy first-level figure remains available during transition and is labelled as such. |
| MC-07 | Misroute review queue with cause tagging | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Misroutes queue for the technical manager on a weekly cadence. Each is tagged model was wrong or person was wrong with a short reason. Unreviewed misroutes age visibly and surface to the support director past a configured age. |
| MC-08 | Tags feed classifier improvement | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Cause tags are retained as labelled training signal, are reportable by cause, account and manager, and a model-was-wrong volume trend is visible beside the classifier's accuracy. |
| MC-09 | Tag sampling by the support director | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The director can sample a manager's tags, record agreement or disagreement per sampled item, and see disagreement rate per manager. Sampling is visible to the manager. |
| MC-10 | Cross-manager variance view | Not started | Unassessed | [Measurement & Calibration](../02-modules/measurement-and-calibration/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Calibration quality, ladder mix, misroute rate and certification completeness compare between managers and between service desk teams, not only within accounts, on a surface the support director and service desk lead own. |

### Account Health & Experience

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| AH-01 | Continuous account activity record | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Every touch on an account, any path, any shift, any person, any reporting line, lands in one account-level record the account owner sees without running a report, including work done by people who do not report to them. |
| AH-02 | Patterns, not a feed | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The account view surfaces recurring requests, repeated themes, commitments made to the client and precedents set, as patterns over a rolling window, not only as a chronological list. |
| AH-03 | Readiness trajectory | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A per-account trajectory composed of front-desk share, path-0 volume and fallback rate, profile maturity and knowledge coverage, calibrated against that account's own historical mix rather than a global target. Rising front-desk share reads as readiness, not as risk. |
| AH-04 | Experience trajectory | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A per-account trajectory composed of CSAT, responsiveness, expectation-management signal and perception notes. No surface renders AH-03 without AH-04 beside it. |
| AH-05 | Ranked account surface | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The CSM, the technical manager, the CSM lead and the director land on accounts ranked by attention need, computed server-side from health movement, exposure, consumption position and open divergences, never on an alphabetical or portfolio-order list. |
| AH-06 | Flexible perception capture | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Meeting transcripts, forwarded emails, typed notes and voice notes attach to the account record, are attributable and timestamped, are searchable, and feed AH-04. Voice notes transcribe. |
| AH-07 | Crystallised prior at cutover | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | An account can be seeded with a dated starting assessment (owner's read of health, known fragility, key relationships, continuity risk) recorded as a stated prior. Later movement renders against the prior rather than against an empty history, and the prior remains readable and attributable. |
| AH-08 | Service-line seam | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The account-health object holds more than one service line. Support is the only line populated at launch; adding a second requires configuration, not schema change, and no surface hard-codes support as the only line. |
| AH-09 | Account touch cadence | Not started | Unassessed | [Account Health & Experience](../02-modules/account-health/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Direct account conversations log against the account with date and participant. Rolling coverage per account is visible, a per-account target interval is configurable, and accounts past their interval surface on AH-05. |

### Time Certification

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| TC-01 | Daily certification flow | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Every role from agent to director completes a card-based end-of-day wrap-up in under a minute. It is available on any device and does not require opening a ticket. |
| TC-02 | System-proposed activity | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The first card proposes the day's activities from ticket, comment, time-entry and calendar signals for confirmation. The person confirms, removes or corrects; nothing is entered from a blank screen. |
| TC-03 | Off-system capture by text or voice | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | One prompt asks whether anything else happened, answerable by typing or by speaking. Spoken input is transcribed into a candidate entry the person confirms. |
| TC-04 | Effort estimation against placeholders | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Each confirmed activity gets one card for effort. Duration fields show a placeholder and are never pre-filled with a computed actual; the person supplies the figure. |
| TC-05 | Catch-all bucket | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | An other bucket accepts effort without forcing a ticket, an account or an activity type, so no one is blocked from completing the wrap-up. |
| TC-06 | Other-bucket guardrail, weekly | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The size of other is policed weekly, never daily. Crossing a role-configurable threshold raises to the person and their manager, and the threshold and its owner appear in the CG-01 register. |
| TC-07 | Completeness tracking, not content grading | Not started | Unassessed | [Time Certification](../02-modules/time-certification/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A missed evening is permitted; the next login shows outstanding wrap-ups. Completeness is reportable per person and per period and may drive enforcement. No report, screen or export renders certification magnitude as a performance measure of a person, and this is enforced rather than conventional. |

### Collaboration Signal

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| CL-01 | Closure grading of collaborators | Not started | Unassessed | [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | At closure the ticket owner grades each TM-21 participant on a short scale with optional comment. Skipping is permitted and the skip rate is reportable. |
| CL-02 | CSM grading from client-relayed feedback | Not started | Unassessed | [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A CSM records feedback about a named person as relayed from the client, attributed to the client source and dated, feeding the client side of CL-04. |
| CL-03 | Weekly collaboration digest | Not started | Unassessed | [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Once a week a person is shown who they worked with and invited to comment. It is skippable, takes under a minute, and never chases. |
| CL-04 | Peer-and-client quadrant view | Not started | Unassessed | [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Peer signal renders against client satisfaction in four quadrants per person and per account. Client satisfaction governs where the two disagree, and the disagreement is itself the reported signal. |
| CL-05 | Asymmetric visibility | Not started | Unassessed | [Collaboration Signal](../02-modules/collaboration-signal/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Positive feedback is attributable and visible to its subject. Concerns are aggregated and anonymised, never rendered attributably, and are withheld from display until a configured minimum contributor count is reached. No interface, export or audit view can resolve an anonymised concern to its author. |

### Configuration Governance

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| CG-01 | Configuration register with named owners | Not started | Unassessed | [Configuration Governance](../02-modules/configuration-governance/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Every configurable parameter appears in one register with a named owner and a plain-language description of what it affects: path rules and credential markings, classifier and queue weights, all thresholds, the TC-06 guardrail, activity and outcome taxonomies, auto-resolution allowlists, consent flags, CL-05 aggregation minimums, and coverage floors. A parameter with no owner is visible as unowned. |
| CG-02 | Audited change with reason and effective date | Not started | Unassessed | [Configuration Governance](../02-modules/configuration-governance/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Changing a parameter records who, when, old value, new value, a reason and an effective date. Prior values remain readable, and no interface edits or deletes the history. |
| CG-03 | Change visible where it moves a number | Not started | Unassessed | [Configuration Governance](../02-modules/configuration-governance/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A trend or scorecard line spanning a configuration change renders a marker for that change, so a step is never read as behaviour when it was a setting. |
| CG-04 | Review cadence and staleness | Not started | Unassessed | [Configuration Governance](../02-modules/configuration-governance/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Each parameter carries a review cadence; parameters past it surface to their owner and, unactioned, to the support director. |

### Outcomes

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| OC-01 | Outcome object above the ticket | Not started | Unassessed | [Outcomes](../02-modules/outcomes/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | An outcome carries name, stated business result, owner, period, status, type, client visibility, linked tickets and linked contract. The type taxonomy is configurable per client from a maintained default list, each type carrying a default client-visibility setting that can be overridden per instance and is audited when it is. |
| OC-02 | Outcome-framed client reporting | Not started | Unassessed | [Outcomes](../02-modules/outcomes/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | The client-facing report leads on business result with tickets and hours as supporting evidence, and shows only client-visible outcome types. |

### Solution Knowledge Base

| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |
|---|---|---|---|---|---|---|---|
| KB-01 | Authoring, lifecycle, ownership, versioning | Built | Unassessed | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | An article moves draft to review to published to retired, has a named owner, and prior versions remain readable. |
| KB-02 | Candidate queue and promotion | Built | Unassessed | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | A candidate submitted at resolution appears in the queue and can be promoted, merged, or rejected with a reportable reason. |
| KB-03 | Client-to-global promotion with sanitisation | Partial | Unassessed | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Promoting to global forces a review for client identifiers and configuration detail, and is blocked unless the source account has explicitly opted in to cross-account contribution (AI-23). |
| KB-04 | Article health and coverage | Partial | Unassessed | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Each article shows reuse count and last-validated date, stale articles flag against the review cadence, and a report lists high-volume patterns with no article. |
| KB-05 | Contribution attribution | Partial | Unassessed | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Author and improver are recorded per version and aggregate per person and per account. |
| AI-23 | Two-scope knowledge contribution consent | Not started | Unassessed | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 0 Unscoped (revision 3 intake) | Functional RTM r3 | Contribution within the originating account is on by default and can be switched off per account. Contribution across accounts is off by default and requires explicit opt-in recorded in account configuration. Both are enforced at the data layer, honoured by KB-02, KB-03, AI-07, RL-08 and any historical backfill, and independent of the AI-11 processing switch. |

## 4. Matrix by module spec


### Accounts & Administration (`02-modules/accounts-and-administration/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| TM-01 | Multi-tenant data isolation | Built | Must Have | 1 Foundations | Workbook |
| TM-06 | Per-client business calendars and timezones | Built | Must Have | 3 Operational replacement | Workbook |
| TM-08 | Assignment groups | Built | Must Have | 1 Foundations | Workbook |
| TM-23 | Account ownership and team construct | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| INT-01 | Identity provider integration (internal) | Built | Must Have | 1 Foundations | Workbook |

### Ticket Management (`02-modules/ticket-management/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| TM-02 | Ticket types with distinct workflows | Built | Must Have | 2 Focused pilot | Workbook |
| TM-03 | Configurable state machine | Built | Must Have | 2 Focused pilot | Workbook |
| TM-04 | Priority / impact matrix | Built | Must Have | 2 Focused pilot | Workbook |
| TM-05 | SLA engine | Built | Must Have | 2 Focused pilot | Workbook |
| TM-07 | SLA clock pause with reason logging | Built | Must Have | 2 Focused pilot | Workbook |
| TM-09 | Parent / child and related ticket linking | Built | Must Have | 2 Focused pilot | Workbook |
| TM-10 | Grouping under project or change window | Built | Must Have | 3 Operational replacement | Workbook |
| TM-11 | Ability to flag out-of-scope / over-budget work | Partial | Must Have | 3 Operational replacement | Workbook |
| TM-12 | Immutable audit trail | Built | Must Have | 1 Foundations | Workbook |
| TM-13 | Public comments vs internal work notes | Built | Must Have | 2 Focused pilot | Workbook |
| TM-14 | Attachments with virus scanning | Built | Must Have | 1 Foundations | Workbook |
| TM-15 | Full-text search and saved filters | Built | Must Have | 2 Focused pilot | Workbook |
| TM-16 | Bulk actions | Built | Nice to Have | 4 Later releases | Workbook |
| TM-18 | Change calendar with conflict detection | Built | Nice to Have | 4 Later releases | Workbook |
| TM-21 | Ticket participant record | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TM-22 | Invite a collaborator without transferring ownership | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TM-24 | Ranked work queue with stall weighting | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TM-25 | Default active-work view | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TM-26 | Ticket-to-outcome association with coverage measure | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TM-27 | Container-case detection | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TM-28 | Shift handover | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Solution Knowledge Base (`02-modules/knowledge-base/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| TM-17 | Ticket templates | Partial | Nice to Have | 4 Later releases | Workbook |
| TM-19 | CMDB / lightweight asset register | Built | Nice to Have | 4 Later releases | Workbook |
| CP-08 | Knowledge base with per-client article visibility | Built | Must Have | 2 Focused pilot | Workbook |
| AI-07 | Similar-ticket retrieval and KB suggestion | Built | Must Have | 2 Focused pilot | Workbook |
| AI-18 | Auto-resolution of allowlisted request types | Partial | Nice to Have | 4 Later releases | Workbook |
| KB-01 | Authoring, lifecycle, ownership, versioning | Built | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| KB-02 | Candidate queue and promotion | Built | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| KB-03 | Client-to-global promotion with sanitisation | Partial | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| KB-04 | Article health and coverage | Partial | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| KB-05 | Contribution attribution | Partial | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AI-23 | Two-scope knowledge contribution consent | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Time, Contracts & Budget (`02-modules/time-and-budget/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| TB-01 | Time entry at ticket level | Built | Must Have | 2 Focused pilot | Workbook |
| TB-02 | Mandatory time entry before resolution | Partial | Must Have | 2 Focused pilot | Workbook |
| TB-03 | Activity type taxonomy | Built | Must Have | 2 Focused pilot | Workbook |
| TB-04 | Billable classification | Built | Must Have | 2 Focused pilot | Workbook |
| TB-05 | Rate cards by client, contract and role | Built | Must Have | 3 Operational replacement | Workbook |
| TB-06 | Contract object with multiple commercial models | Built | Must Have | 2 Focused pilot | Workbook |
| TB-07 | Budget burn-down per client per period | Built | Must Have | 2 Focused pilot | Workbook |
| TB-08 | Forecast to period end | Built | Must Have | 3 Operational replacement | Workbook |
| TB-09 | Threshold alerts | Built | Must Have | 3 Operational replacement | Workbook |
| TB-10 | Per-ticket hours breakdown | Built | Must Have | 2 Focused pilot | Workbook |
| TB-11 | Adjustment and write-off workflow | Built | Must Have | 3 Operational replacement | Workbook |
| TB-12 | Non-ticket time capture | Built | Must Have | 4 Later releases | Workbook |
| TB-13 | After-hours and weekend flagging | Built | Must Have | 3 Operational replacement | Workbook |
| TB-14 | Billing export | Built | Must Have | 3 Operational replacement | Workbook |
| TB-15 | Multi-currency support | Partial | Nice to Have | 4 Later releases | Workbook |
| TB-16 | Profitability view per account | Partial | Nice to Have | 4 Later releases | Workbook |
| TB-17 | Commercial model as a configurable type | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| INT-02 | Finance / billing system export interface | Built | Must Have | 3 Operational replacement | Workbook |
| INT-03 | Renewal and contract expiry alerting | Built | Must Have | 3 Operational replacement | Workbook |

### Capacity & Allocation (`02-modules/capacity-and-allocation/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| CAP-01 | Resource roster | Built | Must Have | 2 Focused pilot | Workbook |
| CAP-02 | PTO and holiday calendar | Built | Must Have | 4 Later releases | Workbook |
| CAP-03 | Available capacity calculation | Built | Must Have | 3 Operational replacement | Workbook |
| CAP-04 | Planned allocation per person per client per period | Built | Must Have | 3 Operational replacement | Workbook |
| CAP-05 | Planned vs actual variance reporting | Built | Must Have | 3 Operational replacement | Workbook |
| CAP-06 | Overallocation detection | Built | Must Have | 3 Operational replacement | Workbook |
| CAP-07 | Skills matrix with single-point-of-failure flagging | Built | Must Have | 3 Operational replacement | Workbook |
| CAP-08 | Forward demand from pipeline | Built | Must Have | 4 Later releases | Workbook |
| CAP-09 | On-call / shift rota | Partial | Nice to Have | 4 Later releases | Workbook |
| CAP-10 | Scenario planning | Not started | Nice to Have | 4 Later releases | Workbook |
| CAP-11 | Account concentration detection with owned response | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CAP-12 | Absence-aware routing | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Client Portal (`02-modules/client-portal/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| CP-01 | SSO via SAML / OIDC | Not started | Must Have | 3 Operational replacement | Workbook |
| CP-02 | Strict data scoping | Built | Must Have | 1 Foundations | Workbook |
| CP-03 | Ticket submission with dynamic forms | Built | Must Have | 2 Focused pilot | Workbook |
| CP-04 | Ticket status tracking and comment threads | Built | Must Have | 2 Focused pilot | Workbook |
| CP-05 | Attachment upload from portal | Built | Must Have | 2 Focused pilot | Workbook |
| CP-06 | Budget / consumption visibility toggle | Built | Must Have | 2 Focused pilot | Workbook |
| CP-07 | CSAT survey on ticket close and every quarter end | Built | Must Have | 3 Operational replacement | Workbook |

### Email Intake & Outbound (`02-modules/email-intake/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| EM-01 | Dedicated inbound address | Built | Must Have | 1 Foundations | Workbook |
| EM-02 | Thread matching on message headers | Built | Must Have | 2 Focused pilot | Workbook |
| EM-03 | Reply-to-update on existing tickets | Built | Must Have | 2 Focused pilot | Workbook |
| EM-04 | Attachment and inline image extraction | Built | Must Have | 2 Focused pilot | Workbook |
| EM-05 | Signature and quoted-reply stripping | Built | Must Have | 2 Focused pilot | Workbook |
| EM-06 | Loop protection and auto-responder suppression | Built | Must Have | 2 Focused pilot | Workbook |
| EM-07 | Unknown-sender quarantine queue | Built | Must Have | 2 Focused pilot | Workbook |
| EM-08 | Outbound email threading and branding | Built | Must Have | 1 Foundations | Workbook |

### Dashboards & Report Packs (`02-modules/dashboard-and-reporting/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| DR-01 | Near-real-time dashboard refresh | Built | Must Have | 2 Focused pilot | Workbook |
| DR-02 | Internal operational view | Built | Must Have | 2 Focused pilot | Workbook |
| DR-03 | Client-facing view | Built | Must Have | 2 Focused pilot | Workbook |
| DR-04 | Auto-generated weekly report pack (PPTX / PDF) | Built | Must Have | 2 Focused pilot | Workbook |
| DR-05 | Scheduled email delivery of report packs | Built | Must Have | 3 Operational replacement | Workbook |
| DR-06 | Export to Excel / CSV on all views | Built | Must Have | 2 Focused pilot | Workbook |
| DR-07 | Historical trend retention | Built | Must Have | 3 Operational replacement | Workbook |
| DR-08 | Automated QBR deck generation | Built | Nice to Have | 4 Later releases | Workbook |
| DR-09 | Customer health score | Built | Nice to Have | 4 Later releases | Workbook |
| DR-10 | Custom report builder | Not started | Nice to Have | 4 Later releases | Workbook |
| DR-12 | Client self-service measure | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| DR-13 | Collaboration and contribution measures | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| DR-14 | Renewal exposure view | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| DR-15 | Portfolio scorecard surface | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| DR-16 | Capture-rate gate on the scorecard | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| DR-17 | Two pillar scorecards from one dataset | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| DR-18 | Service desk team view | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### ServiceNow Sync (`02-modules/servicenow-integration/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| SN-01 | Bidirectional sync with configurable field mapping | Built | Must Have | 3 Operational replacement | Workbook |
| SN-02 | State machine translation | Built | Must Have | 3 Operational replacement | Workbook |
| SN-03 | Loop prevention | Built | Must Have | 3 Operational replacement | Workbook |
| SN-04 | Conflict resolution policy | Built | Must Have | 3 Operational replacement | Workbook |
| SN-05 | Comment and work note sync | Built | Must Have | 3 Operational replacement | Workbook |
| SN-06 | Attachment sync | Built | Must Have | 3 Operational replacement | Workbook |
| SN-07 | Sync health monitoring and dead-letter queue | Built | Must Have | 3 Operational replacement | Workbook |
| SN-08 | Multiple concurrent client instances | Built | Must Have | 3 Operational replacement | Workbook |
| SN-09 | One-way ingest mode | Built | Must Have | 2 Focused pilot | Workbook |

### Axel AI Functionality (`02-modules/ai-functionality/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| EM-09 | Priority detection from email content | Partial | Nice to Have | 4 Later releases | Workbook |
| AI-01 | Auto-categorisation and priority suggestion | Built | Must Have | 2 Focused pilot | Workbook |
| AI-02 | Duplicate detection with merge suggestion | Built | Must Have | 2 Focused pilot | Workbook |
| AI-03 | Long-thread summarisation | Built | Must Have | 2 Focused pilot | Workbook |
| AI-04 | Draft response generation | Built | Must Have | 3 Operational replacement | Workbook |
| AI-05 | Weekly report narrative generation | Not started | Must Have | 3 Operational replacement | Workbook |
| AI-06 | Time entry assistance | Not started | Must Have | 3 Operational replacement | Workbook |
| AI-08 | Human-in-the-loop by default | Built | Must Have | 2 Focused pilot | Workbook |
| AI-09 | Confidence thresholds with human fallback | Built | Must Have | 2 Focused pilot | Workbook |
| AI-10 | AI actions logged and attributable | Built | Must Have | 1 Foundations | Workbook |
| AI-11 | Per-client AI disable switch | Built | Must Have | 1 Foundations | Workbook |
| AI-12 | No training on client data; DPA and residency compliance | Built | Must Have | 1 Foundations | Workbook |
| AI-13 | Feedback capture on AI suggestions | Built | Must Have | 2 Focused pilot | Workbook |
| AI-14 | Budget burn anomaly detection | Not started | Must Have | 3 Operational replacement | Workbook |
| AI-15 | Escalation risk and sentiment detection | Not started | Nice to Have | 4 Later releases | Workbook |
| AI-16 | Effort estimation from historical similar work | Not started | Nice to Have | 4 Later releases | Workbook |
| AI-17 | Allocation suggestions | Not started | Nice to Have | 4 Later releases | Workbook |
| AI-19 | Agentic triage and routing without human review | Not started | Nice to Have | 4 Later releases | Workbook |
| AI-20 | Natural language query over reporting data | Not started | Nice to Have | 4 Later releases | Workbook |
| AI-21 | Confidence persisted and calibratable | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AI-22 | Draft outcome capture | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AI-24 | Resolution note drafting | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AI-25 | Shift handover summary | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Data Migration & Cutover (`02-modules/data-migration/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| DM-01 | Historical import from ServiceNow CSM | Built | Must Have | 2 Focused pilot | Workbook |
| DM-02 | Contract and budget history import | Built | Must Have | 3 Operational replacement | Workbook |
| DM-03 | Reconciliation report post-migration | Built | Must Have | 3 Operational replacement | Workbook |
| DM-04 | Parallel run period | Not started | Must Have | 3 Operational replacement | Workbook |
| DM-05 | Knowledge corpus backfill | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Platform Integrations (`02-modules/integrations/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| INT-04 | Slack / Teams integration | Not started | Nice to Have | 4 Later releases | Workbook |
| INT-05 | Calendar integration | Built | Nice to Have | 4 Later releases | Workbook |

### Audit Log & User Analytics (`01-architecture/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| XA-01 | Security audit log | Built | Must Have | 1 Foundations | XMS addition |
| XA-02 | User analytics | Built | Must Have | 1 Foundations | XMS addition |
| XA-03 | Audit and usage reporting | Built | Must Have | 2 Focused pilot | XMS addition |
| XA-04 | Security assurance and audit readiness | Built | Must Have | 1 Foundations | XMS addition |
| XA-05 | Tamper evidence and retention | Built | Must Have | 3 Operational replacement | XMS addition |

### Resolution Ladder & Routing (`02-modules/resolution-ladder/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| RL-01 | Path as a first-class ticket attribute | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-02 | Historical profiling layer | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-03 | Path classification at intake | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-04 | Credential-blocked action taxonomy | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-05 | Path 2 validation touch | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-06 | Path 0 stays on platform | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-07 | Path 0 fallback capture | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-08 | Guided resolution for the front desk | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| RL-09 | Self-service candidate surfacing | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Measurement & Calibration (`02-modules/measurement-and-calibration/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| MC-01 | Intake mix by path | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-02 | Front-desk resolution rate, paths 1 and 2 | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-03 | Engineer resolution rate, path 3 | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-04 | Automatic misroute detection | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-05 | Under-routing and over-routing reported separately | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-06 | First-move-to-resolver measure | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-07 | Misroute review queue with cause tagging | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-08 | Tags feed classifier improvement | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-09 | Tag sampling by the support director | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| MC-10 | Cross-manager variance view | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Account Health & Experience (`02-modules/account-health/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| AH-01 | Continuous account activity record | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-02 | Patterns, not a feed | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-03 | Readiness trajectory | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-04 | Experience trajectory | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-05 | Ranked account surface | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-06 | Flexible perception capture | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-07 | Crystallised prior at cutover | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-08 | Service-line seam | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| AH-09 | Account touch cadence | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Time Certification (`02-modules/time-certification/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| TC-01 | Daily certification flow | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TC-02 | System-proposed activity | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TC-03 | Off-system capture by text or voice | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TC-04 | Effort estimation against placeholders | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TC-05 | Catch-all bucket | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TC-06 | Other-bucket guardrail, weekly | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| TC-07 | Completeness tracking, not content grading | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Collaboration Signal (`02-modules/collaboration-signal/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| CL-01 | Closure grading of collaborators | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CL-02 | CSM grading from client-relayed feedback | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CL-03 | Weekly collaboration digest | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CL-04 | Peer-and-client quadrant view | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CL-05 | Asymmetric visibility | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Configuration Governance (`02-modules/configuration-governance/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| CG-01 | Configuration register with named owners | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CG-02 | Audited change with reason and effective date | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CG-03 | Change visible where it moves a number | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| CG-04 | Review cadence and staleness | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

### Outcomes (`02-modules/outcomes/`)

| ID | Requirement | Status | Priority | Phase | Source |
|---|---|---|---|---|---|
| OC-01 | Outcome object above the ticket | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |
| OC-02 | Outcome-framed client reporting | Not started | Unassessed | 0 Unscoped (revision 3 intake) | Functional RTM r3 |

## 5. Maintenance rule

This file is generated by `00-overview/scripts/build_register.py` (ADR-00 in the Decision Log) from three sources: the workbook, the `EXTRA_REQUIREMENTS` block and the `NEW_REQUIREMENTS` block. Edit the workbook or the relevant block in the script, regenerate, and commit the script and all three outputs together; never hand-edit the tables, or the CSV and this page will diverge.

Regenerate with:

```
py 00-overview/scripts/build_register.py "<path to Copy of DMS_Ticketing_System_Requirements.xlsx>"
```
