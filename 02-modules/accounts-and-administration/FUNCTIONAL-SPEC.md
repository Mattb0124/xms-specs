# Functional Spec: Accounts & Administration

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Domain Model](../../01-architecture/DOMAIN-MODEL.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md)
**Requirements covered:** TM-01, TM-06, TM-08, INT-01 (plus the administration surfaces that every other module's configuration depends on)
**Repos affected:** `backend`, `frontend`, `backend/src/worker`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Problem

Everything a client makes different in managed services is configuration: who works their tickets, which hours count as working hours in which time zone, which states and priorities apply, whether their data may be processed by AI, whether they may see their consumption. ServiceNow puts this behind a platform-administrator role and a change ticket; the DMS team ends up asking for changes they should be able to make themselves. The product needs an administration surface where a XMS administrator can onboard an account, invite and grant users, define groups, calendars and defaults, and switch behaviours on and off, all without a code change and all recorded in the audit trail.

The cases this module must cover:

1. **Accounts:** creating, configuring and offboarding a client account, including its isolation tier, residency region, branding, inbound email aliases, and the settings that other modules read (TM-01).
2. **People:** internal users arriving through the THG identity provider (INT-01), portal users belonging to exactly one account, roles from two catalogs, account grants that decide which accounts an internal user can see, and assignment groups mapped to the CSM, OneStream Technical and Infrastructure teams (TM-08).
3. **Calendars:** business calendars with working hours and holidays in a named time zone per account and per region (UK, Brazil, Australia, Canada, US), used by the SLA engine and after-hours flagging (TM-06).
4. **Configuration catalogs:** operator-wide defaults for state machines, the priority matrix, SLA policies, activity types, billable classes and resolution codes, with per-account overrides.
5. **Machine identities:** API clients for finance and future integrations, with scopes and account grants.

## 2. Current state (what exists today)

- **XMS proof of concept, web:** `web-ui/components/aix-v3/xms/XmsAdminPages.tsx` (Users and Roles admin in the ServiceNow list-and-record grammar, a New User page that sends a Clerk organisation invitation, an IANA time-zone picker, a role editor that is one form over two stores), `XmsAdminPanel.tsx` (the `CompanyProjects` lazy tree used to grant a user visibility of projects), `useXmsPermission.ts` (the two-store permission union, computed in the browser). Approved UI, real against the studio in live mode.
- **XMS proof of concept, backend:** studio `feature/xms-ticketing` migrations 093 (`solution_access_grants`, reconcile-the-whole-set grants keyed by lowercased email) and 096 (`solution_roles`, `solution_role_assignments` with a `solution` discriminator), `tenant_user_profiles` (time zone, language, date format). Real but narrow: no accounts, no calendars, no groups, no configuration catalogs, and the permission union is not enforced server-side.
- **AIX platform:** Clerk for internal staff only (verified: no organisation creation, invitation or SSO-connection code in `app-api`); the framework RBAC engine with a frontend-only permission catalog (`web-ui/lib/rbac/permission-catalog.ts`) and role assignments kept in both Mongo and Clerk metadata; a `bootstrap:admin` script that seeds the first administrator.
- **Not built anywhere:** accounts as a first-class entity, business calendars, assignment groups, per-account configuration overrides, isolation tiers, API clients with scopes, account onboarding and offboarding.

## 3. Goals

1. **Onboard an account in one sitting.** An administrator creates the account, sets its time zone and calendar, chooses isolation tier and residency, sets the AI and portal switches, adds the inbound alias and branding, and invites the first portal administrator, with no engineering involvement.
2. **Grants decide visibility, roles decide capability.** An internal user sees only the accounts they are granted, and can do only what their operator role allows; a portal user sees only their account and can do only what their portal role allows.
3. **Calendars are data.** UK, Brazil, Australia, Canada and US coverage is a matter of creating calendars with hours and holiday sets; SLA clocks and after-hours flags follow them automatically.
4. **Groups model the real teams.** Assignment groups mirror CSM, OneStream Technical and Infrastructure, support group-level and individual assignment, and can be added to without a release.
5. **Defaults with overrides.** Every catalog has an operator default; an account override replaces it for that account only, and the record view shows which one is in force.
6. **Every administrative change is audited.** Who changed which setting, from what to what, with the same evidence quality as a ticket change.

## 4. Non-goals / out of scope

- **Portal user self-registration.** Portal users are invited by an administrator (operator or account admin); open sign-up is never offered. Reason: strict data scoping (CP-02) starts at invitation.
- **Editing identity in XMS.** Names, passwords and MFA are managed in Clerk (or the client IdP). XMS stores a profile (time zone, locale, phone, title) and role data only.
- **Fine-grained record ACLs.** Access is account-level plus role; there are no per-ticket permissions in Phases 1 to 3. Reason: the DMS team works whole accounts.
- **Multi-operator.** The product has one operator (The Hackett Group). Nothing is designed for a second operator; "tenant" is not a concept (see the Glossary).
- **State machine semantics.** The editor lives here; what a transition means (SLA effects, required fields) is owned by [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md).
- **Rate cards and contracts.** Commercial configuration is owned by [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md).
- **The dedicated-tier provisioning automation.** Phase 3 provisions a dedicated database by runbook; self-service provisioning is later.

## 5. User-facing behavior

### 5.1 Vocabulary

| Set | Values | Notes |
|---|---|---|
| Account status | onboarding, active, suspended, offboarding, offboarded | Suspended accounts reject portal sign-in and inbound email (quarantined) but remain visible internally |
| Isolation tier | shared, dedicated | Dedicated routes the account to its own database (mechanics in the Data Model) |
| Residency region | us-east-1 (default), others by agreement | Drives which AI regions are permitted and where backups live |
| User kind | internal, portal | A portal user belongs to exactly one account |
| User status | invited, active, deactivated | Deactivated users keep their history; nothing is reassigned automatically |
| Operator roles (default set) | Consultant, Dispatcher, Account Owner, Finance, Administrator | Editable; permissions come from the operator catalog |
| Portal roles (default set) | Requester, Account Admin, Read-only | Editable per account; permissions come from the portal catalog |
| Assignment group defaults | CSM, OneStream Technical, Infrastructure | Editable; a ticket type can name a default group |
| Calendar kinds | account default, regional coverage, person (owned by Capacity) | An account has one default and any number of regional calendars |
| Catalogs with account overrides | state machines (per ticket type), priority matrix, SLA policy defaults, activity types, billable classes, resolution codes, ticket forms | Forms are owned by the Portal module but surfaced in the same admin tree |

### 5.2 Administration home

An **Admin** section in the XMS Web navigation, visible only to users with the administration permission, in the ServiceNow list-and-record grammar of the POC (`XmsAdminPages.tsx`): a left tree (Accounts, Users, Roles, Groups, Calendars, Catalogs, API clients, System), a dense list on the right, and a full-screen record view for one item. Every list has search, the condition builder and Excel export like the ticket queue.

### 5.3 Accounts

- **List:** key, name, status, isolation tier, region, default time zone, active contracts count, portal enabled, AI enabled, account owner.
- **Record view, sections:** Identity (key, name, legal name, branding logo and accent), Isolation & Residency (tier, region; changing tier opens a confirmation explaining that a migration runbook follows), Calendars (default calendar, regional calendars), Settings (portal enabled, consumption visible in portal, CSAT enabled, sync mode, AI enabled, AI capability opt-ins, AI region check result), Email (inbound aliases, outbound sender identity and verification state), Contacts, Grants (which internal users see this account), Portal users, Overrides (which catalogs this account overrides, each linking to its editor), Offboarding.
- **Onboarding wizard** from the New button: identity, time zone and calendar (pick a template such as "UK standard hours" and adjust), isolation and residency, switches, email alias, first internal account owner grant, first portal admin invitation. Each step can be saved and resumed; the account stays `onboarding` until the administrator activates it.
- **Offboarding:** moving to `offboarding` freezes writes for portal users, exports the account's data package (tickets, comments, attachments manifest, time, contracts, articles visible to it) to S3, requests deletion of Axel threads tagged with the account, and schedules deletion after the retention period. The record shows each step's state.
- **Edge cases:** an account with open tickets cannot be offboarded until they are closed or cancelled; disabling the portal while portal users are signed in ends their sessions at the next request; changing the default time zone does not move existing SLA due times (clocks keep the calendar they were started on) and the confirmation dialog says so.

### 5.4 Users

- **Internal users** appear automatically the first time they sign in through the THG identity provider (INT-01); an administrator can also pre-invite by email so grants and roles are ready before first sign-in. The record shows profile fields (title, phones, time zone, language, date format, as in the POC's New User page), operator roles, account grants (the `CompanyProjects`-style expandable tree from `XmsAdminPanel.tsx`, now listing accounts), group memberships, and the last sign-in.
- **Portal users** are created from the account record or by an account admin in the portal; an invitation email goes out through Clerk; the record shows the account, portal role, status and whether the account's SSO connection or the local fallback is used.
- **Deactivation** removes roles and grants immediately, keeps the user in history, and lists open tickets assigned to them so the dispatcher can reassign.
- **Edge cases:** a user with no grants sees an empty product with a "no accounts granted" notice, not an error; removing the last administrator is refused.

### 5.5 Roles and permissions

- Two catalogs (operator, portal), each listing permission keys with plain-language labels grouped by area, exactly the checkbox-list role editor of the POC (`RoleRecord` in `XmsAdminPages.tsx`), now backed by one server-side store.
- Implications are shown inline ("Administrator implies everything below") and applied transitively.
- A role in use cannot be deleted; it can be deactivated once every assignment is moved.

### 5.6 Assignment groups

- Groups have a name, a description, a service line tag (OneStream, Coupa, FCCS, EPM, Infrastructure), members, a lead, and optional default calendar. Ticket types name a default group; dispatch assigns to a group and optionally to a member (TM-08).
- Removing a member with open assigned tickets lists them for reassignment.

### 5.7 Business calendars

- A calendar has a name, an IANA time zone, weekly working hours per weekday (multiple ranges allowed, for split coverage), a holiday set (pick a country calendar from the shared library and add account-specific closure days), and an effective-from date so that a change applies going forward.
- An account has a default calendar and may add regional calendars; a contract or an SLA policy can name a regional calendar (TM-06).
- Preview: entering a start time and a target in business minutes shows the computed due time, so an administrator can check a calendar before it is used.
- Edge cases: a calendar with no working hours on any day is rejected; deleting a calendar referenced by an open SLA clock is refused.

### 5.8 Catalogs and overrides

- Each catalog opens as a list of operator defaults with an "Overrides" column showing which accounts override it. Opening an override from an account record shows the default side by side with the override, with a "revert to default" action.
- **State machine editor:** per ticket type, a table of states and a matrix of allowed transitions with per-transition flags (required fields, pause reason required, resolution required, approval required); a validation pass refuses a machine with an unreachable terminal state. Semantics per [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md).
- **Priority matrix:** a 3 by 3 grid of impact by urgency producing a priority, per account override.
- **SLA policy defaults:** per ticket type and priority, response and resolution targets in business minutes and the calendar to use; contracts may override (owned by Time & Budget).
- **Activity types, billable classes, resolution codes:** simple lists with a default billable class per activity type and a "no-solution" flag per resolution code (used by the close discipline).
- Every catalog change is versioned; the version in force is shown on records created under it.

### 5.9 API clients

- Created by an administrator with a name, owner, scopes, account grants and expiry; the secret is shown once. The list shows last used and status; revoke is immediate.

### 5.10 System

- Bootstrap: on an empty database the first user who signs in from the THG identity provider and matches the configured bootstrap email becomes Administrator (the AIX `bootstrap:admin` precedent, as a one-time setup step instead of a script).
- Isolation suite status: when the last generated isolation test run is older than a day the System page shows a warning, mirroring the alarm.

## 6. Rollout

1. **Phase 1 (Foundations):** accounts (identity, status, time zone, default calendar, switches), internal users via Clerk with grants and roles, assignment groups, calendars with hours and holidays, the bootstrap step, audit of all admin changes. Depends on the Clerk application and the isolation mechanics from the Data Model. Ships the admin section with Accounts, Users, Roles, Groups, Calendars.
2. **Phase 2 (Focused pilot):** catalogs with overrides (state machines, matrix, SLA defaults, activity types, billable classes, resolution codes), portal user invitations for controlled external access, API clients. Depends on Ticket Management (semantics) and Client Portal (invitation flow).
3. **Phase 3 (Operational replacement):** onboarding wizard, offboarding flow, dedicated isolation tier runbook and UI, residency checks, regional calendars in use by SLA policies, SSO connection status per account.
4. **Phase 4 (Later):** self-service dedicated-tier provisioning, calendar templates library growth, delegated administration for account admins beyond user management.

## 7. Success criteria

- An administrator onboards a fictional UK account with a 08:00 to 18:00 Europe/London calendar and the UK holiday set, grants one consultant, and that consultant sees the account while another consultant without a grant does not, all within fifteen minutes and with no console work.
- A portal user invited to account A who guesses account B's ticket key receives not-found from every portal route, and the isolation suite proves the same at the database level.
- Changing the priority matrix override for one account changes derived priority for that account's new tickets only.
- The calendar preview for a P2 with a 4-hour response target started Friday 17:00 Europe/London shows Monday 12:00 given the standard hours.
- Every administrative change appears in the audit trail with actor, old value and new value.
- Removing the last administrator is refused with a clear message.

## 8. Open questions

- **Portal identity topology:** one Clerk organisation per account with an enterprise connection, or a shared portal organisation with per-account connections? Default assumption: one organisation per account (ADR-03), pending the licensing spike.
- **Where account admins manage their users:** in the portal only, or also in XMS Web? Default assumption: portal only; operator administrators can do it from the account record.
- **Calendar templates:** ship UK, Brazil, Australia, Canada and US standard-hours templates with public holiday sets, or start empty? Default assumption: ship the five templates with holiday data for 2026 and 2027, refreshed by a yearly job.
- **Group lead permissions:** does a group lead get implicit dispatcher rights for their group? Default assumption: no implicit rights; the Dispatcher role is assigned explicitly.
- **Bootstrap email:** a single configured email or a domain? Default assumption: a list of emails in configuration, consumed once.
