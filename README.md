# XMS Ticketing: specification set

The Hackett Group's Digital Managed Services practice is replacing ServiceNow with a standalone product (assessment of 2026-09-03, Option B). This repository holds the complete specification: requirements traceability, architecture, one functional and one technical spec per module, and the delivery plan. The product thesis is that data is the heart: every resolved ticket leaves a documented solution, and the knowledge base is what makes the platform self-service for clients.

**Status:** Draft, pending architecture sign-off (Matt) and the leadership decision on path (2026-09-07).
**Owner:** Matt Brown. **Last updated:** 2026-09-09.

## How to read this set

1. Start with [Product Vision](00-overview/PRODUCT-VISION.md) (why, thesis, personas, scope tiers) and the [Glossary](00-overview/GLOSSARY.md).
2. Read [Architecture](01-architecture/ARCHITECTURE.md), then [Domain Model](01-architecture/DOMAIN-MODEL.md) and [Data Model](01-architecture/DATA-MODEL.md).
3. Read the cross-cutting documents you care about: [Security & Tenancy](01-architecture/SECURITY-AND-TENANCY.md), [Security Assurance](01-architecture/SECURITY-ASSURANCE.md), [AI Integration](01-architecture/AI-INTEGRATION.md), [Integration Patterns](01-architecture/INTEGRATION-PATTERNS.md), [Platform & Operations](01-architecture/PLATFORM-AND-OPERATIONS.md), [Design System](01-architecture/DESIGN-SYSTEM.md), [User Experience](01-architecture/USER-EXPERIENCE.md), [Wireframes v2](01-architecture/WIREFRAMES.md), [Audit Log and User Analytics](01-architecture/AUDIT-AND-ANALYTICS.md), [AIX Pattern Reuse](01-architecture/AIX-PATTERN-REUSE.md).
4. Go to the module you are building. Each module has a `FUNCTIONAL-SPEC.md` (what and why, readable by a non-engineer, no code) and a `TECHNICAL-SPEC.md` (how, grounded in the architecture and in verified AIX code paths).
5. Check the [Requirements Traceability Matrix](00-overview/REQUIREMENTS-TRACEABILITY.md) to see where any row landed, and the [Decision Log](00-overview/DECISION-LOG.md) before reopening a settled question.
6. **Before starting work, read [Clarifications needed](00-overview/CLARIFICATIONS-NEEDED.md).** It carries the questions that block a spec or contradict something already built, including the TM-08 routing conflict.
7. Delivery: [Roadmap](03-delivery/ROADMAP.md), [Thirty-Day Build](03-delivery/THIRTY-DAY-BUILD.md), [Implementation Plan](03-delivery/IMPLEMENTATION-PLAN.md), [Test Strategy](03-delivery/TEST-STRATEGY.md), [TODO](03-delivery/TODO.md).

## Layout

