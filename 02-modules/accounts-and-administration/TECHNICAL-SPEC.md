# Technical Spec: Accounts & Administration

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Architecture](../../01-architecture/ARCHITECTURE.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Design System](../../01-architecture/DESIGN-SYSTEM.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Client Portal](../client-portal/TECHNICAL-SPEC.md)
**Requirements covered:** TM-01, TM-06, TM-08, INT-01
**Repos affected:** `backend`, `frontend`, `backend/src/worker`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Principal resolution and the single guard | [Security & Tenancy §2.2](../../01-architecture/SECURITY-AND-TENANCY.md) | This module owns the tables the guard reads (`op.users`, `op.role_assignments`, `op.account_grants`) |
| RLS session binding | [Data Model §3](../../01-architecture/DATA-MODEL.md) | `op.account_grants` is the source of `xms.account_ids`; `op.accounts.isolation_tier` drives connection routing |
| Clerk JWT verification with clock skew and `peekJwt` | `app-api/src/authtentication/clerk-jwt.ts`, `clerk.strategy.ts` (verified 2026-09-04) | Copied into `backend/src/auth/clerk-verifier.ts` |
| Clerk used only for internal staff in AIX; no organisation or invitation code | `app-api/src/users/users.service.ts:221,250` are the only organisation reads (verified 2026-09-04) | XMS adds organisation creation and invitations through the Clerk Backend SDK; nothing to copy |
| Frontend-only permission catalog with one-level implications | `web-ui/lib/rbac/permission-catalog.ts` (verified 2026-09-04) | XMS moves the catalog to `backend/src/contracts/src/permissions.ts` with transitive closure |
| Role assignments in two stores | `app-api/src/rbac/schemas/*` plus Clerk `publicMetadata.tenantRoles` (verified 2026-09-04) | XMS keeps assignments in PostgreSQL only |
| Solution access grants, reconcile-the-whole-set | studio migration `093_create_solution_access_grants.py`; `web-ui/components/aix-v3/xms/XmsAdminPanel.tsx` (verified 2026-09-04) | `op.account_grants` and the grants admin tree |
| Solution roles and assignments | studio migration `096_create_solution_roles.py` (verified 2026-09-04) | Shape of `op.roles` and `op.role_assignments` |
| User profile fields | studio `tenant_user_profiles`; `web-ui/components/aix-v3/xms/XmsAdminPages.tsx` `NewUserPage` (verified 2026-09-04) | `op.users` profile columns and the New User record |
| Time-zone picker | `XmsAdminPages.tsx` `ALL_TIME_ZONES`, `tzAbbrev` (verified 2026-09-04) | Reused in calendar and user records |
| Bootstrap admin | `app-api/scripts/bootstrap-admin-role.ts` invoked by `npm run bootstrap:admin` (verified 2026-09-04) | XMS bootstraps on first sign-in against configured emails |
| Golden route-table snapshot | studio `tests/golden/route_table.json` (verified 2026-09-04) | Route and permission snapshot test for the admin routes |
| Admin screen grammar | `XmsAdminPages.tsx`, `XmsAdminPanel.tsx`; [Design System §4](../../01-architecture/DESIGN-SYSTEM.md) | List and record views |

Cross-module dependency: everything else reads this module's tables through the `Principal` and through `ConfigResolver` (§3.4). Ticket Management defines state machine semantics; this module stores and edits them.

## 2. Data model

All tables per [Data Model](../../01-architecture/DATA-MODEL.md) conventions. `op.*` tables have no `account_id` and no RLS; `acct.*` tables have both.

### 2.1 `op.accounts`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `key` | text unique | Short code, e.g. `BRK`; immutable after activation |
| `name`, `legal_name` | text | |
| `status` | text | CHECK in (onboarding, active, suspended, offboarding, offboarded) |
| `isolation_tier` | text | CHECK in (shared, dedicated); default shared |
| `residency_region` | text | default `us-east-1` |
| `default_time_zone` | text | IANA |
| `default_calendar_id` | uuid null | references `acct.business_calendars` (same account; validated in service, not FK, because the calendar table is account-scoped) |
| `branding` | jsonb | logo S3 key, accent hex |
| `owner_user_id` | text null | opaque user id (account owner) |
| `dedicated_db_ref` | text null | Secrets Manager name of the dedicated connection when tier is dedicated |
| `offboarding` | jsonb null | step states, export key, scheduled purge date |
| `created_at`, `updated_at`, `version` | | |

