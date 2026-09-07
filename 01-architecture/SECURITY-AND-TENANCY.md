# Security and Tenancy: XMS Ticketing

**Status:** Draft, pending Security review (isolation ruling requested)
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Architecture](./ARCHITECTURE.md), [Data Model](./DATA-MODEL.md), [AI Integration](./AI-INTEGRATION.md), [Accounts & Administration](../02-modules/accounts-and-administration/TECHNICAL-SPEC.md), [Client Portal](../02-modules/client-portal/TECHNICAL-SPEC.md), [Test Strategy](../03-delivery/TEST-STRATEGY.md)
**Requirements covered:** TM-01, TM-12, TM-13, TM-14, CP-01, CP-02, AI-08, AI-10, AI-11, AI-12, INT-01
**Verified against AIX on 2026-09-04:** `app-api/src/authtentication/*`, `src/guards/*`, `src/rbac/*`, `src/security/*`, `src/middleware/tenant-extractor.middleware.ts`, `web-ui/lib/rbac/permission-catalog.ts`, studio `app/auth/*`

---

## 1. Threat model in one paragraph

XMS holds several clients' support history, contracts, hours and attachments in one product operated by one team, and exposes a portal to those clients. The failures that matter most are: one client seeing another's data (the isolation failure), an internal note or work note reaching a client (the visibility failure), a client identity reaching internal surfaces (the realm failure), an attachment carrying malware into the operator or a client, client data reaching a model provider when the client forbade it (the AI failure), and history being edited after the fact (the evidence failure). Every control below maps to one of those.

## 2. Identity

### 2.1 Two populations, one Clerk application (ADR-03)

| Population | Identity provider | Clerk construct | Token claims used |
|---|---|---|---|
| Internal Hackett users | THG IdP (Entra) through a Clerk enterprise connection | One Clerk organisation `hackett` | `sub`, `org_slug = hackett`, email |
| Portal users | The account's IdP (SAML or OIDC) through a Clerk enterprise connection on that account's organisation; local fallback (email plus password with MFA, or magic link) for accounts without federation | One Clerk organisation per account, slug `acct-<account key>` | `sub`, `org_slug`, email |

Why Clerk for both: the assessment's mitigation for client security questionnaires is "reuse existing ISO 27001 controls; keep Clerk; no new vendors", the team is four people, and SAML is not something to hand-roll (AIX's only external-user code today is a hand-rolled HMAC token in `src/services/jwt/simple-jwt.service.ts` with a default secret, which this spec explicitly does not repeat). Clerk supports enterprise connections per organisation, invitations, MFA and session management. The Phase 1 spike confirms licensing for portal MAUs and the per-organisation SAML topology; if it fails, the fallback is a XMS-owned portal realm (`openid-client`, `@node-saml/node-saml`, argon2 local accounts) behind the same principal interface, so nothing above the guard changes.

AIX findings adopted: `CLERK_JWT_CLOCK_SKEW_MS = 60_000` and the `peekJwt` diagnostic (`app-api/src/authtentication/clerk-jwt.ts`); a long-lived `agents` JWT template exists in AIX's Clerk dashboard for minute-long agent turns and XMS defines the same template for the Axel panel.

AIX gaps corrected in XMS (verified 2026-09-04): app-api verifies the same token up to three times per request across `clerk.strategy.ts`, `common/helpers/token-helper.ts` and `tenant-extractor.middleware.ts`, never passes Clerk's `authorizedParties`, and accepts the long-lived `agents` token on every route. XMS verifies once in the guard with `authorizedParties` set to the XMS hosts, mints the long-lived token with a distinct `aud` claim that the guard accepts only on the Axel adapter routes, and fails loudly at startup if the template is missing instead of silently falling back to short tokens.

### 2.2 Principal resolution (one place, fail closed)

The API resolves a `Principal` once per request in a single guard:

| Field | Source |
|---|---|
| `kind` | `internal`, `portal`, `api_client`, `harness` |
| `userId` | Clerk `sub` mapped to `op.users.id`; API clients and the harness map to a service user |
| `accountIds` | Internal: `op.account_grants`; portal: exactly the account of the organisation in `org_slug`; API client: its grants |
| `permissions` | Transitive closure of role assignments (operator or portal catalog) plus global grants |

