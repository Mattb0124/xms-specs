# AI Integration: the Axel adapter

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Architecture](./ARCHITECTURE.md), [Security & Tenancy](./SECURITY-AND-TENANCY.md), [Axel AI Functionality](../02-modules/ai-functionality/FUNCTIONAL-SPEC.md), [Solution Knowledge Base](../02-modules/knowledge-base/TECHNICAL-SPEC.md), [AIX Pattern Reuse](./AIX-PATTERN-REUSE.md)
**Verified against:** `os-aixelerator-studio` branch `mb/xda` at `48abb08e` on 2026-09-04 (paths below are relative to that repo at `C:\Users\matt.brown\Documents\repos\OS-AIX\os-aixelerator-studio\`)

The AI harness (`os-aixelerator-studio`, called `os-ai-api` in conversation) is the only AI engine XMS uses. This document fixes the contract between XMS and the harness so that the [AI functionality module](../02-modules/ai-functionality/TECHNICAL-SPEC.md) only has to describe capabilities, prompts and the human-in-the-loop flow.

---

## 1. Principles

1. **One egress.** Every byte of account data that reaches a model passes through the XMS Axel adapter (a NestJS module in the XMS API plus a worker handler). Nothing else in XMS holds a harness credential or a Bedrock permission.
2. **The harness does the thinking; XMS keeps the data.** Ticket, contract and knowledge data live in XMS PostgreSQL. The harness receives what a turn needs (through tools that read XMS) and returns suggestions; it stores chat threads and produced files, nothing else about XMS.
3. **The harness is not changed for XMS except where listed in §8.** Everything else uses the published contract.
4. **Per-account switch and audit are XMS properties.** The harness has no per-tenant kill switch (verified: no `ai_disabled` or tenant model override exists in `app/`), so XMS enforces the switch before any call, and records every suggestion and action in its own audit trail.

## 2. The harness contract (verified in code)

| Piece | Where in the harness | What XMS uses |
|---|---|---|
| Published external-caller contract | `app/modules/ai_execution/XT_AXEL_API.md` | The document the adapter is implemented against; the sections below only restate what XMS depends on |
| Auth entry point | `app/auth/dependencies.py:106` `get_current_user` | Accepts a Clerk RS256 JWT or a studio HS256 session token; tenant comes from the `org_slug` claim only |
| Session token exchange | `POST /api/auth/session` (`app/auth/session_router.py:69`), signs with `SESSION_SECRET`, default 8 hours | XMS exchanges the user's short-lived Clerk token once per user and caches the session token, because Clerk tokens live about 60 seconds and agent turns run for minutes (`app/modules/aix_mcp/mcp_session_manager.py:87` documents the same problem) |
| SSE chat | `POST /api/ai-execution/chat/stream/{agent_id}` (`chat_stream_router.py:819`), request `AiExecutionChatRequest` with `extra="forbid"` (`schemas/chat.py:13`) | Interactive Axel panel and single-shot suggestions |
| Lifecycle | `/chat/stream/{stream_id}/cancel`, `/status`, `/detach` (`chat_stream_router.py:892, 933, 958`) | Cancel on panel close; detach on navigation |
| Durable threads without an AIX opportunity | `is_scope_only_opportunity()` (`chat_stream_router.py:70`) whitelists ids prefixed `solution:` | XMS sends `opportunity_id = "solution:xms"` so threads persist and the opportunity ownership probe (which hard-404s unknown ids) is skipped |
| Environment hint | `Origin`/`Referer` sniffing (`chat_stream_router.py:60`, `global_utils/api_base_resolver.py:29`); no header resolves to prod | XMS always sends an explicit `Origin` header |
| Headless run | `app/modules/agent_harness/runtime/headless.py` `execute_agent_headless(...)`; output is a real `ChatThread` plus `ChatAttachment` rows in S3 | Scheduled report narrative and batch suggestions |
| Scheduler | `ai_routines` table and `routine_engine.py` (Postgres row claiming, multi-instance safe) | Not used by XMS: XMS owns its schedules in its worker and calls the headless entry point, so schedule failures stay inside the product boundary |
| Inline agent definition | `app/modules/agents/catalog/registry.py` `INLINE_AGENTS`; canonical skeleton `app/modules/ai_execution/services/xt_axel_agent.py` (`enabledToolboxes=[]`, `enabledTools=[render_pptx_preview, render_document_pages_as_vision]`) | XMS agents are defined this way, versioned with the harness, no database rows |
| Tool surface for external data | MCP client `app/modules/aix_mcp/mcp_session_manager.py:106`; `useCallerToken` servers get a minted 8-hour session token; MCP is skipped silently without `opportunity_id` and `tenant_slug` (`runtime/mcp_setup.py:65`) | XMS exposes its data to Axel as an MCP server (§4) |
| Toolbox alternative | `app/modules/agent_toolkit/tools/aix_data_tools.py` pattern (`_headers()` forwards `get_token()`), presets gated by `tenants: [...]` in `toolbox/presets.py` | Fallback if MCP latency is unacceptable; not planned |
| Embeddings | `app/modules/ai_core/embedding_service.py` Titan `amazon.titan-embed-text-v2:0`, 1024 dimensions; no HTTP endpoint exposes it | XMS needs an embeddings endpoint (§8) |
| Models | `app/modules/agent_harness/compile/model_providers.py`; Sonnet 5 and Haiku 4.5 ids; region from `AWS_REGION` | Per-agent model choice; XMS agents default to Sonnet 5 for drafting and narrative, Haiku 4.5 for classification |
| Secrets guard | `app/modules/agent_harness/secrets_guard.py` | Scrubs harness secrets from tool output; not a PII guard. XMS applies its own redaction before sending (§6) |
| Tracing and cost | Phoenix via `PHOENIX_TRACING`, `runtime/turn_cost.py` | XMS passes a `xms:<account>` project tag in the request so cost per account can be reported |

## 3. Adapter shape (XMS side)

```mermaid
sequenceDiagram
    participant W as XMS Web
    participant A as XMS API: AxelAdapter
    participant S as Harness (studio)
    participant M as XMS MCP server
    participant D as XMS API: domain

    W->>A: POST /axel/turns {agent, message, ticket_id, thread_id?} (Clerk JWT)
    A->>A: account AI switch check; capability opt-in; redaction
    A->>S: POST /api/auth/session (once per user, cached 8h)
    A->>S: POST /api/ai-execution/chat/stream/{xms-agent} (session token, Origin, opportunity_id=solution:xms)
    S->>M: tools/call get_ticket, search_solutions ... (minted session token)
    M->>D: GET /tickets/{id} ... (as the user, RLS applied)
    D-->>M: account-scoped data
    M-->>S: tool result (prose)
    S-->>A: SSE frames (content, tool_call, attachment, thread_created, [DONE])
    A->>D: persist AISuggestion (offered) + audit event (actor=ai)
    A-->>W: SSE relay
    W->>D: accept / reject / edit (human decision)
    D->>D: apply change; audit event links suggestion -> action
```

The adapter has three faces:

| Face | Used by | Behaviour |
|---|---|---|
| Interactive turn (`/axel/turns`) | The Axel panel in XMS Web | Relays SSE; captures `stream_id` for cancel; persists `thread_id` on the ticket or the user's workspace; every structured suggestion the agent emits (through a `propose_*` MCP tool) becomes an AISuggestion row |
| Single-shot suggestion (`/axel/suggest`) | Ticket intake, duplicate check, summarise button | Same chat route with a fixed prompt and `session_id` per call, non-persisted thread; the adapter parses the final JSON block into an AISuggestion |
| Batch and scheduled (worker `axel.batch` queue) | Weekly narrative, unlogged-time nudges, burn anomaly scan | Calls `execute_agent_headless` through the harness's headless HTTP route (§8) with a service user's session token; output attachment keys are copied into XMS S3 |

Every face runs the same pre-flight: account `ai_enabled` is true, the capability is enabled for the account, the user (or the service principal) holds `ai:use`, and the redaction pass has run. If any check fails the adapter returns a typed `withheld` result and writes an audit event with the reason; nothing is sent.

## 4. XMS as an MCP server

Axel reads XMS data through a XMS-owned MCP server, not through a harness toolbox, because it keeps the data path inside the XMS boundary:

- `backend/src/mcp`, a third entrypoint beside the API and the worker, built to its own image and ECS service `xms-mcp` (ADR-19). It mounts the same `*CoreModule` providers the worker mounts, so a tool answers from the same domain code a route does, and reads through the same pool-per-role and session binding, so tenancy is the same data-layer property either way. It was a Python module in the house `aix-mcp` repository until 2026-09-12; ADR-19 records why it moved.
- Registered in app-api's `McpServer` catalog with `transport: streamable_http`, `useCallerToken: true`, `credentialScope: opportunity`, no credential schema; the XMS agents list it in `enabledMcpServers`.
- Auth: the harness mints an 8-hour HS256 session token for the calling user and sends it as the bearer. The MCP entrypoint validates it with the shared `SESSION_SECRET` and resolves the XMS principal through the same guard the API uses, rather than validating a signature and forwarding the token to a service that resolves it again.
- The guard maps `sub`/`email` to the XMS user and binds the session exactly as for a browser call (§5), so RLS applies unchanged. Axel can therefore never read more than the invoking user can, and that is enforced by the data layer rather than by the tool implementations.
- Tools return prose, are read-mostly, and every write tool is a `propose_*` that creates an AISuggestion rather than mutating the ticket. The only direct writes are `add_work_note` (internal, marked AI) and `create_article_draft` (status draft), both of which are still human-reviewed.
- The guard settles what the caller may see; it does not settle whether that account's data may travel towards a model at all, which is the adapter's question and is asked in `backend/src/mcp/gate.ts` before any tool runs. Every tool declares where its account comes from: from the ticket key it was given, or across the accounts the caller may see. The gate resolves `AiSettingsService.effective` for that account, which covers the account's own switch, the residency rule and the operator kill switch in one call, and a tool for an account with AI off does not run rather than running and having its answer discarded, so a write to such an account never reaches the database. A tool spanning accounts is narrowed to those with AI on through the `account_id` filter the service already takes; where a service takes no such filter the answer is confined on the way out instead, a row owned by an account with AI off dropped and a row with no account of its own (the global knowledge library) kept.
- Everything a tool returns is redacted at that account's own profile by `domain/ai/redaction`, the same function the Axel adapter uses, so there is one redaction policy rather than two. It is walked field by field rather than applied to the serialised whole, so the fields an agent reads as fields survive. Under `strict` the gate hands the ticket's requester over to be labelled by role, because `redact` only labels names it is given; a tool spanning accounts has no one ticket to take participants from and passes none, which is recorded in `GateScope`. A payload still carrying a hard block after masking (a private key) is withheld rather than sent.
- A refusal names the rule that caused it in the adapter's own vocabulary (`switch_off`, `residency`, `kill_switch`, `redaction_refused`) so an agent can tell "AI is off for this account" from "that ticket does not exist" and say which to the person. The operator kill switch closing the tools is what C-07 settled: it needs no mechanism of its own, though it propagates in up to 60 seconds because the AI defaults come through the 60-second `ConfigService` cache.

| Tool | Reads | Notes |
|---|---|---|
| `get_ticket`, `list_tickets`, `get_ticket_thread` | Ticket, comments, work notes, events, time | Work notes included only for internal callers |
| `search_solutions`, `get_article` | Knowledge base with account visibility | Vector plus full-text hybrid search served by XMS |
| `find_similar_tickets` | Resolved tickets with solution links | Embedding search inside the account plus global articles |
| `get_contract_position` | Consumption, forecast, thresholds | For burn anomaly and WSR narrative |
| `get_period_metrics` | Daily snapshots | For WSR narrative |
| `get_unlogged_time` | Roster calendar vs time entries | For time nudges |
| `propose_classification`, `propose_priority`, `propose_duplicate`, `propose_reply`, `propose_summary`, `propose_time_entry` | writes an AISuggestion | Human confirms in XMS Web |
| `add_work_note` | writes | Actor recorded as AI |
| `create_article_draft` | writes | Draft only |

## 5. Identity and authorisation

| Caller | Token | Verified by | Scope |
|---|---|---|---|
| XMS Web user | Clerk JWT (XMS Clerk application) | XMS API guard | User's account grants |
| XMS API calling the harness | Harness session token minted from the user's Clerk JWT | Harness `get_current_user` | Harness tenant `org_slug` = the XMS operator slug; XMS is one tenant in the harness |
| Harness calling XMS MCP | Harness-minted session token for the same user | The XMS guard, once, in the MCP entrypoint | The same user, same RLS |
| XMS worker batch | Session token minted for a XMS service principal user per account | Harness and XMS API | A service user with grants limited to the accounts in the batch |

The harness sees one tenant (the operator) for all XMS accounts. Account isolation is therefore entirely a XMS property: the harness never receives an account id as a trust boundary, only as a tool argument that XMS validates against the caller's grants. Threads in the harness are keyed by user and `solution:xms`; XMS stores which ticket a thread belongs to.

## 6. Data protection

- **Redaction before egress:** the adapter strips attachment binaries (Axel receives file names and XMS-extracted text only), masks credential-shaped strings and card or bank numbers, and replaces portal user email addresses with role labels for accounts that require it (an account setting).
- **No training, residency:** Amazon Bedrock does not use customer content to train models; the harness calls Bedrock in `us-east-1` with `us.` cross-region inference profiles that stay in the United States. For accounts whose DPA requires another region, the account setting `ai_region` is checked by the adapter and, until a matching harness region exists, the account's AI switch cannot be enabled (withheld with reason `residency`). The Axel owners must confirm availability, retention and no-training terms in writing (assessment appendix B).
- **Retention:** harness chat threads for XMS are subject to the harness's own retention; XMS persists the suggestion, the decision and a reference to the thread id, not the thread. When an account is offboarded, XMS requests thread deletion for `solution:xms` threads tagged with that account (a harness change, §8).
- **Prompt provenance:** every AISuggestion stores the agent id, the prompt version (a constant exported by each inline agent), the model id and the harness build tag from the `stream_started` frame, so a suggestion can be explained later.

## 7. Failure handling

| Failure | Behaviour |
|---|---|
| Harness unreachable or 5xx | Adapter returns `unavailable`; the UI shows "Axel is unavailable" and every human path still works; worker batch retries with backoff, then DLQ |
| Session token rejected (secret rotated) | Adapter re-exchanges once, then fails the turn |
| Harness 422 (schema drift, `extra="forbid"`) | Contract test catches it before deploy; at runtime the adapter logs the response body and returns `unavailable` |
| Tool call fails inside the turn | The agent is prompted to say so; the adapter marks the suggestion `withheld` if no structured proposal arrived |
| Low confidence | The `propose_*` payload carries a confidence; below the account threshold the suggestion is stored as `withheld` and routed to a human queue, never shown as a suggestion (AI-09) |
| Stream status lost after a harness deploy | `/status` is in-memory in the harness; the adapter treats `unknown` after 15 minutes as failed and lets the user retry |

## 8. Changes requested of the harness (small, listed for the Axel owners)

1. **Embeddings endpoint** `POST /api/ai-core/embeddings` wrapping `embedding_service.generate_batch_embeddings`, authenticated like every other route, so XMS can embed articles and ticket summaries through the harness rather than calling Bedrock directly. Until it exists, the XMS worker calls Bedrock Titan directly with the same model id under the same AWS account, recorded as a temporary exception in ADR-04.
2. **Headless run HTTP route** exposing `execute_agent_headless` for an authenticated service caller (today the function is in-process only, driven by `ai_routines`). Alternative if declined: XMS registers `ai_routines` rows through the existing router and reads results from `GET /chat/threads/{thread_id}/messages`; this keeps scheduling in the harness, which the roadmap prefers to avoid.
3. **Thread deletion by scope tag** for offboarding (`solution:xms` threads carrying an account tag).
4. **Inline agent registrations** for `xms-triage`, `xms-desk-assistant`, `xms-narrative`, `xms-time-assistant` in `INLINE_AGENTS`, each a copy of the `xt_axel` skeleton with `enabledToolboxes=[]` and the XMS MCP server enabled, prompts in `app/modules/ai_execution/services/xms_*_agent.py`.
5. **Confirmation of the `solution:` sentinel** as a supported contract (it is code today, not documented in `XT_AXEL_API.md`).

Items 4 and 5 are required for Phase 2; items 1 to 3 are required for Phase 3.

A sixth item stood here until 2026-09-12: a `current_bearer` context variable in `aix-mcp/app/mcp_common/auth_middleware.py`, so that a Python MCP module could forward the bearer it had validated. ADR-19 withdrew it. The MCP is a TypeScript entrypoint in `backend/` now and holds the token itself, so the request would be asking another team for work XMS no longer needs.

## 9. What XMS does not do

- Does not call Bedrock or any model provider directly (except the temporary embeddings exception above).
- Does not store harness credentials per account; there is one harness tenant.
- Does not let the harness write to XMS tables except through the MCP `propose_*`, `add_work_note` and `create_article_draft` tools, which go through the XMS API with the user's identity.
- Does not run autonomous actions in Phases 1 to 3. Auto-apply per capability is an account opt-in delivered in Phase 4 after measured accuracy (AI-18, AI-19).
