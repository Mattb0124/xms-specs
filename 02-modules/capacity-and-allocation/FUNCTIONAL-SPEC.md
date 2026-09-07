# Functional Spec: Capacity & Allocation

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md)
**Requirements covered:** CAP-01, CAP-02, CAP-03, CAP-04, CAP-05, CAP-06, CAP-07, CAP-08, CAP-09 (nice), CAP-10 (nice), AI-16 (nice, data only)
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Problem

The team that serves every account is small, spread across five countries, and shared with other work. Today nobody can answer, from one place, who has capacity next month, who is the only person who can service a given client or technology, whether the hours planned for Brookfield in November match what was actually logged, or what a prospective win does to the calendar. Capacity lives in a spreadsheet, PTO in another system, skills in people's heads, and the assignment dropdown on a ticket has no idea whether the person is already overcommitted.

The workbook names the cases: a roster with commercial and calendar attributes (CAP-01), PTO and per-country holidays feeding availability (CAP-02), an available-capacity calculation with an admin overhead factor (CAP-03), a planned allocation grid per person per client per period (CAP-04), planned versus actual variance against logged time, "the report that actually changes behaviour" (CAP-05), an overallocation warning at assignment time (CAP-06), a skills matrix with single-point-of-failure flags (CAP-07), forward demand from the pipeline (CAP-08), and, later, rota management (CAP-09), scenario planning (CAP-10) and Axel allocation suggestions (AI-16).

## 2. Current state (what exists today)

- **XMS proof of concept**: the roster is the Clerk organisation membership read at runtime (`web-ui/components/aix-v3/xms/store.tsx` `useTenantRoster`), keyed by lowercased email, used only to fill assignee pickers; `XmsAdminPages.tsx` carries a users directory with a time zone picker and profile fields (title, phones, language, date format) stored in the studio `tenant_user_profiles` table. Nothing about FTE, rates, skills, calendars, PTO, allocation or capacity exists.
- **Time entries** exist in the POC (see [Time, Contracts & Budget §2](../time-and-budget/FUNCTIONAL-SPEC.md)) and are the "actual" side of planned versus actual.
- **Holiday calendars** are not built anywhere in AIX; the account business calendar is specified in [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md) and this module shares the per-country holiday sets with it.
- **Pipeline data**: AIX ingests Salesforce opportunities into its own stores (a nightly sync exists in `app-api`), but XMS does not depend on it; forward demand is entered or imported (see 5.7).

## 3. Goals

1. **One roster that is true.** Every internal person has a role, FTE percentage, cost and bill rates, skills with levels, certifications with expiry, a time zone and a working calendar, maintained by team leads.
2. **Capacity is computed, not guessed.** Contracted hours minus PTO minus holidays minus an admin overhead factor, per person per period, refreshed whenever an input changes.
3. **Plans are visible before the period starts.** A team lead allocates hours per person per account per period in a grid and sees the person's remaining capacity as they type.
4. **Plans are compared with reality.** Planned versus actual per person per account per period, with the variance in hours and percent, from the same time entries finance uses.
5. **Overallocation is caught at the moment of assignment.** The ticket assignment control warns when the assignee is over capacity for the period, with the numbers.
6. **Single points of failure are named.** The skills matrix shows, per account and per technology, where only one person is at the required level.
7. **Tomorrow's demand is in the picture.** Pipeline and project demand appear on the capacity view alongside current allocation.

## 4. Non-goals / out of scope

- **HR system of record.** Employment data, salaries and leave balances stay in HR; XMS stores what capacity math needs (FTE percent, cost rate, PTO dates) and never exposes cost rates to anyone without the finance or admin permission.
- **Automatic assignment.** The warning informs; it never reassigns. Axel allocation suggestions (AI-16) are Phase 4 and human-confirmed.
- **Client visibility.** Nothing in this module is ever shown in the portal or in client report packs. Utilisation appears in the internal operational dashboard only.
- **Rota management and scenario planning (CAP-09, CAP-10)** are Nice to Have and deferred to Phase 4; the model reserves the concepts (shifts, scenarios) so they are additive.
- **Timesheet approval.** Owned by Time, Contracts & Budget.
- **Contractors with their own calendars from a third-party system.** Contractors are roster people with a manually maintained calendar.

## 5. User-facing behavior

### 5.1 Vocabulary (fixed sets)

| Set | Values | Notes |
|---|---|---|
| Role | Consultant, Senior Consultant, Architect, Infrastructure Engineer, Team Lead, Account Manager, Practice Lead | Operator-defined list; rate cards and the skills matrix key on it |
| Skill level | 1 Aware, 2 Working, 3 Proficient, 4 Expert | Single-point-of-failure uses level 3 or above unless configured otherwise |
| Skill kinds | Technology (OneStream, Coupa, FCCS, EPM, Azure, Networking), Account familiarity (one per account), Process (Consolidation, Close, Planning) | Account familiarity skills are generated per account |
| Period | Calendar month | Weeks are shown inside the month for planning detail but allocation is stored per month |
| Capacity inputs | Contracted hours per week (from FTE percent and a 40-hour base), PTO days, holiday days from the person's country calendar, admin overhead percent | Admin overhead default 15 percent, configurable per operator and overridable per person |
| Demand source | Allocation (planned), Pipeline (weighted by probability), Project plan (committed) | Pipeline and project demand are entered or imported per period and account or prospect |
| Overallocation severity | Warning (allocated above 90 percent of available), Over (above 100 percent) | Thresholds configurable per operator |

### 5.2 Roster

