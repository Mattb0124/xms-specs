# Roadmap: XMS Ticketing

**Status:** Draft, pending the team and renewal decisions from the 2026-09-03 assessment
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Product Vision](../00-overview/PRODUCT-VISION.md), [Requirements Traceability](../00-overview/REQUIREMENTS-TRACEABILITY.md), [Architecture](../01-architecture/ARCHITECTURE.md), [Thirty-Day Build](./THIRTY-DAY-BUILD.md), [Implementation Plan](./IMPLEMENTATION-PLAN.md), [TODO](./TODO.md), [Test Strategy](./TEST-STRATEGY.md)

---

## 1. Constraints the plan is built around

| Constraint | Value | Source |
|---|---|---|
| ServiceNow contract ends | December 2026 | Assessment deck p.3 |
| Team today | 3 developers shared with XT plus Vini (ServiceNow SME), about 3.5 to 4 FTE if dedicated | Assessment deck p.10 |
| For a December operational target | 6 to 8 fully dedicated developers (7 working number) | Assessment deck p.10 |
| Pilot definition | A beta: no external clients, no Brookfield production traffic, cannot replace ServiceNow | Assessment deck p.10 |
| Foundations | 4 to 8 weeks (standalone) | Assessment deck p.8 |
| Focused pilot | 14 to 17 weeks, landing early January 2027 with the current team | Assessment deck p.10 |
| Operational replacement | 6 to 9 months, March to June 2027 | Assessment deck p.10 |

The three paths on p.12 of the deck (extend ServiceNow and build properly; hire to 7 and aim for December; cut scope dramatically) are a leadership decision. This roadmap is written for **Path 1** (extend ServiceNow by 6 months, build the definitive product with the current team fully dedicated) because it is the only path that delivers the isolation, Brookfield, migration and SSO work properly. If Path 2 is chosen the phases keep their content and compress; if Path 3 is chosen, Phase 2 becomes the release and Phase 3 is re-planned against the extension that is negotiated as insurance.

Compression (ADR-15, 2026-09-05): the first month builds a pilot-grade core on dev in twenty working days per the [Thirty-Day Build](./THIRTY-DAY-BUILD.md); the phase contents and exit criteria below are unchanged, the calendar for Phases 1 and 2 is replaced by that document and months 2 and 3.

## 2. Phases

Each phase is independently shippable, names what it replaces, and carries its exit criterion. Requirement IDs refer to the [traceability matrix](../00-overview/REQUIREMENTS-TRACEABILITY.md).

### Phase 1: Foundations (weeks 1 to 8, September to October 2026)

Replaces: nothing yet. Makes every later phase possible.

| Workstream | Outcome | Spec |
|---|---|---|
| Repo, pipeline, environments | Azure DevOps pipelines building three images (web, api, worker) to ECR and deploying to ECS in dev and prod; managed PostgreSQL, S3, SQS, CloudWatch provisioned | [Platform & Operations](../01-architecture/PLATFORM-AND-OPERATIONS.md) |
| Internal identity | Internal users sign in through a dedicated XMS Clerk application federated to the THG IdP (INT-01) | [Accounts & Administration](../02-modules/accounts-and-administration/TECHNICAL-SPEC.md) |
| Account isolation | Account context bound to every database session, row-level security forced on every account table, cross-account test suite green (TM-01, CP-02) | [Security & Tenancy](../01-architecture/SECURITY-AND-TENANCY.md) |
| Audit | Append-only audit events on every mutation with actor, old and new values (TM-12) | [Ticket Management](../02-modules/ticket-management/TECHNICAL-SPEC.md) |
| Attachments | Presigned S3 upload, AV scan, quarantine, retention (TM-14) | [Ticket Management](../02-modules/ticket-management/TECHNICAL-SPEC.md) |
| Email plumbing | Dedicated inbound address with aliases, outbound threading and per-account branding (EM-01, EM-08) | [Email Intake](../02-modules/email-intake/TECHNICAL-SPEC.md) |
| Assignment groups | Groups mapped to CSM, OneStream Technical, Infrastructure (TM-08) | [Accounts & Administration](../02-modules/accounts-and-administration/FUNCTIONAL-SPEC.md) |
| Axel adapter contract | Authenticated contract agreed with the Axel owners; per-account AI switch, AI action logging, no-training and residency guarantees documented (AI-08, AI-10, AI-11, AI-12) | [AI Integration](../01-architecture/AI-INTEGRATION.md) |
| Observability | Structured logs, traces, health checks, alarms, cost tags | [Platform & Operations](../01-architecture/PLATFORM-AND-OPERATIONS.md) |

Exit criterion: in dev, a ticket can be created by hand and by email against a seeded account, the audit trail shows both, and the isolation, auth and AV tests are green in the pipeline.

### Phase 2: Focused pilot (weeks 8 to 25, November 2026 to early January 2027)

Replaces: manual tracking for one infrastructure workflow on one internal-facing account. Internal beta only.

