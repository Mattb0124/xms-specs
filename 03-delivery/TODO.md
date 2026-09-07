# TODO: XMS Ticketing (spec set and build)

**Spec:** this repository (`00-overview`, `01-architecture`, `02-modules`, `03-delivery`)
**Ticket:** to be created in ClickUp space "X Platforms" once the path decision lands (2026-09-07)
**Build order:** [Thirty-Day Build](./THIRTY-DAY-BUILD.md) for the first month (day-by-day, ADR-15), then the [Implementation Plan](./IMPLEMENTATION-PLAN.md) (item ids P<phase>.<sprint>.<n>, dependencies, tests)
**Status legend:** `[ ]` not started, `[~]` in progress, `[x]` done and verified

---

## 0. Spec set (this repo)

- [x] Requirements register generated from the workbook with stable IDs, modules and phases (`00-overview/scripts/build_register.py`)
- [x] Product vision, glossary, decision log, roadmap, test strategy
- [x] Architecture set: architecture, domain model, data model, security and tenancy, AI integration, integration patterns, platform and operations, design system, AIX pattern reuse
- [x] Twelve module spec pairs under `02-modules/` (functional and technical) written and cross-link-checked (`check_links.py`, 41 files, 2026-09-04)
- [x] Wireframes v3 (semantic colour, chips, selection bar, rows per page) dissected and adopted (ADR-18): Wireframes §8, Design System §8.1, skills updated, renders in `01-architecture/wireframes/v3/` (2026-09-05)
- [x] Wireframes v2 dissected and adopted (ADR-17): `01-architecture/WIREFRAMES.md`, renders in `01-architecture/wireframes/`, Design System §8, UX §11, frontend skills updated (2026-09-05)
- [x] Security definition of done in place: always-on rule, `xms-security-first` skill, Security Assurance control and evidence map, ADR-16, XA-05 (2026-09-05)
- [ ] Architecture sign-off (Matt) and Security ruling on ADR-02 requested
- [ ] Workbook reconciliation with DMS (110 vs 111 rows, 90 vs 75 Must Have) and regeneration of the register
- [x] Specs published to ClickUp Docs on the XMS list in X Platforms (list `901525777420`, 15 docs, 41 pages, map in [CLICKUP.md](./CLICKUP.md)), 2026-09-04

## 1. Foundations (`frontend/`, `backend/`, `infra/`, `feature/foundations-*`, Phase 1)