### 2.2 `op.users`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `clerk_user_id` | text unique null | null for API-client service users |
| `kind` | text | CHECK in (internal, portal, service) |
| `account_id` | uuid null | required when kind = portal; references `op.accounts` |
| `email` | citext unique | lowercased identity key |
| `first_name`, `last_name`, `title` | text | |
| `business_phone`, `mobile_phone` | text null | |
| `time_zone`, `language`, `date_format` | text | profile per the POC `tenant_user_profiles` |
| `status` | text | CHECK in (invited, active, deactivated) |
| `last_sign_in_at` | timestamptz null | |
| `created_at`, `updated_at`, `version` | | |

### 2.3 Roles, assignments, grants, groups, API clients

| Table | Columns (beyond id and timestamps) | Notes |
|---|---|---|
| `op.roles` | `catalog` (operator, portal), `name`, `description`, `permissions text[]`, `is_system`, `status` | unique (catalog, lower(name)) |
| `op.role_assignments` | `user_id`, `role_id`, `account_id null` | unique (user_id, role_id, account_id); account-scoped assignment only for operator catalog |
| `op.account_grants` | `user_id`, `account_id`, `granted_by`, `granted_at` | unique (user_id, account_id); portal users get exactly one row created with the user |
| `op.assignment_groups` | `name`, `description`, `service_line`, `lead_user_id`, `default_calendar_ref`, `status` | unique lower(name) |
| `op.group_members` | `group_id`, `user_id` | unique pair |
| `op.api_clients` | `name`, `owner_user_id`, `key_prefix`, `lookup_hash` (sha256, unique), `secret_hash` (bcrypt), `scopes text[]`, `expires_at`, `last_used_at`, `status` | fixes the AIX API-key gaps |
| `op.api_client_grants` | `api_client_id`, `account_id` | |
| `op.config_defaults` | `kind` (state_machine, priority_matrix, sla_policy, activity_types, billable_classes, resolution_codes), `scope_key` (ticket type for state_machine and sla_policy, else `*`), `version`, `body jsonb`, `status` (draft, active, retired), `activated_at`, `activated_by` | unique (kind, scope_key, version); one active per (kind, scope_key) enforced by a partial unique index |
| `op.holiday_calendars`, `op.holidays` | `country`, `name`; `calendar_id`, `date`, `label` | shared library |

### 2.4 `acct.business_calendars`, `acct.calendar_hours`, `acct.calendar_holidays`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | RLS |
| `name` | text | unique per account |
| `time_zone` | text | IANA, validated |
| `effective_from` | date | |
| `holiday_calendar_id` | uuid null | reference into `op.holiday_calendars` (opaque id, no FK across schemas) |
| `status` | text | active, retired |

`acct.calendar_hours`: `calendar_id`, `weekday` (0 to 6), `start_minute`, `end_minute` (minutes from midnight; multiple rows per weekday allowed, non-overlapping enforced by an exclusion constraint on `int4range`). `acct.calendar_holidays`: `calendar_id`, `date`, `label` (account-specific closure days added to the library set).

### 2.5 `acct.account_settings` and `acct.config_overrides`

`acct.account_settings` (one row per account): `portal_enabled`, `consumption_visible`, `csat_enabled`, `sync_mode` (off, ingest_only, bidirectional), `ai_enabled`, `ai_opt_ins jsonb` (capability to mode), `ai_region_ok` (computed), `email_branding jsonb`, `outbound_identity` (verified SES identity), `inbound_aliases text[]`, `retention_days`, `attachment_max_bytes`.

`acct.config_overrides`: `account_id`, `kind`, `scope_key`, `version`, `body jsonb`, `status`, `activated_at`, `activated_by`; same shape as `op.config_defaults` so `ConfigResolver` merges by (kind, scope_key).

