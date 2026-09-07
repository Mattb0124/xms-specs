# What was done: the XMS foundation

**Status:** as built, 2026-09-07
**Owner:** Matt Brown
**Related:** [TODO](./TODO.md), [Thirty-day build](./THIRTY-DAY-BUILD.md), [Implementation plan](./IMPLEMENTATION-PLAN.md), [Backend README](../backend/README.md)
**Repos:** `backend/` (xms-backend), `frontend/` (xms-frontend), this repository (xms-specs)

---

## 1. Summary

The pilot-grade core of XMS exists as two deployables plus a web app, built security-first against the architecture and module specifications: forced row-level security per account, a permission-declared route table, append-only audit with tamper evidence, a transactional outbox, and every business rule in one TypeScript codebase shared by the API and the worker. The build followed the thirty-day plan day by day; the items below are what shipped, with the cuts and deviations stated where they were made.

Counts on 2026-09-07: backend 132 unit, 650 integration and 45 end-to-end tests; frontend 242 tests; 193 routes in the golden snapshot; migrations 0001 to 0013.

## 2. Built

| Area | What exists | Where |
|---|---|---|
| Platform | NestJS 12 API and worker, zod environment contract that refuses unsafe settings in production, helmet, URI versioning, global validation, pino JSON logging with an access line per request, health and readiness endpoints | `backend/src/main.ts`, `src/worker`, `src/config/env.ts`, `src/common/logging` |
| Database | Four schemas (`op`, `acct`, `sys`, `rpt`), four roles (app, portal, worker, migrator), SQL-first migrations with checksums and an advisory lock, `sys.apply_account_isolation`, month partitions for the event streams | `backend/src/db` |
| Isolation | Forced RLS on every account-scoped table bound to `xms.account_ids`; portal role read-only and column-granted; administrators bound to every live account; the GLOBAL account for shared knowledge; a generated suite that introspects the catalog and probes read, update, delete and insert under both roles | `src/db/session.ts`, `test/isolation` |
| Identity | Clerk RS256 (JWKS, authorised parties, agents audience on Axel routes only), harness HS256 session tokens, development HS256 refused in production, API keys with scopes; one guard resolving the principal, realm and permission; security events on every decision | `src/common/auth` |
| Audit and events | `acct.audit_events` and `op.audit_events` (append-only, partitioned), `sys.security_events`, `rpt.usage_events` with the telemetry route and the api.request middleware, `rpt.events_v` for search; the audit guard trigger on protected tables; chained daily digests per stream with verification and `integrity.*` events | `src/common/audit`, `src/modules/telemetry`, `src/modules/integrity`, migrations 0003, 0005, 0011 |
| Accounts and administration | Accounts, settings, users (internal, portal, service), roles from the shared permission catalog with transitive implications, grants, groups, versioned configuration catalogs with account overrides, bootstrap of the first administrator | `src/modules/admin` |
| Tickets | Five types as JSON state machines, priority matrix, SLA engine (latch, pause, resume, restamp), close discipline (resolution, solution link, time logged), comments and work notes, links, watchers, notifications, saved views and the condition grammar, catalogs | `src/modules/tickets`, `src/domain/tickets`, `src/domain/sla` |
| Time and contracts | Contracts of four models, periods, buckets, billing periods with locks, time entries and adjustments, burn math and the contract position, my week and unlogged time from the person calendar | `src/modules/time`, `src/modules/contracts` |
| Knowledge | Articles with frozen versions, visibility sets, generalization to GLOBAL with the identifier checklist, retrieval v1, the resolution record, portal search and client notes | `src/modules/knowledge` |
| Portal | Own realm under `/v1/portal`: me, submit, own requests, public timeline, comment, cancel, confirm closure, dashboard strip, knowledge | `src/modules/portal` |
| Attachments and email | Object store (S3 presigned POST or a signed local store), MIME allowlist, scan gating with quarantine, aliases, inbound pipeline (dedupe, loop guard, thread matching, stripping, quarantine decisions), outbound with typed templates and threading headers, suppression, SES event webhook | `src/modules/attachments`, `src/modules/email`, `src/domain/email` |
| Reporting | Measures, operations and account dashboards with view as client, security and usage tiles, Excel and CSV exports with formula neutralisation, audit search with keyset paging, WSR pack on demand, nightly snapshots | `src/modules/reporting`, `src/domain/reporting` |
| Axel adapter | Per-account AI switch with DPA and residency gates and the disable cascade, redaction before egress, single-shot classify, prioritise, duplicate, summarise and draft reply with thresholds and withheld rows, interactive SSE relay with cancel and thread index, decisions applied through the ticket service with AI-actor audit, proposals route, worker intake and expiry, accuracy with the threshold what-if, operator defaults and kill switch, harness contract test | `src/modules/ai`, `src/domain/ai`, `src/contracts/ai.ts` |
| Connectors | The connector framework (ADR-06) with the ServiceNow ingest: instances with a secret reference, versioned field and state maps validated against the dictionary, samples and the state machines before activation, ingest-only mode, the watermark poller behind an inbox keyed on (instance, sys_id, sys_updated_on), apply through the ticket service as a sync principal with origin `sync:<instance>`, per-field conflict policy, state map with accepted and reachable targets, journal comments once, dead letters with replay and discard, kill switch, health with automatic trip, the ticket sync card, and an in-process ServiceNow stand-in (`pnpm standin`) | `src/modules/connectors`, `src/domain/sync`, `src/tools/servicenow-stand-in.ts`, migration 0012 |
| Calendars | Business calendar engine (working minutes after an instant, between instants, next working instant; wall-clock hours across DST; holidays; split shifts), calendar documents per account with the holiday library and the account default, preview route, SLA clocks bound to the calendar they started on, wall clock as the fallback | `src/domain/calendar`, `src/modules/calendars` |
| Roster | People with working calendars, a skills catalog with per-person levels, certifications, import from the sign-in directory; `capacity:view` to read, `admin:users` to create and edit, `capacity:manage` for calendar, skills and certifications; no rate column until the finance grants | `src/modules/roster`, migration 0013 |
| Seed | `pnpm seed:dev`: roles, defaults, administrators, a six-person team across three groups, the Axel service user, two accounts with contrasting calendars and contract models, portal users, articles, tickets across every state with comments, notes, time and backdated clocks | `src/tools/seed.ts` |
| Frontend | Next.js 16 app with token-only styling, RTK Query slice per module, route registry, dev-token sign-in; screens for the queue and ticket record, admin, portal, knowledge, time, attachments, email, dashboards, audit search, security and usage, report packs, connectors (health overview, instance record with map editors, runs, dead letters, ticket Sync card); the AI slice and SSE hook | `frontend/` |