- [x] Frontend and backend scaffolds pushed 2026-09-07: `frontend/` to https://github.com/Mattb0124/xms-frontend (P1.1.2, P1.1.3, gate green: lint, typecheck, config check, 5 unit tests) and `backend/` to https://github.com/Mattb0124/xms-backend (P1.1.1, gate green: lint, typecheck, 5 unit and 2 e2e tests); each folder is its own git repository
- [~] Application folders (ADR-12, ADR-14): `frontend/` (Next.js, `styles/tokens`, `lib/axel-client`, `e2e`), `backend/` (NestJS with `src/domain`, `src/db`, `src/contracts`, `src/worker`, `test/kit`), `infra/` (Terraform, pipeline templates), `xms_mcp` module in `aix-mcp`; folders and READMEs created 2026-09-04, generic AIX skills seeded under `.claude/` and `.cursor/`
- [ ] Terraform: VPC use, ECS services, ECR repos, RDS PostgreSQL 16 with pgvector, S3 with GuardDuty Malware Protection, SQS queues and DLQs, SES identities and receipt rules, Secrets Manager, ALB and WAF, CloudWatch alarms
- [ ] Azure DevOps pipeline with the gate stage (lint, `tsc --noEmit`, unit, integration, isolation suite) before build; dev and production branch stages
- [ ] Dedicated XMS Clerk application: internal organisation with the THG IdP enterprise connection; `agents` JWT template; licensing and per-organisation SAML spike (Brayan)
- [x] API guard producing one `Principal` (Clerk JWT with authorizedParties and the agents audience, harness session token, API client, development token refused in production); global permission guard with realm separation; global `ValidationPipe`; route and permission snapshot (`backend/test/golden/routes.json`) and boot-time check; auth rejection suite, 2026-09-07 (backend `2088691`)
- [x] Data layer: SQL-first runner, `op`/`acct`/`sys`/`rpt` schemas, `sys.apply_account_isolation`, RLS session binding only in `withSession`, generated isolation suite (both roles, cross-account read/update/delete/insert) green in Testcontainers, 2026-09-07 (backend `0b64b37`)
- [x] Audit events append-only with trigger and the deferred audit guard on protected tables; `op.audit_events`; AuditService with diff, 2026-09-07
- [~] Security events written by the guard, bootstrap and every admin change (XA-01 done); usage events and telemetry ingestion done (XA-02); the event archive with digests pending (XA-04)
- [x] Admin: accounts with settings and status transitions, users with invite and the last-administrator rule, roles, reconciled grants and groups, configuration defaults seeded from JSON with versions and activation, `/v1/admin/me`, `POST /v1/bootstrap`; 82 integration tests, 2026-09-07 (backend `c0354fb`)
- [x] Frontend shell and house components (P1.4.1, P1.4.2): 32 components, finder bar, sidebar failing closed, palette, route registry, RTK plumbing, dev sign-in, telemetry client; 66 tests, 2026-09-07 (frontend `3c75b05`, `fbf630e`)
- [x] Outbox table and dispatcher (SKIP LOCKED, five attempts, dead letters), inbox and job lease tables, 2026-09-07
- [x] Ticket core (P1.5.1 to P1.5.6, P2.10.1 on the wall clock): tickets, SLA clocks with pause evidence, transitions with the close discipline, comments and work notes as separate tables, links, watchers, notifications with collapse keys, usage events and `POST /v1/telemetry`; 216 integration tests, 2026-09-07 (backend ticket core commit)
- [x] Frontend admin screens (P1.4.3, P1.4.4): accounts, settings, access, users, roles, groups, config viewer; 76 tests, 2026-09-07 (frontend `d2cee58`)
- [x] Frontend ticket screens (P1.5.5, P2.12.4 basics): Queue with system views and chips, New ticket, Ticket record with transitions and close discipline, My work, Dispatch, notifications bell; 99 tests, 2026-09-07 (frontend `d10b275`)
- [x] Portal API (P2.16 cut): `/v1/portal` me, submit, own requests, public timeline, comment, cancel and confirm closure; portal database role read-only, writes on the app role bound to one account, 2026-09-07 (backend `0986696`)
- [x] SLA breach sweeper and at-risk job with database leases (P2.10.2); saved views and the condition grammar (P2.11.1), 2026-09-07 (backend `0986696`)
- [x] Time entries, adjustments, buckets, contract periods, billing period locks, contract position (P2.12.2, P2.12.3, P2.13.1 cut, P2.13.2); 288 integration tests, 2026-09-07
- [x] Knowledge base (P2.14.1 to P2.14.4): articles with frozen versions, visibility sets, GLOBAL generalization with the identifier checklist, retrieval v1, Solutions rail, resolution record, portal knowledge search and client notes; 370 integration tests, 2026-09-07
- [x] Frontend portal screens (P2.16.3): own chrome, search-first home, requests, new request, request detail with the public thread, accessibility checks; 112 tests, 2026-09-07 (frontend `08315de`)
- [ ] Attachments: presigned POST, scan-state gating, quarantine
- [ ] Email plumbing: inbound alias to S3 to SQS to worker, outbound SES with threading headers and per-account branding
- [ ] Axel adapter skeleton: session exchange, SSE relay, per-account switch, audit; harness changes 1, 5, 6 requested from the Axel owners
- [ ] Observability: pino, OpenTelemetry through ADOT, readiness endpoints, alarms
- [ ] Tests: isolation suite, auth rejection suite, outbox idempotency, email threading corpus

## 2. Focused pilot (`feature/pilot-*`, Phase 2)

