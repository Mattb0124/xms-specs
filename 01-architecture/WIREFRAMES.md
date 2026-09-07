# Wireframes v2 and v3: dissection and adoption

**Status:** Adopted as the UI source of truth for the five built screens (ADR-17); v3 supersedes v2 for list semantics and colour (ADR-18)
**Owner:** Matt Brown
**Last updated:** 2026-09-05
**Related:** [User Experience](./USER-EXPERIENCE.md), [Design System](./DESIGN-SYSTEM.md), [Thirty-Day Build](../03-delivery/THIRTY-DAY-BUILD.md), [Implementation Plan](../03-delivery/IMPLEMENTATION-PLAN.md), frontend skills `xms-web-design-system`, `xms-web-data-table`, `xms-web-ui-component`
**Source:** `XMS v2 (standalone).html` and `XMS v3 (standalone).html` (Claude Design prototypes, 1500 by 1020, both delivered 2026-09-05), archived at `01-architecture/wireframes/XMS-v2-standalone.html` and `01-architecture/wireframes/v3/XMS-v3-standalone.html` with rendered screens (`01-queue.png` to `15-axel-open.png`) beside each

This document takes the prototype apart: what it contains, the shell and screen anatomy, the engineering callouts it carries, the visual language it fixes, where it changes earlier decisions, and how it lands in the plan and the skills. The prototype is hi-fi and self-describing (its own header reads "Hi-fi · AIXelerator system · no row striping"), so it is treated as design intent, not as a sketch.

---

## 1. What the prototype contains

| Part | Content |
|---|---|
| Built screens (5) | Queue, Ticket record (six tabs), My work, Dispatch, Operations. Each carries a "Notes for engineering" strip with numbered callouts referencing requirement IDs |
| Navigation tree (27 screens) | Work: My work, Queue, Dispatch, Quarantine. Knowledge: Solutions, Review queue, Configuration items, Templates. Time: My timesheet, Team time, Billing periods. Accounts: Accounts, Contracts. Capacity: Roster, Allocation grid, Skills matrix. Reports: Operations, Portfolio, Report packs, Exports. Admin: Users, Configuration, Connectors, AI, Migration. The 22 unbuilt screens open as stubs with a one-line purpose ("Specified and wireframed, not yet restyled into this system") |
| Shell | Navy finder bar, pinned sidebar with starred views and "Browse all screens", content header bar with filter pills, the All / Favourites / History overlay, the docked Axel panel |
| Prototype controls | `startScreen` (queue, ticket, mywork, dispatch, dashboard), `showCallouts`, `axelDefaultOpen` |
| Sample data | Four fictional accounts (Brookfield UK, Kestrel Retail, Northwind Group, Aldergate Energy), CS keys, KB keys, an EPM Close group, realistic consolidation incidents |

Rendered references (all in `01-architecture/wireframes/`): `01-queue`, `02-ticket-conversation`, `03-ticket-activity`, `04-ticket-time`, `05-ticket-resolution`, `06-ticket-links`, `07-ticket-sync`, `08-mywork`, `09-dispatch`, `10-dashboard`, `11-stub-quarantine`, `12-overlay-all`, `13-overlay-favourites`, `14-overlay-history`, `15-axel-open`.

## 2. Shell anatomy (applies to every internal screen)

