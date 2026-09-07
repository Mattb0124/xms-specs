# Technical Spec: Client Portal

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Architecture](../../01-architecture/ARCHITECTURE.md), [Design System](../../01-architecture/DESIGN-SYSTEM.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Solution Knowledge Base](../knowledge-base/TECHNICAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/TECHNICAL-SPEC.md), [Email Intake & Outbound](../email-intake/TECHNICAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md)
**Requirements covered:** CP-01, CP-02, CP-03, CP-04, CP-05, CP-06, CP-07
**Repos affected:** `frontend`, `backend`, `backend/src/worker`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`, `infra`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Identity decision | [Security & Tenancy §2.1](../../01-architecture/SECURITY-AND-TENANCY.md), ADR-03: one XMS Clerk application, one Clerk organisation per account (`acct-<key>`), enterprise SAML or OIDC connection or local fallback | The portal never sees a credential; it sees a Clerk session whose `org_slug` names the account |
| Principal resolution | [Security & Tenancy §2.2](../../01-architecture/SECURITY-AND-TENANCY.md): single guard, `kind = portal`, `accountIds` = exactly one, portal tokens accepted only in the portal controller group | The `/portal/v1/*` controllers are that group |
| Portal database role | [Data Model §3](../../01-architecture/DATA-MODEL.md): `xms_portal` with `acct_isolation_portal` policy on `xms.account_id`, table-level revokes on work notes, time entries, rate cards, AI suggestions, audit events | The data layer opens portal requests on a pool bound to `xms_portal`; the application cannot reach revoked tables even by bug |
| AIX Clerk verification | `app-api/src/authtentication/clerk-jwt.ts` (`CLERK_JWT_CLOCK_SKEW_MS = 60_000`, `peekJwt`) (verified 2026-09-04) | Same skew and diagnostic in the XMS guard |
| AIX external access (not copied) | `app-api/src/services/jwt/simple-jwt.service.ts` hand-rolled HMAC token; `app-api/src/microsites/*` with `x-microsite-session-token` (verified 2026-09-04) | Evidence that nothing reusable exists; both rejected |
| Attachment flow | [Ticket Management Technical Spec §3](../ticket-management/TECHNICAL-SPEC.md): presigned POST with `content-length-range`, MIME allowlist, GuardDuty scan state; AIX `requestChecksumCalculation: 'WHEN_REQUIRED'` (`app-api/src/files/services/file-storage.service.ts`) | Portal reuses the same service with `origin = portal` |
| Ticket transition and comments | [Ticket Management Technical Spec §3 and §4](../ticket-management/TECHNICAL-SPEC.md): transition endpoint, `acct.comments` (public) vs `acct.work_notes` (internal) as separate tables | Portal replies are public comments; reply on Waiting on you resumes the clock inside the ticket service |
| Consumption computation | [Time, Contracts & Budget Technical Spec §3](../time-and-budget/TECHNICAL-SPEC.md): `ContractPositionService` computes used, remaining, carried, forecast | Portal calls the same service through a portal-scoped route; no second computation |
| Outbound email | [Email Intake & Outbound Technical Spec](../email-intake/TECHNICAL-SPEC.md): SES v2, per-account sending identity, threading headers, in-repo templates | Every portal notification and survey is an outbound message |
| Report snapshots | [Dashboards & Report Packs Technical Spec](../dashboard-and-reporting/TECHNICAL-SPEC.md): `rpt.daily_snapshots` | CSAT scores feed snapshots and the report pack |
| POC form and record grammar | `web-ui/components/aix-v3/xms/NewTicketPage.tsx`, `TicketDrawer.tsx` (verified 2026-09-04) | Portal New request and Ticket pages are reduced variants |
| Notification design | `app-api/src/api/v3/notifications/*` (recipient as identity key, collapse keys, copy in one file) (verified 2026-09-04) | Portal email notifications use the same producer shape in `acct.notifications` with `channel = email` |
| WAF and rate limits | [Platform & Operations §1](../../01-architecture/PLATFORM-AND-OPERATIONS.md): ALB with WAF for `portal.<domain>`, Terraform-managed | Portal host only |

Cross-module ordering: Accounts & Administration owns `op.accounts`, `acct.account_settings` and the Clerk organisation provisioning; Ticket Management owns tickets, comments and attachments; this module adds the portal principal path, its own tables, the portal controller group, the `acct.ticket_timeline_public` view, and the portal route group in `frontend`.

## 2. Data model

### 2.1 `acct.contacts`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid | |
| `email` | citext | Unique per account; the inbound-email matching key |
| `display_name` | text | |
| `portal_user_id` | uuid null | FK `op.users.id` when the contact is also a portal user |
| `clerk_user_id` | text null | Clerk `sub` once bound |
| `portal_role` | text null | CHECK in (`requester`, `account_admin`, `read_only`); null for email-only contacts |
| `flags` | text[] | `executive_sponsor`, `billing_contact`, `csat_recipient` |
| `time_zone` | text | IANA; defaults to the account's |
| `notification_prefs` | jsonb | Per event kind on or off; `waiting_on_you` is not overridable |
| `status` | text | CHECK in (`invited`, `active`, `deactivated`, `email_only`) |
| `invited_at`, `activated_at`, `deactivated_at` | timestamptz null | |
| `last_seen_at` | timestamptz null | |

### 2.2 `acct.ticket_forms` and `acct.ticket_form_versions`

| Column | Type | Notes |
|---|---|---|
| `acct.ticket_forms.id`, `account_id` | uuid | |
| `ticket_type` | text | CHECK in (`incident`, `service_request`, `change`); unique per account with `is_active` |
| `name`, `description` | text | Shown on the request-type card |
| `current_version_id` | uuid null | FK `acct.ticket_form_versions.id` |
| `is_active`, `client_visible` | boolean | |

| Column | Type | Notes |
|---|---|---|
| `acct.ticket_form_versions.id`, `account_id`, `form_id` | uuid | |
| `version_no` | integer | Unique per form |
| `definition` | jsonb | Field list: `key`, `kind` (`short_text`, `long_text`, `choice`, `multi_choice`, `date`, `ci_picker`, `contact_picker`, `urgency`, `impact`, `attachment`), `label`, `help`, `required`, `options`, `visible_when` (`{field, equals}`), `maps_to` (ticket column or `custom.<key>`) |
| `published_at`, `published_by` | timestamptz, text | Append-only once published |

Ticket rows store `form_version_id` and the submitted `custom` fields in `acct.tickets.form_data jsonb` (owned by Ticket Management; this module contributes the column).

### 2.3 `acct.csat_surveys` and `acct.csat_responses`

| Column | Type | Notes |
|---|---|---|
| `acct.csat_surveys.id`, `account_id` | uuid | |
| `kind` | text | CHECK in (`ticket_close`, `quarterly`) |
| `ticket_id` | uuid null | FK; set for `ticket_close` |
| `period` | text null | `2026-Q3` for quarterly |
| `contact_id` | uuid | Recipient |
| `token_hash` | text | SHA-256 of the one-time link token |
| `status` | text | CHECK in (`sent`, `reminded`, `answered`, `expired`, `suppressed`) |
| `sent_at`, `remind_at`, `expires_at`, `answered_at` | timestamptz | |
| `suppression_reason` | text null | `cancelled`, `duplicate`, `too_fast`, `daily_cap` |

| Column | Type | Notes |
|---|---|---|
| `acct.csat_responses.id`, `account_id`, `survey_id` | uuid | Append-only |
| `answers` | jsonb | `{score}` for ticket close; five keyed scores for quarterly |
| `comment` | text null | |
| `anonymous` | boolean | From the account setting at answer time |
| `created_at` | timestamptz | |

### 2.4 `acct.portal_deflection_sessions` (append-only)

| Column | Type | Notes |
|---|---|---|
| `id`, `account_id`, `contact_id` | uuid | |
| `query_hash` | text | SHA-256 of the normalised search text |
| `shown_article_ids`, `opened_article_ids` | uuid[] | |
| `submitted_ticket_id` | uuid null | Set when a request follows within 24 hours |
| `started_at` | timestamptz | |

### 2.5 `acct.ticket_timeline_public` (view)

The only path by which the portal reads a ticket's conversation. It unions `acct.comments` (author display name resolved to first name and group for internal authors, full name for portal authors), `acct.attachments` where `visibility = public and scan_state = clean`, and system lines derived from `acct.audit_events` limited to state changes mapped through the client-facing status mapping. Work notes, time entries, AI events and every other audit event are absent from the view definition, so no query can add them back.

### 2.6 Indexes, constraints and policies

```sql
create unique index ux_contacts_email on acct.contacts (account_id, email);
create index ix_contacts_clerk on acct.contacts (clerk_user_id) where clerk_user_id is not null;
create unique index ux_ticket_forms_active on acct.ticket_forms (account_id, ticket_type) where is_active;
create unique index ux_form_versions_no on acct.ticket_form_versions (form_id, version_no);
create index ix_csat_surveys_due on acct.csat_surveys (status, remind_at) where status in ('sent','reminded');
create unique index ux_csat_ticket_contact on acct.csat_surveys (ticket_id, contact_id) where kind = 'ticket_close';
create unique index ux_csat_quarter_contact on acct.csat_surveys (period, contact_id) where kind = 'quarterly';
create index ix_deflection_contact on acct.portal_deflection_sessions (contact_id, started_at);

-- Standard operator policy on every table (xms_app, xms_worker) plus the portal policy:
alter table acct.contacts enable row level security; alter table acct.contacts force row level security;
create policy contacts_portal on acct.contacts for select to xms_portal
  using (account_id = current_setting('xms.account_id', true)::uuid);
-- Account admins update their own organisation's contacts through the API only; the portal role
-- gets column-level update on (display_name, portal_role, status, notification_prefs, time_zone).
grant select (id, account_id, email, display_name, portal_role, flags, time_zone, notification_prefs, status, last_seen_at)
  on acct.contacts to xms_portal;
grant update (display_name, portal_role, status, notification_prefs, time_zone, last_seen_at) on acct.contacts to xms_portal;
-- Forms: portal reads only the current published version.
create policy forms_portal on acct.ticket_forms for select to xms_portal
  using (account_id = current_setting('xms.account_id', true)::uuid and is_active and client_visible);
create policy form_versions_portal on acct.ticket_form_versions for select to xms_portal
  using (account_id = current_setting('xms.account_id', true)::uuid and published_at is not null);
-- CSAT: the portal can read its own surveys and insert responses; never update or delete.
create policy csat_portal_read on acct.csat_surveys for select to xms_portal
  using (account_id = current_setting('xms.account_id', true)::uuid);
create policy csat_portal_answer on acct.csat_responses for insert to xms_portal
  with check (account_id = current_setting('xms.account_id', true)::uuid);
create trigger trg_csat_responses_append_only before update or delete on acct.csat_responses
  for each row execute function sys.raise_append_only();
create trigger trg_deflection_append_only before update or delete on acct.portal_deflection_sessions
  for each row execute function sys.raise_append_only();
-- The public timeline view runs as the caller (security invoker) so RLS on the underlying
-- tables applies; the portal role has select on the view and NO grant on acct.work_notes.
create view acct.ticket_timeline_public with (security_invoker = true) as ...;
grant select on acct.ticket_timeline_public to xms_portal;
revoke all on acct.work_notes, acct.time_entries, acct.rate_cards, acct.ai_suggestions, acct.audit_events from xms_portal;
```

### 2.7 Service logic worth stating

- **Client-facing status mapping** (`backend/src/domain/portal/status-map.ts`): internal state to one of seven display statuses, per ticket type; the mapping is part of the state machine configuration so an account override cannot produce an unmapped state (a validation on config save).
- **Form definition validation** (`backend/src/domain/portal/form-schema.ts`): every `required` field maps to a ticket column or `custom` key; `visible_when` references an earlier field; `urgency` and `impact` must both exist or neither; at most one `attachment` field. Submission validation runs the same schema server-side; the client only mirrors it.
- **Reply resumes the clock**: the portal comment route calls `TicketService.addPublicComment(origin = portal)`; the ticket service, not the portal, resumes paused clocks when the pause reason is `awaiting_client` ([Ticket Management Technical Spec §3](../ticket-management/TECHNICAL-SPEC.md)).
- **Consumption**: `GET /portal/v1/consumption` calls `ContractPositionService.forAccount(accountId, level)` where `level` comes from `acct.account_settings.consumption_visibility`; with `off` the route returns 404 so the page does not exist for that account.
- **CSAT scheduling** in the worker: on outbox `ticket.closed`, create a `ticket_close` survey unless suppressed (cancelled, resolution code Duplicate, closed within 15 minutes of creation, or the contact already received one today on the account calendar); on the first business day after quarter end, create `quarterly` surveys for account admins and `csat_recipient` contacts; reminders and expiry driven by `ix_csat_surveys_due` with `SKIP LOCKED` claiming. A score of 1 or 2 writes an outbox `csat.low_score` consumed by internal notifications.
- **Deflection**: the pre-submit search writes a session; the ticket create route (portal) links the newest session for the contact within 24 hours by setting `submitted_ticket_id`; the nightly knowledge metrics job classifies the rest (owned by Knowledge Base).

## 3. Producers / core logic

| Producer | Trigger | What it writes |
|---|---|---|
| Invitation (internal admin or account admin) | `POST /v1/accounts/{id}/contacts/invite` or `POST /portal/v1/users/invite` | Contact row `invited`; Clerk organisation invitation on `acct-<key>` through the Clerk backend API; outbox `portal.invited` for the branded email |
| Clerk webhook `organizationMembership.created` | First sign-in after invitation | Binds `clerk_user_id`, creates `op.users` (`kind = portal`), sets contact `active`; signature verified with the Clerk webhook secret |
| Clerk webhook `organizationMembership.deleted`, `user.deleted` | Deactivation | Contact `deactivated`; sessions revoked through the Clerk API |
| Portal ticket create | New request submit | `TicketService.create(origin = portal, requester = contact, form_version_id, form_data)`; priority derived server-side; outbox `ticket.created` |
| Portal comment | Reply | `TicketService.addPublicComment`; outbox `comment.added` (email to watchers and, when the ticket was Waiting on you, the assignee) |
| Portal attachment | Presign and confirm | Same `AttachmentService` with `origin = portal`, `visibility = public` |
| Worker `portal.csat` handler | `ticket.closed`, quarterly schedule, reminder tick | Surveys, reminders, expiry, low-score events |
| Worker `portal.notify` handler | Outbox events with a portal recipient | `acct.notifications` rows with `channel = email` and the outbound message through the Email module |
| Worker `portal.threshold` handler | Consumption threshold events (Time & Budget) | Emails to contacts with `billing_contact` when the account opted in |

## 4. API routes

Portal routes live under `/portal/v1` and accept only `portal` principals; the guard binds `xms.account_id` from the organisation claim. Internal routes for managing portal configuration live under `/v1` and accept `internal` principals. Pagination is cursor-based; mutations accept `Idempotency-Key`. Rate limits: 60 requests per minute per portal user, 10 ticket creates per hour per user, 5 sign-in attempts per 15 minutes per email (Clerk) plus WAF rules on the host.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/portal/v1/me` | any portal | Contact, role, account branding and settings the client may see (consumption level, requester visibility, reopen window) |
| PATCH | `/portal/v1/me` | any portal | Time zone, notification preferences |
| GET | `/portal/v1/tickets` | `portal:submit` or `portal:view-org-tickets` | Own tickets; `scope=org` requires `portal:view-org-tickets` |
| POST | `/portal/v1/tickets` | `portal:submit` | Create from a form version |
| GET | `/portal/v1/tickets/{key}` | as above | Ticket header plus `ticket_timeline_public` rows; 404 for any ticket outside the bound account |
| POST | `/portal/v1/tickets/{key}/comments` | `portal:comment` | Public reply |
| POST | `/portal/v1/tickets/{key}/resolve` | `portal:submit` and account setting | Requester marks resolved |
| POST | `/portal/v1/tickets/{key}/reopen` | `portal:submit` | Within the reopen window |
| POST | `/portal/v1/tickets/{key}/attachments` | `portal:comment` | Presigned POST fields |
| POST | `/portal/v1/attachments/{id}/confirm` | `portal:comment` | Register upload; scan pending |
| GET | `/portal/v1/attachments/{id}/download` | as ticket | Presigned GET only when `scan_state = clean` |
| GET | `/portal/v1/forms` | `portal:submit` | Request-type cards with the current published version |
| GET | `/portal/v1/consumption` | `portal:view-consumption` | Summary or Detailed per the account setting; 404 when Off |
| GET | `/portal/v1/consumption/{period}/statement.(pdf\|csv)` | `portal:view-consumption` | Statement export (rendered by the worker, served as a presigned link) |
| GET, POST | `/portal/v1/surveys`, `/portal/v1/surveys/{id}/answer` | any portal | Pending surveys; answer (one-time token also accepted from the email link without a session, bound to the survey only) |
| GET, POST, PATCH | `/portal/v1/users`, `/portal/v1/users/invite`, `/portal/v1/users/{id}` | `portal:manage-users` | Account admin user management; cannot grant `account_admin` (409, operator confirms) |
| GET | `/portal/v1/solutions*` | `portal:kb` | Owned by Knowledge Base |
| GET, POST, PUT | `/v1/accounts/{id}/forms`, `/v1/accounts/{id}/forms/{formId}/versions` | `admin:config` | Internal form authoring and publish |
| POST | `/v1/accounts/{id}/contacts/invite` | `admin:users` | Internal invitation |
| POST | `/v1/accounts/{id}/portal/fallback` | `admin:users` | Enable local fallback for a named contact for a period; audit event |
| POST | `/webhooks/clerk` | `@Public()` with signature guard | Membership and user lifecycle events |

## 5. Cross-cutting concerns

### 5.1 Realm separation

A portal token on any `/v1` route returns 403 in the guard before permission evaluation; an internal token on `/portal/v1` returns 403 likewise. The route-table snapshot records the principal kinds per route. The web app serves `portal.<domain>` from a separate Next.js route group with its own layout, Clerk configuration (organisation-scoped sign-in, no organisation switcher) and CSP; the internal host never serves portal pages.

### 5.2 Isolation proof (CP-02)

The generated isolation suite runs every account-scoped table under `xms_portal` bound to account A against rows of account B, and additionally asserts: `acct.work_notes` raises permission denied; `ticket_timeline_public` for a ticket with three work notes and two comments returns exactly the two comments and the state lines; a ticket key of B returns 404 from `/portal/v1/tickets/{key}`.

### 5.3 Vocabulary leakage

Portal DTOs in `backend/src/contracts/portal` are separate types from internal DTOs; a mapper produces them, so an internal field cannot appear by accident. A contract test snapshots the portal DTO shapes and fails when a field is added without review.

### 5.4 Availability

The portal degrades when the worker is down: submissions still write the ticket and the outbox; emails and surveys catch up. When the API is down the ALB returns a static maintenance page for the portal host.

### 5.5 Accessibility

`eslint-plugin-jsx-a11y` in the gate stage; axe checks in Playwright on every portal page; a manual keyboard walk recorded in the Phase 3 acceptance.

## 6. Web / client changes

- **Route group** `frontend/app/(portal)/` with layout (account header band with logo and accent from `/portal/v1/me`, navigation built from the settings returned), pages: `home`, `tickets`, `tickets/[key]`, `new`, `consumption`, `knowledge`, `surveys`, `profile`, `users`. Middleware restricts the group to the portal host and the Clerk organisation session.
- **Components**: `RequestTypeCards`, `DynamicForm` (renders a form version definition; validation mirrors `form-schema.ts` from `backend/src/domain`), `PublicTimeline`, `ReplyComposer` with `AttachmentDropzone` (presigned POST, scan state polling every 10 seconds until clean or quarantined), `ConsumptionCards`, `CsatPrompt`, `UsersTable`. Reduced grammar per [Design System §5](../../01-architecture/DESIGN-SYSTEM.md); no condition builder.
- **Solution search** on `new`: `SolutionSearch` from Knowledge Base, recording the deflection session.
- **RTK slice** `portalApi` on the portal base query (Clerk session token, no tenant header), tags `PortalMe`, `PortalTickets`, `PortalTicket`, `PortalForms`, `PortalConsumption`, `PortalSurveys`, `PortalUsers`; `PortalTickets` polls at 60 seconds on the list (house cadence from `web-ui/redux/services/xmsApi.ts`), the open ticket refetches on focus and after mutations.
- **Internal admin screens** (owned here, rendered in the internal app): form builder at `/accounts/{id}/forms` (field list editor, preview using the same `DynamicForm`, publish), contacts and invitations at `/accounts/{id}/contacts`, portal settings on the account record.

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/client-portal-identity` (Phase 1) | Clerk organisation provisioning per account, portal principal in the guard, `xms_portal` role and pool, `acct.contacts`, Clerk webhook, isolation suite cases | Accounts & Administration identity settings; the Clerk spike |
| 2 | `feature/client-portal-core` (Phase 2) | Forms tables and validation, `ticket_timeline_public`, portal controller group (tickets, comments, attachments, forms, me), route group and pages, email notifications | Ticket Management core, Email outbound, Knowledge Base core |
| 3 | `feature/client-portal-consumption` (Phase 2) | Consumption route and cards (Summary) behind the toggle | Time, Contracts & Budget core |
| 4 | `feature/client-portal-sso` (Phase 3) | Enterprise connections per account, fallback procedure, account-admin user management, organisation tickets | 1 |
| 5 | `feature/client-portal-csat` (Phase 3) | Surveys tables, worker handlers, prompts, low-score events, snapshot feed | Dashboards snapshots |
| 6 | `feature/client-portal-statements` (Phase 3) | Detailed consumption, statement exports | Billing periods |
| 7 | `feature/client-portal-templates` (Phase 4) | Common requests, anonymous CSAT, custom domains | Knowledge Base templates |

Deploy order inside each: db migration, worker, api, web. The Clerk organisation for each account is created by the Accounts admin flow before any invitation.

## 8. Testing & verification

- **Domain (Jest):** status mapping covers every internal state for every ticket type (a table-driven test fails when a state is unmapped); form schema validation cases (required mapping, `visible_when` ordering, impact and urgency pairing); CSAT suppression rules; reopen window on the account calendar.
- **Data layer (Testcontainers):** the portal role cannot select `acct.work_notes` (permission denied), `ticket_timeline_public` excludes work notes and internal audit events, RLS on all five portal tables under both roles, append-only triggers on responses and deflection sessions, column grants on contacts.
- **HTTP (supertest):** portal token on `/v1/tickets` is 403; internal token on `/portal/v1/tickets` is 403; anonymous and garbage tokens rejected on every portal route; ticket key of another account is 404; `resolve` with the account setting off is 409; `users/{id}` granting `account_admin` is 409; consumption with setting Off is 404; survey answer with a reused one-time token is 410; rate limit returns 429 with `Retry-After`.
- **Worker:** CSAT creation on `ticket.closed` with each suppression case; reminder and expiry transitions; quarterly generation on the first business day using a constructed calendar; low-score outbox event.
- **Contract:** portal DTO snapshot; Clerk webhook signature verification rejects a tampered payload.
- **Web (Vitest):** `DynamicForm` renders conditional fields and blocks submit on required; `AttachmentDropzone` shows scanning then clean or quarantined states.
- **E2E (Playwright, seed accounts A and B):** invite a portal user for A, sign in with the local fallback and MFA, search a solution, submit a request with an attachment, see the ticket, receive the assignee's public comment, reply, confirm a work note added internally never appears, attempt B's ticket key and get not-found, close the ticket and answer the CSAT; axe scan on every page.
- **Security:** ZAP baseline on the portal host in the dev pipeline; a manual SAML test against a sandbox IdP in Phase 3.

## 9. Risks / notes

- **Clerk topology and cost (ADR-03).** One organisation per account with an enterprise connection each is the assumed model; the Phase 1 spike must confirm licensing for portal MAUs and that enterprise connections can be scoped per organisation on the XMS plan. Fallback is the XMS-owned realm behind the same `Principal`, which would move `acct.contacts` credential fields into a `portal_credentials` table; nothing above the guard changes.
- **One-time survey links without a session** are the only unauthenticated write path; the token is single use, bound to one survey, hashed at rest, expires with the survey, and the route is rate limited.
- **Client-facing status mapping** hides nuance; the pause reason text shown to clients is authored by the consultant when pausing (Ticket Management) and is the only free text that crosses from a pause into the portal.
- **Requesters seeing organisation tickets** is off by default; turning it on for an account is an audit event because it widens visibility inside the account.
- **Branding assets** (logo) are account settings stored in S3 under the account prefix and served through the API, never as user-supplied URLs.

## 10. As-built notes

(To be filled during the build; graduates into `WHAT-WAS-DONE.md`.)
