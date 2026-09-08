# Register gaps survey, 2026-09-09

**Register used:** [`00-overview/requirements.csv`](../00-overview/requirements.csv), the machine-readable copy of [REQUIREMENTS-TRACEABILITY.md](../00-overview/REQUIREMENTS-TRACEABILITY.md). **115 rows**: 110 workbook rows plus the 5 XMS-added `XA` rows. **95 Must Have, 20 Nice to Have, no Should Have rows** (the workbook has only two priority values, so the Should Have half of the brief is empty).

**Rows surveyed:** all 20 Nice to Have rows, plus every Must Have row that sits under a `[ ]` or `[~]` line in [TODO.md](./TODO.md) or under section 3 of [WHAT-WAS-DONE.md](./WHAT-WAS-DONE.md). The 60-odd Must Have rows that sit under a clean `[x]` line are not repeated here.

**Trees read:** spec repo at `9bf486d`, `backend/` at `5f9fae4`, `frontend/` at `894675f`. Nothing was changed and no suite was run.

**One register correction:** TODO section 3 labels the public API and outbound webhooks work "(INT-05)". The register's INT-05 is calendar integration; the webhook work carries no register id of its own. Both rows are assessed below on the register's meaning.

---

## Built

| id | title | priority | module | status | evidence | note |
|---|---|---|---|---|---|---|
| TM-14 | Attachments with virus scanning | Must Have | ticket-management | built | `backend/src/modules/attachments/`, migration `0008_email_and_attachments.sql`, EICAR quarantine in the scan gate | GuardDuty Malware Protection is the infra half and waits for AWS |
| TM-18 | Change calendar with conflict detection | Nice to Have | ticket-management | built | migration `0038_change_windows.sql`, `GET /v1/change-calendar` and `/v1/change-calendar/at`, `backend/src/modules/tickets/change-windows.module.ts`, `frontend/app/(internal)/tickets/change-calendar/page.tsx` (frontend `894675f`) | |
| TM-01 | Multi-tenant data isolation | Must Have | accounts-and-administration | built | migration `0001_foundation.sql`, `sys.apply_account_isolation`, the generated isolation suite | the open item is a Security ruling on the production tier, not code |
| EM-01 | Dedicated inbound address | Must Have | email-intake | built | `backend/src/modules/email/`, `POST /v1/admin/accounts/:id/aliases`, migration `0008` | the SES receipt rule to SQS waits for AWS |
| SN-02 | State machine translation | Must Have | servicenow-integration | built | `backend/src/modules/connectors/`, migrations `0012`, `0030` | green against the in-process stand-in |
| SN-03 | Loop prevention | Must Have | servicenow-integration | built | `origin = sync:<instance>` guard and the echo hash on the link, migration `0030` | |
| SN-04 | Conflict resolution policy | Must Have | servicenow-integration | built | outbound conflict vocabulary in `connectors`, per-link overrides | |
| SN-05 | Comment and work note sync | Must Have | servicenow-integration | built | journal entries with the correlation marker, migration `0030` | internal work notes are refused outbound by design |
| SN-06 | Attachment sync | Must Have | servicenow-integration | built | migration `0031_sync_attachments.sql`, both directions through the scan gate | |
| SN-07 | Sync health monitoring and dead-letter queue | Must Have | servicenow-integration | built | `GET /v1/connectors/health`, `GET /v1/connectors/:instanceId/dead-letters`, `frontend/app/(internal)/admin/connectors/[id]/page.tsx` | |
| SN-08 | Multiple concurrent client instances | Must Have | servicenow-integration | built | `acct.connector_instances`, per-instance claim with SKIP LOCKED | |
| SN-09 | One-way ingest mode | Must Have | servicenow-integration | built | ingest-only mode, watermark poll, inbox apply (migration `0012`) | |
| AI-07 | Similar-ticket retrieval and KB suggestion | Must Have | knowledge-base | built | `GET /v1/tickets/:key/solutions`, `GET /v1/search/solutions`, the Solutions rail in `frontend/components/knowledge/` | |
| AI-08 | Human-in-the-loop by default | Must Have | ai-functionality | built | `backend/src/modules/ai/suggestion.service.ts` decision flow, `POST /v1/axel/suggestions/:id/decisions` | |
| AI-10 | AI actions logged and attributable | Must Have | ai-functionality | built | AI-actor audit rows through the ticket service, migration `0010_ai.sql` | |
| AI-13 | Feedback capture on AI suggestions | Must Have | ai-functionality | built | `POST /v1/axel/suggestions/:id/feedback`, `frontend/components/axel/suggestion-card.tsx` | |
| XA-03 | Audit and usage reporting | Must Have | audit-and-analytics | built | `POST /v1/audit/search`, `/v1/audit/export`, `GET /v1/dashboards/security`, `/usage`, `/security/integrity`, migrations `0033`, `0036`; screens under `frontend/app/(internal)/admin/audit`, `/security`, `/usage` | the TODO line is still `[~]` but both named seams closed on 2026-09-08 |
| XA-05 | Tamper evidence and retention | Must Have | audit-and-analytics | built | migration `0011_integrity.sql`, `GET /v1/admin/integrity/status`, `/digests`, `POST /v1/admin/integrity/verify` | |