| Zone | What it is | Rules from the prototype |
|---|---|---|
| Navy finder bar (56px, `#10193A`) | Logo and "The Hackett Group"; three finders All, Favourites, History; a centre workspace pill ("THG PROD, Queue: my group, open" with a star); global search ("Search tickets, accounts, solutions", shortcut `/`); Axel button; notifications bell with unread count; user avatar | The bar holds finders only, never destinations. Each finder opens the same overlay against a dimmed workspace. The centre pill names the instance and the current view; its star favourites that exact view, which is what populates the pinned sidebar and Favourites |
| Pinned sidebar (238px, white) | "Pinned" header with an edit pencil; six pinned screens with count badges (Queue 42, Dispatch 7, Quarantine 3); "Starred views" (saved views with counts); "Browse all screens · 27" at the foot | A short pinned list plus starred views, not the module tree. The full tree lives in the All overlay, where each item has a pin toggle |
| All / Favourites / History overlay | Navy panel anchored under the finder bar: All shows the 27 screens grouped by section with pin icons and badges and a "Filter screens" box; Favourites lists screens, saved views, accounts and report packs with a type label; History lists recent records and screens with relative time | One overlay component, three data sources |
| Content header bar (grey `#F0F3FA`, 44px) | Hamburger, funnel icon, screen title with a chevron (a screen switcher), filter pills, gear, a local search, the primary action (blue "New") | The first pill is the primary "Show:" dimension in blue outline; the rest are plain. Pills are the saved-view state and rewrite the URL |
| Breadcrumb line | "All › My group › Open", right-aligned count ("42 open tickets") and "Save as view" | The condition trail; clicking a segment removes that criterion |
| Notes for engineering | A strip below the workspace with numbered callouts and requirement references | Prototype only; not a product surface |
| Axel panel (docked right, 340px) | Header "Axel · desk" or "Axel · CS0001204"; suggestion cards with Accept and Reject; tool-call rows in mono ("search_solutions(ci="HFM PROD") → 3 results"); withheld notices; "Ask about this ticket" input; footer rule "Nothing applies without a click. Every accept, edit and reject lands in Activity" | Context follows the screen; the panel pushes the content, it does not overlay it |

## 3. Screen anatomy and behaviour

### 3.1 Queue

- Card with a "Count 42" badge, an in-card search ("Search by key, description or requester"), filter and column icons; then the table: checkbox, Key (mono, blue link), Short description, Account, Type, Priority pill, State pill, Assignee, SLA (mono countdown; "−38m" red for breached, amber under 25 percent, "paused" grey, "no SLA" grey), Updated; SLA is the default sort; pager 1 to 5.
- Callouts: filter pills are the saved-view state and rewrite the URL so a pasted link reproduces the list (TM-15); no row striping, rows separate on a hairline and a hover fill (design); row click navigates in place and browser back restores view, filter, sort, scroll and selection (UX §6); export carries the current columns and the permission filter of the person who ran it (DR-06).

### 3.2 Ticket record

- Record bar: key (mono, blue) and title; a row of pills: state ("In progress" with a chevron, the transition menu), priority (P2), SLA ("Resolution 3h 12m left" in mono with a blue dot); "Ask Axel" and a more menu on the right.
- Three columns: **Properties** (label-left stacked list: Account, Requester, Type, Category, Configuration item, Impact / urgency, Priority "P2 · derived from the matrix", Contract, Group, Assignee, Source, Out of scope, External reference, Watchers); **work area** with tabs Conversation, Activity, Time, Resolution, Links, Sync; **rail** with Service levels (Response "met 15:36" filled bar; Resolution meter with a grey paused segment and the caption "Grey segment is 2h 10m paused, awaiting client"), Contract (87.5 of 100 h with a burn bar and "Forecast 103 h. The 90 percent threshold notified the owner on 2 Sep"), Similar solutions (article title, "KB000142 · used 9 times", "Use").
- Conversation: composer with a Public reply / Work note toggle, "Draft with Axel", "Template", "Emails the requester and 2 watchers", Send; an "Axel summary" block ("regenerated on new activity") in the AI tint; the thread with initials, name, kind chip ("Public · email in", "Public reply" with the "First response met" marker, "Work note", "Public · portal") and time.
- Activity: actor filter chips All, User, Portal, System, Sync, AI; rows with an actor chip, text and time (category suggestion accepted with confidence, SLA clocks stamped on the account calendar, state changes, first response met, pause reason, portal reply resumed the clock with excluded minutes, comment dispatched to ServiceNow).
- Time: rows of person, activity, class, hours, including a linked adjustment shown as its own row.
- Resolution: Resolution code, Solution ("KB000142, or create an article from this ticket"), Resolution notes ("Cause and fix, in the requester's language"), Time exemption; the Close discipline checklist (notes describe cause and fix, solution linked or article drafted, time logged for all contributors, requester informed by public reply).
- Links: parent, duplicate, related, blocks, each with key and title. Sync: the external record and direction.
- Callouts: the state pill is the only route through the state machine and collects required fields inline (TM-03, TM-09); properties commit on change or blur with rollback on conflict (UX §6); public reply emails requester and watchers with threading, work notes never leave (TM-10); violet marks AI-origin content only and is never used for status (AI-04); meters show target, elapsed, remaining and pause segments with the reason, a breach latches and survives reopen (TM-05, TM-07).