```sql
-- indexes and constraints (excerpt)
create unique index ux_op_accounts_key on op.accounts (key);
create unique index ux_op_users_email on op.users (email);
create unique index ux_op_role_assignments on op.role_assignments (user_id, role_id, coalesce(account_id, '00000000-0000-0000-0000-000000000000'));
create unique index ux_op_account_grants on op.account_grants (user_id, account_id);
create unique index ux_op_config_defaults_active on op.config_defaults (kind, scope_key) where status = 'active';
create unique index ux_acct_config_overrides_active on acct.config_overrides (account_id, kind, scope_key) where status = 'active';
alter table acct.calendar_hours add constraint ex_calendar_hours_overlap
  exclude using gist (calendar_id with =, weekday with =, int4range(start_minute, end_minute) with &&);

-- RLS on every acct.* table in this module (pattern repeated per table)
alter table acct.business_calendars enable row level security;
alter table acct.business_calendars force row level security;
create policy acct_isolation_operator on acct.business_calendars
  using (account_id = any (current_setting('xms.account_ids', true)::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids', true)::uuid[]));
create policy acct_isolation_portal on acct.business_calendars to xms_portal
  using (account_id = current_setting('xms.account_id', true)::uuid);
```

Service logic that is not obvious: `op.users.email` is the identity key used by every denormalised `actor_id`; activation of a config version retires the previous active version in the same transaction and writes an audit event with both bodies; offboarding is a state machine in `op.accounts.offboarding` driven by worker jobs (export, thread deletion request, purge) each idempotent on its step key.

## 3. Producers / core logic

### 3.1 `backend/src/domain/identity`

- `Principal` type and `resolvePrincipal(claims, repos)` (pure given loaded rows): maps a Clerk `sub` to a user, loads grants and role permissions, applies `expandPermissions` (transitive closure over `PERMISSION_IMPLICATIONS` from `backend/src/contracts`).
- `assertNotLastAdmin(users)` guard used by deactivate and role removal.

### 3.2 `backend/src/domain/calendar`

- `BusinessCalendar` value object built from hours, holidays and time zone; `addBusinessMinutes(start, minutes)`, `businessMinutesBetween(a, b)`, `isWorkingTime(t)`, `nextWorkingInstant(t)`. Pure, uses `@date-fns/tz` for zone math, no I/O. This is the engine the SLA module calls (TM-06).

### 3.3 `backend/src/admin/*` services

`AccountsService`, `UsersService`, `RolesService`, `GroupsService`, `CalendarsService`, `ConfigService` (defaults and overrides), `ApiClientsService`, `BootstrapService`. Each is thin on HTTP, owns validation, and writes an audit event through `AuditService` with entity kind `admin.<table>`.

Clerk integration (`backend/src/auth/clerk-admin.ts`): create organisation per account (`acct-<key>`), create invitation for portal and pre-invited internal users, deactivate memberships. Webhook `user.created`, `session.created`, `organizationMembership.deleted` updates `op.users.status` and `last_sign_in_at` (webhook signature verified, fail closed).

### 3.4 `ConfigResolver`

`resolve(kind, scopeKey, accountId)` returns the active override if present, else the active default, with the version id; cached per process for 60 seconds and invalidated by an outbox event `config.activated`. Every consumer (state machine, matrix, SLA policy, activity types) goes through it and stamps the version on the record it creates.

### 3.5 Worker jobs

| Job | Trigger | Behaviour |
|---|---|---|
| `admin.offboarding` | outbox `account.offboarding_started` | Runs export, thread-deletion request, schedules purge; idempotent per step |
| `admin.holiday_refresh` | yearly schedule | Loads next year's public holidays into `op.holidays` from a vendored dataset |
| `admin.clerk_reconcile` | daily | Compares Clerk memberships with `op.users`; reports drift, never auto-deletes |

## 4. API routes