## Partial

| id | title | priority | module | status | evidence | what is missing, and where |
|---|---|---|---|---|---|---|
| TM-16 | Bulk actions | Nice to Have | ticket-management | partial | `frontend/app/(internal)/tickets/page.tsx` (`assignSelected`, `watchSelected`), `frontend/components/xms/selection-bar.tsx` | no server bulk route: the browser loops one call per ticket, so a partial failure is silent and there is no bulk transition, bulk comment or bulk group move. **backend + frontend** |
| TM-19 | CMDB / lightweight asset register | Nice to Have | knowledge-base | partial | `acct.configuration_items` in migration `0007_knowledge.sql`; read by `change-windows.module.ts` (`conflictsOnItem`) and `knowledge.repository.ts`; `acct.tickets.configuration_item_id` in migration `0004` | the table and the two readers exist; no CRUD route in `backend/test/golden/routes.json`, no screen, and no way to attach a configuration item to a ticket from the UI. **backend + frontend** |
| TB-15 | Multi-currency support | Nice to Have | time-and-budget | partial | `currency char(3) not null default 'USD'` in migrations `0004`, `0013`, `0016` | column only: no rate table, no conversion in `backend/src/domain/time/billing.ts`, no per-account currency setting and no cross-currency rollup in reporting. **backend, then frontend display** |
| EM-09 | Priority detection from email content | Nice to Have | ai-functionality | partial | `prioritise` builder in `backend/src/modules/ai/capabilities.ts`, worker intake at `suggestion.service.ts:142` | the capability runs on every ticket including email-created ones, but nothing reads the message's own urgency cues or header priority, so there is no email-specific signal. **backend** |
| DR-08 | Automated QBR deck generation | Nice to Have | dashboard-and-reporting | partial | `pack_type in ('wsr','qbr','custom')` in migration `0009_reporting.sql` and `schedules.module.ts:101` | vocabulary only: the seeded template and every render path in `reporting.service.ts` are `wsr`. **backend + frontend** |
| DM-01 | Historical import from ServiceNow CSM | Must Have | data-migration | partial | migration `0014_migration.sql`, `/v1/migration/batches`, `frontend/app/(internal)/admin/migration/` | `migration.service.ts` loads `object_kind: 'case'` only, against the in-process stand-in. **backend + needs client facts** |
| DM-03 | Reconciliation report post-migration | Must Have | data-migration | partial | `GET /v1/migration/reconciliation`, `POST /v1/migration/reconciliation/:id/sign-off` | the `hours_by_contract_period` and `balance_by_contract_period` reconciliation kinds have no importer feeding them, so only case counts reconcile. **backend** |
| SN-01 | Bidirectional sync with configurable field mapping | Must Have | servicenow-integration | partial | migrations `0030`, `0031`, `GET /v1/connectors/:instanceId/outbound`, the Outbound tab on the connector record | green against the stand-in only; the webhook receiver `POST /webhooks/servicenow/{instanceId}`, outbound record creation (`create_outbound`) and the SQS FIFO transport are open. **backend + needs client facts** |
| AI-01 | Auto-categorisation and priority suggestion | Must Have | ai-functionality | partial | `capabilities.ts` classify and prioritise, `POST /v1/axel/suggest`, `frontend/components/tickets/suggestions-strip.tsx` | the AI settings, accuracy and defaults screens are held, so thresholds and the kill switch have no operator surface. **frontend (held)** |
| AI-02 | Duplicate detection with merge suggestion | Must Have | ai-functionality | partial | `capabilities.ts` duplicate, `suggestion.service.ts` merge_into apply | trigram candidates stand in until the harness exposes an embeddings endpoint. **backend + harness** |
| AI-03 | Long-thread summarisation | Must Have | ai-functionality | partial | `capabilities.ts` summarise, `POST /v1/axel/turns` with the SSE relay | the Axel panel that would show it is held; the slice, parser and `useAxelTurn` hook are on frontend main. **frontend (held)** |
| AI-04 | Draft response generation | Must Have | ai-functionality | partial | `capabilities.ts` draft_reply, the proposal shape in `axel.service.ts` | no web surface at all: the panel and the suggestion cards for it are held. **frontend (held)** |
| AI-09 | Confidence thresholds with human fallback | Must Have | ai-functionality | partial | `GET`/`PUT /v1/axel/config/defaults`, withheld reasons in `backend/src/contracts/ai.ts` | no defaults screen, so thresholds can only be moved through the API. **frontend (held)** |
| AI-11 | Per-client AI disable switch | Must Have | ai-functionality | partial | `GET`/`PUT /v1/accounts/:id/ai-settings` with the disable cascade | no AI settings screen on the account record. **frontend (held)** |
| AI-12 | No training on client data; DPA and residency compliance | Must Have | ai-functionality | partial | the DPA and residency gates and redaction before egress in `backend/src/modules/ai/` | the gates have no operator surface, so an administrator cannot see or set them. **frontend (held)** |
| XA-04 | Security assurance and audit readiness | Must Have | audit-and-analytics | partial | migration `0021_archive.sql`, `GET /v1/admin/integrity/archives`, the hourly archive job | Parquet, Glue and partition detachment wait for the AWS environment. **infra** |

