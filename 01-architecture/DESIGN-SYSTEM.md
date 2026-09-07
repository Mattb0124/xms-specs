# Design System: XMS Web

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Architecture](./ARCHITECTURE.md), [Wireframes v2](./WIREFRAMES.md), [User Experience](./USER-EXPERIENCE.md), [AIX Pattern Reuse](./AIX-PATTERN-REUSE.md), XMS POC [Style Guide](C:/Users/matt.brown/Documents/AIX%20Docs/AIX/Specs/xms-ticketing/STYLE-GUIDE.md) and [Screens](C:/Users/matt.brown/Documents/AIX%20Docs/AIX/Specs/xms-ticketing/SCREENS.md)
**Verified against:** `web-ui/app/globals.css`, `web-ui/app/aiinnovation-tokens.css`, `web-ui/tailwind.config.js`, `web-ui/app/layout.tsx`, `web-ui/components/aix-v3/xms/*` on 2026-09-04

---

## 1. Decision

XMS Web looks like the XMS proof of concept: the AI Innovation (aiinds) token system underneath, the Ink & Cobalt solution identity on top, ServiceNow-shaped screens (dense list, condition builder, full-screen record form, label-left properties). It is a separate Next.js application, so the tokens are **seeded once into `frontend/styles/tokens`** from the four AIX files below and then owned by XMS (no shared package: the repositories are separate, ADR-12). No AIX code is copied at runtime; the tokens are the one deliberate seed.

## 2. What is carried over (verified in code)

| Layer in AIX | Where (web-ui) | Carried into XMS as |
|---|---|---|
| Vendored aiinds tokens (`--aiinds-*`, `--color-primary: #245ce8`) | `app/aiinnovation-tokens.css` (1454 lines, "must never be edited") | `frontend/styles/tokens/aiinnovation-tokens.css`, still treated as vendored |
| House aliases and recipes (`--aix-*` aliases, `--state-*` trios, `.aix-state-pill`, dark flips) | `app/globals.css` lines 1 to 282 | `frontend/styles/tokens/house.css` |
| The solution scope (`.xms-scope`, `--xms-*` vars, `.xms-card-shell`, `.xms-section`, `.xms-eyebrow`, `.xms-banner`, `.xms-pill`, control geometry with `!important`, single-typeface rule) | `app/globals.css` from line 1021 | `frontend/styles/tokens/xms-scope.css` with the prefix renamed `--xms-*` and the scope class `.xms-scope` applied on the app root, so the whole product is inside the scope |
| Tailwind colour namespaces (`aix.*`, `xms.*`, `aiinds.*`, shadcn hsl pairs), `darkMode: ["class"]` | `tailwind.config.js` lines 3 and 54 to 160 | `frontend/styles/tokens/tailwind-preset.js` exporting the `xms.*` and `aiinds.*` namespaces |
| Fonts: Inter, Manrope (500 to 800), JetBrains Mono via `next/font/google`, with Noto Color Emoji appended after text fonts | `app/layout.tsx` lines 2 to 23, `globals.css` lines 18 to 31 | Same wiring in `frontend/app/layout.tsx`; the XMS rule "one typeface, Inter, inside the scope" stands |
| Dark mode: `next-themes`, `attribute="class"`, `.dark` and `[data-theme="dark"]` both targeted, `color-scheme: dark` set after the light root | `components/theme-provider.tsx`, `components/client-providers.tsx` | Same provider; portal defaults to light with the account's branding accent |
| shadcn config and the primitives XMS needs (`button`, `dialog`, `select`, `popover`, `command`, `table`, `sheet`, `tabs`, `tooltip`, `form`, `toast`, `skeleton`, `resizable`, `scroll-area`) | `components.json`, `components/ui/*` | Regenerated with the shadcn CLI in XMS, not copied, so versions are XMS-owned |
| House composition components: `sortable-table.tsx` (sticky header, frozen columns, `SortableColumn`), `Panel.tsx`, `BlueTabBar.tsx`, `scorecard.tsx` | `components/aix-v3/` | Rewritten in XMS as `SortableTable`, `Panel`, `TabBar`, `ScoreCard` with the same props; the XMS POC already restyles them, so the XMS versions start from the XMS look |

