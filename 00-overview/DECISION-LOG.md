# Decision Log: XMS Ticketing

**Status:** Living document
**Owner:** Matt Brown
**Last updated:** 2026-09-05
**Related:** [Product Vision](./PRODUCT-VISION.md), [Architecture](../01-architecture/ARCHITECTURE.md), [Roadmap](../03-delivery/ROADMAP.md)

Each record: context, decision, alternatives rejected, consequences, status. Decisions are never deleted; a reversed decision gets a new record that supersedes it.

---

## ADR-00: The requirements register is generated, not hand-maintained

**Context.** 110 workbook rows must trace to specs and phases, and the workbook will change (the deck already cites 111 rows and 75 Must Have).
**Decision.** `00-overview/scripts/build_register.py` reads the workbook and emits the CSV, JSON and the traceability matrix. Module and phase mappings live in the script.
**Consequences.** Never edit the matrix by hand. Reconciling to the deck's reprioritised workbook is an open item (Sofi/DMS to supply the current file).
**Status.** Accepted 2026-09-04.

## ADR-01: Standalone product (Option B), not a module inside AIX

**Context.** Assessment of 2026-09-03 compared Option A (inside AIX) and Option B (standalone); weighted 64 vs 81 in favour of standalone.
**Decision.** Build XMS Ticketing as its own product: one web app, one API, one worker, one MCP server, PostgreSQL, S3, SQS, its own pipeline and observability, in the AIX AWS accounts. Axel is the only assumed dependency.
**Rejected.** Option A: shared releases, security surface and capacity with AIX; external clients would need AIX hardened as a client-facing product.
**Consequences.** 4 to 8 weeks of foundations that Option A would not need; product cost is measurable; no AIX code is copied.
**Status.** Recommended, pending Matt's sign-off and the leadership decision on path (extension, hiring, or scope cut).

## ADR-02: PostgreSQL system of record with database-enforced account isolation and a dedicated tier

**Context.** TM-01 asks for hard isolation per client at the data layer, "not row-level filtering". Security (Juan) must rule on shared tables, schema, database, account or region. The same team serves every account and needs cross-account views.
**Decision.** One RDS PostgreSQL per environment; every account-scoped table carries `account_id`, `FORCE ROW LEVEL SECURITY`, and policies keyed on session variables set by the data layer in one place; a separate portal database role with table-level revokes; generated isolation tests on every build; an `isolation_tier` per account where `dedicated` routes that account to its own database with the same schema and policies.
**Rejected.** Application-level filtering (the requirement rejects it; the POC audit found exactly that class of leak). Schema-per-account (cross-account operator views become unions; migrations multiply; heavy for 4 developers). Database-per-account for all (operational cost; kept as the dedicated tier).
**Consequences.** Isolation is provable and auditable; physical separation is available per account without redesign. Security's ruling may move specific accounts to the dedicated tier.
**Status.** Accepted pending Security review.

## ADR-03: One dedicated XMS Clerk application for internal users and portal users

**Context.** Internal users must use the THG IdP (INT-01). Portal users need SAML or OIDC against the client IdP with a local fallback (CP-01). AIX uses Clerk only for internal staff; nothing exists for external users except a hand-rolled token that must not be copied. The assessment flags Clerk licensing and SSO topology as a risk with a spike owner (Brayan) and recommends "keep Clerk; no new vendors".
**Decision.** A dedicated XMS Clerk application; the internal population in one organisation with the THG enterprise connection; each account in its own organisation with an enterprise SAML or OIDC connection or the local fallback; one API guard producing one `Principal` type.
**Rejected.** Building a portal identity realm from scratch (SAML is security-critical and the team is small). Reusing the AIX Clerk instance (couples XMS releases and user pools to AIX).
**Consequences.** Licensing and per-organisation SAML topology must be confirmed in the Phase 1 spike. If it fails, the fallback is a XMS-owned realm behind the same `Principal` interface.
**Status.** Accepted pending the spike.