## Not built

| id | title | priority | module | status | evidence | what is missing, and where |
|---|---|---|---|---|---|---|
| TM-17 | Ticket templates | Nice to Have | knowledge-base | not built | none found | the per-account portal request forms (migration `0040_ticket_forms.sql`, `/v1/accounts/:id/forms`) are intake schemas, not desk-side templates that prefill a new ticket. **backend + frontend** |
| TB-16 | Profitability view per account | Nice to Have | time-and-budget | not built | none found | needs a cost rate beside the bill rate on the roster and a margin measure in reporting. **backend + frontend** |
| CAP-09 | On-call / shift rota | Nice to Have | capacity-and-allocation | not built | none found | the roster has PTO, calendars and FTE (migrations `0013`, `0018`) but no shift or rota entity. **backend + frontend** |
| CAP-10 | Scenario planning | Nice to Have | capacity-and-allocation | not built | none found | forward demand (migration `0020`) carries one probability-weighted overlay, not saved what-if scenarios. **backend + frontend** |
| DR-09 | Customer health score | Nice to Have | dashboard-and-reporting | not built | none found | CSAT (migration `0023`), SLA attainment and burn are all already measured; the score is a composition over them. **backend + frontend** |
| DR-10 | Custom report builder | Nice to Have | dashboard-and-reporting | not built | none found | the audit saved-query grammar (`op.audit_saved_queries`, migration `0036`) is the nearest pattern to generalize. **backend + frontend** |
| AI-05 | Weekly report narrative generation | Must Have | ai-functionality | not built | `backend/src/modules/ai/capabilities.ts:147` `wsr_narrative: undefined` | a pack stays `templated` or `edited`; `axel` is an unreachable narrative source until the builder exists. **backend + harness** |
| AI-06 | Time entry assistance | Must Have | ai-functionality | not built | `capabilities.ts:148` `time_entry: undefined` | **backend + harness** |
| AI-14 | Budget burn anomaly detection | Must Have | ai-functionality | not built | `capabilities.ts:149` `burn_anomaly: undefined` | the `contract_period` AI target kind already exists in `backend/src/contracts/ai.ts`. **backend + harness** |
| AI-15 | Escalation risk and sentiment detection | Nice to Have | ai-functionality | not built | none found | needs a new capability key in `src/contracts/ai.ts` plus a builder. **backend + frontend + harness** |
| AI-16 | Effort estimation from historical similar work | Nice to Have | ai-functionality | not built | none found | depends on the embeddings endpoint. **backend + harness** |
| AI-17 | Allocation suggestions | Nice to Have | ai-functionality | not built | none found | **backend + harness** |
| AI-18 | Auto-resolution of allowlisted request types | Nice to Have | knowledge-base | not built | none found | **backend + frontend + harness** |
| AI-19 | Agentic triage and routing without human review | Nice to Have | ai-functionality | not built | none found | sits against the AI-08 human-in-the-loop default until an explicit allowlist exists. **backend + harness** |
| AI-20 | Natural language query over reporting data | Nice to Have | ai-functionality | not built | none found | `queue_query` is already a declared AI target kind with no capability behind it. **backend + frontend + harness** |
| INT-04 | Slack / Teams integration | Nice to Have | integrations | not built | none found | the webhook subscription machinery (migration `0024_webhooks.sql`) is the delivery seam to build on. **backend** |
| INT-05 | Calendar integration | Nice to Have | integrations | not built | none found | push change windows and scheduled work to Outlook; the change window records now exist (migration `0038`). Not to be confused with the TODO's "(INT-05)" label on the webhook work. **backend** |
| DM-02 | Contract and budget history import | Must Have | data-migration | not built | the `object_kind` vocabulary names `contract` and `contract_period_balance` in migration `0014`, and `source_kind` names `finance_workbook` | no extractor and no loader for either; `migration.service.ts` handles `case` only. **backend + needs client facts** |
| DM-04 | Parallel run period | Must Have | data-migration | not built | none found | a cutover procedure over a real environment, not application code. **infra + needs client facts** |
| INT-01 | Identity provider integration (internal) | Must Have | accounts-and-administration | not built | `frontend/app/(internal)/dev/sign-in/page.tsx` only; the guard accepts a Clerk JWT but no application is provisioned | the dedicated XMS Clerk application with the THG IdP enterprise connection. **Clerk provisioning + infra** |
| CP-01 | SSO via SAML / OIDC | Must Have | client-portal | not built | none found | per-account portal SSO with fallback; blocked on the Clerk licensing and SAML topology decision. **Clerk provisioning + infra** |

