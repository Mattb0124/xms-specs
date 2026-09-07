# Requirements Traceability Matrix: XMS Ticketing

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Source:** `Copy of DMS_Ticketing_System_Requirements.xlsx` (sheet `Requirements`, 110 rows). Machine-readable copies: [requirements.csv](./requirements.csv), [requirements.json](./requirements.json). Four XMS-added rows (prefix `XA`, category "XMS additions") cover the audit log and user analytics capability.
**Related:** [Product Vision](./PRODUCT-VISION.md), [Roadmap](../03-delivery/ROADMAP.md), [Architecture](../01-architecture/ARCHITECTURE.md)

---

## 1. How to read this matrix

Every workbook row has a stable ID (`<category prefix>-<nn>`, numbered in workbook order within its category). Each row maps to exactly one primary module spec under `02-modules/` and to one delivery phase from the [Roadmap](../03-delivery/ROADMAP.md). Secondary modules are named in the module specs themselves. The workbook this matrix was generated from carries 110 rows (90 Must Have, 20 Nice to Have); the assessment deck of 2026-09-03 cites 111 items and 75 Must Have after a reprioritisation pass that is not in this copy. Treat the deck's 75 as the pilot-scoping source and this matrix as the full target register; the reconciliation is an open item in the [Decision Log](./DECISION-LOG.md).

Phases: **1 Foundations** (auth, isolation, pipeline, monitoring, email infrastructure), **2 Focused pilot** (internal beta, no external clients, no Brookfield production traffic), **3 Operational replacement** (ServiceNow can be switched off), **4 Later releases** (incremental).

## 2. Summary

| Phase | Must Have | Nice to Have |
|---|---|---|
| 1 Foundations | 14 | 0 |
| 2 Focused pilot | 42 | 0 |
| 3 Operational replacement | 36 | 0 |
| 4 Later releases | 3 | 20 |
| **Total** | **95** | **20** |