- [ ] Ticket core: five types, configurable state machines, priority matrix, SLA engine on calendars with pause reasons and sweeper, links, comments and work notes, search and saved views
- [ ] Time and contracts: entries, mandatory time before resolution, activity taxonomy, billable classes, contract models, burn-down, per-ticket breakdown
- [ ] Roster
- [ ] Knowledge base: articles, versions, visibility, resolution record, similar solutions rail, portal search-first
- [ ] Portal (controlled access): forms, threads, attachments, consumption toggle
- [ ] Email intake: thread matching, reply-to-update, extraction, stripping, loop protection, quarantine
- [ ] Reporting: internal and client dashboards, exports, basic WSR pack
- [ ] Audit search, Security dashboard and Usage dashboard under Admin (XA-03)
- [ ] ServiceNow one-way ingest for one instance against the stand-in, then Brookfield sandbox
- [ ] Axel assistive: categorise, prioritise, duplicates, summarise, similar solutions, HITL, thresholds, feedback
- [ ] Migration rehearsal import
- [ ] Tests: state machine and SLA suites at 100 percent branch coverage, e2e golden paths, ZAP baseline

## 3. Operational replacement (`feature/ops-*`, Phase 3)

- [ ] Security-approved isolation in production; dedicated tier if ruled
- [ ] Portal SSO per account with fallback
- [ ] Calendars and time zones driving SLA and after-hours flags
- [ ] Rate cards, forecast, thresholds, adjustments, billing periods and export, finance connector, renewal alerts
- [ ] Capacity: calculation, allocation grid, planned vs actual, overallocation, skills matrix
- [ ] Brookfield bidirectional sync with maps, loop prevention, conflict policy, comments and attachments, health and DLQ
- [ ] Scheduled report delivery, snapshots, CSAT
- [ ] Axel: draft replies, WSR narrative, time assistance, burn anomaly; harness changes 2 to 4
- [ ] Full migration, reconciliation sign-off, parallel run, cutover, decommission
- [ ] Availability and recovery objectives met; runbooks rehearsed

## 4. Later releases (Phase 4)

- [ ] Groups and change windows, out-of-scope flag workflow, PTO and holidays, non-ticket time, pipeline demand, forecasting, additional dashboards, all Nice to Have rows per the register

## Decisions locked

- Standalone product, Option B (ADR-01); PostgreSQL with forced RLS and a dedicated tier (ADR-02); one XMS Clerk application for both populations pending the spike (ADR-03); Axel only, through the adapter, XMS as an MCP server (ADR-04); knowledge base first-class, resolution is a record (ADR-05); one connector framework (ADR-06); XMS POC ported, studio module retired (ADR-07); TypeScript worker sharing domain code (ADR-08); gates in the pipeline and Terraform in the repo (ADR-09); operator-wide CS keys (ADR-10); report packs rendered in XMS with an Axel narrative (ADR-11); separate repositories `frontend`, `backend`, `infra` plus `xms_mcp` in `aix-mcp`, no monorepo (ADR-12); the apps live in this repository as `frontend/`, `backend/`, `infra/` (ADR-14); pilot-grade core built in one month with scope cuts, not date moves (ADR-15).

## Blocked / open

- Path decision (Ignacio, 2026-09-07): building for Path 1 by default.
- Isolation ruling (Juan / Security, 2026-09-18): shared tables with forced RLS plus dedicated tier by default.
- Pilot subset and workbook reconciliation (Sofi / DMS, 2026-09-18): Appendix C and this register's phase column by default.
- Brookfield facts (Vini, 2026-09-25): ingest-only first, Table API with OAuth client credentials by default.
- Harness changes and guarantees (Axel owners, 2026-10-15): items 1, 5, 6 in Phase 1; 2 to 4 by Phase 3.
- AV product and environments (Infrastructure, 2026-09-25): GuardDuty by default.
- Clerk licensing and SAML topology (Brayan, 2026-10-02): works within plan by default; XMS-owned realm as fallback.
