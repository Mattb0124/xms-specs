# Platform and Operations: XMS Ticketing

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Architecture](./ARCHITECTURE.md), [Test Strategy](../03-delivery/TEST-STRATEGY.md), [AIX Pattern Reuse](./AIX-PATTERN-REUSE.md), [Roadmap](../03-delivery/ROADMAP.md)
**Verified against AIX on 2026-09-04:** `app-api/azure-pipeline-aix-dev.yaml`, `web-ui/azure-pipeline-aix-dev.yaml`, `os-aixelerator-studio/azure-pipeline-aix-dev.yaml`, `web-ui/Dockerfile`, `app-api/Dockerfile`, `workers/azure_pipelines/*`

---

## 1. What "same AWS patterns as AIX" means concretely

| Concern | AIX today (verified) | XMS |
|---|---|---|
| Compute | ECS on Fargate, one service per app, clusters `aix-dev-cluster` (account 580550011189) and `aix-prod-cluster` (303927186342) | Same clusters and accounts; services `xms-web` (from `frontend/`), `xms-api` and `xms-worker` (from `backend/`), `xms-mcp` |
| Registry | Shared-account ECR `471565333457.dkr.ecr.us-east-1.amazonaws.com/aixelerator/<app>`, tags `aix-{dev,prod}-<build>` and `-latest` | Repositories `aixelerator/xms-web`, `backend`, `xms-worker`, `xms-mcp`, same tagging |
| CI | Azure DevOps, one YAML per repo identical on every branch, stage selected by branch (`dev`, `production`), `batch: true`, `lockBehavior: sequential`, self-hosted ARM64 pool `xplr-arm64`, cross-account `sts:AssumeRole` into `aix-{env}-deploy` with `credential_source = EcsContainer` | Same shape, one pipeline per application (`frontend/`, `backend/`) in this repository, path-filtered, each with a **gate stage** before build (lint, type-check, unit, integration, isolation suite); the `backend/` pipeline builds both the API and the worker images from one checkout; `infra/` runs Terraform plan on pull request and apply on merge |
| Deploy step | Reads the live task definition, patches `.containerDefinitions[0].image` with `jq`, re-registers, `update-service --force-new-deployment`; `secrets[]` and `environment[]` survive because they are read from the live definition | Terraform owns task definitions; the pipeline runs `terraform apply` with the new image tag as a variable. Production configuration lives in the repo, not in production |
| Region | `us-east-1` | Same |
| Secrets | Vault for build-time values in the web pipeline (`/vault/secrets/ado-agents.env`); Secrets Manager and SSM through ECS `secrets[]` at runtime | Secrets Manager for all runtime secrets, referenced by Terraform; Vault only for the two build-time public keys the web image needs |
| Ingress | ALB per service (managed outside the repos) | ALB with WAF for `portal.<domain>`, Terraform-managed |
| Datastore | app-api on DocumentDB; studio on RDS PostgreSQL with pgvector | RDS PostgreSQL 16 with pgvector, Multi-AZ in prod |
| Object store | One bucket, tenant as first key segment | One bucket per environment, account as first key segment, versioning, lifecycle rules, GuardDuty Malware Protection |
| Queue | SQS, one producer in app-api, Python consumers in `workers`; no DLQs | SQS queues with redrive to DLQs, Terraform-managed |
| Logs | CloudWatch Logs through the awslogs driver | Same, structured JSON |
| Health | Static `{status: 'OK'}` in app-api | Real liveness and readiness (§5) |
| IaC | None in any repo; task definitions are the source of truth | Terraform in `infra` |

## 2. Images