## 3. Cut or held

- Axel panel and AI screens in the web app, and the `xms_mcp` server in `aix-mcp`: held on 2026-09-07 at the request of the product owner (foundation first). The AI slice, SSE parser and hook are on frontend main; the panel draft is uncommitted; the MCP draft is stashed on `feature/xms-mcp`.
- Infrastructure, CI/CD, the pilot account and Clerk provisioning: deferred by the product owner.
- Parquet export and Athena over the event archive, OpenTelemetry through ADOT, alarms: wait for the AWS environment.
- Embeddings and the duplicate v2, WSR narrative, time assistant, burn anomaly: Phase 3 with the harness changes.
- ServiceNow bidirectional mode, webhooks and attachment sync (Phase 3); capacity and portal SSO: later phases per the plan.

## 4. Deviations from the specification

| Deviation | Why | Where recorded |
|---|---|---|
| SQL-first migrations with `pg`, no Drizzle | Policies, triggers and partitions are SQL; one source of truth | `backend/src/db/migrate.ts` |
| Portal writes on the app role bound to one account | The portal database role stays read-only by design | `src/db/unit-of-work.ts` |
| Typed HTML mail templates instead of MJML | No build step, testable functions | `src/modules/email/templates.ts` |
| Harness session tokens minted locally with the shared secret | The Clerk exchange cannot cross two Clerk applications (ADR-03) | `src/modules/ai/session-token.service.ts` |
| Trigram duplicate candidates | No harness embeddings endpoint yet | `src/modules/ai/ai.repository.ts` |
| Synthetic `axel-service` worker principal | Single-shot intake carries the facts in the message; a real service user exists from the seed for tool-using batch work later | `src/modules/ai/suggestion.service.ts` |
| Rate limits are per process and the CSP report endpoint is public | The WAF carries the global limits; a browser report carries no token | `src/common/rate-limit`, `src/modules/security/csp.module.ts` |
| Known audit exception: image-size (via pptxgenjs) has no patched release for the ICNS, JXL and HEIF parsers | XMS feeds it only the bundled template images; re-check on every pptxgenjs release | `backend/package.json` audit script |
| Loop-guard auto-disable of an alias deferred | Manual disable through the alias route is enough for the pilot | `src/modules/email/email.service.ts` |

## 5. Local run-through (2026-09-07)

The built API was run against the compose database outside the test harness: `pnpm db:migrate` applied the eleven migrations, `SEED_TICKETS=15 pnpm seed:dev` produced 30 tickets, 6 articles and 14 users in 4.5 seconds, and the API answered `/healthz`, `/readyz` (database ok, S3 and SQS skipped), `/v1/admin/me`, `/v1/tickets`, `/v1/dashboards/operations`, `/v1/admin/integrity/status`, `/v1/axel/suggest` (withheld, switch off for that account), `/v1/portal/me` with a portal token, refused a portal token on an internal route with 403, and accepted a CSP report with 204. The run found and fixed five packaging gaps (backend `fix(platform)` commit).

The compiled worker booted against the same database (`/readyz` ok), dispatched the seed's outbox rows with no dead letters, and ran the AI intake for the account with the switch on: 45 withheld suggestions (`unavailable` without a harness, `no_content` where no duplicate candidate existed), the expected outcome for an environment without Axel. The frontend dev server answered `/`, `/portal`, `/tickets` and `/dev/sign-in` with 200. The five Playwright golden paths then ran against that stack with a desk token and a portal token (`E2E_API_TOKEN`, `E2E_PORTAL_TOKEN`): shell and scope, state ramp, portal search-first home, security headers, and the ticket path (create with the priority preview, public reply with the first response, work note, transition to In progress, the Mine view).

The connector was run the same way: `pnpm standin` on port 3005 with one seeded case, `SEED_SERVICENOW_URL=http://127.0.0.1:3005 pnpm seed:dev` created the Brookfield instance with validated and active field and state maps in ingest-only mode, and the compiled worker polled the stand-in, advanced the watermark and applied the case as a sync ticket with its journal comment (one poll run and one inbound run, both success).

## 6. How to verify

```
cd backend && pnpm install && pnpm db:up && pnpm db:migrate && pnpm seed:dev && pnpm test:all
cd ../frontend && pnpm install && pnpm check
```

The isolation suite fails on any new account-scoped table without the standard policies; the route snapshot fails on any route without a declared permission; the harness contract test fails on any body field outside the published schema.