All under `/v1/admin`, principal kind `internal` only unless stated; permission per row; pagination `?cursor=&limit=` (default 50, max 200); `POST` routes accept `Idempotency-Key`.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET/POST | `/accounts` | `admin:accounts` | List, create (status onboarding) |
| GET/PATCH | `/accounts/{id}` | `admin:accounts` | Record, edit identity and settings (optimistic `version`) |
| POST | `/accounts/{id}/activate`, `/suspend`, `/offboard` | `admin:accounts` | Status transitions with guards |
| GET/PUT | `/accounts/{id}/settings` | `admin:accounts`; `ai_*` fields also require `ai:configure` | Switches |
| GET/PUT | `/accounts/{id}/grants` | `admin:users` | Reconcile the whole set of internal users granted |
| GET/POST | `/accounts/{id}/portal-users` | `admin:users` | List, invite |
| GET/POST | `/users` | `admin:users` | List, pre-invite internal |
| GET/PATCH | `/users/{id}` | `admin:users` | Profile, status |
| PUT | `/users/{id}/roles` | `admin:users` | Reconcile role assignments |
| PUT | `/users/{id}/grants` | `admin:users` | Reconcile account grants |
| GET/POST, GET/PATCH/DELETE | `/roles`, `/roles/{id}` | `admin:users` | Two catalogs by `?catalog=` |
| GET | `/permissions?catalog=` | `admin:users` | Catalog with labels and implications |
| GET/POST, GET/PATCH | `/groups`, `/groups/{id}` | `admin:users` | Groups |
| PUT | `/groups/{id}/members` | `admin:users` | Reconcile members |
| GET/POST, GET/PATCH | `/accounts/{id}/calendars`, `/calendars/{id}` | `admin:config` | Calendars with hours and holidays in one document |
| POST | `/calendars/{id}/preview` | `admin:config` | `{start, minutes}` returns due time (TM-06 check) |
| GET | `/holiday-calendars` | `admin:config` | Library |
| GET | `/config/{kind}?scope=` | `admin:config` | Active default and versions |
| POST | `/config/{kind}/versions` | `admin:config` | Create draft |
| POST | `/config/{kind}/versions/{id}/activate` | `admin:config` | Activate (validates, retires previous) |
| GET/POST/DELETE | `/accounts/{id}/overrides/{kind}` | `admin:config` | Override lifecycle; DELETE reverts to default |
| GET/POST, DELETE | `/api-clients`, `/api-clients/{id}` | `admin:accounts` | Secret returned once on create |
| POST | `/bootstrap` | `@Public()` with the bootstrap guard (matching email, empty admin set) | One-time first administrator |
| GET | `/me` | any authenticated principal | Principal, permissions, granted accounts (used by the web shell) |

Non-admin read routes used by other screens: `GET /v1/accounts` (granted accounts summary, `tickets:view`), `GET /v1/groups` and `GET /v1/users?assignable=true` (pickers, `tickets:view`), `GET /v1/calendars/{id}` (`tickets:view`). Portal principals reach only `GET /v1/portal/me` and the portal user management routes in the Client Portal spec.

## 5. Cross-cutting concerns

- **Principal caching:** grants and permissions are loaded per request from PostgreSQL (two indexed queries); no cross-request cache in Phase 1 so revocation is immediate. If latency requires it later, a 30-second cache keyed by user version is acceptable because deactivation also ends the Clerk session.
- **Audit:** admin tables are operator-scoped, so their audit events go to `acct.audit_events` only when the entity belongs to an account (settings, calendars, overrides, grants) and to a partitioned `op.audit_events` (same shape, no RLS) otherwise. The Ticket Management spec owns the account-scoped table; this module adds the operator one.
- **Isolation tier changes:** setting `dedicated` records the intent and creates a runbook task; the connection router reads `dedicated_db_ref` only after the migration job marks the account moved. During the move the account is `suspended`.
- **Clerk outages:** the API verifies tokens with cached JWKS, so sign-in continues; invitations queue in the outbox and retry.
- **Configuration versions on records:** consumers stamp `config_version_id` so a ticket created under matrix version 3 explains its priority even after version 4 activates.

## 6. Web / client changes

