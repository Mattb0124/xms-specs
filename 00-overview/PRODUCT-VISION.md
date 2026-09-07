# Product Vision: XMS Ticketing (ServiceNow replacement)

**Status:** Draft, pending architecture sign-off
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Requirements Traceability](./REQUIREMENTS-TRACEABILITY.md), [Architecture](../01-architecture/ARCHITECTURE.md), [Decision Log](./DECISION-LOG.md), [Roadmap](../03-delivery/ROADMAP.md)
**Source inputs:** DMS requirements workbook (110 rows), "DMS Ticketing: replacing ServiceNow" assessment deck (Juan Cetrangolo with Erick Alonso, Xavi, Ale, Vini; 2026-09-03), the XMS proof of concept in `web-ui/components/aix-v3/xms/`

---

## 1. Why this product exists

The Hackett Group's Digital Managed Services practice (DMS) runs client support for OneStream, Coupa, FCCS, EPM and infrastructure work on ServiceNow. ServiceNow costs more than $100K a year, the contract ends in December 2026, and it treats every ticket the same. The thing that makes managed services different is the layer ServiceNow does not have: which client contract a ticket bills against, how many hours remain, which SLA clock applies in which time zone, who on the roster has capacity, and what the client sees in their weekly report.

The 2026-09-03 assessment concluded that the build is feasible and recommended Option B: a standalone product with its own web app, API, worker, PostgreSQL, S3 and SQS, sharing the same technology family and AWS patterns as AIX, with Axel (the AIX AI harness) as the only assumed dependency. This spec set is the architecture and requirement-level design for that product.

## 2. The thesis: data is the heart

A ticketing system is a workflow tool. This product is a knowledge system that happens to run tickets. Every ticket that is resolved leaves behind a documented solution: what was wrong, on which configuration item, what was done, how long it took, and whether the client could have done it themselves. Over time that corpus is what makes the platform self-service: a client opens the portal, describes the problem, and is shown the three solutions that fixed it before, one of which they can apply or request with a click.

Four consequences of the thesis run through every module spec:

1. **Resolution is a record, not a status.** A ticket cannot close without a resolution code, resolution notes, and either a link to an existing solution article or a candidate for a new one. The knowledge base grows as a by-product of doing the work, not as a separate documentation chore.
2. **Everything is attributable and replayable.** Append-only audit events, immutable time entries with linked adjustments, point-in-time snapshots for reporting. The hour-justification conversation with a client is won with evidence, not memory.
3. **Axel reads the corpus and the human decides.** Categorisation, duplicate detection, similar-ticket retrieval, draft replies, summaries and the weekly report narrative are all AI suggestions grounded in this product's own data, confirmed by a person, logged as AI actions, and switchable off per client.
4. **The client sees their slice, completely.** Their tickets, their SLAs, their consumption, their CSAT, their knowledge articles. Nothing else, enforced at the data layer and proven by automated tests.

## 3. What the product replaces and what it adds

| Today (ServiceNow CSM + spreadsheets) | XMS Ticketing |
|---|---|
| Tickets with generic incident/request workflows | Five ticket types with their own configurable state machines and billing treatment |
| SLA timers on wall-clock time | SLA engine on per-client business calendars across UK, Brazil, Australia, Canada and US, with pause reasons stored as evidence |
| Time logged in a separate tool, reconciled by hand | Time entries on the ticket with activity taxonomy, billable class, effective-dated rate cards, contract burn-down and a locked billing period |
| Capacity in a spreadsheet | Roster, PTO, allocation grid, planned vs actual, single-point-of-failure flags |
| Weekly status report built by hand every week | Auto-generated report pack (PPTX and PDF) from live snapshots with an Axel-written talk track, scheduled and emailed per client |
| Client visibility by email | Client portal with SSO, dynamic forms, public threads, consumption toggle, CSAT, knowledge base |
| Brookfield synced through ServiceNow | Connector framework with field mapping, state translation, loop prevention, DLQ and replay; ServiceNow becomes one connector among many |
| No AI | Axel-assisted triage, summaries, drafts, similar cases, narrative, time-entry nudges, with human-in-the-loop and per-client switch |

## 4. Who uses it

