# Functional Spec: Solution Knowledge Base

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Product Vision](../../00-overview/PRODUCT-VISION.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md)
**Requirements covered:** CP-08, AI-07, AI-17 (Nice to Have), TM-19 (Nice to Have), TM-17 (Nice to Have)
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `aix-mcp/app/modules/xms_mcp`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Problem

Every managed-services ticket ends with someone knowing how the problem was fixed, and today that knowledge leaves with the ticket. ServiceNow CSM records a close code and free text; nothing turns that into a reusable solution, nothing shows the next consultant that the same OneStream consolidation error was fixed four times last quarter, and nothing lets a client find the fix without opening a ticket. The DMS team re-diagnoses recurring problems, clients wait on tickets that a two-step runbook would have closed, and the practice cannot show a client what it has learned about their environment.

The product thesis ([Product Vision §2](../../00-overview/PRODUCT-VISION.md)) is that this product is a knowledge system that happens to run tickets. This module is where that thesis lives. It must cover five distinct cases:

1. **Closing a ticket produces a solution record.** The consultant links the ticket to the article that fixed it or drafts a new one, and the ticket cannot close without one (unless the resolution code says there was nothing to fix).
2. **Finding a solution while working a ticket.** Comparable resolved tickets and relevant articles surface on the ticket record without a search (AI-07).
3. **Finding a solution before opening a ticket.** A portal user describes the problem and sees the articles that fixed it before (CP-08), scoped to what their account may see.
4. **Curating knowledge.** Articles have owners, reviews, versions, and a path from "this fixed Brookfield's problem" to "this fixes anyone's problem" that strips client identifiers on the way.
5. **Knowing what is in the environment.** A lightweight register of configuration items per account (TM-19) gives tickets and articles something concrete to attach to.

## 2. Current state (what exists today)

- **XMS proof of concept (web-ui `components/aix-v3/xms/`):** `vocab.ts` defines `RESOLUTION_CODES` (Solution provided, Workaround provided, Known error, Configuration change, User education, No fault found, Duplicate, Cancelled by client) and `XMS_CATEGORIES`; `TicketDrawer.tsx` has a Resolution Information tab with code and notes. Resolution is free text. There is no article, no link, no search.
- **Studio `xms_ticketing` module (branch `feature/xms-ticketing`):** migration 092 added `resolution_code`, `resolution_notes`, `resolved_by` and the close discipline in `service.py` (a ticket cannot resolve without a code). No knowledge tables, no agent tools. Ported per ADR-07, not reused.
- **AIX harness knowledge stack:** the studio has a document vectorizer, a tenant corpus (`document_chunks`, `tenant_documents`, Titan embeddings at 1024 dimensions) and the `search_documents` and `search_tenant_corpus` tools. It stores documents, not solutions, in the harness's own database. ADR-04 rejects moving XMS ticket knowledge there; XMS keeps the corpus and serves it to Axel through the XMS MCP server.
- **Not built anywhere:** solution articles, versions, per-account visibility, generalisation workflow, ticket-to-article links, configuration items, ticket templates, deflection, effectiveness metrics, self-service runbooks.

## 3. Goals

1. **Every resolution is a solution record.** A resolved ticket points at the article version that fixed it, or created the candidate that became one; the knowledge base grows as a by-product of closing tickets.
2. **Solutions find the consultant.** The ticket record shows similar resolved tickets and matching articles as soon as the ticket is categorised, without a search, when the account allows AI.
3. **Clients solve what they can themselves.** The portal shows matching solutions before a request is submitted, and the product measures how often that avoids a ticket.
4. **Knowledge is safe to share.** An article is visible only to the accounts it was written for until a curator generalises it; visibility is enforced by the same database policy as every other account row.
5. **Knowledge is trustworthy.** Articles have owners, review, versions, feedback and retirement; a ticket always links to the exact version that was used.
6. **The environment is known.** Configuration items per account give tickets, articles and reports a shared vocabulary for "which system".
7. **Recurring requests get cheaper.** Ticket templates pre-fill recurring requests, and, later, allowlisted runbooks can resolve simple requests with no human touch for accounts that opt in.