## ADR-04: Axel is the only AI engine, reached through a XMS-owned adapter; XMS exposes itself to Axel as an MCP server

**Context.** The harness has a published external-caller contract, session token exchange, a `solution:` sentinel for durable threads, headless runs, inline agents and an MCP client. It has no per-tenant AI kill switch and no embeddings endpoint.
**Decision.** All AI calls go through the XMS Axel adapter (interactive, single-shot and batch faces) which enforces the per-account switch, opt-ins, thresholds, redaction and audit. XMS agents are defined inline in the harness. Tools are served by a XMS MCP server with caller-token forwarding. Six small harness changes are requested; until the embeddings endpoint exists the worker calls Bedrock Titan directly as a temporary exception.
**Rejected.** Calling Bedrock directly from XMS for generation (violates "reuse the harness for all AI work"). A XMS toolbox inside the harness (needs harness code per tool; kept as fallback). Storing the ticket corpus in the harness vectorstore (moves client data outside the boundary and defeats the per-account switch).
**Consequences.** The harness sees one tenant (the operator); account isolation for AI is a XMS property; harness owners must confirm no-training, residency, retention and availability.
**Status.** Accepted pending the Axel owners' confirmation.

## ADR-05: The solution knowledge base is a first-class module and resolution is a record

**Context.** The product thesis: solutions documented to the point where the platform becomes self-service.
**Decision.** `knowledge-base` is its own module owning articles, versions, visibility, configuration items, ticket-solution links, templates, feedback and embeddings. A ticket cannot resolve without a resolution code, notes, and a solution link or new-article candidate (no-solution codes excepted). The portal searches solutions before submission.
**Rejected.** Treating the knowledge base as a portal feature (the workbook lists it under Client Portal).
**Consequences.** Close discipline is stricter than ServiceNow's; adoption needs the AI draft-article assist to keep it cheap.
**Status.** Accepted.

## ADR-06: One connector framework; ServiceNow is a connector

**Context.** SN-01 to SN-09, EM-06, TB-14 and DR-05 all ask for the same plumbing properties.
**Decision.** Transactional outbox, inbox deduplication, correlation ids and watermarks, per-field conflict policy, SQS with DLQs, replay, kill switch and per-instance configuration as data, built once in the worker. ServiceNow, email, finance export and report delivery are connectors on it.
**Rejected.** A bespoke ServiceNow sync service.
**Consequences.** Brookfield's first mode is ingest-only; bidirectional after ownership rules are agreed.
**Status.** Accepted.

## ADR-07: Port the XMS proof of concept into XMS; retire the studio module

**Context.** A working ticketing backend exists in the studio (`feature/xms-ticketing`: 1932-line service, SLA math, sweeper, notifications, tests) and a web POC in web-ui. Leaving it there would put ticket data behind the AI service's database and auth.
**Decision.** Port the vocabulary, SLA math, close discipline, admin grammar and screens into XMS (TypeScript, XMS PostgreSQL). The studio module is the reference until Phase 2 ships, then is removed; the web-ui POC route stays until XMS Web replaces it.
**Rejected.** Keeping ticketing in the studio and proxying (violates ADR-01).
**Consequences.** Migration 092 numbering collision on the studio branch is irrelevant to XMS; nobody continues the studio module.
**Status.** Accepted.

## ADR-08: TypeScript worker sharing the API's domain packages; no Python batch jobs except the MCP server

**Context.** AIX's `repos/workers` is Python task folders in a different AWS account with no DLQs.
**Decision.** `backend/src/worker` is a NestJS standalone application importing `backend/src/domain` and `backend/src/db`, so every business rule exists once. Only `aix-mcp/app/modules/xms_mcp` is Python, because the `aix-mcp` scaffolding is Python.
**Status.** Accepted.

## ADR-09: Quality gates in the pipeline; Terraform in the repo