- Admin section in `frontend/app/(internal)/admin/*` behind `admin:*` permissions (navigation gate plus route guard, per the settings-sidebar rule "hiding a link does not protect a route").
- Screens in the list-and-record grammar: `AccountsList`, `AccountRecord` (sections per Functional §5.3, onboarding wizard as a stepper inside the record), `UsersList`, `UserRecord` (profile, roles checkbox list, grants tree ported from `XmsAdminPanel.tsx` `CompanyProjects` with accounts instead of companies, groups), `RolesList`, `RoleRecord` (one form, catalog by query), `GroupsList`, `GroupRecord`, `CalendarsList`, `CalendarRecord` (weekly hours grid, holiday picker, preview widget), `CatalogList`, `CatalogVersionRecord` (state machine matrix editor, matrix grid, SLA grid, simple lists), `ApiClientsList`, `SystemPage`.
- RTK slice `adminApi` injected into the XMS base API with tags `Accounts`, `Account`, `Users`, `User`, `Roles`, `Groups`, `Calendars`, `Config`, `ApiClients`; reconcile endpoints (`PUT .../grants`, `.../roles`, `.../members`) invalidate the record tag only.
- The `useMe()` hook reads `/v1/admin/me` once and provides `hasPermission(key)` and `grantedAccounts` to every screen; permission checks are display gating only, the API decides.
- Components reuse the XMS token package and `SortableTable`; the time-zone picker is ported from `XmsAdminPages.tsx`.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/admin-foundations` | `backend/src/db` migrations for all `op.*` tables and the calendar tables with RLS; `backend/src/domain/identity` and `calendar`; API guard, `/me`, bootstrap; accounts, users, roles, groups, calendars services and routes | Clerk application provisioned |
| 2 | `feature/admin-web` | Admin section screens for Phase 1 entities | 1 deployed |
| 3 | `feature/admin-config-catalogs` | `config_defaults`, `config_overrides`, `ConfigResolver`, catalog editors | Ticket Management semantics agreed |
| 4 | `feature/admin-portal-users` | Portal user invitation and Clerk organisations per account | Client Portal Phase 2 |
| 5 | `feature/admin-lifecycle` | Onboarding wizard, offboarding jobs, dedicated tier, residency checks, API clients | Phase 3 |

Deploy order per release: db migration, worker, api, web.

## 8. Testing & verification

- **Domain (Jest):** `expandPermissions` is transitive (A implies B implies C yields C); `assertNotLastAdmin`; `BusinessCalendar.addBusinessMinutes` across a weekend, a holiday, a DST change in Europe/London and America/Sao_Paulo, split shifts, and a start outside working hours; `businessMinutesBetween` is the inverse.
- **Data layer (Testcontainers):** calendar hours exclusion constraint rejects overlaps; one active config version per (kind, scope); the generated isolation suite covers `acct.business_calendars`, `acct.calendar_hours`, `acct.calendar_holidays`, `acct.account_settings`, `acct.config_overrides`.
- **HTTP (supertest):** every admin route rejects anonymous, garbage and portal tokens; `admin:users` without `admin:config` cannot activate a config version; `/bootstrap` refuses once an administrator exists; reconcile endpoints are idempotent; route and permission snapshot test.
- **Clerk adapter:** invitation creation and webhook handling with recorded fixtures; webhook with a bad signature is rejected.
- **Web (Vitest and Testing Library):** calendar preview widget renders the API result; grants tree reconciles the whole set; role editor shows implications.
- **E2E (Playwright):** onboard an account, grant a consultant, verify visibility difference between two consultants (Functional §7).

## 9. Risks / notes

- **Clerk licensing and per-organisation SAML** (ADR-03): the spike must land in Phase 1; the `Principal` interface isolates the fallback.
- **Holiday data freshness:** vendored datasets go stale; the yearly refresh job and an alarm when next year's set is missing by 1 October.
- **Configuration version sprawl:** drafts that are never activated accumulate; a retention job deletes drafts older than 90 days.
- **Dedicated tier operational cost:** each dedicated account is another RDS instance; the roadmap assumes zero to two such accounts.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