### 3.3 My work

- Four scorecards (Assigned to me 11 across 3 accounts, Breached 1 with the key, At risk 3 under 25 percent, Awaiting client 4 clocks paused); a one-line Axel brief with Dismiss ("Two P1s on Brookfield are within an hour of breach, and you logged 2.5 of 7.5 hours yesterday"); "Needs attention" list ("mine first, then group unassigned") with key, title, account, state pill, SLA; a right rail with Time today (2.5 / 7.5 h bar, the unlogged nudge "Unlogged 11:00 to 13:30, likely CS0001204" with Log now and Not now) and Waiting on me (out-of-scope flags to approve, articles in review, report narratives to approve, withheld AI suggestions, each with a count).
- Callouts: scorecards filter the list below on click (TM-15); the brief is one generated line, dismissible, never blocking (AI-06); the nudge writes an entry from here and collapses when there is no gap (AI-06, TB-02).

### 3.4 Dispatch

- One card per unrouted ticket: key, title, account, age badge; a row with Group select, Assignee select, an "Axel suggests S. Ali" chip or a capacity warning chip ("104 percent of capacity, override reason required"), "Assign to me" and a blue "Confirm".
- Callouts: group and assignee are on the row itself, Confirm removes the row and decrements the sidebar badge (TM-08); over 100 percent capacity warns and requires an override reason but never blocks (CAP-06).

### 3.5 Operations (the operations dashboard)

- A synthesis line in the AI tint ("SLA attainment held at 94 percent across 12 accounts this month. Three accounts are trending to overage; Brookfield UK is the exception at 87.5 of 100 hours with 26 days remaining"); six tiles (Open, Breached, At risk, Mean time to resolve, Reopen rate, Utilisation) with a delta caption; four panels (Backlog by age bars, Open by state list with bars, Open by priority bars, Portfolio burn list); filter pills "This month" and "Accounts: all".
- Callouts: the synthesis line is generated from the same snapshots the tiles read, with numbers frozen at render (DR-01, AI-05); every tile and bar links into the Queue with the matching condition set applied (DR-01).

### 3.6 Stubs

Every unbuilt screen renders its title and purpose line from the tree (for example Quarantine: "Email that could not be trusted automatically, with three decisions that each finish the item"). These purpose lines match the [User Experience](./USER-EXPERIENCE.md) catalog and are the acceptance one-liners for those screens.

## 4. Visual language (measured from the prototype)

| Element | Value |
|---|---|
| Canvas | `#F4F5F7`; content header bar `#F0F3FA`; cards `#FFFFFF` with a 1px `#E4E8F5` border and radius 6px; card shadow `0 1px 3px rgba(15,22,35,.04), 0 0 0 1px rgba(37,99,235,.04)` |
| Navy | `#10193A` finder bar and overlay; `#0F1623` darkest text |
| Text | `#0F1623` headings and keys, `#3D4A5C` body, `#5A6784` labels, `#7B8CA0` muted, `#9AA3B2` placeholders |
| Blue (actions and selection) | `#2563EB`, hover `#1D4ED8`; selected pinned item `#EDF1FF` with a 3px `#2563EB` left bar; blue tints `#EFF4FF`, `#D8E3FA`, `#C7D6F7` |
| Signals | Breach red `#DC2626` with `#B42318` on `#FEF3F2` and border `#F5C9C4`; amber `#E8C766` for at-risk; paused grey `#9AA3B2`; state pills blue tint text `#1D4ED8` on `#EFF4FF` |
| AI (violet family) | Summary and suggestion blocks on `#EDF1FF` with `#C7D6F7` borders and `#7C9AE8` accents; used only for AI-origin content |
| Type | Inter 400 / 500 / 600 / 700 for UI; IBM Plex Mono 400 / 500 / 600 for keys, SLA values, counts, tool calls and uppercase labels (11px, 600, `.06em` tracking); IBM Plex Serif 500 appears only in the prototype's own notes header |
| Scale | 11px caps labels; 12px meta and chips; 13px body and table cells; 14px titles and inputs; 15px card titles; 22 to 26px scorecard numbers in mono |
| Radii | 4px inputs and buttons; 5 to 6px cards and panels; 999px pills |
| Geometry | Finder bar 56px; content header 44px; pinned sidebar 238px; controls 32 to 34px; table rows about 47px; rail cards 16px padding; pills `5px 10px` |
| Lists | No row striping; hairline `#E4E8F5` between rows; hover fill; sticky header |

