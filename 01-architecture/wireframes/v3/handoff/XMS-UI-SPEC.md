# XMS UI — implementation spec (v3)

Companion to `XMS v3 (standalone).html`. Read this **before** trying to match the
mock by eye — most alignment problems come from the rules below, not from CSS values.

**Files**

| File | Use |
|---|---|
| `handoff/aix-tokens.css` | Hackett AIX design system tokens (brand, type, shadow). Unmodified. |
| `handoff/xms-ui.css` | XMS layer: chrome, semantic ramps, components. Source of truth. |
| `XMS v3 (standalone).html` | The visual reference. Inline styles, no classes. |
| `XMS Wireframes (standalone).html` | All 28 screens at wireframe fidelity, with engineering callouts. |

The mock is authored with **inline styles** so it can stream while rendering — that
is a property of the prototyping tool, not a recommendation. Build with
`xms-ui.css` classes. Where a literal in the HTML disagrees with the stylesheet,
**the stylesheet wins**.

---

## 1 · The five rules that cause 90% of drift

1. **No zebra striping.** Rows separate on a single 1px `--xms-line-row` hairline
   plus a hover fill. Adding alternating row backgrounds is the fastest way to
   make this stop looking like the mock.

2. **Blue means interactive, and nothing else.** Links, ticket keys, primary
   buttons, active nav, focus rings. Status uses the state ramp; it does not
   borrow blue except where "In progress" legitimately owns it.

3. **Colour is semantic, never decorative.** Five ramps, five jobs: state, type,
   account, priority, SLA. If a colour is not answering one of those questions,
   it should be grey.

4. **Violet is reserved for AI-origin content.** This is inherited from the AIX
   system and is load-bearing. Do not use it for status, tags, or accent.

5. **Flat surfaces.** XMS drops the AIX card shadow. Shadow is reserved for
   things that genuinely float — the finder dropdown, menus, modals. Everything
   else is separated by hairlines.

---

## 2 · Navigation — four layers, four jobs

This is the part most likely to be rebuilt wrong, because three of the layers
look like "nav".

| Layer | Job | Never |
|---|---|---|
| **Navy bar** | Finders: All / Favourites / History. Global search, instance pill, identity. | A destination. Nothing lives *only* here. |
| **Left sidebar** | The only destination list. Pinned screens + starred views + "Browse all screens". | The full 27-item module tree by default. |
| **Grey tool strip** | Where you are + view state: screen name, filter chips, view actions. | Navigation to other screens. |
| **Record tabs** | Sections of one record (Conversation, Activity, Time…). | Navigating away from the record. |

**Sidebar contents.** Six pinned screens with icons and badges, three starred
views, then `Browse all screens (27)` at the foot. The full tree opens as the
same overlay the navy **All** tab opens. Admin sections never sit permanently in
a consultant's peripheral vision.

**The finder dropdown.** Anchored under the tab that opened it, `left: 186px`,
640px wide, max 520px tall, rounded at the bottom only. The active tab takes the
same translucent fill and a `-8px` bottom margin so tab and panel read as one
surface with no seam. The workspace behind dims to `--xms-drop-scrim`.
All text inside the panel is white.

**Environment switch.** Internal desk / Client portal is an explicit segmented
control beside the logo, not a sidebar row — the two are different shells for
different audiences, so the switch must be deliberate.

---

## 3 · Semantic ramps

### Ticket state (pill, always)
| State | Ink | Fill | Edge |
|---|---|---|---|
| New | `#334155` | `#F1F5F9` | `#D7DEE8` |
| In progress | `#1D4ED8` | `#EFF4FF` | `#CBDCFA` |
| Awaiting client | `#9A5B06` | `#FEF6E7` | `#F4DDB4` |
| Awaiting approval | `#0E7490` | `#ECFAFE` | `#BFE6F0` |
| Resolved | `#0F7A50` | `#EDFAF3` | `#BEE6D3` |
| Closed | `#64748B` | `#FFFFFF` | `#DDE2EA` |

