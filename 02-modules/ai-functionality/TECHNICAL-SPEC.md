# Technical Spec: Axel AI Functionality

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md) (harness contract, adapter faces, MCP server, requested harness changes; not repeated here), [Security & Tenancy §8](../../01-architecture/SECURITY-AND-TENANCY.md), [Data Model](../../01-architecture/DATA-MODEL.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Solution Knowledge Base](../knowledge-base/TECHNICAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/TECHNICAL-SPEC.md), [Test Strategy](../../03-delivery/TEST-STRATEGY.md)
**Requirements covered:** AI-01 to AI-06, AI-08 to AI-16, AI-18 to AI-20, EM-09
**Repos affected:** `backend` Axel adapter module, `backend/src/worker` `axel.batch` handler and jobs, `frontend` panel and surfaces, `aix-mcp/app/modules/xms_mcp`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`); `os-aixelerator-studio` (inline XMS agents, embeddings endpoint, headless route, thread deletion) and `aix-mcp` (`current_bearer` context variable) per [AI Integration §8](../../01-architecture/AI-INTEGRATION.md)

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Harness contract | `os-aixelerator-studio` `app/modules/ai_execution/XT_AXEL_API.md`; `POST /api/auth/session` (`app/auth/session_router.py:69`); SSE `POST /api/ai-execution/chat/stream/{agent_id}` (`chat_stream_router.py:819`); request schema `extra="forbid"` (`schemas/chat.py:13`); `solution:` sentinel (`chat_stream_router.py:70`); headless `runtime/headless.py` (verified 2026-09-04) | Fixed in [AI Integration §2](../../01-architecture/AI-INTEGRATION.md); the adapter implements against it |
| Inline agent skeleton | `app/modules/ai_execution/services/xt_axel_agent.py` (`enabledToolboxes=[]`, `enabledTools=[render_pptx_preview, render_document_pages_as_vision]`, Sonnet 5, effort medium), registry `app/modules/agents/catalog/registry.py` `INLINE_AGENTS` (verified 2026-09-04) | The four XMS agents are copies of this skeleton with the XMS MCP server enabled |
| Models | `app/modules/agent_harness/compile/model_providers.py` (`BEDROCK_SONNET_5_MODEL_ID`, `BEDROCK_HAIKU_4_5_MODEL_ID`) (verified 2026-09-04) | Classify and duplicate on Haiku 4.5; summarise, draft, narrative on Sonnet 5 |
| MCP client and caller token | `app/modules/aix_mcp/mcp_session_manager.py:106`, `:113` (`useCallerToken` mints an 8-hour session token), `runtime/mcp_setup.py:65` (MCP skipped without `opportunity_id` and `tenant_slug`) (verified 2026-09-04) | XMS MCP server registration; `opportunity_id = solution:xms` on every turn |
| MCP scaffolding | `aix-mcp/app/mcp_common/*`; `AuthenticatedUser` does not retain the raw token (`mcp_common/auth.py`) (verified 2026-09-04) | `aix-mcp/app/modules/xms_mcp` and the `current_bearer` change |
| Embeddings | `app/modules/ai_core/embedding_service.py` Titan v2 1024 dimensions, no HTTP endpoint (verified 2026-09-04) | Knowledge module owns `acct.embeddings`; this module owns the switch policy on it |
| No per-tenant kill switch, no PII guard in the harness | `app/modules/agent_harness/secrets_guard.py` is secrets-only; no `ai_disabled` in `app/` (verified 2026-09-04) | AI-11 and redaction are XMS properties |
| SSE parsing rules | `web-ui/redux/services/discoveryApi.ts:842-1310`; the `agents` Clerk template `useDiscoveryChat.ts:127` (verified 2026-09-04) | `frontend/lib/axel-client` streaming loop |
| Panel registration precedent | `web-ui/store/axelChatStore.ts` (`setPageAgent`), `AxelSplitPanel.tsx` width persistence and invalidation on close (verified 2026-09-04) | XMS panel store copies the shape, not the component |
| Audit events | `acct.audit_events` per [Data Model §5](../../01-architecture/DATA-MODEL.md) with `actor_kind = ai` | AI-10 linkage |
| Scheduler pattern | studio `routine_engine.py` `SKIP LOCKED` claiming (verified 2026-09-04) | Time assistant digest and burn anomaly jobs |
| Connector framework | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) `axel.batch` queue with DLQ | Batch face transport |

Cross-repo dependency and order: harness changes (items 1, 5, 6 in Phase 2; 2, 3, 4 in Phase 3) deploy before the XMS release that uses them; app-api catalog row for the XMS MCP server seeded per environment before Phase 2.

## 2. Data model

### 2.1 `acct.ai_settings` (mutable, RLS; one row per account)

| Column | Type | Notes |
|---|---|---|
| account_id | uuid pk | |
| enabled | boolean not null default false | The master switch (AI-11) |
| dpa_reference | text null | Required non-null to enable |
| residency_region | text not null default 'us' | Copied from the account; enabling requires a harness region match (AI-12) |
| redaction_profile | text not null default 'standard' | check in (`standard`, `strict`) |
| draft_tone | text not null default 'plain' | check in (`plain`, `formal`) |
| capabilities | jsonb not null | `{ classify: {enabled, threshold, auto_apply, auto_min}, prioritise: {...}, ... }` validated against `backend/src/contracts` capability keys; missing keys inherit operator defaults |
| auto_apply_approval_ref | text null | Required when any `auto_apply` is true |
| version, created_at, updated_at | | |

### 2.2 `acct.ai_suggestions` (append-only, RLS)

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| account_id | uuid not null | |
| capability | text not null | check against the catalog |
| target_kind | text not null | check in (`ticket`, `report_run`, `person_day`, `contract_period`, `queue_query`) |
| target_id | text not null | Ticket id, run id, `<user>:<date>`, contract period id |
| status_initial | text not null | check in (`offered`, `withheld`) |
| withheld_reason | text null | check in (`below_threshold`, `switch_off`, `capability_off`, `residency`, `redaction_refused`, `unavailable`, `no_content`, `schema_error`) |
| payload | jsonb not null | Capability-specific proposal (§2.5) |
| confidence | numeric(4,3) null | Null for free-text capabilities |
| agent_id | text not null | `xms-triage`, `xms-desk-assistant`, `xms-narrative`, `xms-time-assistant` |
| prompt_version | text not null | Constant exported by the inline agent |
| model_id | text not null | From the harness |
| thread_id | text null | Harness thread when interactive |
| harness_build | text null | From `stream_started` |
| latency_ms | integer null | |
| expires_at | timestamptz null | Per capability life |
| requested_by | text not null | actor id (user or job) |
| created_at | timestamptz not null default now() | |

### 2.3 `acct.ai_suggestion_decisions` (append-only, RLS)

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| account_id | uuid not null | |
| suggestion_id | uuid not null | references `acct.ai_suggestions` |
| decision | text not null | check in (`accepted`, `edited_accepted`, `rejected`, `expired`, `auto_applied`) |
| decided_by_kind | text not null | `user`, `system` |
| decided_by_id | text not null | |
| applied_payload | jsonb null | What was actually applied (differs from `payload` when edited) |
| edit_distance | integer null | For text capabilities |
| reject_reason | text null | check in (`wrong`, `unnecessary`, `already_done`, `unclear`, `other`) |
| audit_event_id | uuid null | The AI action event written when applied (AI-10) |
| policy_version | text null | For auto-applied |
| created_at | timestamptz not null default now() | |

### 2.4 `acct.ai_feedback` (append-only, RLS)

Free-form feedback beyond the decision: `suggestion_id`, `rating` (1 to 5), `comment`, `author_id`, `created_at`. Optional; the decision table is the primary accuracy source (AI-13).

```sql
create index ix_acct_ai_suggestions_target on acct.ai_suggestions (account_id, target_kind, target_id, created_at desc);
create index ix_acct_ai_suggestions_accuracy on acct.ai_suggestions (account_id, capability, created_at);
create unique index ux_acct_ai_decisions_one_final
  on acct.ai_suggestion_decisions (suggestion_id) where decision <> 'expired';
-- RLS: standard operator and worker policies; the portal role has NO grant on any ai_* table
alter table acct.ai_suggestions enable row level security;
alter table acct.ai_suggestions force row level security;
create policy ai_suggestions_operator on acct.ai_suggestions for all to xms_app, xms_worker
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[])
              and exists (select 1 from acct.ai_settings s where s.account_id = ai_suggestions.account_id
                          and (s.enabled or ai_suggestions.status_initial = 'withheld')));
-- The AI switch enforced at the data layer (AI-11): an offered suggestion cannot be inserted for a
-- disabled account; withheld rows are allowed so the outage and switch history remain measurable.
create policy embeddings_switch on acct.embeddings for insert to xms_app, xms_worker
  with check (exists (select 1 from acct.ai_settings s where s.account_id = embeddings.account_id and s.enabled));
create trigger trg_ai_settings_disable after update of enabled on acct.ai_settings
  for each row when (old.enabled and not new.enabled)
  execute function acct.ai_disable_cascade();  -- deletes embeddings, expires open suggestions, writes an audit event
create trigger trg_ai_suggestions_append_only before update or delete on acct.ai_suggestions
  for each row execute function sys.raise_append_only();
```

### 2.5 Suggestion payloads (validated in `backend/src/contracts`)

| Capability | Payload |
|---|---|
| classify | `{category, ticket_type, ci_ids[], reasons: {field: text}}` plus per-field confidence |
| prioritise | `{impact, urgency, priority, reason}` |
| duplicate | `{candidates: [{ticket_id, similarity, reason}], merge_into: ticket_id}` |
| summarise | `{situation, done, waiting_on, next_step, risks, sources: {comments, work_notes, events}}` |
| draft_reply | `{text, citations: [{article_version_id}], tone}` |
| wsr_narrative | `{sections: [{key, headline, text}]}` |
| time_entry | `{entries: [{ticket_id, minutes, activity_type, description, evidence: [event ids]}]}` |
| burn_anomaly | `{direction, magnitude_pct, likely_cause, evidence}` |

### 2.6 Suggestion state machine

```
offered ──accept──────────▶ accepted        ──▶ audit event (actor ai, confirmed_by user)
offered ──edit+accept─────▶ edited_accepted ──▶ audit event (applied_payload)
offered ──reject──────────▶ rejected
offered ──expiry job──────▶ expired
offered ──policy (P4)─────▶ auto_applied    ──▶ audit event (policy_version)
withheld                    (terminal; measured only)
```

Guards: a decision is accepted only while the target is in a state the capability allows (intake chips only before first assignment; drafts only while the composer is open); a second final decision is rejected by the unique index; applying a decision and writing the audit event happen in one transaction in the domain service that owns the target (ticket service for classify, prioritise, duplicate; time service for time entries; report service for the narrative).

### 2.7 AI switch policy (AI-11), in order

1. `acct.ai_settings.enabled` must be true, `dpa_reference` non-null, residency satisfied.
2. Capability enabled for the account and globally (operator kill switch in `op.config_defaults` kind `ai`).
3. Caller holds `ai:use` (interactive) or is the service principal (batch).
4. Redaction pass succeeds (a refusal, for example an unmaskable credential blob, withholds).
5. Only then does the adapter call the harness. Withheld outcomes are recorded before returning.

The database policies in §2.4 are the backstop: even a bypassed adapter cannot insert an offered suggestion or an embedding for a disabled account, and disabling cascades.

## 3. Producers / core logic

| Logic | Where | Notes |
|---|---|---|
| Axel adapter (three faces) | `backend/axel/` (`axel-adapter.service.ts`, `session-token.service.ts`, `redaction.service.ts`, `stream-relay.service.ts`, `suggestion.service.ts`) | Per [AI Integration §3](../../01-architecture/AI-INTEGRATION.md); the single egress |
| Capability drivers | `backend/axel/capabilities/*.ts`, one per capability: builds the request from XMS data, names the agent, parses the structured result into a payload, sets `expires_at` | Structured results arrive as the agent's final fenced JSON block or through `propose_*` MCP tools; both land in `suggestion.service.ts` |
| Intake trigger | Ticket service emits an outbox event `ticket.created` and `ticket.text_changed`; the worker's `axel.batch` handler runs classify, prioritise and duplicate as single-shot calls, so intake never waits on the harness | Results appear within seconds by polling the ticket record |
| Summarise on reassignment | Ticket service transition hook emits `ticket.reassigned`; worker runs summarise and attaches the payload to the handover notification | |
| Draft reply and on-demand summarise | Interactive face from the composer and record buttons | Synchronous SSE relay |
| Narrative | Report generator calls the batch face with frozen measures ([Dashboards & Report Packs §5.2](../dashboard-and-reporting/TECHNICAL-SPEC.md)) | Suggestion accepted on report approval |
| Time assistant | `backend/src/worker/jobs/time-assistant.job.ts` at 16:00 person-local (claimed with `SKIP LOCKED` per person per day): computes unlogged blocks from the person calendar minus entries, gathers the person's events per ticket, calls the batch face for descriptions, creates one suggestion per person-day; inline "Tidy" is a single-shot call | Nudge notification through `acct.notifications` |
| Burn anomaly | `backend/src/worker/jobs/burn-anomaly.job.ts` nightly per open contract period: deterministic detector in `backend/src/domain` (deviation from linear expectation over 15 percent for three days) decides whether to ask Axel for the likely cause; the suggestion carries both | Detector is testable without the harness |
| Expiry | `backend/src/worker/jobs/suggestion-expiry.job.ts` every 5 minutes | Writes `expired` decisions |
| Accuracy | `backend/axel/accuracy.service.ts` reads suggestions and decisions; threshold what-if computed from stored confidences | |
| XMS agents (harness) | `app/modules/ai_execution/services/xms_triage_agent.py`, `xms_desk_assistant_agent.py`, `xms_narrative_agent.py`, `xms_time_assistant_agent.py`, each exporting `PROMPT_VERSION` | Copies of the `xt_axel` skeleton; `enabledToolboxes=[]`; XMS MCP server enabled |
| XMS MCP tools | `aix-mcp/app/modules/xms_mcp/server.py` per [AI Integration §4](../../01-architecture/AI-INTEGRATION.md) | |

Agent responsibilities and tools:

| Agent | Model | Responsibility | MCP tools |
|---|---|---|---|
| xms-triage | Haiku 4.5 | Classify, prioritise, duplicate, EM-09; returns one JSON block | `get_ticket`, `list_tickets` (recent, same account), `find_similar_tickets`, `get_configuration_items`, `propose_classification`, `propose_priority`, `propose_duplicate` |
| xms-desk-assistant | Sonnet 5 | Panel conversation, summarise, draft reply, similar solutions, queue questions | `get_ticket`, `get_ticket_thread`, `list_tickets`, `search_solutions`, `get_article`, `find_similar_tickets`, `propose_summary`, `propose_reply`, `add_work_note`, `create_article_draft` |
| xms-narrative | Sonnet 5 | WSR and QBR narrative from frozen measures | `get_period_metrics`, `get_contract_position`, `list_tickets` (notable), `propose_narrative` |
| xms-time-assistant | Haiku 4.5 | Time entry proposals and description tidying; burn anomaly explanation | `get_unlogged_time`, `get_ticket_thread`, `get_contract_position`, `propose_time_entry`, `propose_anomaly` |

Redaction rules (`redaction.service.ts`, applied to every outbound payload): attachments replaced by name, type, size and XMS-extracted text; credential-shaped strings (`backend/src/domain/redaction` patterns for keys, tokens, passwords in `key=value` and URL forms, card and IBAN numbers) replaced by `[redacted:<kind>]`; under `strict`, portal user emails and names replaced by role labels (`[requester]`, `[approver]`) with a reversible map kept only in the adapter for rendering the reply; work notes included only for internal callers and never in drafts or narratives; a payload that still matches a hard-block pattern after masking withholds with `redaction_refused`.

## 4. API routes

| Method | Path | Permission | Purpose |
|---|---|---|---|
| POST | `/axel/turns` | `ai:use` | Interactive turn (SSE relay); body: agent, message, binding (`ticket`, `queue`, `report_run`), thread_id |
| POST | `/axel/turns/{stream_id}/cancel` | `ai:use` | Cancel relay to the harness |
| POST | `/axel/suggest` | `ai:use` | Single-shot: capability plus target; returns the suggestion or `withheld` |
| GET | `/axel/suggestions?target_kind=&target_id=` | `tickets:view` | Open suggestions for a record |
| POST | `/axel/suggestions/{id}/decisions` | route depends on capability: `tickets:work` for intake, `time:log` for time, `reports:review` for narrative | Accept, edit-accept, reject with payload |
| GET | `/axel/threads?ticket=` | `ai:use` | Thread ids per ticket for the panel |
| GET | `/accounts/{id}/ai-settings` | `ai:configure` | Read |
| PUT | `/accounts/{id}/ai-settings` | `ai:configure` | Update; validates residency and DPA; audit event |
| GET | `/axel/accuracy?account=&capability=&from=&to=&threshold=` | `ai:configure` | Metrics and what-if |
| GET | `/axel/config/defaults` | `admin:config` | Operator defaults and kill switches |
| PUT | `/axel/config/defaults` | `admin:config` | Update |

No portal route exists for any of these; the portal controller group has no AI endpoints.

## 5. Cross-cutting concerns

- **Harness identity and tokens**: per [AI Integration §5](../../01-architecture/AI-INTEGRATION.md); session tokens cached per user in the API process with a 7-hour refresh, service principal token for batch.
- **Origin header and sentinel**: every call sets `Origin: <AXEL_ORIGIN>` and `opportunity_id: solution:xms`; a contract test asserts both, because a missing Origin silently routes to prod and a missing sentinel disables MCP.
- **Request schema drift**: `extra="forbid"` on the harness request; the adapter builds requests from a typed contract in `backend/src/contracts/axel` and the pipeline runs a recorded-fixture test against the harness OpenAPI.
- **Cost attribution**: a `xms:<account_id>` tag on every request; the worker aggregates harness token usage per account from the `stream_started` and terminal frames into `rpt.portfolio_daily` measure `ai_cost`.
- **Isolation**: the MCP path runs as the user, so RLS applies; batch jobs bind `xms.account_ids` to the single account of the job; a suggestion can never reference a target in another account (FK-free target ids are validated against the bound account before insert).
- **Availability**: harness outage withholds with `unavailable` and never blocks a human path; batch retries with backoff then DLQ; the accuracy dashboard shows outage windows.
- **Retention**: suggestions and decisions are kept for the life of the account (they are audit-adjacent); harness threads follow the harness retention and are deleted at offboarding (harness change 4).

## 6. Web / client changes

- `frontend/lib/axel-client`: `streamAxelTurn({endpoint, getToken, request, onChunk, signal})` implementing the line-buffer carry, `:` heartbeat skip, untyped-frame-is-content rule, `stream_started` capture, cancel and detach; no dependency on XMS UI.
- `frontend/stores/axelPanelStore.ts`: `isOpen`, `binding`, `width` (persisted), `open(binding)`, `close()`; the panel mounts in the internal layout only.
- `frontend/components/axel/AxelPanel.tsx`: docked resizable panel, message list, tool activity strip, suggestion cards with accept, edit, reject; on close invalidates the RTK tags for the bound record.
- Ticket record: `AxelSuggestStrip` (intake chips, accept all), `DuplicateBanner`, `SummaryPanel`, `DraftReplyButton` in the public composer, `SimilarSolutionsRail` (knowledge module component consuming this module's decision endpoint).
- Queue: pending-AI marker on rows; "Ask Axel" toolbar action bound to the current filter.
- Time widget: `TidyDescriptionAction`; notifications: nudge item opening `TimeAssistantSheet` with proposed entries.
- Settings: `AccountAiSettingsPage` and the operator `AiDefaultsPage`; `AccuracyDashboardPage` with per-capability tables, calibration chart and threshold what-if slider.
- Audit views: "Show AI actions" filter using `actor_kind = ai`.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/ai-foundations` (`backend/src/db`, `backend/src/contracts`, `backend`) | Settings, suggestion tables, policies, cascade trigger, adapter skeleton with switch policy, redaction, session token exchange | Accounts & Administration; harness items 1, 5, 6 agreed |
| 2 | `feature/ai-mcp-server` (`aix-mcp/app/modules/xms_mcp`, `aix-mcp` change, app-api catalog row) | XMS MCP server with read tools and `propose_*`; harness token acceptance in the API guard | 1 |
| 3 | `feature/ai-triage` (`backend/src/worker`, `backend`, `frontend`, harness `xms-triage`) | Classify, prioritise, duplicate; intake surfaces; decisions; expiry job | 2, Ticket Management core |
| 4 | `feature/ai-desk-assistant` (`frontend/lib/axel-client`, `frontend`, harness `xms-desk-assistant`) | Panel, summarise, similar solutions rail wiring | 2, knowledge base embeddings |
| 5 | `feature/ai-accuracy` | Accuracy dashboard, threshold what-if, feedback | 3 |
| 6 | `feature/ai-draft-narrative` (harness `xms-narrative`) | Draft reply, WSR narrative | 4, Dashboards & Report Packs packs; harness item 3 |
| 7 | `feature/ai-time-assistant` (harness `xms-time-assistant`) | Digest job, inline tidy, burn anomaly | Time & Budget, Capacity calendars |
| 8 (Phase 4) | `feature/ai-auto-apply`, `feature/ai-nl-query`, `feature/ai-allocation`, `feature/ai-sentiment`, `feature/ai-effort`, `feature/ai-email-priority` | Nice to Have rows | 5 and the measurement plan |

Deploy order per release: harness (inline agents, changes), app-api catalog row, db migration, worker, api, web.

## 8. Testing & verification

- **Switch policy (Testcontainers):** with `enabled = false`, the adapter returns `withheld:switch_off` and the stubbed harness records zero calls; a direct insert of an offered suggestion for that account is rejected by the policy; an embedding insert is rejected; flipping enabled to false cascades (embeddings deleted, open suggestions expired, audit event written).
- **Threshold and withholding:** a classify result at 0.69 with threshold 0.70 is stored `withheld:below_threshold` and not returned by the open-suggestions route; at 0.70 it is offered.
- **Decision transitions:** accept after assignment on an intake chip is rejected (409); a second decision on the same suggestion is rejected by the unique index; edited-accept stores `applied_payload` and `edit_distance`; the audit event has `actor_kind = ai`, the suggestion id and the confirming user, in the same transaction as the ticket change (rollback test: a failing ticket update leaves no decision).
- **Redaction:** corpus of credential, card and IBAN strings masked; strict profile masks portal emails and restores them in the rendered draft; a hard-block string withholds with `redaction_refused`.
- **Harness contract (recorded fixtures):** request bodies contain exactly the allowed fields, `Origin`, and `opportunity_id = solution:xms`; SSE fixtures with split frames, heartbeats, untyped content, `tool_call`, `attachment`, `error` and `[DONE]` parse correctly; a 422 fixture yields `unavailable` and a logged body.
- **Jobs:** time assistant computes unlogged blocks correctly across a PTO day and a holiday; two worker instances claim one person-day once; burn anomaly detector flags a constructed series and does not flag a flat one; expiry job expires only past `expires_at`.
- **Accuracy:** acceptance rate and calibration computed from constructed suggestions and decisions; what-if at a higher threshold equals a recount over stored confidences.
- **MCP:** `aix-mcp/app/modules/xms_mcp` tests assert the bearer is forwarded unchanged and that every write tool except `add_work_note` and `create_article_draft` produces a suggestion, not a mutation.
- **HTTP:** every route rejects anonymous and garbage tokens; portal tokens get 403 on all `/axel/*`; `ai:use` required for turns; the route snapshot includes permissions.
- **Web (Vitest, Playwright):** streaming client unit tests on the fixture frames; e2e: create a ticket in the seed account, see chips, accept all, verify audit trail; disable AI for the account, reload, verify no AI element in the DOM.
- **Measurement plan gate:** enabling auto-apply for a capability whose trailing-8-week metrics fail the criteria is rejected with the failing criterion named.

## 9. Risks / notes

- **Harness request schema is strict.** Any harness release that adds a required field breaks the adapter; the contract test in the pipeline plus a pinned harness version tag per XMS release contain this.
- **Latency of intake suggestions.** Haiku on a short prompt with two MCP calls should return in a few seconds; if the harness's MCP session setup adds more, the triage agent falls back to inline context (ticket text in the message) and no tools.
- **Duplicate detection quality depends on embeddings coverage.** Until the harness embeddings endpoint exists the temporary direct-Titan exception applies (ADR-04); the knowledge module owns the backfill.
- **Over-trust of summaries.** Summaries are labelled with their sources and are never stored as comments; handover notifications link to the thread.
- **Accuracy dashboard as a gate.** The measurement plan's 200-suggestion floor means small accounts may never qualify for auto-apply; acceptable and intended.
- **Cost.** Triage on every ticket and every text edit could be noisy; the intake trigger debounces text edits to one call per five minutes per ticket and skips tickets already assigned.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
