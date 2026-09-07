# Functional Spec: Dashboards & Report Packs

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Product Vision](../../00-overview/PRODUCT-VISION.md), [Domain Model §3.8](../../01-architecture/DOMAIN-MODEL.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md) (narrative, NL query), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md) (consumption measures), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md) (client dashboard host), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) (delivery connector)
**Requirements covered:** DR-01, DR-02, DR-03, DR-04, DR-05, DR-06, DR-07 (Must Have); DR-08, DR-09, DR-10, AI-15 (Nice to Have, data side only)
**Repos affected:** `frontend`, `backend`, `backend/src/worker`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`)

---

## 1. Problem

Every week each XMS account owner builds a weekly status report (WSR) by hand: pulling ticket lists out of ServiceNow, counting SLA hits and misses in a spreadsheet, reading contract consumption from another spreadsheet, writing a narrative, pasting it into a deck, and emailing it. The assessment deck calls the automated report pack the highest-ROI item in the build (DR-04) because it replaces that cycle for every account every week.

The dashboards have the same gap. ServiceNow shows tickets; it does not show the things a managed-services practice runs on: SLA attainment against a contract, hours consumed against a budget, backlog by age, reopen rate, who is over capacity. Practice leads cannot see the portfolio at all without a manual roll-up.

The product must cover four distinct audiences and cadences:

1. **The consultant and dispatcher, continuously**: an internal operational view that refreshes near real time (DR-01, DR-02).
2. **The account owner, weekly**: a report pack generated from live data on a schedule, reviewable, presentable on a call, and sent to the client's distribution list (DR-04, DR-05).
3. **The client, whenever they look**: a client-facing view of their tickets, their SLA performance, their consumption if allowed, and their CSAT, and nothing else (DR-03).
4. **Finance and analysts, ad hoc**: raw Excel and CSV exports from every view (DR-06).

Underneath all four, trends must survive record edits and reclassification. If a ticket is re-prioritised in March, the February SLA figure must not change (DR-07).

## 2. Current state (what exists today)

- **XMS POC dashboard** (`web-ui/components/aix-v3/xms/DashboardTab.tsx`): manager tiles, an ink synthesis banner, tickets by status and priority, burn-down per contract, an oldest-unresolved rail. Approved visual grammar with a known defect: it computes everything client-side from a ticket list capped at 200 rows, so the studio's server-side `/dashboard` aggregate (`app/modules/xms_ticketing/router.py:185`) is dead code (POC audit P1-3). XMS keeps the grammar and fixes the data path.
- **Studio `/dashboard` aggregate** (`feature/xms-ticketing`): status counts, priority counts, compliance percentage, per-contract burn, oldest unresolved. Live aggregates only; no snapshots, no history.
- **AIX report generation**: PPTX by an external Lambda (`app-api/src/reports/report.service.ts`), no XLSX or CSV export utility anywhere, no scheduled report and no scheduled email chain in AIX (app-api research report §7). The harness can render branded decks through agents in 10 to 15 minutes per run (`xt_axel_agent.py:174`).
- **Dashboard refresh in AIX**: RTK Query polling at 60 seconds for the notification bell (`web-ui/components/aix-v3/notifications/NotificationsBell.tsx:52`). No WebSocket or push.
- **Nothing** exists for snapshots, CSAT reporting, health scores, or a report builder.

## 3. Goals

1. **Replace the manual WSR cycle.** Every account with a schedule gets a complete, branded report pack generated without anyone opening a spreadsheet, with the account owner spending under ten minutes reviewing the narrative before it goes out.
2. **One honest operational picture.** Dispatchers and consultants see backlog, SLA risk and capacity that is at most 60 seconds stale, scoped to the accounts they are granted.
3. **The client sees exactly their slice.** The portal dashboard renders from the same measures as the WSR so a client never sees two different numbers for the same week.
4. **Trends that do not move.** Every reported figure is a snapshot taken at a known instant; re-editing history never rewrites a past week.
5. **Everything exportable.** Any table or chart in the product can be taken to Excel or CSV as raw rows, including the filters that produced it.
6. **A portfolio view for practice leads.** All accounts on one screen: burn, SLA, backlog, CSAT, health, ranked by attention needed.

## 4. Non-goals / out of scope

- **A general BI tool.** XMS ships a fixed catalog of measures and views. A self-service report builder (DR-10) is Phase 4 and will be built on the same measure catalog, not as a free-form query surface.
- **Push updates in the pilot.** DR-01 is satisfied by a defined 60-second polling interval; server push (SSE or WebSocket) is a Phase 4 enhancement once the operational load justifies it.
- **Agent-built decks.** The harness can produce a whole PPTX through an agent, but the pack is deterministic and rendered inside XMS (ADR-11); Axel writes the narrative only.
- **Editing the pack after generation.** The reviewer edits the narrative and regenerates; nobody edits slides in the product. A downloaded PPTX can be edited in PowerPoint like any file.
- **Real-time SLA math in the dashboard.** The dashboard reads server-computed clocks; it never recomputes due times (Architecture §4).
- **Customer health score (DR-09), QBR deck (DR-08), NL query (AI-15)** are Phase 4. The measure catalog and snapshot model are designed so they need no new data.
- **Finance reconciliation exports** with locked-period semantics belong to [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md); this module exports what a view shows.

## 5. User-facing behavior

### 5.1 Vocabulary

| Term | Meaning |
|---|---|
| Measure | A named number with one definition, one grain and one source (§5.2). The same measure feeds dashboards, packs and exports |
| Live measure | Computed on request from current rows (for example open tickets right now) |
| Snapshot measure | Copied once per account per day at the account's midnight and never recomputed (for example SLA attainment for a day) |
| Period | The window a pack or a dashboard filter covers: week (Monday to Sunday in the account's time zone), month, quarter, contract period |
| Report pack | A generated WSR or QBR: one PPTX, one PDF, one narrative version, one distribution log |
| Schedule | When a pack is generated and to whom it is sent, per account |
| Portfolio | The operator-wide roll-up of every account the viewer is granted |

### 5.2 Measure catalog

The catalog is the single list of numbers the product reports. Each measure has one definition; dashboards, packs and exports label them identically.

| Measure | Definition | Grain | Live or snapshot |
|---|---|---|---|
| Open tickets | Tickets not in a terminal state | account, group, assignee | Live |
| Backlog by age | Open tickets bucketed by business days since creation: 0 to 2, 3 to 5, 6 to 10, over 10 | account | Live and daily snapshot |
| Tickets created, resolved, closed | Counts by event date in the account's time zone | account, day, type | Snapshot |
| Volume trend | Created and resolved per week for the last 13 weeks | account | Snapshot |
| SLA attainment (response) | Tickets whose response clock was met divided by tickets whose response clock ended in the period | account, priority, type | Snapshot |
| SLA attainment (resolution) | Same for the resolution clock; a breached-then-resolved ticket counts as missed | account, priority, type | Snapshot |
| SLA at risk | Open tickets with an unmet clock under 25 percent of its target remaining, or paused past a configurable age | account | Live |
| Breached now | Open tickets with a latched breach | account | Live |
| MTTR by type | Mean business minutes from creation to resolution, excluding paused time, for tickets resolved in the period | account, type, priority | Snapshot |
| Reopen rate | Tickets reopened within 14 days of resolution divided by tickets resolved in the period | account | Snapshot |
| Team utilisation | Logged minutes divided by available capacity minutes for the period | operator, group, person | Snapshot (weekly) |
| Consumption | Billable hours logged in the contract period against contracted hours and value | account, contract, period | Live and daily snapshot |
| Forecast to period end | Consumption projected at the current run rate | account, contract | Live |
| Portfolio budget burn | Consumption for every granted account, ranked by percent consumed | operator | Live |
| CSAT | Mean score and response rate for ticket-close surveys and the latest quarterly survey | account, quarter | Snapshot |
| Notable tickets | P1 and P2 tickets touched in the period, breaches, out-of-scope flags, escalations | account, week | Live at generation, frozen in the pack |
| Health score (Phase 4) | Composite of SLA attainment, CSAT, budget position and engagement signals | account | Snapshot |

Definitions that need care: "resolved in the period" means the resolution stamp falls in the period, not the close; paused minutes are excluded from MTTR because the pause reason is the evidence the client accepted the wait; utilisation uses the capacity definition from [Capacity & Allocation](../capacity-and-allocation/FUNCTIONAL-SPEC.md).

### 5.3 Internal operational dashboard (DR-01, DR-02)

The default landing page for internal users, in the POC grammar (eyebrow "MANAGED SERVICES", title "Operations", one-line subtitle).

- **Scope selector**: the accounts the user is granted, defaulting to all; group and assignee filters; a period selector for snapshot measures (this week, last week, last 4 weeks, custom).
- **Ink banner**: one synthesis line, for example "SLA attainment 94 percent across 6 accounts this week, 3 tickets breached now, 2 accounts over 90 percent consumed". Written from measures, not by Axel.
- **ScoreCard strip**: Open tickets, Breached now, SLA at risk, Resolution attainment (period), Reopen rate (period), Utilisation (period). Each tile filters the ticket list when clicked.
- **Panels**: Backlog by age (bar), Volume trend (13-week line, created vs resolved), SLA attainment by priority (bar), MTTR by type (bar), Consumption per account (progress bars, red over 100 percent).
- **Pillar rail**: Oldest unresolved (top 5 with SLA badge), At-risk tickets (top 5), Accounts needing attention (over threshold or breached).
- **Refresh**: every 60 seconds while the tab is visible; a "Updated 12 seconds ago" stamp; a manual refresh button. Snapshot measures show the snapshot date.
- **Empty states**: no granted accounts shows "Ask an administrator for account access"; an account with no tickets shows the banner with zeros and a "Create the first ticket" link.

### 5.4 Portfolio view (DR-02 portfolio burn)

For practice leads (permission `reports:view-portfolio`): one row per granted account with consumption percent and forecast, resolution attainment, backlog, breached now, CSAT, health (Phase 4), last WSR sent date, next WSR due. Sorted by attention (breached, then over-threshold consumption, then attainment below target). Row click opens that account's dashboard. Export to Excel from the toolbar.

### 5.5 Client dashboard (DR-03)

Rendered inside the portal for portal users with `portal:view-org-tickets`. Same measures, strictly limited:

- Their open tickets by state and priority; their tickets created and resolved this period.
- Their SLA attainment for the period, by priority.
- Their consumption and forecast only if the account setting "consumption visible in portal" is on; otherwise the panel does not render at all (no locked placeholder).
- Their CSAT summary.
- Nothing about other accounts, internal utilisation, work notes, rate cards or assignee names unless the account setting exposes assignee names.

The client dashboard and the WSR read the same snapshot rows, so a number on the call matches the number in the portal.

### 5.6 The weekly report pack (DR-04)

A pack is generated per account per schedule (default Monday 06:00 in the account time zone, covering the previous Monday to Sunday). Structure, one section per slide unless noted:

| Slide | Content | Source |
|---|---|---|
| 1 Cover | Account name and logo, "Weekly Status Report", period, prepared by, operator branding | Account, schedule |
| 2 Executive summary | Three to five sentence narrative plus a four-tile strip (resolution attainment, tickets resolved, consumption percent, CSAT) | Axel narrative (reviewed), measures |
| 3 SLA attainment | Response and resolution attainment by priority for the week and the trailing 4 weeks; list of breaches with reason where a pause reason exists | Snapshots |
| 4 Ticket volume and backlog | Created vs resolved for 13 weeks; backlog by age; open by type | Snapshots |
| 5 Notable tickets | P1 and P2 activity, escalations, out-of-scope flags, tickets awaiting the client, each with key, title, state, next step | Live at generation, frozen |
| 6 Consumption and forecast | Hours consumed vs contracted this period, forecast to period end, threshold status, hours by activity type | Snapshots and live |
| 7 CSAT | Ticket-close scores for the week, trailing quarter trend, verbatims flagged shareable | Snapshots |
| 8 Next week | Planned changes and windows, scheduled work, requests awaiting client action | Ticket groups and states |
| 9 Appendix | Full ticket list for the period (key, title, type, priority, state, opened, resolved, hours) | Live at generation, frozen |

Rules: any slide with no data is replaced by a one-line "No activity this period" slide rather than an empty chart; consumption slides follow the same visibility setting as the portal; the narrative is always reviewed before sending (§5.8); the PDF is the exact rendering of the PPTX.

### 5.7 Schedules and distribution (DR-05)

Administrators and account owners manage one or more schedules per account: cadence (weekly, monthly, quarterly), day and time in the account time zone, period covered, pack type (WSR, QBR later), format (PPTX and PDF, PDF only), distribution list (portal users, contacts, internal recipients), sender identity (the account's branded address), review required (default on), and an enabled flag. A schedule shows its last run outcome and next run time. "Generate now" produces an off-cycle pack for a chosen period.

### 5.8 Review before send

When a schedule runs with review required, the pack is generated to "Ready for review" and the account owner is notified. The review screen shows the narrative in an editable panel beside the rendered slides (page images), the tile numbers, and a "Regenerate with my edits" action. "Approve and send" delivers the email with links to the PDF and PPTX; "Send without changes" is available for reviewers who accept the narrative as written. If nobody reviews within a configurable grace period (default 24 hours) the schedule marks the run "Awaiting review" and reminds the owner; it never sends unreviewed narrative to a client. Schedules with review off (internal recipients only, or accounts that opted out) send immediately.

### 5.9 Delivery

Delivery runs on the connector framework's report connector: an email to the distribution list with the account branding, a summary of the four headline tiles in the body, presigned links valid for 14 days, and the PDF attached when under 10 MB. Delivery outcome (sent, bounced, failed) is shown on the run; failures retry and then dead-letter with an alert to the account owner.

### 5.10 Exports (DR-06)

Every list and every chart has "Export" with Excel and CSV. Exports contain the raw rows behind the view with the current filters, a header row with measure names, the generation time and the filter description in a second sheet (Excel) or a leading comment line (CSV). Small exports download immediately; exports over 5,000 rows are generated in the background, and the user is notified with a link valid for 7 days. Portal exports are limited to the client dashboard measures and their own tickets.

### 5.11 History and snapshots (DR-07)

Every snapshot measure is captured once per account per day. Editing a ticket after the fact (priority, type, resolution) changes today's picture and never yesterday's. The dashboard marks snapshot measures with the snapshot date; the pack states the generation timestamp on the cover. If a snapshot day is missing (worker outage), the backfill recomputes it from audit events, and the dashboard flags "Backfilled" on that day.

### 5.12 Later: QBR, health score, report builder, NL query

- **QBR deck (DR-08)**: quarterly pack with the WSR structure plus a quarter-over-quarter section, a knowledge base contribution section (articles created, deflections), a capacity and roster section, and a renewal section. Same template and review flow.
- **Health score (DR-09)**: composite of resolution attainment, CSAT, budget position, reopen rate and engagement signals (portal logins, survey responses), weighted per operator configuration, shown on the portfolio view with the reasons.
- **Report builder (DR-10)**: a power user picks measures, grains, filters and a chart from the catalog, saves it as a shared view, and schedules it as an export.
- **NL query (AI-15)**: "Which accounts breached a P1 this month" answered from the measure catalog; owned by [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md); this module exposes the catalog and grains it can query.

## 6. Rollout

1. **Phase 1, Foundations (with Accounts & Administration and Ticket Management foundations):** the measure catalog in code, the daily snapshot job running for every account from day one so history exists before the pilot, exports on the ticket list. No dashboard screens yet.
2. **Phase 2, Focused pilot (with Ticket Management, Time & Budget core):** internal operational dashboard, client dashboard in the controlled portal, Excel and CSV on every view, the WSR pack for the pilot account with the review flow, manual "Generate now", email delivery to internal recipients. Depends on the report connector from [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) and the narrative capability from [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md) (with a plain templated narrative as fallback when Axel is off).
3. **Phase 3, Operational replacement:** schedules with client distribution lists, portfolio view, CSAT measures (with [Client Portal](../client-portal/FUNCTIONAL-SPEC.md) surveys), utilisation (with [Capacity & Allocation](../capacity-and-allocation/FUNCTIONAL-SPEC.md)), backfill tooling, retention.
4. **Phase 4, Later releases:** QBR deck, health score, report builder, push refresh, NL query data surface.

## 7. Success criteria

- A schedule set for Monday 06:00 Europe/London produces a pack covering the previous Monday to Sunday, in "Ready for review" state, before 06:15 London time, for an account with 300 tickets.
- The account owner edits one sentence of the narrative, regenerates, approves, and the distribution list receives the email with working links within five minutes; the run shows "Sent" with the recipients.
- A ticket resolved on Tuesday is re-prioritised on Thursday; the Wednesday snapshot and the Monday pack are unchanged, and Thursday's live view reflects the new priority.
- A portal user of account A opens the client dashboard and sees only account A measures; with consumption visibility off, no consumption panel exists in the page markup at all.
- The internal dashboard with 8 granted accounts and 20,000 open tickets renders in under two seconds and refreshes every 60 seconds without a full reload.
- Exporting the portfolio view produces an Excel file whose per-account consumption percentages equal the values on screen and whose second sheet records the filters.
- A worker outage of 36 hours is followed by a backfill that fills the missing snapshot days from audit events, marked "Backfilled" on the dashboard.

## 8. Open questions

- **Week definition for accounts spanning time zones (UK and Australia teams on one account).** Default assumption: the account's default calendar time zone defines the week; a second schedule can be added for a regional list.
- **Do clients receive the PPTX or only the PDF?** Default assumption: PDF attached, both linked; per-schedule format setting.
- **Should breach reasons (pause reasons) appear in the client pack verbatim?** Default assumption: yes for pauses of kind "awaiting client" and "awaiting third party", since they are the hour-justification evidence; internal-only notes never appear.
- **Narrative fallback when Axel is off for an account.** Default assumption: a templated narrative built from the measures ("Resolution attainment was 94 percent, up from 91 percent") so the pack still ships.
- **Utilisation in the client pack.** Default assumption: never; utilisation is operator data.
- **Reprioritised workbook.** The deck's 75 Must Haves may drop DR-05 or DR-07 from the pilot. Default assumption: this spec's phase mapping stands until Sofi/DMS supply the current workbook (Decision Log open item).