## Held

| id | title | priority | module | status | evidence | what is missing, and where |
|---|---|---|---|---|---|---|
| (cross-cutting) | Axel panel, suggestion cards, AI settings, accuracy and defaults screens | n/a | ai-functionality | held | the AI slice, SSE parser and `useAxelTurn` hook are on frontend main (`bd80d4f`); `frontend/components/axel/suggestion-card.tsx` and `frontend/components/tickets/suggestions-strip.tsx` exist; the panel draft is uncommitted | held 2026-09-07 by the product owner, foundation first. Covers the frontend half of AI-01, AI-03, AI-04, AI-09, AI-11, AI-12. **frontend** |
| (cross-cutting) | `xms_mcp` module in `aix-mcp` | n/a | ai-functionality | held | draft stashed on `feature/xms-mcp` in `aix-mcp` | held 2026-09-07, not needed yet. **aix-mcp** |

## Deferred

| id | title | priority | module | status | evidence | what is missing, and where |
|---|---|---|---|---|---|---|
| (cross-cutting) | Terraform, ECS, RDS, S3 with GuardDuty, SQS, SES, Secrets Manager, ALB and WAF | n/a | platform | deferred | none found; no `infra/` Terraform in the tree | deferred by the product owner. Gates the infra halves of TM-14, EM-01, XA-04, XA-05 and DM-04. **infra** |
| (cross-cutting) | Azure DevOps pipeline with the gate stage | n/a | platform | deferred | none found | **infra** |
| (cross-cutting) | OpenTelemetry through ADOT, CloudWatch alarms, ZAP baseline | n/a | platform | deferred | pino logging and `/readyz` are in place | waits for deployed hosts. **infra** |

