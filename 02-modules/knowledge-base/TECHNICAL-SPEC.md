# Technical Spec: Solution Knowledge Base

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Client Portal](../client-portal/TECHNICAL-SPEC.md), [Axel AI Functionality](../ai-functionality/TECHNICAL-SPEC.md)
**Requirements covered:** CP-08, AI-07, AI-17, TM-19, TM-17
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `aix-mcp/app/modules/xms_mcp`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Account isolation mechanics | [Data Model §3](../../01-architecture/DATA-MODEL.md): RLS forced, `xms.account_ids` / `xms.account_id` session variables, `acct.article_visible()` security-definer function | Every knowledge table is `acct.*`; article visibility extends the standard policy, never bypasses it |
| Ticket transition endpoint | [Ticket Management Technical Spec §3](../ticket-management/TECHNICAL-SPEC.md): `POST /v1/tickets/{id}/transitions` runs in one transaction | The close-discipline check (solution link or candidate) is a transition rule contributed by this module |
| Axel adapter faces | [AI Integration §3](../../01-architecture/AI-INTEGRATION.md): single-shot `/axel/suggest`, batch worker queue `axel.batch`, per-account switch pre-flight | Article drafting, generalization proposals and embedding generation all pass through it |
| XMS MCP tools | [AI Integration §4](../../01-architecture/AI-INTEGRATION.md): `search_solutions`, `get_article`, `find_similar_tickets`, `create_article_draft` | This module implements the API endpoints those tools call |
| Embedding model | Studio `app/modules/ai_core/embedding_service.py`, Titan `amazon.titan-embed-text-v2:0`, 1024 dimensions (verified 2026-09-04) | XMS uses the same model and dimension so a future move to the harness embeddings endpoint changes nothing in the table |
| Studio retrieval tools as shape reference | Studio `app/modules/tenant_vectorstore/agent/tools.py` (`search_tenant_corpus` reads tenant from a contextvar; prose result strings) (verified 2026-09-04) | The MCP tools return prose and never accept an account id from the model |
| POC resolution vocabulary and close discipline | `web-ui/components/aix-v3/xms/vocab.ts` (`RESOLUTION_CODES`), studio `xms_ticketing` migration 092 and `service.py` (verified 2026-09-04) | Ported per ADR-07 |
| POC record grammar | `web-ui/components/aix-v3/xms/TicketDrawer.tsx`, `QueueTab.tsx`, `XmsAdminPages.tsx` (verified 2026-09-04) | Article list and record screens reuse the same list plus record shape |
| Full-text and trigram search | [Data Model §1](../../01-architecture/DATA-MODEL.md) conventions: `tsvector` generated columns, `pg_trgm`, `ivfflat` cosine index | Hybrid retrieval |
| Outbox | [Integration Patterns §2](../../01-architecture/INTEGRATION-PATTERNS.md) | Article publish and ticket-solution events feed embeddings, notifications and snapshots |

Cross-module ordering: Ticket Management ships the transition endpoint and `acct.tickets` first; this module adds its tables and the transition rule in the same Phase 2 train; the AI features depend on the Axel adapter and the XMS MCP server from Axel AI Functionality.

## 2. Data model

All tables are `acct.*`, carry `account_id uuid not null references op.accounts(id)`, `created_at`, `updated_at`, `version` (mutable tables), and the standard RLS policies unless stated. Types follow [Data Model §1](../../01-architecture/DATA-MODEL.md).

