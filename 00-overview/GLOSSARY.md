# Glossary: XMS Ticketing

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04

---

| Term | Meaning in this spec set |
|---|---|
| **XMS** | Xelerated Managed Services: the product this spec set describes (web, API, worker, MCP module). Named after the proof of concept. |
| **DMS** | The Hackett Group's Digital Managed Services practice: the team that runs client support and will operate XMS. Also the name on the source workbook and assessment deck. Never the product. |
| **Account** | A client organisation served by DMS (Brookfield, for example). The unit of data isolation, contracts, calendars, portal users and AI switches. Called "client" in the workbook. |
| **Operator** | The Hackett Group as the party running the product. Operator data (roster, skills, allocation, global configuration) is not owned by any one account. |
| **Tenant** | Not used for accounts. If it appears, it means the whole operator deployment. The AIX word "tenant" maps to operator here. |
| **Engagement** | A commercial relationship between the operator and an account, carrying one or more contracts. |
| **Contract** | The commercial agreement a ticket bills against: retainer hours, prepaid block, time and materials, or fixed fee, with rollover and overage rules and an effective-dated rate card. |
| **Ticket** | The unit of work. Types: Incident, Service Request, Change, Problem, Project Task. Display key `CS0001234` (ServiceNow-style, kept for adoption). |
| **State machine** | The configured set of states and allowed transitions for one ticket type, with per-transition rules (required fields, SLA effects, approvals). |
| **SLA clock** | A response or resolution timer for one ticket, driven by policy (ticket type, priority, contract), running on the account's business calendar, pausable with a reason. |
| **Breach latch** | Once a clock is breached the breach is recorded permanently; later pauses or edits never un-breach it. |
| **Work note** | Internal comment, never visible to the client or to public sync. Distinct object from a public comment. |
| **Public comment** | Client-visible comment on a ticket; the first public reply from the operator stamps response-met. |
| **Solution article** | Knowledge base entry describing a documented fix, with visibility (global or specific accounts), versions, linked configuration items and the tickets it resolved. |
| **Configuration item (CI)** | A lightweight asset register entry per account (an environment, an application, an integration) that tickets and solution articles link to. |
| **Time entry** | Immutable record of minutes worked: date performed, activity type, billable class, description, rate snapshot. Adjustments are separate linked records. |
| **Activity type** | Analysis, Development, Testing, Client Communication, Documentation, Meeting. Each has a default billable class. |
| **Billable class** | Billable, Non-billable, Internal, Pre-sales. |
| **Rate card** | Effective-dated rates by account, contract and role. A time entry snapshots the rate in force on the date performed. |
| **Billing period** | A per-account period that can be locked after approval; exported data cannot change afterwards. |
| **Roster** | Operator people with role, FTE percentage, cost and bill rates, skills, certifications, time zone and working calendar. |
| **Capacity** | Contracted hours minus PTO minus holidays minus an admin overhead factor, per person per period. |
| **Allocation** | Planned hours per person per account per period, compared against actual logged time. |
| **Business calendar** | Working hours and holiday set for an account or a person, in a named time zone. SLA clocks and after-hours flagging use it. |
| **Portal** | The client-facing web surface: submit, track, comment, attach, consumption view, CSAT, knowledge base. |
| **Portal user** | A person at an account authenticating through the account's identity provider (SAML or OIDC) or a local fallback account. |
| **Axel** | The AIX AI assistant, delivered by the AI harness (`os-aixelerator-studio`, referred to as `os-ai-api` in conversation). The only AI engine this product uses. |
| **Axel adapter** | The XMS-owned API contract through which Axel reads account-scoped context and writes suggestions back. The single AI egress and ingress point. |
| **AI action** | Any suggestion or change produced by Axel, recorded in the audit trail as AI, with model, confidence, prompt version and the human decision. |
| **Connector** | A XMS worker component that syncs with an external system (ServiceNow instances, finance export, email) using the shared outbox/inbox, idempotency, loop prevention, retries, DLQ, replay and kill switch. |
| **Outbox / inbox** | Transactional outbox rows written with the domain change and delivered by the worker; inbox rows deduplicate inbound messages by correlation id. |
| **Correlation id** | The stable identity of a change as it crosses a connector, used for loop prevention and watermarking. |
| **Dead-letter queue (DLQ)** | Where failed messages are retained with their error, for alerting and manual replay. |
| **Report pack / WSR** | The weekly status report generated as PPTX and PDF from live snapshots, with an Axel narrative, scheduled per account. |
| **Snapshot** | Point-in-time copy of reporting measures so trends survive later edits and reclassification. |
| **Saved view** | A user-defined filter over the ticket list, optionally shared with a team or an account. |
| **Quarantine queue** | Where inbound email from unknown senders, and attachments flagged by the virus scan, wait for a human decision. |
| **Security event** | An append-only record of an authentication, authorisation, administration, data-movement, abuse or AI decision, with the shared event envelope. |
| **Usage event** | An append-only record of a screen view, named action, search, Axel decision or API request; carries identifiers and structured facts, never content. |
| **Integrity digest** | The chained daily SHA-256 over each event stream stored in an Object Lock bucket for tamper evidence. |
| **ADR-nn** | An architecture decision record in the [Decision Log](./DECISION-LOG.md). |
| **TM-nn, TB-nn, CAP-nn, CP-nn, EM-nn, DR-nn, SN-nn, AI-nn, DM-nn, INT-nn** | Requirement IDs from the [Requirements Traceability Matrix](./REQUIREMENTS-TRACEABILITY.md), prefixed by workbook category (Ticket Management, Time & Budget, Capacity, Client Portal, Email, Dashboard & Reporting, ServiceNow, AI, Data Migration, Integrations). |