---

## Counts by status

| status | rows |
|---|---|
| built | 18 |
| partial | 16 |
| not built | 21 |
| held | 2 cross-cutting entries |
| deferred | 3 cross-cutting entries |

Fifty-five register rows are listed. The other sixty sit under clean `[x]` lines in TODO.md and were not re-derived.

---

## Buildable now, ranked

These are the not-built and partial rows that need no infra, no Clerk provisioning, no client facts and none of the held Axel or MCP work. Each is one briefable chunk.

1. **TM-16 bulk actions** (backend + frontend). A `POST /v1/tickets/bulk` taking a set of keys and one operation (assign, group, watch, transition, comment), applied per ticket inside one transaction with a per-key outcome, and the selection bar rewired to it so a partial failure is reported rather than swallowed.
2. **TM-19 configuration items** (backend + frontend). CRUD routes over `acct.configuration_items` under the admin permissions, the CI picker on the ticket record and the New ticket form, and the CI named in the change-conflict refusal that already reads the table.
3. **DR-08 QBR pack** (backend + frontend). A second pack template beside `wsr` over the existing `PackDocument` description, quarter-shaped period math, both renditions, and `qbr` offered on the schedule form.
4. **DR-09 customer health score** (backend + frontend). A composed measure over SLA attainment, backlog age, burn against contract and the CSAT averages that already exist, as a tile on the account dashboard with the drill-through to each component.
5. **TB-16 profitability per account** (backend + frontend). A cost rate beside the bill rate on the roster person, frozen on the time entry the way the bill rate already is, and a margin row on the Budget tab.
6. **INT-05 calendar integration** (backend). An authenticated ICS feed per account and per person over the change windows migration `0038` created, plus scheduled work from the allocations grid.
7. **TB-15 multi-currency** (backend, then display). A currency on the account, a rate table with an effective date, the rate frozen on the entry beside the amount, and reporting stating which currency each figure is in.
8. **INT-04 Slack / Teams** (backend). A connector type over the existing webhook subscription delivery (migration `0024`) that posts the public event catalog to an incoming webhook, with the same signing, retry and pause behaviour.
9. **DR-10 custom report builder** (backend + frontend). Generalize the audit saved-query grammar (`op.audit_saved_queries`, migration `0036`) over the reporting measures, saved and shared the same way.
10. **CAP-09 on-call rota** (backend + frontend). A shift entity per group over a date range with the roster's calendar rules, surfaced on Dispatch and used by the assignment-time capacity check.
11. **CAP-10 scenario planning** (backend + frontend). Named, saved variants of the demand and allocation set with a side-by-side month view, over migrations `0018` and `0020`.
12. **DM-03 reconciliation completion** (backend). Feed the `hours_by_contract_period` and `balance_by_contract_period` kinds from a workbook source so the report reconciles more than case counts; the reconciliation routes already exist.

Also open and not a register row: the **webhook subscription admin screen** (the API clients screen at `frontend/app/(internal)/admin/api-clients/page.tsx` says outright that subscriptions are not registered there, so there is no UI for them at all). Small, backend-complete, frontend only.