### 2.1 `acct.solution_articles`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | Owning account (the account whose ticket created it, or the operator's global-articles account for Global) |
| `display_key` | text unique | `KB` + 6 digits from sequence `acct.article_key_seq` |
| `kind` | text | CHECK in (`solution`, `workaround`, `known_error`, `procedure`, `reference`) |
| `status` | text | CHECK in (`draft`, `in_review`, `published`, `retired`) |
| `is_global` | boolean | True only after generalization; `account_id` then points at the operator's `global` account row |
| `title` | text | |
| `categories` | text[] | From the ticket category vocabulary |
| `self_service` | text | CHECK in (`none`, `follow`, `request`, `auto`) |
| `effort_band` | text | CHECK in (`lt_15m`, `lt_1h`, `lt_4h`, `gt_4h`) |
| `owner_user_id`, `owner_name` | text | Opaque identity |
| `reviewer_user_id`, `reviewer_name` | text null | Set at publish |
| `published_version_id` | uuid null | FK `acct.article_versions.id`; the live version |
| `last_verified_at` | timestamptz null | Set at publish; curator can re-verify |
| `retired_at`, `retired_reason` | timestamptz null, text null | |
| `source_ticket_id` | uuid null | FK `acct.tickets.id` ON DELETE SET NULL |
| `generalized_from_id` | uuid null | FK self; set on the global copy |
| `search_vector` | tsvector generated | From title, categories and the published version's problem statement and symptoms (maintained by the publish transaction) |

### 2.2 `acct.article_versions` (append-only content)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | |
| `article_id` | uuid | FK `acct.solution_articles.id` ON DELETE CASCADE |
| `version_no` | integer | Unique per article; drafts use `version_no` of the next number with `status = draft` on the article |
| `problem_statement`, `environment`, `symptoms`, `cause`, `steps`, `verification`, `rollback`, `client_notes` | text | Markdown; `client_notes` is the only section the portal renders |
| `ci_snapshot` | jsonb | Names and types of linked configuration items at publish time |
| `authored_by`, `authored_name` | text | |
| `published_at` | timestamptz null | Null while draft |
| `ai_suggestion_id` | uuid null | FK `acct.ai_suggestions.id` when the text originated from an Axel draft |
| `created_at` | timestamptz | No `updated_at`: a version is edited only while it is the unpublished draft, by replacing the row through the service with the same `version_no` (the service deletes and re-inserts the draft; published rows are protected by the append-only trigger) |

### 2.3 `acct.article_visibility`

| Column | Type | Notes |
|---|---|---|
| `article_id` | uuid | FK CASCADE |
| `owner_account_id` | uuid | The article's owning account (the RLS key for this row) |
| `visible_account_id` | uuid | FK `op.accounts.id`; an account allowed to read the article |
| `granted_by`, `granted_at` | text, timestamptz | |

Primary key `(article_id, visible_account_id)`. Column `owner_account_id` is the `account_id` for RLS purposes and is named explicitly to avoid confusion with the visible account.

### 2.4 `acct.ticket_solutions` (the resolution record, append-only)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | |
| `ticket_id` | uuid | FK `acct.tickets.id` ON DELETE RESTRICT |
| `article_id` | uuid | FK `acct.solution_articles.id` ON DELETE RESTRICT |
| `article_version_id` | uuid | FK `acct.article_versions.id` ON DELETE RESTRICT; the exact version used |
| `outcome` | text | CHECK in (`resolved_by`, `partially_resolved_by`, `created_from`) |
| `actor_kind`, `actor_id`, `actor_name` | text | `ai` for Phase 4 runbook executions |
| `created_at` | timestamptz | |

### 2.5 `acct.article_feedback` (append-only)

| Column | Type | Notes |
|---|---|---|
| `id`, `account_id`, `article_id`, `article_version_id` | uuid | |
| `verdict` | text | CHECK in (`useful`, `not_useful`, `out_of_date`) |
| `comment` | text null | |
| `principal_kind` | text | `internal` or `portal` |
| `actor_id`, `actor_name` | text | |
| `context` | text | `ticket_rail`, `portal_search`, `portal_kb`, `article_record` |
| `context_ref` | text null | Ticket id or portal session id |
| `created_at` | timestamptz | |

### 2.6 `acct.configuration_items` and `acct.ci_links`

| Column | Type | Notes |
|---|---|---|
| `id`, `account_id` | uuid | |
| `ci_type` | text | CHECK in (`environment`, `application`, `module`, `integration`, `server`, `report`, `other`) |
| `name` | text | Unique per account with `ci_type` |
| `attributes` | jsonb | Free key-value (version, url, tier) |
| `owner_contact_id` | uuid null | FK `acct.contacts.id` |
| `external_ref` | text null | ServiceNow `sys_id` when imported |
| `status` | text | CHECK in (`active`, `retired`) |