## 5. What changes from the earlier documents

| Topic | Before (Design System, UX, skills) | Now (wireframes v2) | Decision |
|---|---|---|---|
| Dense list rows | Zebra striping (POC and the frontend skills) | No striping: hairline plus hover fill | Wireframes win; `--xms-zebra` retired, `--xms-row-hover` kept |
| Top bar | Slim top bar, product-owned hamburger | Navy finder bar with All / Favourites / History, centre workspace pill with star, global search, Axel, bell, avatar | Adopted; the hamburger stays in the content header |
| Sidebar | Full module tree filtered by permission | Pinned list plus starred views plus "Browse all screens"; the tree lives in the All overlay with pin toggles | Adopted; permission filtering applies to the tree and the pins |
| Screen switching | Sidebar only | Content header title with a chevron switches between screens of the same family | Adopted |
| Identity palette | Ink `#0c1626`, cobalt `#2e5bff`, canvas `#fbfcfe`, tint `#eff3fa` | Navy `#10193A`, blue `#2563EB`, canvas `#F4F5F7`, tints `#F0F3FA` and `#EFF4FF` | Token values updated; token names unchanged so components do not change |
| Typeface | One typeface, Inter | Inter plus IBM Plex Mono for keys, SLA, counts and caps labels | Adopted; mono is the second face |
| Dashboard name | Operations dashboard | "Operations" | Adopted in navigation labels |
| AI colour | Not specified beyond chips | Violet family for AI-origin content only, never for status | Adopted as a rule |
| Ticket record composition | Properties, tabs, rail | Same three zones; rail order fixed as Service levels, Contract, Similar solutions; tabs fixed as Conversation, Activity, Time, Resolution, Links, Sync | Adopted |
| Dispatch | Table rows with inline pickers | One card per ticket with pickers, Axel suggestion chip, capacity warning, Assign to me, Confirm | Adopted |
| Portal | Not in the prototype | Unchanged from the UX document; portal wireframes are a follow-up | Open |

## 6. How it lands

- **Design tokens** (`frontend/styles/tokens/xms-scope.css`): the `--xms-*` values in §4; `--xms-mono` font family added; `--xms-ai-bg`, `--xms-ai-border`, `--xms-ai-accent` added for the violet family; `--xms-zebra` removed.
- **Components** (Implementation Plan P1.4.1 and P1.4.2, Thirty-Day Build days 1 to 4): `FinderBar`, `WorkspacePill`, `FinderOverlay` (All, Favourites, History), `PinnedSidebar` with `StarredViews`, `ContentHeaderBar` with `FilterPill`, `BreadcrumbTrail`, `DenseTable` (no striping), `KeyLink` (mono), `StatePill`, `PriorityPill`, `SlaValue` (mono), `ScoreTile`, `MeterBar` with pause segments, `RailCard`, `ActorChip`, `AxelPanel` with `SuggestionCard`, `ToolCallRow`, `WithheldNote`, `BriefLine`, `NudgeCard`, `DispatchCard`, `CloseDisciplineChecklist`.
- **Skills**: `xms-web-design-system` and `xms-web-data-table` updated (no striping, navy shell, mono, AI violet); `xms-web-ui-component` unchanged.
- **Plan**: the five built screens are the acceptance reference for P1.5.5, P2.12.4, P2.19.3 and the day-30 demo; stub purpose lines are the acceptance one-liners for the other 22 screens.
- **Prototype callouts** become acceptance checks in the relevant "Done when" lines (they already cite the requirement IDs).

## 7. Gaps the prototype does not cover

