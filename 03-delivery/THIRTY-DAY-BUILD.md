# Thirty-Day Build: XMS in one month

**Status:** Draft, supersedes the sprint calendar in the Implementation Plan for the first month (ADR-15)
**Owner:** Matt Brown
**Last updated:** 2026-09-05
**Related:** [Implementation Plan](./IMPLEMENTATION-PLAN.md) (item ids referenced below), [Roadmap](./ROADMAP.md), [TODO](./TODO.md), [Test Strategy](./TEST-STRATEGY.md), [User Experience](../01-architecture/USER-EXPERIENCE.md), [Decision Log](../00-overview/DECISION-LOG.md)

Matt's direction (2026-09-05): build XMS in a month. This document says exactly what that means, what is in and out, the order of work by day, and the two points where scope is cut rather than the date. The Implementation Plan's item ids (`P1.3.2` and so on) stay the reference for each piece of work; this document re-sequences and trims them into 20 working days.

---

## 1. What "built in a month" means

On day 30 the DMS team can run the chosen pilot workflow on one account in XMS, on the dev environment, with real tickets, and every hard guarantee in place. Concretely, the day-30 build:

| Guarantee | In the day-30 build |
|---|---|
| Isolation | Forced row-level security on every account table, the generated isolation suite green on every build, portal role revoked from internal tables |
| Identity | Internal users through the XMS Clerk application; invited portal users through one Clerk organisation for the pilot account (email plus password with MFA; SSO later) |
| Audit | Domain audit events, security events and usage events written from day one, append-only, searchable in Admin |
| Ticketing | Five types on the default state machines, priority matrix, SLA clocks with pause reasons and the breach sweeper on a 24x7 calendar, comments and work notes, links, search and saved views, dispatch |
| Time and contracts | Time entries with the activity taxonomy and billable classes, mandatory time before resolution, one contract per model with burn-down and hours remaining on the ticket |
| Knowledge | Solution articles with versions and visibility, close discipline (resolution code plus solution link), similar-solution rail on full-text search, portal search-first |
| Email | Inbound alias to ticket with thread matching, reply-to-update, unknown-sender quarantine; outbound replies threaded and branded |
| Portal | Home with search-first, new request on a form, request detail with the public thread, attachments; invited users only |
| Axel | Panel on the desk, category and priority chips, duplicate hint, summarise, similar solutions; per-account switch enforced; suggestions and decisions audited |
| Reporting | Operations dashboard, account dashboard, Excel and CSV export on every list, a basic WSR pack generated on demand |
| Platform | Terraform dev, pipeline with the gate stage, structured logs and traces, readiness, alarms, runbooks v0 |

Not in the day-30 build (each with its landing month in §7): business calendars and time zones, portal SSO, rate cards and billing periods and finance export, forecasts and threshold alerts, capacity and allocation, ServiceNow sync (stand-in ingest only if day 18 allows), migration beyond a CSV rehearsal, scheduled report delivery and CSAT, Axel draft replies and narrative and time nudges, bidirectional anything, production environment and cutover.

Requirement coverage on day 30 (register IDs): TM-01 to TM-05, TM-07 to TM-09, TM-12 to TM-15; TB-01 to TB-04, TB-06 (basic), TB-07, TB-10; CAP-01 (roster list only); CP-02 to CP-05, CP-08; EM-01 to EM-03, EM-07, EM-08; DR-01 to DR-04 (basic), DR-06; AI-01 to AI-03, AI-07 to AI-11, AI-13; INT-01; XA-01 to XA-03. That is 50 of the 94 Must Have rows, and every row that a pilot needs to be trustworthy.

## 2. Preconditions for day 1 (must be true on 2026-09-08)

1. Team of four fully dedicated plus Matt; no XT work except one hour a day of fixes (assessment path 1 assumption).
2. AWS dev deploy role, ADO project and ARM64 pool, ECR repositories, Clerk `XMS` application with the internal organisation and the THG connection, SES sandbox lifted for `mail.dev.<domain>` (P0.0.2 to P0.0.4).
3. Harness owners have accepted change 1 (bearer context variable) and change 5 (inline agent registration) for delivery by day 12; if not, the day-12 fallback in §6 applies.
4. Pilot account, pilot workflow and the DMS contact who will use the build weekly are named (P0.0.6).
5. Every developer has Claude Code with the seeded skills in the `xms` repo and has read `CLAUDE.md`; specs are the prompts.