`acct.ci_links`: `(account_id, ci_id, target_kind CHECK in ('ticket','article'), target_id, created_at)`, primary key `(ci_id, target_kind, target_id)`.

### 2.7 `acct.ticket_templates`

| Column | Type | Notes |
|---|---|---|
| `id`, `account_id` | uuid | Global templates live under the operator's global account row with `is_global = true` |
| `name`, `description` | text | |
| `ticket_type`, `category`, `title_pattern`, `description_checklist` | text | |
| `form_id` | uuid null | FK `acct.ticket_forms.id` |
| `assignment_group_id` | uuid null | Opaque reference to `op.assignment_groups` |
| `article_id`, `ci_id` | uuid null | |
| `is_global`, `client_visible`, `is_active` | boolean | |

### 2.8 `acct.embeddings`

| Column | Type | Notes |
|---|---|---|
| `id`, `account_id` | uuid | |
| `subject_kind` | text | CHECK in (`article_version`, `ticket_summary`) |
| `subject_id` | uuid | Article version id or ticket id |
| `model` | text | `amazon.titan-embed-text-v2:0` |
| `content_hash` | text | SHA-256 of the embedded text; skip regeneration when unchanged |
| `vector` | vector(1024) | |
| `created_at` | timestamptz | |

Unique `(subject_kind, subject_id, model)`.

### 2.9 Indexes, constraints and policies

```sql
create index ix_solution_articles_search on acct.solution_articles using gin (search_vector);
create index ix_solution_articles_published on acct.solution_articles (account_id, status) where status = 'published';
create index ix_solution_articles_key_trgm on acct.solution_articles using gin (display_key gin_trgm_ops);
create unique index ux_article_versions_no on acct.article_versions (article_id, version_no);
create index ix_ticket_solutions_ticket on acct.ticket_solutions (ticket_id);
create index ix_ticket_solutions_article on acct.ticket_solutions (article_id, created_at);
create index ix_article_feedback_article on acct.article_feedback (article_id, created_at);
create unique index ux_configuration_items_name on acct.configuration_items (account_id, ci_type, lower(name));
create index ix_embeddings_vector on acct.embeddings using ivfflat (vector vector_cosine_ops) with (lists = 100);
create unique index ux_embeddings_subject on acct.embeddings (subject_kind, subject_id, model);

-- Visibility: an article is readable when it is global, or owned by a granted account,
-- or explicitly shared with a granted account. SECURITY DEFINER so the visibility
-- table can be consulted without the caller holding a grant on the owner account.
create function acct.article_visible(p_article_id uuid) returns boolean
language sql stable security definer as $$
  select exists (
    select 1 from acct.solution_articles a
    where a.id = p_article_id
      and (a.is_global
           or a.account_id = any (current_setting('xms.account_ids', true)::uuid[])
           or exists (select 1 from acct.article_visibility v
                      where v.article_id = a.id
                        and v.visible_account_id = any (current_setting('xms.account_ids', true)::uuid[])))
  )
$$;

alter table acct.solution_articles enable row level security;
alter table acct.solution_articles force row level security;
create policy article_read_operator on acct.solution_articles for select to xms_app, xms_worker
  using (acct.article_visible(id));
create policy article_write_operator on acct.solution_articles for all to xms_app, xms_worker
  using (account_id = any (current_setting('xms.account_ids', true)::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids', true)::uuid[]));
-- Portal: published only, visible to the single bound account.
create policy article_read_portal on acct.solution_articles for select to xms_portal
  using (status = 'published' and acct.article_visible(id));
-- article_versions and article_feedback inherit through the article id.
create policy version_read on acct.article_versions for select to xms_app, xms_worker, xms_portal
  using (acct.article_visible(article_id));
-- Portal role has column-level grants only on client-facing columns.
revoke all on acct.article_versions from xms_portal;
grant select (id, article_id, version_no, client_notes, published_at) on acct.article_versions to xms_portal;
-- Embeddings exist only for accounts with AI on (mirrors AI Integration §8 controls).
create policy embeddings_ai_on on acct.embeddings for all to xms_app, xms_worker
  using (account_id = any (current_setting('xms.account_ids', true)::uuid[])
         and exists (select 1 from acct.ai_settings s where s.account_id = acct.embeddings.account_id and s.enabled))
  with check (exists (select 1 from acct.ai_settings s where s.account_id = acct.embeddings.account_id and s.enabled));
-- Append-only guards
create trigger trg_ticket_solutions_append_only before update or delete on acct.ticket_solutions
  for each row execute function sys.raise_append_only();
create trigger trg_article_feedback_append_only before update or delete on acct.article_feedback
  for each row execute function sys.raise_append_only();
create trigger trg_article_versions_published_frozen before update or delete on acct.article_versions
  for each row when (old.published_at is not null) execute function sys.raise_append_only();
```

