# ClickUp publication map

**Status:** Published 2026-09-04, revision 3 modules added 2026-09-10, MCP and go-live re-sync 2026-09-13. **ClickUp is the system of record for specs from 2026-09-13** (see the ruling below)
**Owner:** Matt Brown
**Workspace:** 9015896416, space "X Platforms" (901511370980)
**List:** XMS, id `901525777420`, https://app.clickup.com/9015896416/v/l/li/901525777420

## The ruling, 2026-09-13: ClickUp is the system of record

Until 2026-09-13 ClickUp was a one-way copy of this repository: edit the markdown, then
re-sync the page, never edit ClickUp first. **That is reversed. A spec is now edited on
its ClickUp page**, and the markdown in this repository is the frozen record of how each
document read on 2026-09-13.

Why it was reversed: the one-way copy kept going stale, because nothing obliged anyone
to push it. On 2026-09-13 fourteen pages had drifted from disk, including every path
touched by the ADR-19 move of the MCP into `backend/src/mcp`, so ClickUp still sent a
reader to another team's Python repository. Worse, the two current delivery plans (the
[Go-Live Plan](./GO-LIVE-PLAN.md) and its [Implementation Plan](./IMPLEMENTATION-PLAN-GO-LIVE.md))
had never been published at all, so the page a reader found was the superseded plan,
presented as though it were live. A copy nobody has to refresh is a copy that lies, and
the honest fix is to stop keeping two.

How to work now:

- **Edit a spec:** find its `document_id` and `page_id` below and use
  `clickup_update_document_page`. Editing the markdown here reaches nobody.
- **Add a spec:** `clickup_create_document_page` under the right document, then add its
  row to the table below in the same change. A page missing from this map is a page the
  next person cannot find.
- **Read a spec:** read the page. The markdown here is only trustworthy for anything
  dated on or before 2026-09-13.
- The `xms-write-spec` skill carries the same rule, and `aibl-clickup` carries the
  mechanics (folder, ids, the create and update calls, the markdown ClickUp rejects).

What the repository still owns, and why the frozen tree is kept rather than deleted:

1. `00-overview/scripts/build_register.py` reads the requirements **workbook**, not the
   specs, and writes `requirements.csv`, `requirements.json` and
   `REQUIREMENTS-TRACEABILITY.md`. It still runs and is still never hand-edited. Its
   markdown output now has to be published like any other spec change.
