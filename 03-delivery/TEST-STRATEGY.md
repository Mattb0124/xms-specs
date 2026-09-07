# Test Strategy: XMS Ticketing

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Roadmap](./ROADMAP.md), [Platform & Operations](../01-architecture/PLATFORM-AND-OPERATIONS.md), [Security & Tenancy](../01-architecture/SECURITY-AND-TENANCY.md)
**Standards applied:** Write Isolated Tests With Constructed Data (never live credentials); Do Not Suppress Type-Check and Lint Errors in Builds

---

## 1. Principles

1. **Test behaviour at the lowest layer that exercises it.** SLA math is tested in the domain service with constructed clocks; the HTTP layer is tested for mapping and auth, not for SLA math.
2. **Isolation is a tested property, not a review item.** Every account-scoped table gets a generated cross-account test; the build fails if a new table appears without one.
3. **Constructed data, mocked externals.** Factories for accounts, users, tickets, contracts and time entries; ServiceNow, SES, S3, SQS and the Axel adapter are stubbed. No live credentials, no production URLs, ever.
4. **Meaningful assertions only.** No "should be defined" scaffolding.
5. **The pipeline runs the gates.** Unlike the current AIX pipelines, which build and deploy only, the XMS pipeline runs lint, type-check, unit, integration and isolation tests before it builds an image, and the build fails on any of them.

## 2. Layers and tools

| Layer | Tool | Where | What it proves |
|---|---|---|---|
| Static | ESLint, `tsc --noEmit`, Prettier check | all packages | No suppressed errors; `ignoreBuildErrors` and `ignoreDuringBuilds` are forbidden by a lint rule on the Next config |
| Domain unit | Jest | `backend/src/**/*.spec.ts` | State machine transitions, priority matrix, SLA business-minute math on calendars, pause accounting, breach latching, burn-down, capacity, rate snapshotting, period locking, loop detection, header threading, signature stripping |
| Data layer integration | Jest + Testcontainers PostgreSQL | `backend/test/db/**` | Migrations apply from empty; RLS policies deny cross-account reads and writes for every account-scoped table; append-only triggers reject updates and deletes on audit, time entry, pause, inbound message and snapshot tables; locked periods reject writes |
| HTTP | Jest + supertest | `backend/test/http/**` | Every route rejects anonymous and garbage tokens; portal tokens cannot reach operator routes; internal tokens without an account grant get 404 on that account's data; DTO validation; controllers are thin (one service call) |
| Worker | Jest | `backend/src/worker/src/**/*.spec.ts` | Outbox dispatch idempotency, inbox deduplication, retry classification, DLQ routing, connector contract tests against recorded fixtures, email parsing corpus |
| Axel adapter contract | Jest + recorded fixtures | `backend/test/axel/**` | Request shapes sent to the harness, per-account switch enforcement (no call when off), suggestion persistence, HITL state transitions, confidence withholding |
| Web unit | Vitest | `frontend/**/*.test.ts(x)` | Pure logic (SLA display math, condition builder serialisation, form validation) and component behaviour with Testing Library |
| End to end | Playwright | `frontend/e2e/**` | Golden paths in a seeded environment: create by form, create by email fixture, work a ticket to close with time and solution, portal user sees only their account, WSR pack generated and downloadable, Brookfield stand-in round trip |
| Load | k6 | `load/**` | Queue list at 50k tickets per account under 500ms p95; dashboard aggregates; SES inbound burst of 500 messages |
| Security | OWASP ZAP baseline, dependency audit, secrets scan, Terraform policy check, the auth rejection and realm suites, the portal visibility suite | pipeline | No high findings on the portal; no known-vulnerable dependencies; no secret literal; no public bucket or wildcard IAM; every route rejects anonymous, garbage, wrong-realm and ungranted principals; no internal field reaches a portal principal (per the `xms-security-first` skill section 3) |

## 3. The isolation suite (mandatory from Phase 1)

Generated from the schema: for every table with an `account_id` column the suite creates two accounts and one row each, then asserts under a session bound to account A that: select returns only A's row; update and delete of B's row affect zero rows; insert with `account_id = B` is rejected; a join through any foreign key cannot reach B. The suite also runs with the portal database role to prove the tighter policy (single account, comments only, no work notes table access). Any table missing from the suite fails the build via a schema-introspection check.

## 4. Fixtures and factories

- `backend/test/kit`: factories (`anAccount()`, `aUser({kind})`, `aTicket({type, state})`, `aContract({model})`, `aTimeEntry()`), a Testcontainers Postgres harness with migrations applied once per run and a transactional rollback per test, stubs for SES, S3, SQS and the Axel adapter, an email corpus (Outlook, Gmail, Apple Mail, ServiceNow notification, out-of-office, bounce, loop) and a ServiceNow payload corpus captured from the stand-in.
- Seeds: `seed:dev` creates two accounts with contrasting calendars (UK and Australia), one internal team across three groups, contracts of each model, 200 tickets across all states, articles at each visibility, and one ServiceNow stand-in instance. Used by e2e and demos.

## 5. Pipeline gates (in order)

1. Install with a single frozen lockfile (pnpm).
2. Lint, format check, `tsc --noEmit` across the workspace.
3. Unit tests (API, worker, web).
4. Data layer and HTTP integration tests against Testcontainers Postgres.
5. Isolation suite and schema check.
6. Build images.
7. Deploy to dev; run Playwright e2e against dev with the seed; run ZAP baseline against the portal.
8. Promote to prod on a tagged release; smoke tests; migration dry-run against a prod snapshot beforehand.

A red step stops the pipeline. There is no flag to skip a gate.

## 6. Coverage expectations

Coverage is a floor, not a target: 80 percent lines on the API domain services and worker handlers, with the state machine, SLA engine, isolation, period locking and loop prevention at 100 percent branch coverage because a miss there is a client-visible incident.

## 7. Test data hygiene

- Real client names never appear in fixtures; the seed uses fictional accounts.
- Migration rehearsal data from ServiceNow is used only in an isolated migration environment with the same isolation controls as prod, and deleted after the reconciliation sign-off.