**Context.** AIX pipelines build and deploy only; task definitions are patched live; web-ui suppresses type errors at build.
**Decision.** The XMS pipeline runs lint, type-check, unit, integration and the isolation suite before building; `infra` holds Terraform for every AWS resource; no suppression flags.
**Status.** Accepted.

## ADR-10: Ticket keys are operator-wide and ServiceNow-style

**Context.** Clients quote keys on calls; migrated tickets keep their ServiceNow numbers as external references. The POC used `CS` plus seven digits.
**Decision.** `CS0001234` from one operator-wide sequence; migrated tickets store the source key in `external_ref` and are searchable by it.
**Status.** Accepted.

## ADR-11: Report packs are rendered inside XMS; the narrative comes from Axel

**Context.** The harness can render branded PPTX through agents (10 to 15 minutes per run), and AIX renders PPTX through an external Lambda. The assessment calls the WSR the highest-ROI item.
**Decision.** Numbers and charts come from XMS snapshots; the narrative is an Axel batch suggestion reviewed by the account owner; rendering uses `pptxgenjs` from the operator's template plus headless Chromium for PDF, in the worker. Deterministic, fast, and inside the boundary.
**Rejected.** Letting an agent build the whole deck (slow, non-deterministic, outside the boundary).
**Status.** Accepted.

## ADR-12: Separate repositories mirroring the AIX shape, not a monorepo

**Context.** The first draft of this set assumed one pnpm monorepo. Matt's direction (2026-09-04) is separate repositories in the AIX style: a React and Next.js web repository and a NestJS API repository, with the worker sharing the API code.
**Decision.** Four homes: `frontend` (Next.js and React; internal app and portal; design tokens seeded from AIX under `styles/tokens`; Axel streaming client under `lib/axel-client`; Playwright under `e2e/`), `backend` (NestJS; `src/domain`, `src/db` with Drizzle migrations, `src/contracts` with DTOs and the permission catalog, `src/worker` as a second entrypoint built into its own image; `test/kit`), `infra` (Terraform and pipeline templates), and the `xms_mcp` module inside the house `aix-mcp` repository. Web client types are generated from the API's OpenAPI document rather than shared through a package.
**Rejected.** A pnpm monorepo (not the house shape). A separate worker repository (would duplicate every business rule). A standalone Python MCP repository copying `mcp_common` (violates "no AIX code copied"; the house pattern is a module in `aix-mcp`).
**Consequences.** The API and worker deploy from one pipeline; the MCP module rides the `aix-mcp` release train, which is the one XMS surface outside the XMS boundary and is acceptable because it is the Axel-facing adapter. Contract drift between web and API is caught by regenerating types in the web pipeline.
**Status.** Accepted 2026-09-04.

## ADR-13: The product is called XMS; DMS is the practice

**Context.** The workbook and the assessment deck say "DMS Ticketing" because DMS (Digital Managed Services) is the practice that commissioned it. The proof of concept was already named XMS (Xelerated Managed Services). Matt's direction (2026-09-04): the solution is XMS.
**Decision.** Product, repositories, hosts, roles, agents and identifiers use XMS (`frontend`, `backend`, `infra`, `xms_mcp`, `solution:xms`, `xms.account_ids`, `.xms-scope`). "DMS" appears only for the practice, its team, and the titles of the source workbook and deck.
**Consequences.** The `.xms-scope` token names and `xms:*` vocabulary from the proof of concept carry over unchanged. The studio module `xms_ticketing` and the web-ui POC keep their names until retired (ADR-07).
**Status.** Accepted 2026-09-04.

## ADR-14: The applications live in this repository as `frontend/` and `backend/`