| Persona | Where | What they need most |
|---|---|---|
| Support consultant (CSM, OneStream Technical, Infrastructure) | XMS Web | Queue with honest SLA clocks, fast time logging, similar solutions at hand, one-click draft replies |
| Team lead / dispatcher | XMS Web | Dispatch, capacity, overallocation warnings, planned vs actual, skills gaps |
| Account owner / practice lead | XMS Web | Budget burn, forecast, threshold alerts, renewal alerts, portfolio dashboard, WSR on a call |
| Finance | Exports | Locked billing periods, rate-card-correct exports, reconciliation |
| Client requester | Client portal | Submit, track, comment, attach, see consumption if allowed, find a solution without submitting |
| Client executive | Report pack, portal dashboard | SLA attainment, consumption, CSAT, trends |
| Axel (AI) | Axel adapter | Authorised, account-scoped read of tickets and knowledge; suggestions written back as attributable AI actions |
| XMS administrator | XMS Web admin | Accounts, users, roles, calendars, state machines, field mappings, AI switches, all without a code change |

## 5. Product principles

1. **Product boundary equals technical boundary.** One web app, one API, one worker, one database, one S3 bucket, one set of queues, one pipeline. Failures, costs and changes stay inside the boundary. No AIX code is copied; patterns are.
2. **Configuration over code for anything a client makes different.** State machines, priority matrices, SLA targets, calendars, forms, field mappings, AI switches and thresholds are data owned by administrators.
3. **Server is the only author of truth.** SLA due times, breach latches, burn-down, priority derivation and permissions are computed server-side. The UI renders and counts down; it never decides.
4. **Isolation is a data-layer property.** Client scoping is enforced in the database session, not by remembering a filter, and the test suite proves it on every build.
5. **Human in the loop by default.** No AI action takes effect without confirmation unless a client has explicitly opted in per request type, and every AI action is visible as AI in the audit trail.
6. **Ship in phases that each replace something.** Foundations, then a focused pilot, then operational replacement, then later releases. Each phase names what it makes unnecessary.

## 6. Scope tiers (from the assessment, refined here)

| Tier | Contents | Exit criterion |
|---|---|---|
| Foundations (4 to 8 weeks) | Repo, pipeline, environments, auth for internal users, account isolation, audit, S3 with AV scan, inbound and outbound email plumbing, observability, Axel adapter contract | A ticket can be created by email and by hand in dev, with the audit and isolation tests green |
| Focused pilot (14 to 17 weeks) | One infrastructure workflow, portal and email creation, assignment, statuses, priority, search and views, essential SLAs, public comments and internal notes, attachments, time entry, basic contract and consumption, accounts roster, one budget dashboard, controlled external access, representative import plus one integration scenario, Axel assistive only, per-account AI switch and feedback, basic exportable WSR | Internal beta in use by the DMS team on live work for at least one account |
| Operational replacement (6 to 9 months) | Security-approved isolation, SSO with fallback, production-grade Brookfield integration, migration and reconciliation, robust email, calendars and time zones, confirmed reporting, capacity and billing, availability and recovery objectives | ServiceNow decommissioned with rollback no longer required |
| Later releases | Forecasting, PTO and holidays, non-ticket time, pipeline demand, additional dashboards, AI automation and generated replies, new contract models, all Nice to Have rows | Incremental |

The [Requirements Traceability Matrix](./REQUIREMENTS-TRACEABILITY.md) assigns every workbook row to one of these tiers.

## 7. What this is not

- Not a module inside AIX (Option A was assessed and not recommended: shared releases, security surface and capacity; external clients need a dedicated product boundary).
- Not a ServiceNow clone. It reproduces the outcomes XMS needs, not the object model. Where ServiceNow vocabulary helps adoption (CS-numbered tickets, work notes, resolution codes) it is kept on purpose.
- Not a general-purpose PSA or ERP. Finance owns invoicing; this product owns the locked, exportable truth that invoicing consumes.
- Not an autonomous AI agent. Autonomous triage and auto-resolution are Nice to Have rows gated on measured accuracy of the human-in-the-loop versions.

## 8. Decisions this vision assumes

Recorded in the [Decision Log](./DECISION-LOG.md). The ones a reader of this page should know: standalone product (ADR-01), PostgreSQL system of record with database-enforced account isolation (ADR-02), Clerk for internal users and a dedicated client-portal identity path (ADR-03), Axel as the only AI engine through an adapter (ADR-04), knowledge base as a first-class module (ADR-05), ServiceNow as a connector on the shared connector framework (ADR-06).