The `xms.account_ids` array for portal principals is the single bound account (the data layer sets both variables for portal sessions so one function serves both roles).

### 2.10 Service logic worth stating

- **Global articles** are owned by a reserved operator account row (`op.accounts` with key `GLOBAL`, status `system`) that every internal principal is implicitly granted. The portal role never binds that account; portal reads reach global articles only through `is_global` inside `article_visible()`.
- **Publish** in one transaction: set `published_at` on the draft version, set `published_version_id`, `status = published`, `last_verified_at`, refresh `search_vector`, insert the audit event, write an outbox row `article.published` (embedding regeneration, notifications, snapshot counters).
- **Generalize**: creates a new article under `GLOBAL` with `generalized_from_id`, copies the draft text (or the Axel-proposed rewrite), runs the identifier checklist (`backend/src/domain/knowledge/generalization-check.ts`: account name, contact names, hostnames from the account's configuration items, email addresses, attachment references); the check must return zero findings before publish is allowed.
- **Close discipline** is a transition rule registered by this module with the ticket state machine: on entering `resolved`, if the resolution code is not in the no-solution set, require at least one `acct.ticket_solutions` row for the ticket with outcome `resolved_by`, `partially_resolved_by` or `created_from`. The rule is evaluated inside the transition transaction.
- **Retrieval** (`backend/src/domain/knowledge/retrieval.ts`): full-text query on `search_vector` and trigram on `display_key` always; when the account AI switch is on and an embedding exists for the query (generated on demand through the adapter), a cosine query on `acct.embeddings` is unioned and the two lists are fused with reciprocal rank fusion; results are filtered by RLS, so the service never adds a visibility clause of its own.

## 3. Producers / core logic

| Producer | Trigger | What it writes |
|---|---|---|
| Ticket service (Ticket Management) | Transition to `resolved` | Consults the close-discipline rule; on `created_from`, calls `ArticleService.createCandidate(ticketId)` |
| `ArticleService.createCandidate` | From the resolution panel | Draft article and version 1 from ticket fields and work notes flagged `include_in_solution`; if AI is on, requests `propose_article_draft` through `/axel/suggest` and stores the suggestion id on the version |
| `ArticleService.publish`, `retire`, `generalize` | Curator actions | Version freeze, outbox events, audit |
| Worker `knowledge.embed` handler | Outbox `article.published`, `ticket.resolved` (with a summary), nightly reconcile | Embeds article versions and ticket summaries through the Axel adapter batch face (or the Bedrock Titan exception in ADR-04) when the account AI switch is on; deletes embeddings when an account switches AI off |
| Worker `knowledge.metrics` handler | Nightly | Writes coverage, reuse, deflection, feedback and staleness measures into `rpt.daily_snapshots` |
| Portal request flow | Pre-submit search | `acct.article_feedback` rows with context `portal_search` and a `portal_deflection_sessions` row (owned by Client Portal) recording shown and opened articles |
| XMS MCP tools | Axel turns | `search_solutions`, `get_article`, `find_similar_tickets` call the read routes; `create_article_draft` calls the candidate route with the caller's token |

## 4. API routes

All routes are versioned under `/v1`; internal routes accept `internal`, `api_client` and `harness` principals; portal routes accept `portal`. Pagination is cursor-based (`limit` default 25, max 100, `cursor`). Mutations accept an `Idempotency-Key` header.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/articles` | `kb:read` (implied by `tickets:view`) | List with filters `status`, `kind`, `category`, `account_id`, `q` |
| POST | `/v1/articles` | `kb:author` | Create draft (manual) |
| POST | `/v1/tickets/{id}/article-candidate` | `kb:author` | Create candidate from a ticket (5.2) |
| GET | `/v1/articles/{id}` | `kb:read` | Record with versions, links, feedback |
| PUT | `/v1/articles/{id}/draft` | `kb:author` | Replace the draft version text |
| POST | `/v1/articles/{id}/submit` | `kb:author` | Draft to In review |
| POST | `/v1/articles/{id}/publish` | `kb:publish` | Publish current draft; reviewer must differ from author |
| POST | `/v1/articles/{id}/retire` | `kb:publish` | Retire with reason |
| POST | `/v1/articles/{id}/generalize` | `kb:publish` | Create the global copy; returns checklist findings when blocked |
| PUT | `/v1/articles/{id}/visibility` | `kb:publish` | Replace the account set |
| POST | `/v1/articles/{id}/feedback` | `kb:read` | Feedback row |
| GET | `/v1/tickets/{id}/solutions` | `tickets:view` | The Solutions rail: matching articles plus similar tickets |
| POST | `/v1/tickets/{id}/solutions` | `tickets:resolve` | Add a ticket-solution link (also callable inside the transition body) |
| GET | `/v1/search/solutions?q=` | `kb:read` | Hybrid retrieval, used by the MCP tool |
| GET, POST, PATCH | `/v1/configuration-items` | `tickets:view` / `tickets:work` | Register |
| GET, POST, PATCH | `/v1/ticket-templates` | `tickets:view` / `admin:config` | Templates |
| GET | `/v1/knowledge/queue` | `kb:publish` | Curator queue (5.5) |
| GET | `/v1/knowledge/metrics` | `reports:view-portfolio` | Effectiveness measures |
| GET | `/portal/v1/solutions?q=` | `portal:kb` | Pre-submit search and Knowledge page; published, visible, client sections only |
| GET | `/portal/v1/solutions/{id}` | `portal:kb` | Client view; records an `opened` event on the deflection session |
| POST | `/portal/v1/solutions/{id}/feedback` | `portal:kb` | Feedback |
| GET, POST | `/portal/v1/configuration-items` | `portal:submit` | List and add items (name and type only) |

The harness-facing route set is the same internal set; the MCP server adds no routes.

## 5. Cross-cutting concerns

### 5.1 Visibility is a database property

No service method filters articles by account in application code. Every read goes through RLS with `article_visible()`. The isolation suite gains article-specific cases: an article shared with B but owned by A is readable under B's grants; a draft is never readable by the portal role; a global article is readable by every portal role.

### 5.2 AI switch

Embeddings and Axel-drafted text exist only when `acct.ai_settings.enabled` is true (policy in 2.9 plus the adapter pre-flight). Turning the switch off enqueues `knowledge.purge_embeddings` for the account; the Solutions rail degrades to keyword matches and says so.

### 5.3 Similar tickets across accounts

`find_similar_tickets` searches `ticket_summary` embeddings across the caller's granted accounts only; RLS does the filtering. Results show the other account's key and title to internal users who hold the grant. Portal users never reach this route.

### 5.4 Deflection honesty

A deflection is counted only for a portal session that opened an article and did not submit within 24 hours; sessions are tied to the portal user and the search text hash, not to cookies, so the count survives a page reload and does not double count.

## 6. Web / client changes

- **Article list and record** under `/knowledge`: the ServiceNow grammar from `QueueTab.tsx` and `TicketDrawer.tsx` (list with condition builder; record with properties column, sectioned content editor with Markdown, versions and links tabs). Shared components `SortableTable`, `RecordBar`, `PropertyGrid`, `SectionEditor`.
- **Solutions rail** on the ticket record: `SolutionsRail` component with two lists and the "Use this" action that pre-selects the article in the resolution panel; refetches on category, title, description or configuration item change (RTK `providesTags: ['TicketSolutions']`, invalidated by the ticket patch mutation).
- **Resolution panel** (Ticket Management owns the panel; this module contributes the solution picker and candidate button).
- **Curator queue** at `/knowledge/queue` with four tabs.
- **Configuration items** at `/accounts/{id}/items` and inline picker on the ticket form.
- **Portal**: `SolutionSearch` component embedded in the New request page, `KnowledgePage` list, article view rendering only `client_notes`; feedback buttons. Portal styling per [Design System §5](../../01-architecture/DESIGN-SYSTEM.md).
- **RTK slice** `knowledgeApi` with tags `Articles`, `Article`, `TicketSolutions`, `ConfigurationItems`, `Templates`, `KnowledgeQueue`.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/knowledge-base-core` | `backend/src/db` migrations for 2.1 to 2.7 with policies; `backend/src/domain` close-discipline rule and generalization check; API routes (internal); worker metrics handler | Ticket Management core (`acct.tickets`, transitions) |
| 2 | `feature/knowledge-base-web` | Article screens, Solutions rail (keyword), resolution panel picker, curator queue, configuration items | 1 |
| 3 | `feature/knowledge-base-portal` | Portal search-first and Knowledge page, deflection sessions | Client Portal route group |
| 4 | `feature/knowledge-base-ai` | `acct.embeddings`, worker embed handler, hybrid retrieval, Axel draft and generalization proposals, MCP tool endpoints | Axel adapter, XMS MCP server |
| 5 | `feature/knowledge-base-templates` (Phase 4) | Templates in portal, full configuration item attributes | 2, 3 |
| 6 | `feature/knowledge-base-runbooks` (Phase 4) | Auto-resolution runbooks, opt-ins, dry-run, audit as AI | Connector framework for executable steps |

Deploy order inside each: db migration, worker, api, web.

## 8. Testing & verification

- **Domain (Jest, `backend/src/domain`):** close-discipline rule for each resolution code; generalization check finds account name, hostnames, emails and attachment references and passes clean text; reciprocal rank fusion ordering; deflection classification of sessions.
- **Data layer (Testcontainers):** `article_visible()` truth table (own, shared, global, none) for operator and portal roles; portal cannot read drafts, retired articles or internal columns; published versions reject update and delete; embeddings insert fails when the account AI switch is off; the isolation suite covers all eight tables.
- **HTTP:** every route rejects anonymous and garbage tokens; portal token on `/v1/articles` gets 403; publish by the author gets 409; generalize with findings returns 422 with the findings list; `Idempotency-Key` replay returns the stored response.
- **Worker:** embed handler skips unchanged `content_hash`; purge on switch-off deletes only that account's rows; metrics handler produces the expected counts from constructed tickets and feedback.
- **Axel adapter contract:** recorded fixture for `propose_article_draft`; a withheld result leaves the candidate empty but still creates the draft.
- **Web (Vitest):** Solutions rail renders the keyword-only note when AI is off; resolution panel blocks the Resolve button until a link or candidate exists.
- **E2E (Playwright):** resolve a ticket by creating a candidate, publish it as a curator, see it in the portal for that account and not for the other seed account, generalize it and see it in both.

## 9. Risks / notes

- **Adoption cost of the close discipline.** If drafting an article takes longer than closing, consultants will pick no-solution codes. Mitigation: the Axel draft, the one-click candidate, and a coverage measure per consultant on the Knowledge dashboard so the team lead sees avoidance.
- **Global account row as a modelling trick.** Owning global articles through a reserved account keeps every table uniform under RLS but must be documented in the seed and the isolation suite (the `GLOBAL` account is granted to every internal principal by the guard, never by a data row).
- **Embedding cost and the ADR-04 exception.** Until the harness embeddings endpoint exists the worker calls Bedrock Titan directly; the exception is logged per account and removed when the endpoint ships.
- **ivfflat recall** degrades as rows grow without reindexing; the monthly rebuild job is in [Data Model §7](../../01-architecture/DATA-MODEL.md).
- **Runbook execution (Phase 4)** needs connector-backed executable steps; the spec here only fixes the guardrails and audit shape.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