```
xms/
  README.md
  CLAUDE.md                           repository guide for coding agents; maps AIX vocabulary to XMS
  frontend/                           the Next.js and React application (xms-web); its own git repository: github.com/Mattb0124/xms-frontend
  backend/                            the NestJS application (xms-api, xms-worker); its own git repository: github.com/Mattb0124/xms-backend
  infra/                              Terraform and pipeline templates
  .claude/                            always-on rules (security-first) and spec-repo skills; app skills and commands live under frontend/.claude and backend/.claude
  00-overview/
    PRODUCT-VISION.md                 why the product exists; the data-first thesis; scope tiers
    GLOSSARY.md                       one vocabulary for every document
    DECISION-LOG.md                   ADR-00 to ADR-18 and the open decisions with owners
    CLARIFICATIONS-NEEDED.md          READ FIRST: open questions that block a spec or contradict shipped code
    REQUIREMENTS-TRACEABILITY.md      all 190 rows (workbook, XMS additions, functional RTM r3) (generated)
    requirements.csv / .json          machine-readable register
    scripts/build_register.py         regenerates the register from the workbook
    scripts/check_links.py            verifies every relative link in the set
  01-architecture/
    ARCHITECTURE.md                   system context, containers, request flows, ownership
    DOMAIN-MODEL.md                   bounded contexts, entities, invariants, module ownership
    DATA-MODEL.md                     conventions, schemas, isolation mechanics, table catalog
    SECURITY-AND-TENANCY.md           identity, authorisation, isolation, visibility, audit, AI controls
    SECURITY-ASSURANCE.md             audit readiness: control catalogue, evidence map, secure development gates
    AI-INTEGRATION.md                 the Axel adapter contract with the AI harness
    INTEGRATION-PATTERNS.md           the connector framework (outbox, inbox, DLQ, replay, kill switch)
    PLATFORM-AND-OPERATIONS.md        AWS footprint, pipeline, observability, recovery, costs
    DESIGN-SYSTEM.md                  tokens, screen grammar, portal variant
    WIREFRAMES.md                     dissection of the v2 and v3 prototypes: shell, screens, callouts, palette, deltas
    wireframes/                       the prototype bundles and their rendered screens (v3 under wireframes/v3)
    USER-EXPERIENCE.md                information architecture, every screen, the end-to-end flows
    AUDIT-AND-ANALYTICS.md            security audit log, user analytics, tamper evidence, reporting
    AIX-PATTERN-REUSE.md              what is copied, adapted, avoided, built from scratch, with evidence
  02-modules/
    accounts-and-administration/      accounts, users, roles, groups, calendars, configuration
    ticket-management/                tickets, state machines, SLA engine, comments, attachments, audit
    knowledge-base/                   solution articles, resolution record, CIs, retrieval, deflection
    time-and-budget/                  time entries, contracts, rate cards, burn-down, billing periods
    capacity-and-allocation/          roster, skills, PTO, allocation, planned vs actual
    client-portal/                    portal identity, forms, threads, consumption, CSAT
    email-intake/                     inbound and outbound email, threading, loops, quarantine
    dashboard-and-reporting/          dashboards, snapshots, report packs, exports
    servicenow-integration/           ServiceNow connector instances, maps, sync
    ai-functionality/                 Axel capabilities, suggestions, HITL, feedback, agents
    data-migration/                   historical import, reconciliation, parallel run, cutover
    integrations/                     connector registry, finance connector, public API, Teams, calendar
    resolution-ladder/                the four paths, profiling, classification, guided resolution (new, r3)
    measurement-and-calibration/      intake mix, the two resolution rates, misroutes, the calibration loops (new, r3)
    account-health/                   continuous account record, readiness and experience trajectories (new, r3)
    time-certification/               the daily card-based wrap-up that fills the denominator (new, r3)
    collaboration-signal/             swarm capture, peer-and-client quadrant, asymmetric visibility (new, r3)
    configuration-governance/         the parameter register, audited change, staleness (new, r3)
    outcomes/                         the outcome object above the ticket, outcome-framed reporting (new, r3)
  03-delivery/
    ROADMAP.md                        phases, milestones, team shape, decision gates
    TEST-STRATEGY.md                  layers, isolation suite, pipeline gates
    GO-LIVE-PLAN.md                   build to mid-Oct, parallel run and training to Nov, cutover, go live 1 Dec
    THIRTY-DAY-BUILD.md               the one-month build: day-by-day tracks, cuts, circuit breakers, acceptance
    IMPLEMENTATION-PLAN.md            the ordered work breakdown: every item, its dependencies and its test
    TODO.md                           the durable task list for the spec set and the build
    CLICKUP.md                        where each document is published in ClickUp (list XMS, X Platforms)
```

## Conventions

- Requirement IDs are `<category prefix>-<nn>` (TM, TB, CAP, CP, EM, DR, SN, AI, DM, INT) and are cited inline in every spec.
- Decisions are `ADR-nn` in the Decision Log; specs cite them rather than restating the reasoning.
- Every technical claim about AIX names a real file path verified on 2026-09-04; see [AIX Pattern Reuse](01-architecture/AIX-PATTERN-REUSE.md).
- No em-dashes in any document; absolute dates only.
- The register is generated; do not hand-edit the traceability matrix.

## Source inputs

- `DMS_Ticketing_System_Requirements.xlsx` (110 rows, 90 Must Have, 20 Nice to Have).
- "DMS Ticketing: replacing ServiceNow" assessment deck, 2026-09-03 (Juan Cetrangolo with Erick Alonso, Xavi, Ale, Vini; architecture review Matt).
- The XMS proof of concept: `AIXelerator/web-ui/components/aix-v3/xms/`, `AIXelerator/app-api/src/api/v3/xms/` (branch `feature/xms-ticketing`), `os-aixelerator-studio/app/modules/xms_ticketing/` (branch `feature/xms-ticketing`), and its spec set in `AIX Docs/AIX/Specs/xms-ticketing/`.
- The AI harness `os-aixelerator-studio` (external-caller contract in `app/modules/ai_execution/XT_AXEL_API.md`) and the `aix-mcp` scaffolding.