## 4. Non-goals / out of scope

- **A general document library.** Articles are structured solutions, not uploaded PDFs. Client documentation uploads belong to ticket attachments; a future "runbook attachments" feature can attach files to articles, but articles are authored in the product.
- **A full CMDB.** TM-19 asks for a lightweight register: type, name, attributes, owner, links. No discovery, no dependency mapping, no change impact analysis. Nice to Have, Phase 4.
- **Public or anonymous knowledge.** Every reader is an authenticated portal or internal user. There is no public help centre.
- **Automatic publishing.** Axel drafts; a person with `kb:publish` publishes. No article reaches a client without a human decision (AI-08).
- **Autonomous resolution in Phases 1 to 3.** Allowlisted auto-resolution (AI-17) is Nice to Have, Phase 4, per-account opt-in, after measured accuracy of the human-in-the-loop version.
- **Cross-account learning by default.** An article written for one account is never shown to another until generalised and published as global. There is no "similar tickets across all clients" view for portal users; internal users see cross-account similar tickets only for accounts they hold grants on.
- **Article translation.** Single language in the target solution.

## 5. User-facing behavior

### 5.1 Vocabulary (fixed sets)

| Set | Values | Notes |
|---|---|---|
| Article status | Draft, In review, Published, Retired | Only Published articles are retrievable outside the curation screens; Retired keeps history and stays linked from old tickets |
| Article visibility | Global, Account set | Account set lists one or more accounts; Global means every account and every internal user |
| Article kind | Solution, Workaround, Known error, Procedure (runbook), Reference | Kind drives the template shown to the author and whether self-service applies |
| Self-service eligibility | Not eligible, Client can follow, Client can request (one click), Auto-resolvable (Phase 4) | Set by the curator; "Client can request" creates a ticket pre-filled from the article |
| Effort band | Under 15 minutes, Under 1 hour, Under 4 hours, Over 4 hours | Shown to consultants and used by the effort-estimation suggestion (AI-15, later) |
| Resolution codes | Solution provided, Workaround provided, Known error, Configuration change, User education, No fault found, Duplicate, Cancelled by client | Ported from the POC; the first five require a solution link or a new-article candidate; the last three are no-solution codes |
| Ticket-solution outcome | Resolved by, Partially resolved by, Article created from | One ticket may carry several links |
| Configuration item type | Environment, Application, Module, Integration, Server, Report, Other | Per account; attributes are free key-value pairs |
| Feedback | Useful, Not useful, Out of date | With optional comment; from internal and portal users |

### 5.2 Closing a ticket (the resolution record)

When a consultant moves a ticket to Resolved, the resolution panel asks for a resolution code and notes (as in the POC), then a solution:

- **Link an existing article.** The panel lists the articles already suggested on the ticket's Solutions rail (5.3) first, then a search box. Picking one records "Resolved by" or "Partially resolved by" against the exact published version.
- **Create a new article candidate.** One click drafts an article from the ticket: problem statement from the short description, environment from the linked configuration item, steps from the resolution notes and the work notes marked "include in solution", verification empty. When the account allows AI, Axel proposes the draft text (AI-07 plus the draft capability in [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md)); the consultant edits before saving. The candidate is a Draft article visible to that account only, owned by the consultant, and the ticket carries an "Article created from" link.
- **No solution.** Allowed only with the codes No fault found, Duplicate, Cancelled by client. The panel says why the other codes need a solution.

The ticket cannot reach Resolved until one of the three paths is complete. Reopening a ticket keeps the links; resolving again may add links but never removes one (links are evidence).

### 5.3 The Solutions rail on the ticket record

On every open ticket the right-hand rail shows a **Solutions** section:

- **Matching articles:** up to five published articles the reader may see, ranked by relevance to the ticket's title, description, category and configuration item. Each shows title, kind, last verified date, usage count, and a "Use this" button that opens the article beside the ticket and pre-selects it for the resolution record.
- **Similar resolved tickets:** up to five resolved tickets from accounts the reader holds grants on, with their resolution code, the article they linked, and time logged. Internal users only; the portal never shows other tickets here.
- **Refresh:** the rail refreshes when the title, description, category or configuration item changes. When the account's AI switch is off, the rail shows keyword matches only and says "Similar-ticket ranking is off for this account".
- **Empty state:** "No documented solution yet. Resolving this ticket will create the first one."

### 5.4 Article record

Articles use the same list and record grammar as tickets ([Design System §4](../../01-architecture/DESIGN-SYSTEM.md)). The record has a properties column (key `KB000123`, kind, status, visibility, owner, reviewer, configuration items, categories, self-service eligibility, effort band, last verified, source ticket) and a content area with fixed sections: Problem statement, Environment, Symptoms, Cause, Steps, Verification, Rollback, Notes for the client (the only section shown verbatim in the portal when the article is client-visible). Below the content: linked tickets (with outcome and date), versions, feedback.

Editing a Published article creates a new Draft version; the published version stays live until the new one is published. Tickets keep pointing at the version they used.

### 5.5 Lifecycle and curation

| Transition | Who | Rule |
|---|---|---|
| Draft to In review | Author (`kb:author`) | Problem statement, Steps and Verification must be non-empty; at least one category |
| In review to Published | Curator (`kb:publish`), not the author | Sets last verified date; assigns the version number |
| Published to Draft (new version) | Author or curator | Creates a draft version; published version stays live |
| Published to Retired | Curator | Requires a reason; retired articles disappear from retrieval and the portal but remain linked from tickets with a "Retired" badge |
| Account set to Global | Curator | Runs the generalisation checklist (5.6) |

Curators see a **Knowledge queue**: drafts awaiting review, articles not verified in 12 months, articles with two or more "Out of date" votes, and articles used by three or more tickets in the last quarter that are still account-only (generalisation candidates).

### 5.6 Visibility and generalisation

An article starts visible to the account whose ticket created it. Making it Global requires the curator to complete the checklist: no client name, no hostnames, no user names, no attachment references, no contract terms in any section; environment described generically ("OneStream 8.x with Cube Views" not "Brookfield PROD"). When the account allows AI, Axel proposes a generalised rewrite and lists the identifiers it removed; the curator accepts or edits. The account-specific version is not deleted: the global article is a new article that records "Generalised from KB000123" and the original stays visible to its account with a pointer to the global one.

Adding a second account to an account set (without going global) is allowed for articles about a shared platform version; the checklist still runs.

### 5.7 Portal: find a solution before you submit

The portal's New request flow ([Client Portal §5.4](../client-portal/FUNCTIONAL-SPEC.md)) opens with a search field. As the user types the problem, the page shows up to five published articles visible to their account with the "Notes for the client" section and, when eligible, a "Follow these steps" or "Request this" button. "Request this" opens the request form pre-filled from the article's template. If the user continues to submit, the request records which articles were shown and whether one was opened, so deflection can be measured honestly: a request submitted after reading an article is not a deflection; a session that opened an article and did not submit within 24 hours is.

The portal's Knowledge page lists the same articles by category with search and feedback buttons. Portal users never see internal sections (Cause, Rollback, Notes), other accounts' articles, or draft and retired articles.

### 5.8 Configuration items

Each account has a configuration item list (type, name, attributes such as version, URL, environment tier, owner contact). Tickets and articles pick from it; the ticket form's "Affected item" field searches it. Consultants and account admins in the portal may add items; only internal users edit attributes. The item record shows its open and recent tickets and linked articles.

### 5.9 Ticket templates

A template pre-fills type, category, form, title pattern, description checklist, default assignment group, and optional links to an article and a configuration item. Templates are per account or global. Internal users pick a template on New ticket; portal users see templates surfaced as "Common requests" on the portal home when the template is marked client-visible.

### 5.10 Effectiveness metrics