## 3. Working model for the month

- **Four parallel tracks, one integration point.** Tracks: A (tickets, SLA, portal), B (time, contracts, knowledge, reporting), C (email, worker, outbox, attachments, exports), M (Matt: platform, identity, isolation, Axel, reviews). Every track merges to `dev` daily; the pipeline gate is the only integration meeting.
- **Vertical from day 6.** Days 1 to 5 are horizontal foundations because nothing vertical is safe without them; from day 6 every track ships a usable slice per two days.
- **Specs are the backlog.** Each day's item is an Implementation Plan id; the spec sections it names are the prompt; the "Done when" line is the test that must exist before merge. No new design documents during the month; decisions go to the Decision Log as one-line ADR addenda.
- **AI-assisted development conventions.** Agents generate scaffolds, migrations, DTOs, repositories, tests and screens from the specs; humans own the domain rules (state machine, SLA engine, isolation binding, guard) and review every migration and every policy. The route-and-permission snapshot and the isolation suite are the two tests no agent may edit without Matt's review.
- **Cadence.** Ten-minute stand-up at 09:00, demo at 16:30 every day on `dev`, decisions from Matt within the hour, no other meetings.
- **Definition of done per item.** The Implementation Plan's "Done when" line, plus lint and type-check clean, plus the pipeline gate green.

## 3a. Security is not a phase in this month

Every item in section 4 is built under the security definition of done (ADR-16, the `xms-security-first` skill): the threat note first, the controls before the feature, the tests before the code, the checklist on the pull request. Specific security items in the month: day 3 RLS and the generated isolation suite; day 4 the guard, the route-and-permission snapshot and security events; day 5 circuit breaker 1 on those suites; day 6 attachments with scan gating; day 11 the portal role revokes and realm suite (no portal screen before it is green); day 15 hardening (ZAP, dependency audit, rate limits, CSP, secrets scan); day 17 the security review with Juan; day 18 runbook rehearsal. Nothing on the cut list in section 5 is a security control.

## 4. Day-by-day sequence

Days are working days. Item ids refer to the [Implementation Plan](./IMPLEMENTATION-PLAN.md); "(cut)" marks a reduced version of that item, defined in §5.

### Week 1: foundations (days 1 to 5)

| Day | Track A | Track B | Track C | Track M |
|---|---|---|---|---|
| 1 | P1.1.2 frontend scaffold, P1.1.3 tokens from Wireframes v2 §4 | P1.4.5 config seeds (state machines, matrix, catalogs) as JSON | P1.1.5 local environment (compose, LocalStack, MailHog) | P1.1.1 backend scaffold, P1.1.6 Terraform skeleton |
| 2 | P1.1.4 OpenAPI type generation, P1.4.2 components (Count-card dense table with chips, selection bar and rows-per-page, record form, state-ramp pills, type bars, account dots, mono key and SLA values, tab bar) per Wireframes §6 and §8 | P1.3.1 schema 0002 (operator tables) | P1.2.2 S3, SQS, SES in Terraform (with M) | P1.1.7 pipeline with gate, P1.2.1 dev environment (ECS, ALB, RDS) |
| 3 | P1.4.2 continued (condition builder, ink banner, skeletons) | P1.3.6 audit events and audit guard trigger | P1.2.4 observability (pino, OTel, readiness) | P1.3.2 RLS framework, P1.3.3 isolation suite generator |
| 4 | P1.4.1 shell (sign-in, navy finder bar, finder overlay, pinned sidebar with starred views, content header bar, RTK base) per Wireframes v2 §2 | P1.3.7 bootstrap and seed skeleton | P1.5.3 outbox, dispatcher, inbox, dead letters, job leases | P1.3.4 Principal and guard, P1.3.5 permission catalog and route snapshot, P1.3.8 security events |
| 5 | P1.4.3 accounts basic screens, P1.4.4 users, roles, groups screens | P1.4.3 and P1.4.4 APIs (accounts, users, grants, groups) | P1.5.4 notifications writer and feed | P1.2.3 secrets, P1.2.5 migration runner; **circuit breaker 1 review** |