| Workstream | Outcome |
|---|---|
| Ticket core | Five ticket types with configurable state machines, priority matrix, essential SLA engine with pause reasons, linking, public comments and work notes, full-text search and saved views (TM-02 to TM-07, TM-09, TM-13, TM-15) |
| Time and contracts | Ticket-level time entry, mandatory time before resolution, activity taxonomy, billable class, contract object, burn-down, per-ticket hours breakdown (TB-01 to TB-04, TB-06, TB-07, TB-10) |
| Roster | Resource roster (CAP-01) |
| Portal (controlled) | Dynamic forms, status and public threads, portal attachments, consumption toggle, knowledge base with per-account visibility, behind invitation-only access (CP-03 to CP-06, CP-08) |
| Email intake | Thread matching, reply-to-update, attachment and inline extraction, signature stripping, loop protection, unknown-sender quarantine (EM-02 to EM-07) |
| Reporting | Near-real-time internal and client views, Excel/CSV export everywhere, basic exportable WSR pack (DR-01 to DR-04, DR-06) |
| ServiceNow | One-way ingest from one instance as the integration scenario (SN-09) |
| Axel assistive | Categorisation and priority suggestion, duplicate detection, summarisation, similar-ticket and KB suggestion, HITL, confidence thresholds, feedback capture (AI-01 to AI-03, AI-07, AI-09, AI-13) |
| Migration rehearsal | Representative historical import from ServiceNow CSM (DM-01) |

Exit criterion: the DMS team runs at least one account's live infrastructure workflow in the product for two consecutive weeks, produces that account's WSR from the product, and Axel suggestion acceptance is being measured.

### Phase 3: Operational replacement (January to June 2027)

Replaces: ServiceNow.

| Workstream | Outcome |
|---|---|
| Isolation sign-off | Security-approved isolation model in production, including any dedicated-database accounts (TM-01 ruling) |
| External identity | Client SSO via SAML and OIDC with local fallback (CP-01) |
| Calendars and time zones | Per-account business calendars driving SLA clocks and after-hours flagging (TM-06, TB-13) |
| Commercial completeness | Rate cards, forecast, threshold alerts, adjustments and write-offs, billing export with locked periods, finance interface, renewal alerts (TB-05, TB-08, TB-09, TB-11, TB-14, INT-02, INT-03) |
| Capacity | Capacity calculation, allocation grid, planned vs actual, overallocation, skills matrix (CAP-03 to CAP-06) |
| Brookfield | Bidirectional sync with mappings, state translation, loop prevention, conflict policy, comment and attachment sync, health and DLQ, multiple instances (SN-01 to SN-08) |
| Reporting | Scheduled report delivery, historical trend retention, CSAT on close and quarterly (DR-05, DR-07, CP-07) |
| Axel | Draft responses, WSR narrative, time-entry assistance, burn anomaly detection (AI-04 to AI-06, AI-14) |
| Migration | Full historical import, contract and budget history, reconciliation report, parallel run, cutover with rollback (DM-01 to DM-04) |
| Operations | Availability and recovery objectives, backups tested, runbooks, support policy |

Exit criterion: reconciliation report signed off, parallel run completed, ServiceNow write-back suspended then decommissioned.

### Phase 4: Later releases (from mid 2027)

Grouping under projects and change windows, out-of-scope flag workflow, PTO and holidays, non-ticket time, pipeline demand, forecasting, additional dashboards, and every Nice to Have row (bulk actions, templates, change calendar, CMDB, multi-currency, profitability, rota, scenario planning, QBR deck, health score, report builder, sentiment, effort estimation, allocation suggestions, allowlisted auto-resolution, autonomous triage, natural-language reporting, Slack and Teams, calendar push). Ordering is decided per quarter with DMS.

## 3. Deploy order inside every release

Database migration, then worker, then API, then web. Migrations are additive-first (expand, migrate, contract) so an older API can run against a newer schema during a rolling deploy. The Axel adapter contract is versioned; the studio side deploys before any XMS release that depends on a new contract version.

## 4. Team shape (current 4, fully dedicated)

| Person | Primary | Secondary |
|---|---|---|
| Developer A | Ticket core, SLA engine, state machines | Portal |
| Developer B | Time, contracts, capacity, reporting and report packs | Exports |
| Developer C | Email, connectors, ServiceNow sync, migration | Worker platform |
| Vini (ServiceNow SME) | Brookfield mappings, migration extraction, reconciliation | Field-level acceptance |
| Matt | Architecture, Axel adapter, security and isolation, reviews | Pipeline |

Weekly sprints with fixed weekly objectives, per the assessment's mitigation for team capacity.

## 5. Milestones and decision gates

| Date | Gate |
|---|---|
| 2026-09-07 | Leadership decision on path, renewal terms, dedication, hiring |
| 2026-09-11 | Architecture sign-off on this spec set; Security ruling requested on isolation (ADR-02) |
| 2026-09-18 | DMS clarification session: pilot subset confirmed, workbook reconciliation (110 vs 111 rows, 90 vs 75 Must Have) |
| 2026-09-25 | Brookfield documentation received (flows, mappings, auth, volumes, ownership) |
| 2026-10-30 | Foundations exit |
| 2027-01-08 | Pilot exit |
| 2027-03 to 2027-06 | Parallel run, cutover, decommission |