Known gotchas carried into the XMS token package README, all verified in the source comments: `var()` breaks Tailwind opacity modifiers, so a few colours are raw hex; moving Noto Color Emoji earlier in the stack turns numerals into keycap emoji; `.dark` must be declared after the light `:root` or native controls stay light; `web-ui/styles/globals.css` is a stale second copy and is not a source.

## 3. Tokens

### 3.1 Identity tokens (`.xms-scope`)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--xms-ink` | `#0c1626` | `#eaf0f8` | Titles, ticket keys, all body text (no gray text policy, verified in `.xms-scope`) |
| `--xms-accent` | `#2e5bff` | `#7ea0ff` | Eyebrows, active tab, links, focus, selected row stroke. Never large fills |
| `--xms-accent-light` | `#7ea0ff` | `#7ea0ff` | Accent text inside ink banners |
| `--xms-line` | `#dce3ec` | `#243349` | Borders, dividers, table rules |
| `--xms-bg` | `#fbfcfe` | `#0c1626` | Page canvas |
| `--xms-card` | `#ffffff` | `#141f31` | Cards, tables |
| `--xms-tint` | `#eff3fa` | `#1a2740` | Selected row, table header band, highlighted card |
| `--xms-banner-bg` / `--xms-banner-fg` | `#0c1626` / `#eaf0f8` | inverted | Synthesis banners and empty-state heroes |
| `--xms-zebra`, `--xms-row-hover`, `--xms-cell-hover` | `#f6f7f9`, `#e9effc`, `#d9e4fa` | tinted | Dense list rows |

### 3.2 Signal tokens (never re-themed)

SLA, priority, status and scan-state colours use the shared `--state-*` trios exactly as XMS does (`vocab.ts` `stateTrio(name)`): `needs-input` (amber), `ready`, `blocked`, `progress`, `complete`, `stale`, `overdue` (red). A breached clock is red because red means breached everywhere; the identity accent never colours a signal. P1 and P2 light up; P3 and P4 stay quiet so the priority column reads by exception (POC decision kept).

### 3.3 Per-account branding

Outbound email and the portal carry the account's logo and accent (Account settings). The accent is applied only to the portal header band and email header; the working UI never changes colour per account, so consultants working across accounts see one consistent product.

## 4. Screen grammar (ServiceNow-shaped, from the POC)

These are the patterns the POC converged on and that XMS keeps, with the POC file that demonstrates each:

| Pattern | POC reference | Rule |
|---|---|---|
| Dense list with slim toolbar, funnel, "Show" dimension dropdowns, search, New | `QueueTab.tsx` | Edge-to-edge table, sticky header, zebra rows, row hover then cell hover, 34px controls, 4px radii |
| Condition builder | `QueueTab.tsx` | Field, operator, value rows stacked with AND; breadcrumb filter trail where clicking a segment removes that criterion; saved as a view |
| Full-screen record form for New | `NewTicketPage.tsx` | Slim topbar (back, "Ticket · New record", Cancel, Submit), two-column label-left grid with red asterisks, full-width short description and description, searchable roster combobox for assignee, requester suggestions from contacts seen on the account |
| Record view | `TicketDrawer.tsx` | Thin record bar, editable properties that commit on change or blur, tabbed work area (Conversation, Activity, Resolution), slim related-info rail (contract hours, time, attachments, links) |
| Admin lists and records in the same grammar | `XmsAdminPages.tsx` | Users, roles, accounts, calendars, state machines all use list plus record view; no bespoke admin chrome |
| Sidebar docked, toggled by a header hamburger | `XmsWorkspace.tsx`, `atoms.tsx` | The product owns its own navigation column; the AIX global header is not present in XMS |
| Skeleton mirrors the anatomy | `XmsSkeleton.tsx` | Shown on initial load only; refetches keep rendered data |
| Eyebrow anatomy on each page | `atoms.tsx` `TabHeader` | ALL-CAPS accent eyebrow, ink title, one-line subtitle |
| Ink banner for synthesis and empty states | `atoms.tsx` `InkBanner` | Lead phrase in accent-light, remainder in banner foreground |