Exit of week 1: an administrator signs in on `xms.dev`, creates the pilot account, invites a user, assigns grants; the isolation suite, auth rejection suite and route snapshot are green in the pipeline; an outbox row dispatches to SQS in dev.

### Week 2: the ticket loop (days 6 to 10)

| Day | Track A | Track B | Track C | Track M |
|---|---|---|---|---|
| 6 | P1.5.1 ticket tables, P1.5.2 ticket service (state machines, priority, transitions, comments, work notes) | P2.12.2 time entries and activity taxonomy (append-only, adjustments) | P1.6.1 attachments (presigned POST, scan state, quarantine consumer) | P1.5.6 usage events, telemetry endpoint and client; P1.7.1 Axel adapter (session exchange, SSE relay) |
| 7 | P1.5.5 Queue (system views), New ticket form, Ticket record (properties, conversation, activity) | P2.12.3 mandatory time before resolution; P2.13.1 contracts (cut: one period, no rollover or overage rules, no rate cards) | P1.6.3 inbound email (alias, thread matching, append or create, quarantine) | P1.7.2 AI switch enforcement and suggestion tables; P1.7.3 `xms_mcp` read tools |
| 8 | P2.10.1 SLA engine on the 24x7 calendar (clocks, pauses, latches, response met) | P2.13.2 contract position endpoint; P2.13.3 contract screens (cut: no burn chart) | P1.6.4 outbound email (templates, threading, branding, bounce handling) | P1.7.4 Axel panel and `xms-desk-assistant` (fallback in §6 if the harness change slipped) |
| 9 | P2.10.3 SLA badge, meters, pause and resume UI; P2.10.2 sweeper (with C) | P2.14.1 knowledge tables and `article_visible()`; P2.14.2 article lifecycle (cut: generalise deferred) | P1.6.2 attachments UI, P1.6.5 quarantine screen, raw email view | P1.7.5 alarms and runbooks v0; P1.7.6 archive and digests (cut: digest job only, Athena deferred) |
| 10 | P2.11.2 links (cut: parent, child, related, duplicate; no groups) | P2.14.3 close discipline; P2.14.4 retrieval v1 (full-text plus trigram) | P2.11.3 bulk actions (cut: assign and tag only) | Demo day; **circuit breaker 2 review** |

Exit of week 2: an email to the pilot alias becomes a ticket with running SLA clocks; a consultant replies (threaded email out), logs time, resolves with a solution link; the Axel panel answers about the queue; suggestions are switched off per account and it shows.

### Week 3: the desk and the portal (days 11 to 15)

| Day | Track A | Track B | Track C | Track M |
|---|---|---|---|---|
| 11 | P2.11.1 search, condition builder API, saved views | P2.15.1 Solutions list and record (cut: no review queue, no CI screens) | P2.11.4 exports (Excel and CSV, streaming) | P2.16.1 portal identity (Clerk organisation for the pilot account, invitation, MFA local fallback, realm separation) |
| 12 | P2.11.4 Queue complete (condition builder, saved views, column chooser, bulk) | P2.15.2 Resolution tab and Solutions rail | P2.18.1 email hardening (cut: signature and quote stripping, out-of-office suppression, loop guard scoring without auto-disable) | P2.17.1 suggestion lifecycle, `propose_*` tools, `xms-triage` agent (cut: classification, priority, duplicate, summary; no embeddings) |
| 13 | P2.12.4 Dispatch, My Work (cut: needs-attention list and mentions, no time nudge) | P2.19.1 measures (cut: the ten measures the dashboards show) | P2.16.2 portal read model, forms (cut: one default form per type, no editor), portal routes | P2.17.3 inline chips, Summarise, AI settings on the account |
| 14 | P2.16.3 portal screens (sign-in, home search-first, new request, request detail, knowledge) | P2.19.3 operations dashboard and account dashboard with "View as client" | P2.18.2 quarantine complete; P2.12.1 roster list (cut: people and skills, no rates) | P2.11.5 audit search (cut: unified view and condition builder, no saved queries) |
| 15 | Portal accessibility pass (axe), keyboard shortcuts on the desk | P2.20.1 basic WSR pack on demand (cut: five slides, templated narrative, no schedule) | P1.8.3 seed and demo data for the pilot account | P1.8.1 hardening (ZAP, audit, rate limits, CSP); demo day |