**Context.** ADR-12 rejected a pnpm monorepo and named separate repositories. Matt's direction (2026-09-04): create `frontend` and `backend` folders in the `xms` repository and seed the generic AIX skills into it.
**Decision.** This repository holds the specification set plus three application folders: `frontend/` (the Next.js and React app, deployable `xms-web`), `backend/` (the NestJS app with the worker as a second entrypoint, deployables `xms-api` and `xms-worker`) and `infra/` (Terraform). Each application has its own `package.json`, lockfile, Dockerfile and path-filtered pipeline stage; there is no workspace tooling joining them, and the frontend consumes the backend only through its OpenAPI document and generated types. `xms_mcp` stays a module in the house `aix-mcp` repository. Generic engineering skills, house standards and commands are seeded under `.claude/` and `.cursor/` from the AIX workspace, with `AIXelerator/.claude/sync-skills.ps1` as the source of truth and `CLAUDE.md` mapping AIX vocabulary to XMS.
**Rejected.** Three git repositories (more ceremony than a four-person team needs; the specs and the code belong together). Workspace tooling (ADR-12 stands: no monorepo build graph).
**Consequences.** Paths in every spec read `frontend/...`, `backend/...`, `infra/...`; ECS service and ECR image names keep the `xms-web`, `xms-api`, `xms-worker`, `xms-mcp` names. ADR-12's repository names are superseded by these folder names; its reasoning about sharing domain code between API and worker is unchanged.
**Status.** Accepted 2026-09-04.

## ADR-15: Build the pilot-grade core in one month

**Context.** Matt's direction (2026-09-05): build XMS in a month. The Implementation Plan sequenced foundations over eight weeks and the pilot over seventeen with the same four people.
**Decision.** Twenty working days, four parallel tracks, foundations in week 1, vertical slices from day 6, two circuit breakers (day 5: isolation and guard green or the portal is cut; day 10: email creating tickets or email moves to month 2). Scope is cut, the date is not; the cut list and the day-30 acceptance script are in [Thirty-Day Build](../03-delivery/THIRTY-DAY-BUILD.md). The month delivers a pilot-grade core on the dev environment (50 of the 94 Must Have rows, every trust guarantee: isolation, identity, audit, AI switch), not production or cutover; months 2 and 3 restore the cuts and continue the Implementation Plan.
**Rejected.** Skipping the isolation layer, the pipeline gate or the audit streams to save days (they are the reason a standalone product was chosen). Building the portal before the portal role and realm suite are green.
**Consequences.** Business calendars, SSO, rate cards, billing periods, capacity, ServiceNow sync, migration, scheduled reports, CSAT and Axel generation land in months 2 and 3 as listed; the Roadmap phase exit criteria are unchanged.
**Status.** Accepted 2026-09-05.

## ADR-16: Security first; every change is built to pass audits

**Context.** Matt's direction (2026-09-05): the solution must be security tight and everything must be developed around passing security audits. XMS holds several clients' data in one product and will face ISO 27001, SOC 2 and client security audits.
**Decision.** A security definition of done applies to every change and is enforced three ways: an always-on repository rule (`.claude/rules/xms/security-first.md`), a skill with the checklist, required tests, forbidden patterns and evidence list (`.claude/skills/xms-security-first`, mirrored to `.cursor`), and pipeline gates that cannot be skipped. Controls are catalogued and mapped to the audit criteria with the evidence each produces automatically ([Security Assurance](../01-architecture/SECURITY-ASSURANCE.md)); a pull request without a completed checklist is not reviewed; the isolation, visibility, realm, evidence and egress controls exist from the first migration and the first route, including in the one-month build.
**Rejected.** Treating security as a hardening phase at the end; producing audit evidence by hand; any "temporary" bypass of the isolation layer, the guard or the audit streams.
**Consequences.** Slightly slower first days; no security debt to pay before cutover; questionnaire answers come from an evidence map rather than from engineers. Requirement XA-05 tracks it in the register.
**Status.** Accepted 2026-09-05.

## ADR-17: The v2 wireframes are the UI source of truth for the shell and the five built screens