| Image | Base | Notes |
|---|---|---|
| `xms-web` (from `frontend/`) | `node:20-alpine`, multi-stage, `output: 'standalone'`, non-root `nextjs:nodejs` (the AIX web-ui Dockerfile discipline) | `NEXT_PUBLIC_*` values are baked per environment, so the image is environment-specific; the pipeline builds one per target |
| `xms-api` (from `backend/`) | `node:20-alpine`, multi-stage, `pnpm install --frozen-lockfile`, prod deps only, non-root | The RDS CA bundle is vendored in the repo, not downloaded at build time (AIX's app-api Dockerfile fetches it with `wget` during the build) |
| `xms-worker` | Same as API plus Chromium for PDF rendering | Separate image so the API stays small |
| `xms-mcp` | `python:3.12-slim` on the `aix-mcp` scaffolding | Built from `aix-mcp/app/modules/xms_mcp` |

All images are ARM64 because the build pool is ARM64; base images and native dependencies (Chromium, `sharp`) are chosen accordingly.

## 3. Pipeline stages

1. **Gate** (ubuntu or ARM64 pool): install with frozen lockfile; lint; `tsc --noEmit`; unit tests; Testcontainers integration tests; isolation suite; dependency audit. Fails the run on any error. No flag skips it.
2. **Build**: `docker buildx build --push` for each changed app, tags `aix-<env>-<build>` and `aix-<env>-latest`.
3. **Migrate**: run Drizzle migrations against the target environment with the `xms_migrator` role from a one-off ECS task; on prod, preceded by a dry-run against the latest snapshot.
4. **Deploy**: `terraform apply` with the image tags; ECS rolls worker, API, then web (the deploy order in the [Roadmap](../03-delivery/ROADMAP.md)).
5. **Verify**: smoke tests; on dev, Playwright e2e against the seed and a ZAP baseline against the portal.

Branch policy follows AIX: `dev` deploys to dev on every merge; `production` deploys to prod; releases are tagged.

## 4. Environment configuration

| Variable group | Examples | Where |
|---|---|---|
| Database | `DATABASE_URL` (per role: app, worker, portal, migrator) | Secrets Manager |
| Clerk | `CLERK_PUBLISHABLE_KEY` (web, build-time), `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`, `CLERK_ISSUER` | Secrets Manager; publishable key via Vault at build |
| Harness | `AXEL_BASE_URL`, `AXEL_SESSION_SECRET` (shared with the harness for MCP token validation), `AXEL_ORIGIN` (the explicit `Origin` header value) | Secrets Manager |
| AWS | `AWS_REGION`, `S3_BUCKET`, queue URLs, SES identities | Terraform outputs into task environment |
| Email | `INBOUND_DOMAIN`, `OUTBOUND_DEFAULT_FROM` | Terraform |
| Feature flags | `FLAGS_JSON` (a small set of boolean flags read at boot; anything per account is data, not a flag) | Task environment |

Rule from AIX carried over: an empty-string environment variable shadows a baked value with `""` in Next.js; the deploy config never sets empty values.

## 5. Observability

| Signal | Implementation |
|---|---|
| Logs | `pino` with `pino-http`; JSON lines with `request_id`, `trace_id`, `principal.kind`, `account_ids` (ids only, never content); CloudWatch Logs with subscription filters for errors |
| Traces | OpenTelemetry Node SDK with auto-instrumentation (HTTP, pg, aws-sdk) exporting through the ADOT sidecar to X-Ray; trace id propagated into outbox rows and into harness calls as a header so an Axel turn can be followed across products |
| Metrics | CloudWatch EMF from the API and worker: request latency by route, queue age, DLQ depth, outbox lag, SLA breaches per hour, sweeper batch size, email loop suppressions, connector error rate per instance, Axel calls and withheld counts per account |
| Health | `/healthz` (process alive) and `/readyz` (PostgreSQL query, S3 head, SQS get-queue-attributes, harness reachability as informational) on API and worker; ALB uses `/readyz` |
| Alarms | ALB 5xx rate, p95 latency, `ApproximateAgeOfOldestMessage` per queue, DLQ depth greater than zero, outbox lag, RDS CPU and storage, failed SES deliveries, sweeper not run in 15 minutes, report run failed, connector instance unhealthy, isolation suite last run older than a day |
| Cost | Cost allocation tags `product=xms`, `env`, `service`; monthly report of infrastructure cost and harness token cost per account (from the adapter's per-account tag) |
| Errors | CloudWatch Logs Insights saved queries plus X-Ray error groups; no third-party error tracker in Phase 1 to 3 (no new vendors) |

## 6. Availability and recovery

| Objective | Target | Means |
|---|---|---|
| Availability (internal app, prod) | 99.5 percent monthly | Two tasks per service across AZs, Multi-AZ RDS |
| Availability (portal) | 99.5 percent monthly | Same; portal degrades to read-only if the worker is down (submissions still write to the outbox) |
| RPO | 5 minutes | RDS point-in-time recovery, S3 versioning |
| RTO | 2 hours | Terraform re-creation, RDS restore, runbook rehearsed quarterly |
| Email intake outage | No loss | SES stores in S3 before SQS; the worker catches up |
| Harness outage | No loss of human function | Adapter returns `unavailable`; batch jobs retry then DLQ |

## 7. Retention and lifecycle

| Data | Rule |
|---|---|
| Tickets, comments, audit, time | Life of the account plus the contractual retention (default 7 years for commercial records) |
| Raw inbound email in S3 | 90 days by default (parsed content is on the ticket); per-account override |
| Attachments | Life of the ticket plus account retention; quarantined files 30 days then deleted |
| Report packs and exports | 2 years |
| Snapshots | Life of the account |
| Harness threads | Per harness retention; deletion requested at offboarding |

Lifecycle rules are Terraform-managed S3 rules keyed by prefix; database retention is a worker job with a dry-run mode and an audit event per purge.

## 8. Runbooks (written in Phase 1, rehearsed in Phase 3)

Deploy and rollback; migration failure; DLQ replay; email loop detected (severity 1: disable the alias, drain, replay); connector kill switch and re-enable; account offboarding; secrets rotation (Clerk, harness session secret, connector credentials); restore from backup; isolation incident response (freeze, evidence, notify).

## 9. Costs (order of magnitude, prod)

| Item | Monthly |
|---|---|
| ECS Fargate (4 services, 2 tasks each, small) | 300 to 500 USD |
| RDS PostgreSQL Multi-AZ (db.m6g.large class) | 300 to 400 USD |
| S3, SQS, SES, CloudWatch, ADOT | 100 to 200 USD |
| GuardDuty Malware Protection for S3 | Volume-based, low at expected attachment volume |
| Clerk | Per the licensing spike (internal seats plus portal MAUs) |
| Harness tokens | Reported per account from the adapter; budgeted per account |

The point of the standalone product is that this table is the whole cost, measurable, and attributable (assessment comparison p.9, "makes product cost measurable").