Copy rules: no em-dashes anywhere (house rule, overrides the theme's voice guide), middots in tags, arrows allowed in flow statements, ServiceNow vocabulary where it helps adoption (CS keys, work notes, resolution codes, "New record").

## 5. Portal variant

The portal shares the token package and the same components but runs a reduced grammar: no condition builder, no admin, a simpler list (my tickets, my organisation's tickets if permitted), a guided New request form driven by the account's dynamic form definition, article search first ("Find a solution before you submit"), and consumption tiles only when the account setting allows. Accessibility target for the portal is WCAG 2.1 AA because it is client-facing; the internal app targets AA for text contrast and keyboard operation of the list and record views.

## 6. Accessibility and density

- Body text stays `--xms-ink` on `--xms-card` or `--xms-bg` (both pass AA); muted is for de-emphasis only and never carries essential copy.
- Keyboard: list rows focusable and openable with Enter; condition builder operable without a mouse; record form fields in reading order.
- Density: 13.5 to 14px body, 28px page titles, 34px controls, 32px buttons, matching the XMS `!important` geometry block.

## 7. What XMS does not carry over

- The AIX global header, tenant selector, opportunity switcher, dynamic-page navigation folders: XMS has one operator, no opportunities, and a product-owned navigation.
- The `DiscoveryChatWithPanel` component (1316 lines, coupled to eight RTK slices): XMS renders its own Axel panel over a small streaming client (see [AI Integration](./AI-INTEGRATION.md)).
- `next.config.mjs` flags that suppress type and lint errors: XMS builds fail on either (Packmind standard).

## 8. Wireframes v2 alignment (2026-09-05, ADR-17)

The hi-fi prototype in [Wireframes v2](./WIREFRAMES.md) fixes the values that this document had left to the POC. Where the two disagree, the prototype wins for the internal application:

| Token | Value now | Was |
|---|---|---|
| `--xms-ink` | `#0F1623` | `#0c1626` |
| `--xms-body` | `#3D4A5C` | ink |
| `--xms-label` (new) | `#5A6784` | none |
| `--xms-muted` | `#7B8CA0` | ink (no gray text policy relaxed to labels and meta only) |
| `--xms-accent` | `#2563EB`, hover `#1D4ED8` | `#2e5bff` |
| `--xms-navy` (new) | `#10193A` | none (finder bar and overlay) |
| `--xms-line` | `#E4E8F5`, strong `#C9D2E6` | `#dce3ec` |
| `--xms-bg` | `#F4F5F7` | `#fbfcfe` |
| `--xms-bar` (new) | `#F0F3FA` | none (content header bar) |
| `--xms-tint` | `#EFF4FF` | `#eff3fa` |
| `--xms-ai-bg`, `--xms-ai-border`, `--xms-ai-accent` (new) | `#EDF1FF`, `#C7D6F7`, `#7C9AE8` | none; AI-origin content only, never status |
| `--xms-zebra` | removed | `#f6f7f9` |
| `--xms-mono` (new) | IBM Plex Mono | none |

Rules that change: dense lists have **no row striping** (hairline plus hover fill); **IBM Plex Mono** is the second typeface for keys, SLA values, counts, tool calls and 11px uppercase labels with `.06em` tracking; the shell is the **navy finder bar plus pinned sidebar** described in Wireframes v2 §2; the operations dashboard is named **Operations**. The signal rules (red breach, amber at risk, P1 and P2 light up) and the portal branding rule are unchanged. Body text remains ink on card; `--xms-muted` is for labels, meta and placeholders only.

### 8.1 Version 3 semantic colour (2026-09-05, ADR-18)

The v3 prototype adds three semantic colour systems, all recorded in [Wireframes v2 and v3 §8](./WIREFRAMES.md):

- **State ramp** for ticket state pills: `--xms-state-new`, `-in-progress`, `-awaiting-client`, `-awaiting-approval`, `-resolved`, `-closed`, each with `-fg`, `-bg`, `-br`. This replaces the generic `--state-*` trios for ticket states; SLA and priority signals keep their own tokens, and a state colour is never used for a clock.
- **Type bars**: `--xms-type-incident` (red), `-request` (teal), `-change` (violet), `-problem` (amber), a 3px bar beside the type label only.
- **Account identity dots**: `--xms-account-1` to `-6`, an 8px dot before the account name, assigned per account at creation and stored on the account record.

The list also gains removable filter chips with "Add filter" and "Clear all", a blue selection bar for bulk actions, and a rows-per-page footer; those are grammar, not colour, and live in the `xms-web-data-table` skill.