**Context.** Matt delivered the hi-fi prototype `XMS v2 (standalone).html` on 2026-09-05 (Queue, Ticket record, My work, Dispatch, Operations; the 27-screen tree; twenty engineering callouts referencing requirement IDs). It differs from the POC and the earlier documents in the shell (navy finder bar, pinned sidebar, finder overlay), the palette, the second typeface and the list rows.
**Decision.** The prototype governs the shell and the five built screens; [Wireframes v2](../01-architecture/WIREFRAMES.md) records the dissection and the deltas; the Design System token values, the frontend skills and the plans are updated to match. Dense lists have no row striping. IBM Plex Mono is the second typeface. Violet marks AI-origin content only. The 22 stub screens and the portal follow the User Experience catalog until wireframed; a second prototype round covers New ticket, Quarantine, Solutions and the portal before day 11 of the build.
**Rejected.** Keeping the POC's zebra rows and single-typeface rule (the prototype explicitly overrides both). Re-theming the prototype to the POC's cobalt palette (the token names stay, the values change).
**Consequences.** `--xms-zebra` is retired; `--xms-navy`, `--xms-bar`, `--xms-label`, `--xms-ai-*` and `--xms-mono` are added; the shell components in Implementation Plan P1.4.1 and P1.4.2 change shape; the prototype's callouts become acceptance checks.
**Status.** Accepted 2026-09-05.

## ADR-18: Version 3 semantic colour and list patterns supersede v2 for lists

**Context.** Matt delivered `XMS v3 (standalone).html` on 2026-09-05 after v2: a state ramp (New slate, In progress blue, Awaiting client amber, Awaiting approval teal, Resolved green, Closed grey), 3px type bars, per-account identity dots, and three list patterns from Kefron (removable filter chips with Add filter and Clear all, a blue selection bar for bulk actions, rows per page).
**Decision.** v3 governs list semantics and colour; v2 remains the reference for everything it did not change. Ticket state pills use the ramp; SLA and priority keep their own signals and never share a cell with a state colour; type bars and account dots are the only colour in their cells; the account hue is assigned at creation and stored on the account; page size is part of the saved-view state.
**Rejected.** Colouring the whole row by state or type (the prototype keeps colour to the pill, the bar and the dot). Reusing the generic `--state-*` trios for ticket states (they stay for SLA, priority and scan state).
**Consequences.** New tokens (`--xms-state-*`, `--xms-type-*`, `--xms-account-*`), new components (FilterChip, AddFilterButton, ClearAllLink, SelectionBar, TableFooter, TypeBar, AccountDot), `op.accounts.identity_hue`, `page_size` on saved views; the frontend skills and the plans are updated.
**Status.** Accepted 2026-09-05.

## Open decisions (owner, default assumption, due)

| Question | Owner | Default assumption | Due |
|---|---|---|---|
| Path 1, 2 or 3 (extend ServiceNow, hire, cut scope) | Ignacio | Path 1 (six-month extension, current team dedicated) | 2026-09-07 |
| Isolation model ruling | Juan / Security | Shared tables with forced RLS plus dedicated tier per account | 2026-09-18 |
| Pilot subset of the Must Haves and workbook reconciliation (110 vs 111 rows, 90 vs 75 Must Have) | Sofi / DMS | Appendix C of the deck; this register's phase column | 2026-09-18 |
| Brookfield integration facts (flows, mappings, auth, volumes, errors, ownership) | Vini | Ingest-only first; Table API with OAuth client credentials | 2026-09-25 |
| Harness contract items: session tokens for service principals, embeddings endpoint, headless route, thread deletion, no-training and residency statements | Axel owners | Items 1, 5, 6 in Phase 1; items 2 to 4 by Phase 3 | 2026-10-15 |
| AV scanning product (GuardDuty Malware Protection vs ClamAV Lambda), environments, backups, repo and DevOps setup | Infrastructure | GuardDuty | 2026-09-25 |
| One-way or bidirectional Brookfield sync in the first release | Product / DMS | One-way in the pilot, bidirectional for operational replacement | 2026-09-18 |
| Clerk licensing and per-organisation SAML topology for portal users | Brayan | Works within the current plan | 2026-10-02 |