Exit of week 3: the invited pilot user submits from the portal after a search, sees the reply; the desk has search, views, dispatch, dashboards and exports; the WSR pack downloads.

### Week 4: pilot readiness (days 16 to 20)

| Day | Track A | Track B | Track C | Track M |
|---|---|---|---|---|
| 16 | P2.23.1 e2e golden paths in the pipeline (form, email, work to close, portal isolation) | P2.20.2 report pack screen (runs, download, review read-only) | P2.21.1 ServiceNow stand-in (only if C is clear; else defect fixing) | P2.19.4 security and usage dashboards (cut: eight tiles) |
| 17 | Defect fixing from the daily demos | Defect fixing | P2.21.2 connector model (only if 16 done); else defects | Security review of the guard, RLS policies and the portal role with Juan (P3.36.2 preview) |
| 18 | P2.24.1 pilot onboarding through the screens only | Data checks on measures against seeded tickets | P2.21.3 ingest-only against the stand-in (only if 17 done) | P1.8.2 load baseline (50k tickets), runbook rehearsal for DLQ replay and loop |
| 19 | Full walkthrough with the DMS pilot users; fixes | Fixes | Fixes | Fixes; TODO and Decision Log updated; ClickUp re-sync |
| 20 | Day-30 demo and acceptance against §8; handover of month 2 backlog | | | Phase 1 and pilot gate checklists signed where met, exceptions listed |

## 5. What "(cut)" means per item

| Item | Day-30 version | Restored in |
|---|---|---|
| P2.13.1 contracts | One active period per contract, consumed minutes, hours remaining; models stored but rollover, overage and rate cards not applied | Month 2 |
| P2.14.2 articles | Draft, publish, retire, visibility set; no generalise, no identifier checklist, no CI screens | Month 2 |
| P2.11.2 links | Parent, child, related, duplicate; no ticket groups or change windows | Month 2 |
| P2.11.3 bulk | Assign and tag only | Month 2 |
| P2.18.1 email hardening | Stripping and out-of-office suppression; loop score written, alias auto-disable manual | Month 2 (auto-disable) |
| P2.17.1 suggestions | Classification, priority, duplicate, summary; no embeddings, no draft reply | Month 2 (embeddings), Month 3 (drafts, narrative, nudges) |
| P2.16.2 forms | One default form per type from seed; no editor | Month 2 |
| P2.19.1 measures | Ten measures: open, breached, at risk, SLA attainment, MTTR, backlog by age, volume, reopen rate, consumption, time logged | Month 2 (the full catalog and snapshots) |
| P2.20.1 WSR | Five slides on demand, templated narrative, no schedule or delivery | Month 2 (schedule), Month 3 (Axel narrative) |
| P2.12.1 roster | People and skills list; no rates, PTO or calendars | Month 3 (capacity) |
| P2.11.5 audit search | Unified view with the condition builder; no saved queries | Month 2 |
| P1.7.6 archive | Digest job and Object Lock bucket; Athena deferred | Month 3 |
| P2.19.4 dashboards | Eight tiles (sign-in failures, denials, isolation probes, admin changes; active users, adoption, funnel, no-result searches) | Month 2 |

## 6. Circuit breakers and fallbacks

- **Circuit breaker 1 (end of day 5).** If the isolation suite, the guard and the pipeline gate are not green on `dev`, week 2 starts with those and the portal (days 11 to 14 of track M and A) is cut from the month. Nothing vertical is built on an unproven isolation layer.
- **Circuit breaker 2 (end of day 10).** If inbound email is not creating tickets in dev, the month keeps manual and portal intake only and email moves to month 2; the pilot workflow is chosen to tolerate that.
- **Harness change 1 slips.** `xms_mcp` uses a dev-only internal secret bridge to the XMS API (an API client with read scopes bound to a service user with grants on the pilot account); removed when the bearer forwarding lands. Recorded as a security exception with an expiry.
- **Harness change 5 slips.** The desk assistant is registered as a stored `user_agents` row in the harness dev tenant instead of an inline agent; prompts move to the file-based definition when the change lands.
- **Clerk organisation-per-account cannot be created in time.** Portal users are invited into a single `portal-pilot` organisation with the account bound in `op.users`; the per-account organisation model is restored before a second account is onboarded.
- **Anything else slips.** The cut list in §5 grows; the date does not move. A slip is announced at the 16:30 demo the day it is known.