The Knowledge dashboard (internal) shows per account and overall: articles published, coverage (share of resolved tickets with a solution link), reuse (tickets resolved by an existing article vs new candidates), deflection rate (portal sessions that opened an article and did not submit), feedback score, stale articles, single-use articles. The client-facing report pack ([Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md)) shows the client's own coverage and deflection.

### 5.11 Allowlisted self-service auto-resolution (Phase 4)

For accounts that opt in per request type, a runbook article marked Auto-resolvable may be executed by the product for a matching request (for example, reset a OneStream user's password through a connector, or grant a documented report permission): the request is created, the runbook runs, the outcome is posted as a public comment, and the ticket is resolved with "Resolved by" the runbook version and actor "AI (policy)". Guardrails: the account opt-in names the request type and the runbook; the runbook has a dry-run mode and a rollback section; a failure or any deviation routes the ticket to a human with the log attached; the client can switch it off at any time; every execution is an AI action in the audit trail.

## 6. Rollout

1. **Phase 2 (Focused pilot), with Ticket Management:** article entity with versions, status, visibility (account set and global), the resolution record and close discipline, article list and record screens, keyword retrieval on the Solutions rail and in the portal search, feedback, configuration items (minimal: type, name, links), curation queue basics. Requires the ticket transition endpoint and the portal route group.
2. **Phase 2, with Axel AI Functionality:** AI-drafted article candidates, generalisation proposals, embedding-based similar tickets and article ranking when the account AI switch is on (AI-07). Requires the Axel adapter and the XMS MCP server.
3. **Phase 3 (Operational replacement):** deflection measurement, effectiveness dashboard and report pack section, stale-article and generalisation-candidate queues, templates for internal users, migration of ServiceNow knowledge articles where they exist (Data Migration).
4. **Phase 4 (Later releases):** ticket templates in the portal (TM-17), full configuration item attributes and per-item history (TM-19), allowlisted auto-resolution runbooks (AI-17), effort estimation from article effort bands (AI-15).

## 7. Success criteria

- A consultant resolving a ticket with code "Solution provided" and no linked article is stopped with a message naming the two ways to satisfy it; with code "Duplicate" the ticket resolves without an article.
- Creating an article candidate from a resolved ticket produces a Draft visible only to that ticket's account, with the ticket showing an "Article created from" link, and the draft appears in the curator's queue.
- After a curator publishes an article visible to account A, a portal user of account B searching the same words sees nothing, and an internal user with a grant only on B sees nothing, while account A's portal user sees it.
- Generalising that article to Global creates a new global article, keeps the original under A, and the checklist blocks publishing while the account's name remains in any section.
- On a ticket for an account with AI on, the Solutions rail shows a ranked article within one refresh of setting the category; with AI off it shows keyword matches and the "ranking is off" note.
- Editing a published article and publishing the edit leaves the earlier ticket pointing at version 1 and new tickets at version 2.
- A portal session that opens an article from the pre-submit search and does not submit is counted as a deflection on the Knowledge dashboard the next day; a session that opens an article and submits is not.
- The isolation suite includes every knowledge table, and the portal database role cannot read draft or retired articles or any internal section.

## 8. Open questions

- **Should work notes be draftable into articles automatically?** Default assumption: only work notes the author marks "include in solution" feed the candidate; everything else stays internal.
- **Who may generalise?** Default assumption: any curator (`kb:publish`), with the checklist as the control; no separate role.
- **Do configuration items sync from ServiceNow's CMDB for Brookfield?** Default assumption: not in Phases 1 to 3; Brookfield CI names are imported once during migration as plain items.
- **Client-authored articles?** Default assumption: no; portal users give feedback and request articles through a ticket, they do not author.
- **Retention of retired articles?** Default assumption: retained for the life of the account; retired articles linked from tickets are never purged.
- **Global article ownership when the originating account offboards?** Default assumption: global articles survive offboarding because they contain no client identifiers by construction; account-only articles are deleted with the account after the retention period.