Portal screens, New ticket record form, Quarantine, Solutions record, Timesheet, Contracts, Report pack review, Admin screens, and every empty and error state. These follow the [User Experience](./USER-EXPERIENCE.md) catalog and the grammar in §2 to §4 until wireframed; a second prototype round should cover New ticket, Quarantine, Solutions and the portal Home and Request screens before day 11 of the build.

## 8. Version 3 (2026-09-05): semantic colour and the three list patterns

The v3 prototype (`XMS v3 color.dc.html`, header "Hi-fi · semantic color: state, type, account") keeps everything in §2 to §7 and changes the list and the colour semantics. Renders are in `01-architecture/wireframes/v3/`; compare `v3/01-queue.png` with `01-queue.png`.

### 8.1 State ramp (one colour family per ticket state)

| State | Text | Fill | Border |
|---|---|---|---|
| New | slate `#334155` | `#F1F5F9` | `#D7DEE8` |
| In progress | blue `#1D4ED8` | `#EFF4FF` | `#CBDCFA` |
| Awaiting client | amber `#9A5B06` | `#FEF6E7` | `#F4DDB4` |
| Awaiting approval | teal `#0E7490` | `#ECFAFE` | `#BFE6F0` |
| Resolved | green `#0F7A50` | `#EDFAF3` | `#BEE6D3` |
| Closed | grey `#64748B` | `#FFFFFF` | `#DDE2EA` |

State pills use this ramp everywhere a state appears (Queue, My work, the record bar, Operations lists). SLA and priority keep their own signals (breach red, at risk amber, P1 red, P2 to P4 quiet), so a state colour never reads as an SLA colour: Awaiting client amber is a state, at-risk amber is a clock, and the two never sit in the same cell.

### 8.2 Type bars

A 3px vertical bar to the left of the Type value: Incident red `#DC2626`, Request teal `#0E7490`, Change violet `#7A5AF8`, Problem amber `#B45309` (Project Task takes the next free hue when it is added). The bar is the only colour in the Type cell; the label stays body text.

### 8.3 Account identity dots

An 8px dot before every account name (list cells, Dispatch cards, My work rows) from a six-hue palette assigned per account: blue `#2563EB`, teal `#0E7490`, amber `#B45309`, green `#0F7A50`, violet `#7A5AF8`, magenta `#BE185D`; unknown accounts fall back to grey `#64748B`. The assignment is deterministic per account (stored on the account record at creation, editable by an administrator) so a consultant learns "Brookfield is blue" once. Dots never replace the name.

### 8.4 The three Kefron list patterns

| Pattern | What the prototype shows | Behaviour |
|---|---|---|
| Removable filter chips | Each filter pill carries a "×"; a dashed "+ Add filter" button follows the pills; "Clear all" sits after it. Present on Queue, My work, Dispatch, Operations and the Ticket header | "×" removes that criterion and rewrites the URL; "Add filter" opens the condition builder for one new criterion; "Clear all" returns to the system default for the screen; the primary "Show:" pill is not removable |
| Blue selection bar | When rows are checked, a blue-tinted bar appears under the card header: "3 selected", then Assign, Change state, Add tag, Export, and on the right "one audit event written per record" with a dismiss "×" | Actions apply to the selection (bulk, TM-16) and each writes one audit event per record; Export exports the selection with the current columns; Escape or "×" clears the selection |
| Rows per page | Footer: "Showing 1 to 10 of 42", the pager, and a "Rows per page" select (10 default; 25, 50, 100) | The page size is part of the saved-view state and the URL |

### 8.5 What v3 changes in the adoption

- Tokens: `--xms-state-<name>-fg/-bg/-br` for the six states; `--xms-type-<name>` for the four types; `--xms-account-1` to `-6` for identity dots.
- Components: `FilterChip` (removable), `AddFilterButton`, `ClearAllLink`, `SelectionBar` with `BulkAction`, `TableFooter` with `RowsPerPage`, `TypeBar`, `AccountDot`; `StatePill` now takes the ramp, not the generic `--state-*` trios.
- Data: `op.accounts.identity_hue` (1 to 6) set at creation; saved views persist `page_size`.
- Skills: `xms-web-data-table` and `xms-web-design-system` updated for the ramp, the bars, the dots and the three patterns.
- Everything else in v2 (shell, screens, callouts, type scale) is unchanged; the engineering callouts are identical.