2. `00-overview/scripts/check_links.py` validates relative links between the frozen
   files. It cannot see ClickUp pages, so a cross-document link written on a page is
   checked by nothing: name the document and section in words ("AI Integration section
   4") rather than relying on a relative path that will not resolve there.
3. Every skill, `CLAUDE.md` and spec that cites a section by path ("Security & Tenancy
   section 2.1") now names the frozen copy. That is still the right way to name a
   section; the path is the document's name, not a live link.

**Still open, and worth a decision:** the frozen markdown and the ClickUp pages will
drift the first time somebody edits a page, and nothing detects that. A checker that
diffs each page against its frozen file would catch it, or the frozen tree could be
deleted outright once the team trusts the pages. Neither is built.

| Document | document_id | Pages (local source) |
|---|---|---|
| XMS 00 · Overview | `8cp7ab0-48195` | README, Product Vision, Glossary, Decision Log, Requirements Traceability Matrix, Clarifications needed |
| XMS 01 · Architecture | `8cp7ab0-48215` | Architecture, Domain Model, Data Model, Security and Tenancy, Security Assurance, AI Integration, Integration Patterns, Platform and Operations, Design System, User Experience, Wireframes v2, Audit Log and User Analytics, AIX Pattern Reuse |
| XMS 02 · Accounts & Administration | `8cp7ab0-48235` | Functional Spec, Technical Spec |
| XMS 02 · Ticket Management | `8cp7ab0-48255` | Functional Spec, Technical Spec |
| XMS 02 · Solution Knowledge Base | `8cp7ab0-48275` | Functional Spec, Technical Spec |
| XMS 02 · Time, Contracts & Budget | `8cp7ab0-48295` | Functional Spec, Technical Spec |
| XMS 02 · Capacity & Allocation | `8cp7ab0-48315` | Functional Spec, Technical Spec |
| XMS 02 · Client Portal | `8cp7ab0-48335` | Functional Spec, Technical Spec |
| XMS 02 · Email Intake & Outbound | `8cp7ab0-48355` | Functional Spec, Technical Spec |
| XMS 02 · Dashboards & Report Packs | `8cp7ab0-48375` | Functional Spec, Technical Spec |
| XMS 02 · ServiceNow Sync | `8cp7ab0-48395` | Functional Spec, Technical Spec |
| XMS 02 · Axel AI Functionality | `8cp7ab0-48415` | Functional Spec, Technical Spec |
| XMS 02 · Data Migration & Cutover | `8cp7ab0-48435` | Functional Spec, Technical Spec |
| XMS 02 · Platform Integrations | `8cp7ab0-48455` | Functional Spec, Technical Spec |
| XMS 02 · Resolution Ladder & Routing | `8cp7ab0-50115` | Functional Spec, Technical Spec |
| XMS 02 · Measurement & Calibration | `8cp7ab0-50135` | Functional Spec, Technical Spec |
| XMS 02 · Account Health & Experience | `8cp7ab0-50155` | Functional Spec, Technical Spec |
| XMS 02 · Time Certification | `8cp7ab0-50175` | Functional Spec, Technical Spec |
| XMS 02 · Collaboration Signal | `8cp7ab0-50195` | Functional Spec, Technical Spec |
| XMS 02 · Configuration Governance | `8cp7ab0-50215` | Functional Spec, Technical Spec |
| XMS 02 · Outcomes | `8cp7ab0-50235` | Functional Spec, Technical Spec |
| XMS 03 · Delivery | `8cp7ab0-48475` | Roadmap, Test Strategy, Thirty-Day Build, Implementation Plan (superseded), TODO, ClickUp Publication Map, **Go-Live Plan** (page `8cp7ab0-15355`, added 2026-09-13), **Implementation Plan to go-live** (page `8cp7ab0-15375`, added 2026-09-13, the current plan) |

Publishing rule learned 2026-09-04: ClickUp rejects a page (HTTP 400) when a markdown table cell contains an unescaped pipe inside a code span; `check_links.py` now flags this. Escape as `\|`.

Full re-sync of every page run 2026-09-04 after ADR-14 and the audit and analytics addition.

Re-sync of 2026-09-13, the last one under the old one-way rule, covering everything that
had drifted since 2026-09-10: AI Integration (the MCP tool gate, C-07 and C-08), Decision
Log (ADR-19), TODO, Architecture, Platform and Operations, AIX Pattern Reuse, Axel AI
Functionality (both pages), Platform Integrations (both pages), Solution Knowledge Base
(both pages) and Thirty-Day Build; plus the two go-live pages, which had never been
published. The Integrations pair and the AI technical spec were corrected rather than
copied: they still specified the `GET /v1/internal/connectors/mcp/state` kill switch that
C-07 withdrew, and the `current_bearer` harness change that ADR-19 withdrew.

One page was deliberately not re-synced: **Implementation Plan** (`8cp7ab0-12795`), the
2026-09-04 plan. It is superseded from 2026-09-14 by the go-live plan now published
beside it, and its only drift is the MCP path rename plus its own superseded status line.
It is listed here so the gap is known rather than discovered.

Document URL pattern: `https://app.clickup.com/9015896416/docs/<document_id>`.

Note: an older list "ServiceNow Replacement Project" (`901525427419`) exists in the same space from the assessment phase; the XMS list is the home for these published docs. It is a docs home only: XMS tickets go in the current sprint list under the `X Platform Sprints` folder, never in this list.
