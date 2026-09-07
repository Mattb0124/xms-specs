# ClickUp publication map

**Status:** Published 2026-09-04
**Owner:** Matt Brown
**Workspace:** 9015896416, space "X Platforms" (901511370980)
**List:** XMS, id `901525777420`, https://app.clickup.com/9015896416/v/l/li/901525777420

ClickUp is a one-way copy of this repository. Edit the local markdown, then re-sync the page with `clickup_update_document_page` (document id below, page id from `clickup_list_document_pages`). Never edit content in ClickUp first.

| Document | document_id | Pages (local source) |
|---|---|---|
| XMS 00 · Overview | `8cp7ab0-48195` | README, Product Vision, Glossary, Decision Log, Requirements Traceability Matrix |
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
| XMS 03 · Delivery | `8cp7ab0-48475` | Roadmap, Test Strategy, Thirty-Day Build, Implementation Plan, TODO, ClickUp Publication Map |

Publishing rule learned 2026-09-04: ClickUp rejects a page (HTTP 400) when a markdown table cell contains an unescaped pipe inside a code span; `check_links.py` now flags this. Escape as `\|`.

Full re-sync of every page run 2026-09-04 after ADR-14 and the audit and analytics addition; ClickUp matches disk as of that sync.

Document URL pattern: `https://app.clickup.com/9015896416/docs/<document_id>`.

Note: an older list "ServiceNow Replacement Project" (`901525427419`) exists in the same space from the assessment phase; the XMS list is the home for these published docs. It is a docs home only: XMS tickets go in the current sprint list under the `X Platform Sprints` folder, never in this list.