| Module spec | Rows | Must Have |
|---|---|---|
| [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 4 | 4 |
| [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 14 | 12 |
| [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 5 | 2 |
| [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 18 | 16 |
| [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 10 | 8 |
| [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 7 | 7 |
| [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 8 | 8 |
| [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 10 | 7 |
| [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 9 | 9 |
| [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 19 | 13 |
| [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 4 | 4 |
| [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 2 | 0 |
| [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 5 | 5 |

## 3. Matrix by workbook category


### Ticket Management

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| TM-01 | Multi-tenant data isolation | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 1 Foundations | Hard isolation per client at the data layer, not row-level filtering. |
| TM-02 | Ticket types with distinct workflows | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Incident, Service Request, Change, Problem, Project Task. Each with its own workflow and billing treatment. |
| TM-03 | Configurable state machine | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | States and transitions aligned to the existing DMS ticket lifecycle procedure. Configurable per ticket type. |
| TM-04 | Priority / impact matrix | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Standard impact x urgency matrix producing priority, with per-client override capability. |
| TM-05 | SLA engine | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Response and resolution targets per ticket type, priority and client contract. |
| TM-06 | Per-client business calendars and timezones | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Required for UK, Brazil, Australia, Canada and US coverage. SLA clocks must respect local working hours and holidays. |
| TM-07 | SLA clock pause with reason logging | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Pause on 'Awaiting Client' / 'Awaiting Third Party'. Pause reason and duration stored - this is the evidence used in hour-justification discussions. |
| TM-08 | Assignment groups | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 1 Foundations | Groups mapped to CSM, OneStream Technical and Infrastructure teams. Support for group-level and individual assignment. |
| TM-09 | Parent / child and related ticket linking | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Link types: parent-child, related, duplicate, blocks/blocked-by. |
| TM-10 | Grouping under project or change window | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Ability to group a ticket tree under a project or scheduled window (e.g. one tree per Azure Files cutover weekend). |
| TM-11 | Ability to flag out-of-scope / over-budget work | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Configurable flag with client-side visibility. Ticket blocked from progressing until approved. |
| TM-12 | Immutable audit trail | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 1 Foundations | Every field change recorded with user, timestamp, old value, new value. Non-editable, non-deletable. |
| TM-13 | Public comments vs internal work notes | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Two distinct objects. Internal notes must never be exposed through the portal or ServiceNow public sync. |
| TM-14 | Attachments with virus scanning | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 1 Foundations | Size limits, allowed file types, AV scan on upload, quarantine on detection. |
| TM-15 | Full-text search and saved filters | Must Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Search across ticket fields, comments and attachments metadata. User-defined saved views. |

### Time Tracking & Budget

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| TB-01 | Time entry at ticket level | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Fields: duration, date performed, activity type, billable flag, description. Multiple entries per ticket per user. |
| TB-02 | Mandatory time entry before resolution | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | A ticket cannot move to Resolved/Closed with zero logged time unless an exemption reason is selected. |
| TB-03 | Activity type taxonomy | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Analysis, Development, Testing, Client Communication, Documentation, Meeting. This is what makes 'where did the hours go' answerable. |
| TB-04 | Billable classification | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Billable / Non-billable / Internal / Pre-sales, set per time entry with a default per activity type. |
| TB-05 | Rate cards by client, contract and role | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Effective-dated versions so historical entries retain the rate in force at the time performed. |
| TB-06 | Contract object with multiple commercial models | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Retainer hours, prepaid blocks, T&M, fixed fee. Includes rollover rules and overage rules. |
| TB-07 | Budget burn-down per client per period | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Consumed vs contracted hours and value, by period, with drill-through to source entries. |
| TB-08 | Forecast to period end | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Projected consumption at period end based on current run rate. |
| TB-09 | Threshold alerts | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Configurable percentage thresholds (e.g. 50/75/90/100%) alerting internal owner and optionally the client contact. |
| TB-10 | Per-ticket hours breakdown | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Hours by person, role, date and activity type for any single ticket. Exportable to Excel/CSV. |
| TB-11 | Adjustment and write-off workflow | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Original entry preserved; adjustment recorded as a separate linked record. |
| TB-12 | Non-ticket time capture | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 4 Later releases | Per-client buckets for governance, QBR prep, account management and escalation handling. Without this, utilisation reads artificially low and budget burn reads artificially favourable. |
| TB-13 | After-hours and weekend flagging | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Automatic flagging based on the client business calendar, with premium rate or comp-time handling. Needed across the cutover weekend programme. |
| TB-14 | Billing export | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Export in the format THG finance consumes, with a locked/approved period concept so exported data cannot be silently altered. |

### Team Allocation & Capacity

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| CAP-01 | Resource roster | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Role, FTE %, cost rate, bill rate, skills, certifications, timezone and working calendar per person. |
| CAP-02 | PTO and holiday calendar | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Per-country holiday calendars and individual PTO, feeding the capacity calculation. |
| CAP-03 | Available capacity calculation | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Contracted hours minus PTO minus holidays minus a configurable admin overhead factor. |
| CAP-04 | Planned allocation per person per client per period | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Forward-looking allocation grid, editable by team lead. |
| CAP-05 | Planned vs actual variance reporting | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Planned allocation compared against logged time. This is the report that actually changes behaviour. |
| CAP-06 | Overallocation detection | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Warning raised at assignment time when a person exceeds available capacity in a period. |
| CAP-07 | Skills matrix with single-point-of-failure flagging | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Identify where only one person can service a given client or technology. |
| CAP-08 | Forward demand from pipeline | Must Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Pipeline and project demand included in capacity view, not only current ticket load. |

### Client Portal

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| CP-01 | SSO via SAML / OIDC | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Authenticate against the client IdP, with local account fallback for clients without federation. |
| CP-02 | Strict data scoping | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 1 Foundations | A client user sees only their own organisation's tickets and data. Enforced server-side, verified by automated test. |
| CP-03 | Ticket submission with dynamic forms | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Form fields vary by request type; required fields enforced at submission. |
| CP-04 | Ticket status tracking and comment threads | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Client can view status, add comments and see public updates only. |
| CP-05 | Attachment upload from portal | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Same AV scanning and size limits as internal upload. |
| CP-06 | Budget / consumption visibility toggle | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Per-client switch controlling whether consumption data is exposed in the portal. |
| CP-07 | CSAT survey on ticket close and every quarter end | Must Have | [Client Portal](../02-modules/client-portal/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Triggered on closure, plus a periodic relationship survey. Results feed reporting. |
| CP-08 | Knowledge base with per-client article visibility | Must Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Articles scoped to global or specific clients. |

### Email Intake

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| EM-01 | Dedicated inbound address | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 1 Foundations | With alias support so existing client-facing addresses can be retained. |
| EM-02 | Thread matching on message headers | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Match on Message-ID / References / In-Reply-To. |
| EM-03 | Reply-to-update on existing tickets | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | A reply to a ticket notification appends a comment rather than creating a duplicate. |
| EM-04 | Attachment and inline image extraction | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Attachments stored on the ticket; inline images preserved in the comment body. |
| EM-05 | Signature and quoted-reply stripping | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Strip signatures, disclaimers and quoted history so comments stay readable. |
| EM-06 | Loop protection and auto-responder suppression | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Detect and suppress mail loops and out-of-office auto-replies. A loop with a client mail system is a severity-1 event. |
| EM-07 | Unknown-sender quarantine queue | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Unrecognised senders go to a review queue rather than auto-creating tickets. |
| EM-08 | Outbound email threading and branding | Must Have | [Email Intake & Outbound](../02-modules/email-intake/FUNCTIONAL-SPEC.md) | 1 Foundations | Outbound notifications correctly threaded and branded per client. |

### Dashboard & Reporting

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| DR-01 | Near-real-time dashboard refresh | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Defined refresh interval / push updates. Role-scoped and client-scoped. |
| DR-02 | Internal operational view | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Backlog by age, SLA attainment and at-risk, MTTR by type, reopen rate, volume trend, team utilisation, portfolio budget burn. |
| DR-03 | Client-facing view | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Their tickets, their SLA performance, their consumption, their CSAT. Nothing else. |
| DR-04 | Auto-generated weekly report pack (PPTX / PDF) | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Generated from live data on a schedule. Highest-ROI item in the build - it replaces the manual WSR cycle. We would present on a call from a dashboard that can be exported and sent via email for client review |
| DR-05 | Scheduled email delivery of report packs | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Per-client schedule and distribution list. |
| DR-06 | Export to Excel / CSV on all views | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Raw data export for ad-hoc analysis and finance reconciliation. |
| DR-07 | Historical trend retention | Must Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Point-in-time snapshots so trends survive record edits and reclassification. |

### ServiceNow Integration

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| SN-01 | Bidirectional sync with configurable field mapping | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Per-client-instance mapping configuration, maintainable without a code change. |
| SN-02 | State machine translation | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Translate between the internal state model and each client's. They will not match out of the box. |
| SN-03 | Loop prevention | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Correlation IDs and update watermarking to prevent infinite update ping-pong. |
| SN-04 | Conflict resolution policy | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Defined system of record per field. Last-write-wins is not acceptable as a blanket rule. |
| SN-05 | Comment and work note sync | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Respecting the public vs internal distinction in both directions. |
| SN-06 | Attachment sync | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Two-way attachment transfer with size limit handling. |
| SN-07 | Sync health monitoring and dead-letter queue | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Failed messages retained, alerting on failure, manual replay capability. |
| SN-08 | Multiple concurrent client instances | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Different schemas, different auth, different versions - running simultaneously. |
| SN-09 | One-way ingest mode | Must Have | [ServiceNow Sync](../02-modules/servicenow-integration/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Read-only ingest as a lower-risk starting configuration and as a fallback if write-back is suspended. |

### AI Functionality

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| AI-01 | Auto-categorisation and priority suggestion | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Category, priority, account and CI tagging suggested on intake, human-confirmed. |
| AI-02 | Duplicate detection with merge suggestion | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Flag likely duplicates at creation and propose a merge. |
| AI-03 | Long-thread summarisation | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Summarise ticket history for handover, shift change and escalation briefing. |
| AI-04 | Draft response generation | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Generate a suggested reply; a human always reviews and sends. |
| AI-05 | Weekly report narrative generation | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Convert dashboard figures into the written talk track for the WSR. |
| AI-06 | Time entry assistance | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Normalise work descriptions and prompt on unlogged time (e.g. 'you have 6 unlogged hours on Tuesday'). |
| AI-07 | Similar-ticket retrieval and KB suggestion | Must Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Surface comparable resolved tickets and relevant knowledge articles to the assignee. |
| AI-08 | Human-in-the-loop by default | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | No AI action takes effect without human confirmation unless explicitly opted in per client. |
| AI-09 | Confidence thresholds with human fallback | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Below threshold, the suggestion is withheld and the item routes to a human. |
| AI-10 | AI actions logged and attributable | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 1 Foundations | Every AI suggestion and action recorded in the audit trail, distinguishable from human actions. |
| AI-11 | Per-client AI disable switch | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 1 Foundations | Some clients will contractually prohibit AI processing of their data. Must be enforceable at the data layer. |
| AI-12 | No training on client data; DPA and residency compliance | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 1 Foundations | Contractual and technical guarantee before any client data reaches a model provider. |
| AI-13 | Feedback capture on AI suggestions | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Accept/reject captured to measure accuracy and drive tuning. |

### Data Migration

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| DM-01 | Historical import from ServiceNow CSM | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 2 Focused pilot | Open and closed tickets, comments, attachments and time entries. Without history the baseline is lost. |
| DM-02 | Contract and budget history import | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Existing contracts, consumed hours and current balances, reconciled to finance records. |
| DM-03 | Reconciliation report post-migration | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Record counts and hour totals reconciled source vs target, signed off before cutover. |
| DM-04 | Parallel run period | Must Have | [Data Migration & Cutover](../02-modules/data-migration/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Both systems operating concurrently for an agreed period before decommissioning the old one. |

### Integrations

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| INT-01 | Identity provider integration (internal) | Must Have | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) | 1 Foundations | Internal users authenticate via the THG IdP. |
| INT-02 | Finance / billing system export interface | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Structured interface to the billing system rather than manual file handling. |

### AI Functionality

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| AI-14 | Budget burn anomaly detection | Must Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Flag accounts tracking materially above or below expected run rate. |

### Integrations

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| INT-03 | Renewal and contract expiry alerting | Must Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 3 Operational replacement | Alerts ahead of contract end dates, surfaced to the account owner. |

### Ticket Management

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| TM-16 | Bulk actions | Nice to Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 4 Later releases | Bulk reassign, bulk state change, bulk tag - with audit entries per affected record. |
| TM-17 | Ticket templates | Nice to Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 4 Later releases | Pre-filled templates for recurring request types to reduce intake time. |
| TM-18 | Change calendar with conflict detection | Nice to Have | [Ticket Management](../02-modules/ticket-management/FUNCTIONAL-SPEC.md) | 4 Later releases | Visual change calendar with freeze windows and overlap warnings across clients. |
| TM-19 | CMDB / lightweight asset register | Nice to Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 4 Later releases | Per-client configuration item register, linkable to tickets. |

### Time Tracking & Budget

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| TB-15 | Multi-currency support | Nice to Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 4 Later releases | Rate cards and reporting in local currency with FX conversion for consolidated views. |
| TB-16 | Profitability view per account | Nice to Have | [Time, Contracts & Budget](../02-modules/time-and-budget/FUNCTIONAL-SPEC.md) | 4 Later releases | Revenue vs delivery cost using cost rates, at account and engagement level. |

### Team Allocation & Capacity

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| CAP-09 | On-call / shift rota | Nice to Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Rota management with coverage gap detection, linked to after-hours flagging. |
| CAP-10 | Scenario planning | Nice to Have | [Capacity & Allocation](../02-modules/capacity-and-allocation/FUNCTIONAL-SPEC.md) | 4 Later releases | Model the capacity impact of a prospective win before it is booked. |

### Email Intake

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| EM-09 | Priority detection from email content | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Suggest priority based on message content, subject to human confirmation. |

### Dashboard & Reporting

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| DR-08 | Automated QBR deck generation | Nice to Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 4 Later releases | Quarterly pack assembled from the period's data, following the standard QBR structure. |
| DR-09 | Customer health score | Nice to Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 4 Later releases | Composite of CSAT, SLA attainment, budget position and engagement signals. |
| DR-10 | Custom report builder | Nice to Have | [Dashboards & Report Packs](../02-modules/dashboard-and-reporting/FUNCTIONAL-SPEC.md) | 4 Later releases | Self-service report definition for power users without developer involvement. |

### AI Functionality

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| AI-15 | Escalation risk and sentiment detection | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Early warning on threads trending negative, before a formal escalation occurs. |
| AI-16 | Effort estimation from historical similar work | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Suggested effort range on new tickets based on comparable closed work. |
| AI-17 | Allocation suggestions | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Recommend assignee based on skills, current capacity and account familiarity. |
| AI-18 | Auto-resolution of allowlisted request types | Nice to Have | [Solution Knowledge Base](../02-modules/knowledge-base/FUNCTIONAL-SPEC.md) | 4 Later releases | Fully automated handling of simple, explicitly allowlisted requests. Requires strong guardrails and per-client opt-in. |
| AI-19 | Agentic triage and routing without human review | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Autonomous triage. Only after measured accuracy on the human-in-the-loop version. |
| AI-20 | Natural language query over reporting data | Nice to Have | [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md) | 4 Later releases | Ask questions of the dataset in plain language and get a chart or table back. |

### Integrations

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| INT-04 | Slack / Teams integration | Nice to Have | [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 4 Later releases | Ticket notifications, create-from-message, and time logging via command. |
| INT-05 | Calendar integration | Nice to Have | [Platform Integrations](../02-modules/integrations/FUNCTIONAL-SPEC.md) | 4 Later releases | Push change windows and scheduled work to Outlook calendars. |

### XMS additions

| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |
|---|---|---|---|---|---|
| XA-01 | Security audit log | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 1 Foundations | Every authentication, authorisation, administration, data-movement, abuse and AI decision is recorded as an append-only security event with actor, principal kind, request and trace ids; searchable and exportable. |
| XA-02 | User analytics | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 1 Foundations | Screen views, named actions, searches, Axel decisions and API requests are captured as usage events (no ticket, email or article content), per role and per account, with portal capture governed by an account setting. |
| XA-03 | Audit and usage reporting | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 2 Focused pilot | Admin screens for audit search over all three streams, a security dashboard and a usage dashboard (active users, feature adoption, core-loop funnel, knowledge gaps, Axel acceptance, portal deflection), with exports and an analyst SQL surface. |
| XA-04 | Security assurance and audit readiness | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 1 Foundations | Every change passes the security definition of done (isolation, visibility, realm, evidence, egress) with the required tests and a completed checklist; controls are mapped to ISO 27001, SOC 2 and OWASP ASVS with evidence produced automatically; monthly access reviews, quarterly runbook rehearsals, annual penetration test. |
| XA-05 | Tamper evidence and retention | Must Have | [Audit Log & User Analytics](../01-architecture/AUDIT-AND-ANALYTICS.md) | 3 Operational replacement | Append-only event tables, nightly Parquet archive to an Object Lock bucket, chained daily digests with weekly verification, retention per stream and per account DPA, pseudonymisation for erasure requests. |

## 4. Matrix by module spec


### Accounts & Administration (`02-modules/accounts-and-administration/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| TM-01 | Multi-tenant data isolation | Must Have | 1 Foundations |
| TM-06 | Per-client business calendars and timezones | Must Have | 3 Operational replacement |
| TM-08 | Assignment groups | Must Have | 1 Foundations |
| INT-01 | Identity provider integration (internal) | Must Have | 1 Foundations |

### Ticket Management (`02-modules/ticket-management/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| TM-02 | Ticket types with distinct workflows | Must Have | 2 Focused pilot |
| TM-03 | Configurable state machine | Must Have | 2 Focused pilot |
| TM-04 | Priority / impact matrix | Must Have | 2 Focused pilot |
| TM-05 | SLA engine | Must Have | 2 Focused pilot |
| TM-07 | SLA clock pause with reason logging | Must Have | 2 Focused pilot |
| TM-09 | Parent / child and related ticket linking | Must Have | 2 Focused pilot |
| TM-10 | Grouping under project or change window | Must Have | 3 Operational replacement |
| TM-11 | Ability to flag out-of-scope / over-budget work | Must Have | 3 Operational replacement |
| TM-12 | Immutable audit trail | Must Have | 1 Foundations |
| TM-13 | Public comments vs internal work notes | Must Have | 2 Focused pilot |
| TM-14 | Attachments with virus scanning | Must Have | 1 Foundations |
| TM-15 | Full-text search and saved filters | Must Have | 2 Focused pilot |
| TM-16 | Bulk actions | Nice to Have | 4 Later releases |
| TM-18 | Change calendar with conflict detection | Nice to Have | 4 Later releases |

### Solution Knowledge Base (`02-modules/knowledge-base/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| CP-08 | Knowledge base with per-client article visibility | Must Have | 2 Focused pilot |
| AI-07 | Similar-ticket retrieval and KB suggestion | Must Have | 2 Focused pilot |
| TM-17 | Ticket templates | Nice to Have | 4 Later releases |
| TM-19 | CMDB / lightweight asset register | Nice to Have | 4 Later releases |
| AI-18 | Auto-resolution of allowlisted request types | Nice to Have | 4 Later releases |

### Time, Contracts & Budget (`02-modules/time-and-budget/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| TB-01 | Time entry at ticket level | Must Have | 2 Focused pilot |
| TB-02 | Mandatory time entry before resolution | Must Have | 2 Focused pilot |
| TB-03 | Activity type taxonomy | Must Have | 2 Focused pilot |
| TB-04 | Billable classification | Must Have | 2 Focused pilot |
| TB-05 | Rate cards by client, contract and role | Must Have | 3 Operational replacement |
| TB-06 | Contract object with multiple commercial models | Must Have | 2 Focused pilot |
| TB-07 | Budget burn-down per client per period | Must Have | 2 Focused pilot |
| TB-08 | Forecast to period end | Must Have | 3 Operational replacement |
| TB-09 | Threshold alerts | Must Have | 3 Operational replacement |
| TB-10 | Per-ticket hours breakdown | Must Have | 2 Focused pilot |
| TB-11 | Adjustment and write-off workflow | Must Have | 3 Operational replacement |
| TB-12 | Non-ticket time capture | Must Have | 4 Later releases |
| TB-13 | After-hours and weekend flagging | Must Have | 3 Operational replacement |
| TB-14 | Billing export | Must Have | 3 Operational replacement |
| INT-02 | Finance / billing system export interface | Must Have | 3 Operational replacement |
| INT-03 | Renewal and contract expiry alerting | Must Have | 3 Operational replacement |
| TB-15 | Multi-currency support | Nice to Have | 4 Later releases |
| TB-16 | Profitability view per account | Nice to Have | 4 Later releases |

### Capacity & Allocation (`02-modules/capacity-and-allocation/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| CAP-01 | Resource roster | Must Have | 2 Focused pilot |
| CAP-02 | PTO and holiday calendar | Must Have | 4 Later releases |
| CAP-03 | Available capacity calculation | Must Have | 3 Operational replacement |
| CAP-04 | Planned allocation per person per client per period | Must Have | 3 Operational replacement |
| CAP-05 | Planned vs actual variance reporting | Must Have | 3 Operational replacement |
| CAP-06 | Overallocation detection | Must Have | 3 Operational replacement |
| CAP-07 | Skills matrix with single-point-of-failure flagging | Must Have | 3 Operational replacement |
| CAP-08 | Forward demand from pipeline | Must Have | 4 Later releases |
| CAP-09 | On-call / shift rota | Nice to Have | 4 Later releases |
| CAP-10 | Scenario planning | Nice to Have | 4 Later releases |

### Client Portal (`02-modules/client-portal/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| CP-01 | SSO via SAML / OIDC | Must Have | 3 Operational replacement |
| CP-02 | Strict data scoping | Must Have | 1 Foundations |
| CP-03 | Ticket submission with dynamic forms | Must Have | 2 Focused pilot |
| CP-04 | Ticket status tracking and comment threads | Must Have | 2 Focused pilot |
| CP-05 | Attachment upload from portal | Must Have | 2 Focused pilot |
| CP-06 | Budget / consumption visibility toggle | Must Have | 2 Focused pilot |
| CP-07 | CSAT survey on ticket close and every quarter end | Must Have | 3 Operational replacement |

### Email Intake & Outbound (`02-modules/email-intake/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| EM-01 | Dedicated inbound address | Must Have | 1 Foundations |
| EM-02 | Thread matching on message headers | Must Have | 2 Focused pilot |
| EM-03 | Reply-to-update on existing tickets | Must Have | 2 Focused pilot |
| EM-04 | Attachment and inline image extraction | Must Have | 2 Focused pilot |
| EM-05 | Signature and quoted-reply stripping | Must Have | 2 Focused pilot |
| EM-06 | Loop protection and auto-responder suppression | Must Have | 2 Focused pilot |
| EM-07 | Unknown-sender quarantine queue | Must Have | 2 Focused pilot |
| EM-08 | Outbound email threading and branding | Must Have | 1 Foundations |

### Dashboards & Report Packs (`02-modules/dashboard-and-reporting/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| DR-01 | Near-real-time dashboard refresh | Must Have | 2 Focused pilot |
| DR-02 | Internal operational view | Must Have | 2 Focused pilot |
| DR-03 | Client-facing view | Must Have | 2 Focused pilot |
| DR-04 | Auto-generated weekly report pack (PPTX / PDF) | Must Have | 2 Focused pilot |
| DR-05 | Scheduled email delivery of report packs | Must Have | 3 Operational replacement |
| DR-06 | Export to Excel / CSV on all views | Must Have | 2 Focused pilot |
| DR-07 | Historical trend retention | Must Have | 3 Operational replacement |
| DR-08 | Automated QBR deck generation | Nice to Have | 4 Later releases |
| DR-09 | Customer health score | Nice to Have | 4 Later releases |
| DR-10 | Custom report builder | Nice to Have | 4 Later releases |

### ServiceNow Sync (`02-modules/servicenow-integration/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| SN-01 | Bidirectional sync with configurable field mapping | Must Have | 3 Operational replacement |
| SN-02 | State machine translation | Must Have | 3 Operational replacement |
| SN-03 | Loop prevention | Must Have | 3 Operational replacement |
| SN-04 | Conflict resolution policy | Must Have | 3 Operational replacement |
| SN-05 | Comment and work note sync | Must Have | 3 Operational replacement |
| SN-06 | Attachment sync | Must Have | 3 Operational replacement |
| SN-07 | Sync health monitoring and dead-letter queue | Must Have | 3 Operational replacement |
| SN-08 | Multiple concurrent client instances | Must Have | 3 Operational replacement |
| SN-09 | One-way ingest mode | Must Have | 2 Focused pilot |

### Axel AI Functionality (`02-modules/ai-functionality/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| AI-01 | Auto-categorisation and priority suggestion | Must Have | 2 Focused pilot |
| AI-02 | Duplicate detection with merge suggestion | Must Have | 2 Focused pilot |
| AI-03 | Long-thread summarisation | Must Have | 2 Focused pilot |
| AI-04 | Draft response generation | Must Have | 3 Operational replacement |
| AI-05 | Weekly report narrative generation | Must Have | 3 Operational replacement |
| AI-06 | Time entry assistance | Must Have | 3 Operational replacement |
| AI-08 | Human-in-the-loop by default | Must Have | 2 Focused pilot |
| AI-09 | Confidence thresholds with human fallback | Must Have | 2 Focused pilot |
| AI-10 | AI actions logged and attributable | Must Have | 1 Foundations |
| AI-11 | Per-client AI disable switch | Must Have | 1 Foundations |
| AI-12 | No training on client data; DPA and residency compliance | Must Have | 1 Foundations |
| AI-13 | Feedback capture on AI suggestions | Must Have | 2 Focused pilot |
| AI-14 | Budget burn anomaly detection | Must Have | 3 Operational replacement |
| EM-09 | Priority detection from email content | Nice to Have | 4 Later releases |
| AI-15 | Escalation risk and sentiment detection | Nice to Have | 4 Later releases |
| AI-16 | Effort estimation from historical similar work | Nice to Have | 4 Later releases |
| AI-17 | Allocation suggestions | Nice to Have | 4 Later releases |
| AI-19 | Agentic triage and routing without human review | Nice to Have | 4 Later releases |
| AI-20 | Natural language query over reporting data | Nice to Have | 4 Later releases |

### Data Migration & Cutover (`02-modules/data-migration/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| DM-01 | Historical import from ServiceNow CSM | Must Have | 2 Focused pilot |
| DM-02 | Contract and budget history import | Must Have | 3 Operational replacement |
| DM-03 | Reconciliation report post-migration | Must Have | 3 Operational replacement |
| DM-04 | Parallel run period | Must Have | 3 Operational replacement |

### Platform Integrations (`02-modules/integrations/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| INT-04 | Slack / Teams integration | Nice to Have | 4 Later releases |
| INT-05 | Calendar integration | Nice to Have | 4 Later releases |

### Audit Log & User Analytics (`01-architecture/`)

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| XA-01 | Security audit log | Must Have | 1 Foundations |
| XA-02 | User analytics | Must Have | 1 Foundations |
| XA-03 | Audit and usage reporting | Must Have | 2 Focused pilot |
| XA-04 | Security assurance and audit readiness | Must Have | 1 Foundations |
| XA-05 | Tamper evidence and retention | Must Have | 3 Operational replacement |

## 5. Maintenance rule

This file is generated from the workbook by `00-overview/scripts/build_register.py` (ADR-00 in the Decision Log). Edit the workbook or the `phase`/`module` mapping in the script, regenerate, and commit both; never hand-edit the tables, or the CSV and this page will diverge.