### Ticket type (3×15px bar, 8px before the label — never a filled pill)
Incident `#DC2626` · Request `#0E7490` · Change `#7A5AF8` · Problem `#B45309`

### Account identity (7px square, 8px before the name)
Assigned at account onboarding and **stable for the life of the account** — the
whole value is that a consultant learns them. Palette in `xms-ui.css` §2c.

### Priority
Only **P1** earns red. P2 slate, P3/P4 quiet grey.

### SLA
Breach red (latched, survives reopen) · at-risk blue · on-track grey ·
paused grey with a `pause` glyph. Show remaining time, not elapsed.

---

## 4 · Density and geometry

```
navy bar        56px          sidebar         238px
grey strip      52px          record rails    262px each
control height  32px (strip) / 38px (card toolbar)
table cell      13px vertical / 14px horizontal padding
content max     1200px        outer gutter    20px
radii           4px controls · 6px cards · 999px pills
borders         1px, always solid, never dashed (except "+ Add filter")
baseline        4px grid — every spacing value is a multiple
```

Type floor is 12px, except 11px uppercase eyebrows.

---

## 5 · Table behaviour

- Row click navigates **in place**. Browser back must restore view, filter, sort,
  scroll position and selection.
- Every column header is sortable: `chevrons-up-down` at 13px `#B4BDCC`,
  swapping to `arrow-up` in `--xms-link` on the sorted column.
- Filter chips are **removable objects**, not fixed dropdowns — caret plus `×`,
  followed by `+ Add filter` (dashed) and `Clear all`. They mirror the saved-view
  state, and the breadcrumb beneath restates it in words.
- The selection bar appears **only** when rows are checked, between the toolbar
  and the table, and writes one audit event per record.
- Footer carries range readout, pager, and rows-per-page.
- Saved views are URLs. A pasted link must reproduce the exact list.
- Horizontal overflow scrolls **inside** the card (`min-width: 1240px` on the
  table, `overflow-x: auto` on its wrapper) — the page never scrolls sideways.

---

## 6 · Icons

Lucide, 1.5px stroke, `currentColor`, never filled, 14–19px rendered on a 24px
canvas.

**Known trap.** Calling `lucide.createIcons()` against a React-managed subtree
mutates the DOM behind React and throws:

```
Failed to execute 'insertBefore' on 'Node':
The node before which the new node is to be inserted is not a child of this node.
```

Use `lucide-react`, or build a one-time `<symbol>` sprite outside the React root
and reference it with `<svg><use href="#i-name"/></svg>`. The mock uses the
sprite approach; the builder script is in the page's `<head>`.

---

## 7 · Interaction states

| State | Treatment |
|---|---|
| Hover (row) | `#F0F3FA` fill |
| Hover (card/button) | one tier lighter; links go `--xms-link-strong` + underline |
| Press | 1–2px inset shadow. **No scale-down.** |
| Focus | 2px `--xms-link` ring, 2px offset. Never removed. |
| Disabled | `--xms-ink-faint` ink, no fill change |

Motion: `cubic-bezier(0.2, 0, 0, 1)`, 160–220ms for UI, 320ms for drawers.
Fades and 4–8px translates only. No bounce, no spring.

---

## 8 · Data-layer notes the UI depends on

- **Optimistic writes.** Property edits commit on change or blur, with rollback
  and a toast on 409 or validation failure.
- **Polling.** Lists refresh every 60s, SLA badges tick every 30s. Keep rendered
  data on screen while refetching; skeletons only on first load.
- **State machine.** The state pill is the only route through it. Its menu lists
  allowed next states and collects required fields inline — not in a modal wizard.
- **Versioning.** Publishing a state machine affects new tickets only; in-flight
  tickets keep the version they were created on until close.

---

## 9 · What is not yet in v3

Five screens are built hi-fi: Queue, Ticket record, My work, Dispatch,
Operations. The other 23 exist at wireframe fidelity in
`XMS Wireframes (standalone).html`, each with numbered engineering callouts and
spec references. Build order should follow the pinned sidebar.