Rules learned from AIX and enforced here: there is no `x-tenant-slug` header and no `'default'` fallback (AIX's `@TenantId()` decorator falls back to `'default'` and its three tenant resolvers disagree; XMS has one resolver and returns 401 when the token lacks the claim). Portal tokens are accepted only by routes in the portal controller group; an internal route receiving a portal token gets 403 regardless of permissions.

### 2.3 Machine identities

| Caller | Credential | Notes |
|---|---|---|
| Worker calling the API | Not needed: the worker uses the domain packages and the database directly with the `xms_worker` role, and binds RLS by setting `xms.account_ids` to the accounts of the job it claimed | Avoids an internal HTTP hop and a shared secret |
| Harness calling XMS MCP, MCP calling the API | Harness-minted HS256 session token validated with the shared `SESSION_SECRET`; the API accepts it as a second token type and maps `sub` to the XMS user | The harness's `type == "session"` check is mirrored |
| Finance system pulling exports, future integrations | API clients: prefix `xms_live_`, SHA-256 lookup hash unique-indexed plus bcrypt confirmation, scopes (`exports:read`, `webhooks:write`), account grants, expiry, last used, owned by the operator not a person | Fixes the AIX API-key gaps (no scopes, O(n) bcrypt scan, user-owned) |
| Inbound webhooks (ServiceNow) | Per-instance HMAC secret verified in the worker before the inbox write | Constant-time compare, fail closed when unconfigured (pattern from `require-internal-secret.guard.ts`) |

## 3. Authorisation

- **Global permission guard** with explicit `@Public()` opt-out; every route declares its permissions or is rejected at startup by a route-table test (the studio's golden route snapshot pattern).
- **Catalog in `backend/src/contracts`**, shared by API and web, validated server-side; unknown keys fail the build. Two catalogs: operator (`tickets:view`, `tickets:work`, `tickets:resolve`, `time:log`, `time:adjust`, `time:lock-period`, `contracts:manage`, `capacity:manage`, `reports:view-portfolio`, `admin:accounts`, `admin:users`, `admin:config`, `admin:connectors`, `ai:use`, `ai:configure`, `kb:author`, `kb:publish`) and portal (`portal:submit`, `portal:view-org-tickets`, `portal:comment`, `portal:view-consumption`, `portal:manage-users`, `portal:kb`).
- **Implications are transitive** (AIX's `expandPermissions` is one level deep and documented as a footgun).
- **Role assignments in PostgreSQL only** (`op.role_assignments`), never in Clerk metadata (AIX keeps them in two places and reconciles).
- **Account grants are explicit** (`op.account_grants`); a consultant with no grant on an account cannot see it exists. The studio's `solution_access_grants` reconcile-the-whole-set semantics are kept for the admin screen.
- **Record-level rules** (own time entries only, approver cannot approve own out-of-scope flag) live in the domain services and are unit-tested.

## 4. Data isolation

Mechanics are in [Data Model §3](./DATA-MODEL.md). Controls, in the order a request meets them:

1. Principal resolution with a closed account set.
2. Data layer binds `xms.account_ids` (or `xms.account_id` for portal) with `SET LOCAL`; a connection without the setting sees nothing.
3. `FORCE ROW LEVEL SECURITY` on every account-scoped table, `WITH CHECK` on writes.
4. Portal database role has no grant at all on `acct.work_notes`, `acct.time_entries`, `acct.rate_cards`, `acct.ai_suggestions`, `acct.audit_events` (portal reads a filtered `acct.ticket_timeline_public` view).
5. S3 keys prefixed by account; presigned URLs minted only after an RLS-protected row read; bucket policy denies unprefixed access.
6. Search indexes and embeddings are account-scoped rows, so retrieval cannot leak across accounts even when the query is a vector.
7. Generated isolation suite runs on every build.
8. `dedicated` isolation tier available per account.

The Security ruling requested (assessment appendix B, Juan/Security) is whether shared tables with forced RLS plus the dedicated tier satisfy TM-01 for all accounts, or whether specific accounts must start on the dedicated tier. The design works either way.

## 5. Visibility (internal never reaches a client)

- Work notes and comments are separate tables; the portal role cannot read work notes; public sync subscriptions cannot receive work-note events (there is no event type mapping from work notes to a public direction).
- Attachments carry `origin` and `visibility`; an attachment on a work note is internal by construction.
- Report packs are generated from snapshot tables that hold no free text except the client-facing narrative, which is reviewed before sending in Phase 2 and 3.
- Outbound email templates receive only fields marked client-visible in the contract package; a template cannot reference a work note type.

## 6. Attachments and malware

- Upload by presigned **POST** with `content-length-range` (25 MB default, per-account override), a MIME and extension allowlist, and the S3 SDK `requestChecksumCalculation: 'WHEN_REQUIRED'` setting (a verified AIX bug fix for presigned uploads).
- GuardDuty Malware Protection for S3 scans every object; the worker consumes the scan result and sets `scan_state` (`pending`, `clean`, `quarantined`). Download is served only for `clean`; quarantined files are moved to a quarantine prefix, the uploader and an admin are notified, and the ticket shows a placeholder. Fallback if GuardDuty is not approved: a ClamAV Lambda with the same state machine.
- Inline images from email are re-encoded server-side (strips active content) before storage.

## 7. Audit and evidence

- `acct.audit_events` is append-only with a trigger that raises on update or delete, partitioned monthly, retained for the life of the account plus the contractual retention period.
- Every event records `actor_kind`, `actor_id`, `actor_name`, `correlation_id`, entity, field, old and new value. AI actions record `actor_kind = ai` plus the suggestion id and the confirming human.
- Time entries, adjustments, SLA pauses, inbound messages and snapshots are append-only too.
- Locked billing periods reject writes at the database level (a trigger checks `acct.billing_periods.locked` for the entry date).
- Exports carry a checksum and are stored, so a finance dispute can be traced to the file that was sent.

Security events (sign-in, token rejection, permission and realm denials, isolation-filtered probes, admin changes, exports, downloads) are a separate append-only stream with the same envelope, tamper-evident archive and alerting; see [Audit Log and User Analytics](./AUDIT-AND-ANALYTICS.md).

## 8. AI-specific controls

Enforced in the Axel adapter and the database (see [AI Integration](./AI-INTEGRATION.md)):

- `acct.ai_settings.enabled = false` means no call is made, no embedding rows exist (a policy on `acct.embeddings` and `acct.ai_suggestions` checks the setting), and existing suggestions are hidden.
- Capability opt-ins and confidence thresholds per account.
- Redaction before egress; attachments never leave as binaries.
- No-training and residency guarantees documented with the Axel owners; accounts whose residency cannot be met cannot enable AI.
- Every suggestion and action is auditable with model, prompt version and confidence.

## 9. Application security baseline

- Global `ValidationPipe` with `whitelist`, `forbidNonWhitelisted`, `transform` (AIX has the decorators but never registers the pipe).
- Helmet, strict CSP for both web hosts, CORS allowlist per environment, rate limiting on portal and webhook routes.
- Secrets in AWS Secrets Manager injected through ECS task definition `secrets[]` managed by Terraform; none in images, none in `NEXT_PUBLIC_*`.
- Dependencies audited in the pipeline; `xlsx` (SheetJS 0.18.5, known advisories) is not used; `exceljs` for generation.
- ZAP baseline against the portal on every dev deploy.
- Backups: RDS automated backups with point-in-time recovery, S3 versioning; recovery objectives in [Platform & Operations](./PLATFORM-AND-OPERATIONS.md).

## 10. Compliance hooks

The audit-readiness programme (control catalogue mapped to ISO 27001, SOC 2 and OWASP ASVS with automatic evidence, the secure development gates, the operating rhythm and the questionnaire answer bank) is in [Security Assurance](./SECURITY-ASSURANCE.md); the per-change rules are the `xms-security-first` skill (ADR-16).

- Data residency and isolation tier per account, offboarding procedure (export, then delete after the retention period, with harness thread deletion request).
- DPA register per account (AI allowed, residency, retention) stored in account settings and shown on the account record.
- Reuse of the operator's ISO 27001 controls for questionnaires (assessment p.13); this document is the technical annex for those answers.