## 7. Months 2 and 3 (after the month)

| Month | Content (Implementation Plan ids) |
|---|---|
| Month 2 (weeks 5 to 8) | Restore the §5 cuts; P2.9.1 and P2.9.2 configuration editors; P2.17.2 embeddings; P2.18.3 timesheet and unlogged time; P2.19.2 snapshots; P2.21.x ServiceNow ingest-only against the Brookfield sandbox; P2.22.x migration rehearsal; P3.26.1 calendars and time zones; P3.26.2 portal SSO spike outcome applied; beta with the DMS team for two weeks (P2.24.2) |
| Month 3 (weeks 9 to 13) | P3.27.x billing periods, forecasts, thresholds; P3.28.x export and finance connector, out-of-scope flags; P3.29.x capacity; P3.30.1 bidirectional sync; P3.31.x scheduled delivery and CSAT; P3.32.1 Axel generation; production environment, backups, runbooks rehearsed (P3.36.1); security review closed (P3.36.2) |
| After | P3.34.1 onward: full migration, reconciliation, parallel run, cutover, decommission, per the Roadmap Phase 3 |

The Roadmap's phase exit criteria are unchanged; this month is a compressed Phase 1 plus the trustworthy core of Phase 2, not a replacement for Phase 3.

Screens are accepted against the rendered wireframes in `01-architecture/wireframes/` (Queue, Ticket record, My work, Dispatch, Operations, the finder overlay and the Axel panel) and the prototype's engineering callouts (Wireframes v2 §3).

## 8. Day-30 acceptance (the demo script)

1. Administrator signs in, opens the pilot account, shows the isolation suite and route snapshot green in the last pipeline run.
2. An email from a known pilot contact becomes a ticket; an email from an unknown sender lands in Quarantine and is turned into a contact and a ticket.
3. The dispatcher assigns from Dispatch; the consultant opens the record, sees the SLA meters, replies publicly (threaded email received in the test mailbox), adds a work note, pauses for Awaiting client with a reason, resumes.
4. Axel chips propose category and priority; the consultant accepts one and rejects one; the Activity tab shows both as AI actions with the confirming user; the account's AI switch is turned off and the chips disappear.
5. The consultant logs time, tries to resolve without a solution link and is refused, links an article from the rail, resolves; the contract card shows the burn.
6. The invited portal user searches, finds the article, clicks "This solved it"; then submits a request on the form and sees the consultant's reply; the work note is absent; the portal token on an internal route returns 403 (shown from the audit search).
7. The operations dashboard, the account dashboard in "View as client", an Excel export of a saved view, and the WSR pack download.
8. Audit search shows the whole demo as one request trail per action; the security dashboard shows the sign-ins and the denied probe.

If every step passes on `dev` with the pilot data, the month is done and month 2 starts on the cut list.

## 9. Risks specific to the month

| Risk | Mitigation |
|---|---|
| Pressure to skip a control to hit a day | ADR-16: controls are never on the cut list; the circuit breakers cut features, not security; Matt reviews every identity, isolation, egress and infrastructure change |
| Foundations take longer than five days | Circuit breaker 1; nothing is allowed to skip the isolation layer to save time |
| Four tracks conflict in the ticket module | Track A owns `tickets`; B, C and M only add through the service API and the outbox, never by editing the ticket service |
| Test debt from generated code | The "Done when" test is written first and reviewed; agents may not weaken a failing test to pass it |
| Portal security shortcuts under time pressure | The portal role revokes and the realm check are day-11 items with their own suite; no portal screen ships before that suite is green |
| Burnout | Twenty working days, no weekends, cuts not overtime; the assessment already flagged burnout under path 3 |
