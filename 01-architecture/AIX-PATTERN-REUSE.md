# AIX Pattern Reuse Catalog

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Architecture](./ARCHITECTURE.md), [Design System](./DESIGN-SYSTEM.md), [AI Integration](./AI-INTEGRATION.md), [Security & Tenancy](./SECURITY-AND-TENANCY.md), [Platform & Operations](./PLATFORM-AND-OPERATIONS.md)
**Verified:** every path below was read on 2026-09-04 in `C:\Users\matt.brown\Documents\repos\AIXelerator\` (app-api, web-ui, aix-mcp), `C:\Users\matt.brown\Documents\repos\OS-AIX\os-aixelerator-studio\` (branch `mb/xda`, plus `feature/xms-ticketing` for the XMS module) and `C:\Users\matt.brown\Documents\repos\workers\`

The assessment's rule is "no AIX code copied, same technology family, familiar patterns". This catalog is the definitive list of what XMS takes from AIX, what it adapts, and what it deliberately leaves behind, with the evidence for each. Module technical specs cite entries here by name instead of repeating the file paths.

---

## 1. Copy the pattern nearly as-is

| Pattern | AIX evidence | XMS use |
|---|---|---|
| Clerk JWT verification with a 60-second clock skew and a non-verifying `peekJwt` diagnostic | `app-api/src/authtentication/clerk-jwt.ts`, `clerk.strategy.ts` | API guard |
| Long-lived `agents` Clerk JWT template for minute-long agent turns, with graceful fallback | `web-ui/components/aix-v3/chat/hooks/useDiscoveryChat.ts:127` | Axel panel token |
| Constant-time internal-secret guard that refuses when unconfigured | `app-api/src/guards/require-internal-secret.guard.ts` | Webhook HMAC verification |
| Notification design: recipient as identity key, collapse keys, TTL retention, `mutedAt` instead of delete, copy in one file | `app-api/src/api/v3/notifications/*` (`user-notification.schema.ts`, `notification-subscription.schema.ts`, `notification-copy.ts`) | `acct.notifications`, watchers |
| Activity and comments: polymorphic target addressing, append-only writes, author stamped from the token | `app-api/src/api/v3/activity/*`, `src/api/v3/comments/*` | Audit events and comments |
| Field-level diff engine and retention sweep as a plain, script-runnable method | `app-api/src/api/v3/activity/versioning/*` (`diff.ts`, `retention.service.ts`) | Audit `old_value`/`new_value` capture; retention job |
| S3 client `requestChecksumCalculation: 'WHEN_REQUIRED'` (presigned PUT 400 BadDigest bug) and account as first key segment | `app-api/src/files/services/file-storage.service.ts`, `src/services/blob/s3.service.ts` | Attachment storage |
| Attachment size cap and MIME allowlist at registration | studio `app/modules/xms_ticketing/service.py` (`MAX_ATTACHMENT_BYTES`, `ALLOWED_ATTACHMENT_TYPES`) | Same, plus presigned POST |
| SLA breach sweeper: idempotent latch shared with the mutation path, append-only event, `FOR UPDATE SKIP LOCKED`, batch cap, multi-instance safe | studio `app/modules/xms_ticketing/sweeper.py` and `service.py` `_latch` | Worker sweeper |
| SLA pause and resume math, latch-before-pause ordering, response-met on first public reply | studio `xms_ticketing/service.py`, POC audit "built better than spec" | `backend/src/domain` SLA engine, generalised to business calendars |
| Server-derived priority from impact and urgency; resolution codes; close discipline | studio migration 091 and 092; `web-ui/components/aix-v3/xms/vocab.ts` `derivePriority`, `RESOLUTION_CODES` | Priority matrix with per-account override; resolution record |
| Postgres row claiming for schedulers instead of in-memory state | studio `app/modules/agent_harness/scheduler/routine_engine.py` | Report schedules, sweeper, retention |
| Golden route-table snapshot test | studio `tests/golden/route_table.json` | API route and permission snapshot |
| Error passthrough proxy (upstream status and body preserved) | `app-api/src/api/v3/xms/xms.service.ts` `forward()`, `observability.service.ts` | Axel adapter error relay |
| MCP `resolve-session` returning `skipped[]` instead of failing the run | `app-api/src/api/v3/mcp/internal-mcp.service.ts` | Connector degradation semantics |
| MCP module scaffolding (`make_mcp`, `build_streamable_app`, `make_auth_middleware`) and catalog row shape with `useCallerToken` | `aix-mcp/app/mcp_common/*`, `app/modules/oracle_epm_mcp/*`, `catalog.json` | `aix-mcp/app/modules/xms_mcp` |
| Harness external-caller contract, session token exchange, `solution:` opportunity sentinel, headless runs | studio `app/modules/ai_execution/XT_AXEL_API.md`, `app/auth/session_router.py`, `chat_stream_router.py:70`, `runtime/headless.py` | Axel adapter |
| Inline agent definition skeleton | studio `app/modules/ai_execution/services/xt_axel_agent.py`, `app/modules/agents/catalog/registry.py` | XMS agents |
| SSE parsing rules: line buffer carry, skip `:` heartbeat frames, untyped frames are content | `web-ui/redux/services/discoveryApi.ts:842-1310`, `XT_AXEL_API.md` | Axel streaming client |
| Design tokens: vendored aiinds file, house aliases, `--state-*` trios, scoped solution theme, dark mode wiring, fonts | `web-ui/app/aiinnovation-tokens.css`, `app/globals.css`, `tailwind.config.js`, `app/layout.tsx`, `components/theme-provider.tsx` | `frontend/styles/tokens` |
| ServiceNow-shaped screen grammar | `web-ui/components/aix-v3/xms/*` (QueueTab, NewTicketPage, TicketDrawer, XmsAdminPages) | XMS Web screens |
| Optimistic status update with rollback on 409 | `web-ui/redux/services/xmsApi.ts:606-667` | Transition mutation |
| Sortable sticky table, Panel, tab bar, scorecards | `web-ui/components/aix-v3/sortable-table.tsx`, `opportunity/shared/Panel.tsx`, `BlueTabBar.tsx` | Rewritten with same props |
| Azure DevOps pipeline shape: one YAML, branch-selected stage, ARM64 pool, shared ECR, cross-account deploy role | `app-api/azure-pipeline-aix-dev.yaml` and siblings | XMS pipeline plus a gate stage |
| Multi-stage non-root Next.js image | `web-ui/Dockerfile` | All XMS images |
| Solution access grants and solution roles with reconcile-whole-set semantics | studio migrations 093 and 096; `web-ui/components/aix-v3/xms/XmsAdminPanel.tsx` | Account grants admin |

## 2. Adapt while copying

| Pattern | AIX state | XMS change |
|---|---|---|
| Guard stack | Three guards each re-checking `@Public()` (`app.module.ts` ~L218) | One composed guard |
| Tenant resolution | Three resolvers with different precedence; `@TenantId()` falls back to `'default'` (`src/decorators/tenant-id.decorator.ts`) | One resolver, fail closed, no header override |
| Permission catalog and implications | Catalog in the frontend only (`web-ui/lib/rbac/permission-catalog.ts`), one-level implications, guard opt-in per controller, assignments in Mongo and Clerk metadata | Catalog in `backend/src/contracts`, transitive closure, global guard, assignments in PostgreSQL |
| Solution role union | Computed in a React hook (`useXmsPermission.ts`); the studio router (`xms_ticketing/router.py`) checks only `org_slug`, so the `/access` and `/roles` admin routes are reachable by any tenant user who bypasses the hidden panel (a live privilege-escalation gap in the POC, verified 2026-09-04) | Server-side permission guard on every route; the route snapshot records the required permission per route, not just the path |
| API keys | No scopes, bcrypt scan over all keys, user-owned (`src/security/security.service.ts`) | Scopes, SHA-256 lookup index, operator-owned |
| Data layer tenancy | Optional `tenantId` parameter on data classes (`src/data/technology.data.ts`) | RLS below the query; scope is bound to the session, never a method parameter |
| Data classes and schemas | Flat `src/data/` and `src/schemas/` directories | Colocated per feature module |
| Soft delete | Three coexisting conventions | One convention per entity kind, enforced in the repository base |
| DTO validation | `class-validator` present but no global `ValidationPipe` (`main.ts`) | Global pipe with whitelist and transform |
| Versioning | URL prefixes in controller strings | `enableVersioning({ type: URI })` |
| Email | Lambda invoke with templates outside the repos; default from-address is a personal Gmail (`src/api/v1/email/email.service.ts`) | SES v2 in-process with in-repo templates |
| Attachments | Presigned PUT, no size limit, no AV, no lifecycle | Presigned POST with range, GuardDuty scan, lifecycle |
| Scheduled jobs | `@Cron` fires once per ECS task; one cron in the estate | `SKIP LOCKED` claiming or EventBridge to a one-off task |
| Worker | Python task folders in `repos/workers` (account 235494824003), `register-task-definition` only, SQS delete-after-process with no DLQ | TypeScript worker sharing domain code; SQS with DLQs; path-filtered pipeline stage kept |
| Health check | Static literal (`src/controllers/health/health.controller.ts`) | Real readiness |
| Reports | PPTX by external Lambda (`src/reports/report.service.ts`), no XLSX export utility, `xlsx` 0.18.5 import only | `pptxgenjs` and `exceljs` in the worker |
| Pipeline | Build and deploy only, no gates | Gate stage |
| Task definitions | Patched live with `jq` | Terraform |
| XMS module location | Ticketing domain inside the studio's PostgreSQL (`feature/xms-ticketing`) | Ported to XMS PostgreSQL in TypeScript; studio module retired |

## 3. Do not copy

| Item | Why |
|---|---|
| `app-api/src/services/jwt/simple-jwt.service.ts` | Hand-rolled HMAC token with a default secret |
| `app-api/src/interceptors/retry-threshold.interceptor.ts` | Global interceptor injecting eight feature services |
| `next.config.mjs` `ignoreBuildErrors` and `ignoreDuringBuilds` | Packmind standard forbids it; XMS builds fail on type or lint errors |
| Dual lockfiles (`package-lock.json` and `pnpm-lock.yaml` in web-ui) | One lockfile, pnpm |
| Direct-to-studio RTK `createApi` instances bypassing the base API (`osAiRoutinesApi.ts` and five siblings) | XMS Web talks only to the XMS API |
| `xlsx` 0.18.5 for generation | Known advisories |
| `DiscoveryChatWithPanel` (1316 lines, eight slices) | XMS renders its own panel over a small streaming client |
| Studio `get_api_key_for_tenant` fallback to `AIX_EEA_API_KEY` | Cross-tenant credential fallback; XMS has no tenant API keys toward the harness |

## 4. Build from scratch (verified absent in AIX)

External client identity (SAML/OIDC plus local fallback; AIX uses Clerk only for internal staff), inbound email to ticket (no SES receipt rules, IMAP or MIME parsing anywhere), webhook receivers with signature verification, bidirectional connector sync (mapping, state translation, loop prevention, conflict policy, DLQ, replay), idempotency keys, transactional outbox, DLQ and redrive, scheduled report generation and delivery, business-hours and multi-time-zone SLA calendars, rate cards and billing-period locking, capacity and allocation, structured logging, OpenTelemetry, metrics and alarms, Terraform.