A roster list in the admin grammar (dense list, then a full-screen record): name, role, FTE percent, country, time zone, working calendar, primary skills, certifications with expiry chips, start and end dates, active flag. Cost and bill rates show only to users with the finance or admin permission; everyone else sees the fields hidden, not masked. A person is linked to their sign-in identity so time entries and assignments resolve to the roster row. Certifications approaching expiry (60 days) show an amber chip and produce a notification to the person and their lead.

### 5.3 PTO and calendars

Each person has a working calendar (working days and hours in their time zone) and a country holiday calendar shared with account calendars. PTO is entered as date ranges with a type (vacation, sick, other) by the person or their lead; approval is out of scope, but a PTO entry is visible to the lead the moment it is entered. Holidays and PTO reduce capacity for the periods they fall in; entering PTO recomputes the affected periods immediately.

### 5.4 Capacity view

A month grid, people as rows, showing per person: contracted hours, minus PTO, minus holidays, minus overhead, equals available; allocated hours (sum of the allocation grid), pipeline and project demand overlaid as a lighter bar; the remaining capacity in hours and percent; a status chip (available, warning, over). Filters: assignment group, role, skill, account. Clicking a person opens their record with a month-by-month strip.

### 5.5 Allocation grid

Per account, a grid with people as rows and the next six months as columns; each cell is planned hours, editable inline by a team lead. As a cell is edited the person's remaining capacity for that month updates in a column at the right and turns amber or red per the thresholds. Rows can be added from the roster; a person without a skill relevant to the account shows a hint but is not blocked. The grid also offers an account-independent view (people as rows, accounts as columns for one month) for balancing.

### 5.6 Planned versus actual

For a month and an account, or for a person across accounts: planned hours (allocation), actual hours (logged time, all billable classes, ticket and non-ticket), variance in hours and percent, with the largest variances first. Each actual figure drills through to the time entries; each planned figure to the allocation cell. The report is exportable and appears in the internal operational dashboard as a tile.

### 5.7 Forward demand

Pipeline demand is entered per prospect or account per month with hours and a probability; project demand is entered per account per month as committed hours. Both can be imported from a spreadsheet template. The capacity view shows weighted pipeline (hours times probability) and committed project demand as a stacked overlay, so a lead can see that October is fine but December is not if two pursuits close.

### 5.8 Skills matrix

A heat map with people as rows and skills as columns, cells coloured by level. A second lens groups by account: for each account, the technologies its contracts require and the people at level 3 or above; where exactly one person qualifies the cell is flagged as a single point of failure, and the account record shows a "Single point of failure: OneStream" chip. Where zero people qualify the cell is flagged as a gap.

### 5.9 Overallocation warning at assignment

When a ticket is assigned (the control lives in Ticket Management), the assignee picker shows each person's remaining capacity for the current month beside their name, and selecting someone in warning or over state shows an inline notice with the numbers and a "Assign anyway" confirmation. The notice never blocks. The same check is available to Axel's allocation suggestions.

### 5.10 Empty and edge states

- No roster yet: the capacity view invites the admin to import the roster from the sign-in directory (creates people with default FTE 100 percent and the operator's default calendar).
- A person with no calendar: capacity shows "Calendar missing" and is excluded from single-point-of-failure math.
- Allocation on an inactive person: cells are read-only and shown struck through.
- Month with no working days (impossible for a whole month but possible per week): shows zero without division errors.
- A person who leaves mid-month: capacity prorated to the end date.

## 6. Rollout

1. **Phase 2 (Focused pilot):** roster with role, FTE, time zone, calendar, skills and certifications (CAP-01); import from the sign-in directory; assignee picker shows the roster. Depends on Accounts & Administration for calendars. Demoable alone.
2. **Phase 3 (Operational replacement):** PTO and holidays (CAP-02), capacity calculation (CAP-03), allocation grid (CAP-04), planned versus actual (CAP-05), overallocation warning (CAP-06), skills matrix with single-point-of-failure flags (CAP-07), forward demand entry and import (CAP-08). Depends on Time, Contracts & Budget entries and the worker read model.
3. **Phase 4 (Later):** rota and coverage gaps linked to after-hours flagging (CAP-09), scenario planning over a copy of the allocation and demand (CAP-10), Axel allocation suggestions (AI-16), Salesforce pipeline import if XMS is granted access.

## 7. Success criteria

- A person at 80 percent FTE in Brazil with 2 PTO days and 1 holiday in a 22-working-day month shows available hours of (0.8 times 40 times 22 divided by 5) minus 3 times 6.4 hours, minus 15 percent overhead, rounded to one decimal, and the number changes within seconds of adding a PTO day.
- Allocating 120 hours to a person whose available is 110 turns the cell red and the assignment picker shows "Over by 10 h" for that person.
- Planned versus actual for October lists a person allocated 40 hours to an account who logged 62 with a variance of plus 22 hours (55 percent), and the 62 drills to exactly those entries.
- The skills matrix flags OneStream for an account where only one person is at level 3 or higher, and the flag clears when a second person is raised to level 3.
- A weighted pipeline entry of 200 hours at 50 percent shows 100 hours of demand on the capacity overlay for that month.
- A portal user, and an internal user without the capacity permission, cannot reach any roster, capacity or allocation screen or endpoint.

## 8. Open questions

- **Hours base.** Whether the contracted week is 40 hours everywhere or per country. Default assumption: 40 hours base, overridable per person.
- **Admin overhead.** A single operator default or per role. Default assumption: operator default 15 percent, overridable per person.
- **Single-point-of-failure level.** Default assumption: level 3 or above.
- **Pipeline source.** Manual and spreadsheet import first; Salesforce import only if XMS is granted read access. Default assumption: manual.
- **Who edits allocation.** Default assumption: team leads and practice leads (`capacity:manage`); consultants read their own row.
