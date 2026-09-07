# Technical Spec: Email Intake & Outbound

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md), [Platform & Operations](../../01-architecture/PLATFORM-AND-OPERATIONS.md), [AIX Pattern Reuse](../../01-architecture/AIX-PATTERN-REUSE.md)
**Requirements covered:** EM-01 to EM-09
**Repos affected:** `backend/src/worker`, `backend`, `frontend`, `backend/src/domain`, `backend/src/db`, `infra`

---

## 1. Architecture context (current state, verified in code)

| Piece | Where | Relevance |
|---|---|---|
| Connector framework (outbox, inbox, DLQ, kill switch) | [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) | Inbound email is an inbox source; outbound email is a connector queue `connector.email-out` |
| Ticket service (single writer of tickets, comments, audit, outbox) | [Ticket Management technical spec](../ticket-management/TECHNICAL-SPEC.md) §3 | The worker's apply step calls it with origin `email`; no email code writes ticket rows directly |
| Attachment pipeline (presigned POST, MIME allowlist, GuardDuty scan state) | [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md) §6 | Email attachments enter the same pipeline server-side (the worker writes objects directly, then registers them) |
| AIX outbound email | `app-api/src/api/v1/email/email.service.ts` (Lambda invoke, templates outside the repo, default from-address a personal Gmail; verified 2026-09-04) | Not copied; the only inherited rule is "never let notification failure propagate into the mutation" from studio `app/modules/xms_ticketing/notify.py` |
| AIX inbound email | Verified absent in app-api, workers and the studio (2026-09-04) | Built from scratch |
| AIX notification schema | `app-api/src/api/v3/notifications/schemas/user-notification.schema.ts` (recipient identity key, collapse keys, TTL) | In-app notifications are owned by Ticket Management; this module consumes `notification.created` outbox events for email delivery |
| S3 client checksum setting | `app-api/src/files/services/file-storage.service.ts` (`requestChecksumCalculation: 'WHEN_REQUIRED'`) | Applied to the worker's S3 client too |
| AIX SQS consumer shape | `workers/tasks/vectorizer/sqs.py` (long poll, delete after process, no DLQ) | Replaced by the framework's redrive and DLQ semantics |
| Design grammar for the quarantine list and record | `web-ui/components/aix-v3/xms/QueueTab.tsx`, `NewTicketPage.tsx` | [Design System](../../01-architecture/DESIGN-SYSTEM.md) §4 |

Cross-container ordering: `infra` (SES domain, receipt rules, S3 prefix, SQS queues, SNS topics) -> `backend/src/db` migration -> `backend/src/worker` (parse, apply, send) -> `backend` (aliases, log, quarantine routes) -> `frontend`.

## 2. Data model

All tables are in schema `acct` with `account_id` and RLS per [Data Model §3](../../01-architecture/DATA-MODEL.md). Append-only tables have no `updated_at` and carry the raise-on-update trigger.

### 2.1 `acct.inbound_aliases`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid NOT NULL | RLS |
| `address` | text NOT NULL | Lowercased; unique across the operator (an address routes to one account) |
| `kind` | text | CHECK IN (`canonical`, `alias`) |
| `default_ticket_type` | text NULL | Overrides the account intake rule |
| `state` | text NOT NULL default `active` | CHECK IN (`active`, `disabled_by_admin`, `disabled_by_loop_guard`) |
| `verification_token` / `verified_at` | text / timestamptz | Alias verification (§3.4) |
| `disabled_reason` / `disabled_at` | text / timestamptz | Set by the loop guard or an admin |
| `created_at` / `updated_at` / `version` | | Mutable row conventions |

### 2.2 `acct.inbound_messages` (append-only)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid NOT NULL | Resolved from the alias; unresolvable messages go to `sys.inbox` with a null account and are rejected, never stored here |
| `alias_id` | uuid NOT NULL FK | |
| `raw_s3_key` | text NOT NULL | `accounts/<account_id>/email/inbound/<yyyy>/<mm>/<message uuid>.eml` |
| `message_id` | text NOT NULL | RFC 5322 Message-ID, normalised; unique per account |
| `in_reply_to` | text NULL | |
| `references` | text[] NOT NULL default `{}` | Ordered |
| `plus_token` | text NULL | From the recipient local part |
| `from_address` / `from_name` | text | Lowercased address |
| `to_addresses` / `cc_addresses` | text[] | |
| `subject` | text | |
| `received_at` | timestamptz NOT NULL | SES receipt time; SLA start |
| `sender_resolution` | text NOT NULL | CHECK IN (`known_contact`, `known_internal`, `portal_user`, `unknown`) |
| `contact_id` / `user_id` | uuid / text NULL | Resolved identity |
| `loop_score` | integer NOT NULL | §2.6 |
| `loop_signals` | text[] NOT NULL default `{}` | Which signals fired |
| `disposition` | text NOT NULL | CHECK IN (`created`, `appended`, `quarantined`, `suppressed`, `rejected`) |
| `suppression_reason` | text NULL | CHECK IN the vocabulary of functional §5.1 |
| `ticket_id` / `comment_id` | uuid NULL | Set for `created` and `appended` |
| `stripped_body_text` / `stripped_body_html` | text | What became the comment |
| `attachment_count` | integer | |
| `size_bytes` | integer | |
| `created_at` | timestamptz | Processing time |

### 2.3 `acct.outbound_messages` (append-only rows; delivery state lives in a sibling mutable table)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `account_id` | uuid NOT NULL | |
| `ticket_id` | uuid NULL | Null for account-level mail (report packs, quarantine digest) |
| `kind` | text NOT NULL | CHECK IN the outbound kind vocabulary |
| `template_version` | text NOT NULL | Git-tracked template id and version |
| `message_id` | text NOT NULL | Generated `<uuid>@support.xms.<domain>`; unique |
| `in_reply_to` / `references` | text / text[] | Threading (§3.5) |
| `from_identity_id` | uuid NOT NULL | Sender identity on the account |
| `to_addresses` / `cc_addresses` | text[] | |
| `subject` | text NOT NULL | |
| `rendered_s3_key` | text NOT NULL | Stored rendered MIME for the preview and audit |
| `outbox_id` | uuid NOT NULL | The originating outbox row (idempotency) |
| `created_at` | timestamptz | |

`acct.outbound_deliveries` (mutable): `outbound_message_id`, `ses_message_id`, `state` CHECK IN (`queued`, `sent`, `delivered`, `bounced`, `complained`, `failed`), `state_at`, `detail` jsonb, `version`.

### 2.4 `acct.sender_identities`, `acct.suppressed_addresses`, `acct.quarantine_items`

| Table | Columns (abridged) |
|---|---|
| `acct.sender_identities` | `id`, `account_id`, `address`, `display_name`, `domain_kind` CHECK IN (`xms`, `client`), `dkim_status` CHECK IN (`pending`, `verified`, `failed`), `dkim_tokens` text[], `is_default` bool, `branding` jsonb (logo S3 key, accent, footer text), timestamps, `version` |
| `acct.suppressed_addresses` | `id`, `account_id`, `address`, `reason` CHECK IN (`bounce_hard`, `complaint`, `manual`), `source_delivery_id`, `created_at`, `cleared_at`, `cleared_by` |
| `acct.quarantine_items` | `id`, `account_id`, `inbound_message_id` FK, `reason` CHECK IN (`unknown_sender`, `suspicious_content`, `scan_quarantined`, `unsupported_content`), `state` CHECK IN (`open`, `decided`, `expired`), `decision` CHECK IN (`create_contact_and_ticket`, `create_ticket_once`, `discard`, `mark_spam`) NULL, `decided_by`, `decided_at`, `resulting_ticket_id`, `created_at`, `version` |

### 2.5 Indexes, constraints, RLS

```sql
create unique index ix_inbound_aliases_address on acct.inbound_aliases (lower(address));
create index ix_inbound_aliases_account_state on acct.inbound_aliases (account_id, state);

create unique index ix_inbound_messages_account_message_id on acct.inbound_messages (account_id, message_id);
create index ix_inbound_messages_ticket on acct.inbound_messages (ticket_id) where ticket_id is not null;
create index ix_inbound_messages_sender_window on acct.inbound_messages (account_id, from_address, received_at desc);
create index ix_inbound_messages_subject_burst on acct.inbound_messages (account_id, alias_id, subject, received_at desc);

create unique index ix_outbound_messages_message_id on acct.outbound_messages (message_id);
create unique index ix_outbound_messages_outbox on acct.outbound_messages (outbox_id);
create index ix_outbound_messages_ticket on acct.outbound_messages (ticket_id, created_at desc) where ticket_id is not null;
create index ix_outbound_deliveries_state on acct.outbound_deliveries (account_id, state) where state in ('queued','bounced','complained','failed');

create unique index ix_quarantine_open on acct.quarantine_items (inbound_message_id) where state = 'open';
create index ix_quarantine_account_open on acct.quarantine_items (account_id, created_at) where state = 'open';

alter table acct.inbound_messages enable row level security;
alter table acct.inbound_messages force row level security;
create policy acct_isolation_operator on acct.inbound_messages
  using (account_id = any (current_setting('xms.account_ids')::uuid[]))
  with check (account_id = any (current_setting('xms.account_ids')::uuid[]));
-- identical policy pairs on every table in this module; the portal role has NO grant on any of them
revoke all on acct.inbound_messages, acct.outbound_messages, acct.quarantine_items,
  acct.sender_identities, acct.suppressed_addresses, acct.inbound_aliases from xms_portal;
create trigger inbound_messages_append_only before update or delete on acct.inbound_messages
  for each row execute function sys.raise_append_only();
```

### 2.6 Thread matching algorithm (`backend/src/domain/email/threadMatcher.ts`)

Inputs: parsed headers, recipient local parts, account id. Output: `{ ticketId, matchedBy } | null`. Order of precedence, first hit wins:

1. **Plus token** in any recipient local part (`<account key>+<token>@...`): the token is a 12-character base32 value stored on `acct.tickets.email_token`; matched by exact lookup. Strongest, because it survives every client's subject and header rewriting.
2. **In-Reply-To** equal to a `message_id` in `acct.outbound_messages` or `acct.inbound_messages` for this account: use that row's `ticket_id`.
3. **References** scanned newest to oldest against the same two tables.
4. **Subject key** `[CS0001234]` present and the ticket belongs to this account: weakest, used only if 1 to 3 miss, and only when the ticket is not Closed for longer than the reopen window.

Matching is strictly inside the account resolved from the alias; a plus token or Message-ID from another account is treated as no match and logged as a cross-account probe (EM-02, EM-03, TM-01).

### 2.7 Loop score (`backend/src/domain/email/loopGuard.ts`)

| Signal | Points | Source |
|---|---|---|
| `Auto-Submitted` present and not `no` | 100 (hard suppress) | RFC 3834 |
| `X-Auto-Response-Suppress`, `X-Autoreply`, `X-Autorespond` | 100 | Common auto-responders |
| `Precedence: bulk`, `list`, `junk`; `List-Id` present | 100 | Bulk mail |
| Our own outbound `message_id` appears twice or more in `References` | 80 | Reflected thread |
| Same sender to the same alias more than 10 times in 10 minutes | 60 | Rate window (`ix_inbound_messages_sender_window`) |
| Identical normalised subject from the same sender 5 times in 10 minutes | 40 | Burst (`ix_inbound_messages_subject_burst`) |
| Subject starts with `Automatic reply`, `Out of Office`, localised variants | 50 | Corpus-maintained list |
| Sender is one of our own sender identities | 100 | Self-reflection |

Score at or above 100 -> `suppressed`. Score 60 to 99 -> processed but flagged `loop_signals`, and counted. **Loop detected** when one sender accrues 3 suppressions or 5 flagged messages on one alias within 10 minutes: the worker sets the alias to `disabled_by_loop_guard`, adds the sender to a temporary outbound pause list, emits the `email.loop_detected` metric and alarm, and writes an audit event on the account. Outbound to that sender resumes when the alias is re-enabled by an admin (EM-06).

### 2.8 Stripping rules (`backend/src/domain/email/stripper.ts`)

Text and HTML paths. Remove, in order: quoted history (lines after the first reply-header pattern such as `On ... wrote:`, `From: ... Sent: ...`, `-----Original Message-----`, `Le ... a écrit :`, `Am ... schrieb`, and `<blockquote type="cite">` or Gmail's `gmail_quote` class in HTML), signature blocks (`-- ` delimiter, the `Sent from my` family, and a corpus-maintained set of signature heuristics), legal disclaimers (paragraphs longer than 400 characters matching the disclaimer lexicon), and trailing whitespace. Inline images referenced by `cid:` are kept and rewritten to attachment URLs. The parser is data-driven: patterns live in `backend/src/domain/email/patterns/*.json` so a new mail client can be supported without a code change, and every pattern has a corpus sample (EM-04, EM-05).

## 3. Producers / core logic

All handlers run in `backend/src/worker` on the connector framework.

### 3.1 Inbound pipeline

1. **SES receipt rule** for the inbound domain: action `S3` to `s3://<bucket>/email/inbound/raw/<messageId>` then `SNS` -> `SQS email-in`. Spam and virus verdicts from SES are kept as headers.
2. **`EmailInboundHandler`** (queue `email-in`): reads the raw object, parses with `mailparser`, normalises headers, resolves the alias from `to` and `cc` and `X-Original-To` and the `Received` chain (forwarded mail keeps the alias in `Delivered-To` or the envelope). No alias -> `rejected` in `sys.inbox` and a metric; nothing stored in `acct`.
3. Writes `sys.inbox` with key (`email`, `message_id`); a duplicate delivery ends here.
4. Moves the raw object to the account prefix, computes loop score, resolves sender (contacts, internal users by email, portal users), runs the thread matcher, strips the body, extracts attachments to `accounts/<account_id>/attachments/<uuid>` (scan state `pending`), re-encodes inline images through `sharp` to strip active content.
5. Decides disposition and calls the ticket service in one transaction: `createTicket({source:'email', receivedAt})`, `appendComment(...)`, or `quarantine(...)`. The ticket service writes the audit event and the outbox rows for notifications. Any failure after the inbox write is retried by SQS; the inbox key makes reprocessing idempotent.
6. Records `acct.inbound_messages` with the disposition.

### 3.2 Outbound pipeline

1. The ticket service and other modules write outbox events (`ticket.created`, `comment.added`, `ticket.transitioned`, `ticket.assigned`, `sla.warning`, `csat.invite`, `report.ready`, `notification.created`).
2. The dispatcher routes them to `connector.email-out` for accounts and recipients whose notification matrix subscribes.
3. **`EmailOutboundHandler`** resolves recipients (watchers, requester, group members) minus `acct.suppressed_addresses` and loop-paused senders, renders the template (`backend/src/domain/email/templates/<kind>.mjml` compiled at build, plus a text alternative), sets threading headers (§3.5), signs through the account's SES identity, sends with SES v2 `SendEmail` with the `outbox_id` as the idempotency token in `acct.outbound_messages` (unique index), and stores the rendered MIME in S3.
4. **SES events** (delivery, bounce, complaint) arrive on SNS -> SQS `email-events` -> `EmailEventHandler`, which updates `acct.outbound_deliveries` and inserts `acct.suppressed_addresses` for hard bounces and complaints, and marks the contact.

### 3.3 Template contract

Templates receive a typed view model built from a `backend/src/contracts` type per kind that contains only client-visible fields (ticket key, title, state label, public comment body, requester name, account branding, links). The build fails if a template references a field outside its view model (`mjml` compile plus a type-checked render step). Work notes are not part of any view model (EM-08, TM-13).

### 3.4 Alias verification

Adding an alias generates `verification_token`; the admin forwards any message to the alias containing the token in the subject; the inbound handler, on seeing an unverified alias, only checks the token and sets `verified_at`. Until verified, the alias accepts nothing else.

### 3.5 Threading headers

Root message per ticket: the first outbound message for a ticket becomes `acct.tickets.email_root_message_id`. Every later outbound message sets `In-Reply-To` to the most recent message in the ticket (inbound or outbound) and `References` to `[root, ..., latest]` capped at 20 entries with the root always first. The subject is `[CS0001234] <title at creation>`; a title edit does not change the subject (Outlook threads on subject as a fallback).

### 3.6 Quarantine decisions and digest

Decisions are API calls (§4) executed by the ticket service with origin `email`; `create_contact_and_ticket` inserts `acct.contacts` first. A daily worker job (claimed with `SKIP LOCKED`) expires items older than 14 days and sends the `quarantine_digest` kind to the account's operator group.

## 4. API routes

All under `/v1`, internal principal unless noted; permissions from the operator catalog.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/accounts/{id}/email/aliases` | `admin:accounts` | List aliases with state |
| POST | `/accounts/{id}/email/aliases` | `admin:accounts` | Add alias, returns verification token |
| PATCH | `/accounts/{id}/email/aliases/{aliasId}` | `admin:accounts` | Enable or disable, default ticket type; re-enable after loop guard requires `admin:accounts` and writes an audit event |
| GET/POST/PATCH | `/accounts/{id}/email/sender-identities[...]` | `admin:accounts` | Manage identities, request DKIM tokens, set default and branding |
| GET | `/accounts/{id}/email/notification-matrix` and PUT | `admin:accounts` | Which kinds go to which audience |
| GET | `/accounts/{id}/email/log?direction=&state=&from=&to=` | `tickets:view` | Account email log |
| GET | `/tickets/{id}/email` | `tickets:view` | Ticket Email tab: inbound and outbound with delivery state and preview links |
| GET | `/email/messages/{id}/raw` | `tickets:view` plus internal principal only | Presigned link to the raw `.eml` |
| GET | `/email/quarantine?accountId=&reason=` | `tickets:work` | Quarantine list |
| POST | `/email/quarantine/{id}/decision` | `tickets:work` | Body `{decision, ticketInput?}`; idempotent per item |
| GET/DELETE | `/accounts/{id}/email/suppressions[...]` | `admin:accounts` | View and clear suppressed addresses |
| POST | `/email/test-send` | `admin:accounts` | Send a test notification to the caller |

No route accepts a portal principal. Inbound processing has no HTTP surface; SES and SNS deliver to SQS only. Idempotency keys are required on every POST per [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md).

## 5. Cross-cutting concerns

- **Isolation:** the alias is the only way an inbound message acquires an account; matching and sender resolution run inside that account's RLS context; the worker binds `xms.account_ids` to the single resolved account for the transaction.
- **Visibility:** work notes have no template view model and no outbox event type that routes to `connector.email-out` with a client audience.
- **Malware:** attachments extracted from email are written with scan state `pending`; download is gated by GuardDuty results exactly like uploads.
- **SLA:** `received_at` from SES is passed to the ticket service as the creation instant.
- **Idempotency:** `sys.inbox` on `message_id` for inbound; `outbox_id` unique index for outbound; SES `SendEmail` is retried only when no `acct.outbound_messages` row exists.
- **Rate and abuse:** SES receipt rules drop mail over 40 MB (SES limit); the handler rejects over the account limit with a bounce template; per-sender rate windows feed the loop score.
- **Observability:** metrics `email.inbound.count{disposition}`, `email.inbound.lag_seconds` (received to processed), `email.loop_detected`, `email.outbound.count{kind,state}`, `email.bounce_rate`; alarms on loop detected, lag over 5 minutes, bounce rate over 5 percent, queue age.

## 6. Web / client changes

- **Quarantine queue** (`frontend/app/(internal)/intake/quarantine`): list in the standard grammar with the columns of functional §5.4, record view with the stripped body, attachment list with scan badges, and the four decision buttons; "Create contact and ticket" opens the full-screen New record form pre-filled.
- **Account record, Email tab:** aliases with state and verification, sender identities with DKIM status and CNAME records to copy, notification matrix grid, suppression list, email log.
- **Ticket record, Email tab:** outbound and inbound rows with preview drawer (rendered HTML in a sandboxed iframe) and raw link for internal users.
- **Comment rendering:** a "via email" chip; inline images rendered from attachment URLs; a "show quoted history" link that fetches the raw message for internal users only.
- RTK Query slice `emailApi` with tags `EmailAliases`, `EmailLog`, `Quarantine`; quarantine list polls at 60 seconds (house cadence).

## 7. Ordering / branches

| Order | Branch | Scope | Depends on |
|---|---|---|---|
| 1 | `feature/email-intake-infra` (`infra`) | SES domain and DKIM, receipt rules, S3 prefixes, SQS `email-in`, `email-events`, `connector.email-out` with DLQs, SNS topics | Foundations infra |
| 2 | `feature/email-intake-db` (`backend/src/db`) | Tables of §2 with RLS and triggers | Accounts and tickets tables |
| 3 | `feature/email-intake-outbound` (`backend/src/domain`, `backend/src/worker`) | Templates, threading, SES v2 send, events handler | Ticket service outbox events |
| 4 | `feature/email-intake-inbound` (`backend/src/domain`, `backend/src/worker`) | Parser, matcher, stripper, loop guard, apply | 3 |
| 5 | `feature/email-intake-api` (`backend`) | Routes of §4 | 2 |
| 6 | `feature/email-intake-web` (`frontend`) | Screens of §6 | 5 |

Deploy order every release: infra -> db -> worker -> api -> web.

## 8. Testing & verification

- **Corpus tests** (`backend/src/domain/email/__tests__/corpus/*.eml` with expected `.txt` and `.json` outputs): Outlook desktop and web replies, Gmail web and mobile, Apple Mail, ServiceNow notification with its own footer, out-of-office (Exchange and Gmail variants), hard bounce DSN, complaint ARF, a reflected loop chain, forwarded mail with `Delivered-To`, HTML-only mail with `cid:` images, attachment-only mail, oversized mail, S/MIME signed, non-English quote headers. Assertions are exact stripped output, matched ticket, disposition, loop score and signals.
- **Matcher unit tests:** precedence order, cross-account token treated as no match, reopen window boundary on the account calendar.
- **Loop guard tests:** each signal in isolation; the 3-suppression and 5-flag thresholds; alias disable and re-enable flow; outbound pause list.
- **Worker integration tests** (Testcontainers Postgres plus LocalStack S3 and SQS): raw object -> ticket created with `received_at` preserved; duplicate delivery processed once; failure after inbox write retried without a second ticket.
- **Outbound tests:** template render against the view-model type (a template referencing a non-model field fails compilation); threading headers across five messages; suppression list honoured; SES stub records one send per outbox id under retry.
- **Chaos:** SES stub returns throttling then success (one row, two attempts); handler crash mid-transaction (no partial ticket).
- **Isolation suite:** every table in §2 generated into the cross-account suite.
- **HTTP tests:** anonymous and portal tokens rejected on every route; quarantine decision idempotent; raw link denied to portal principals.
- **e2e (Playwright with MailHog):** submit a message to the seed alias, see the ticket, reply from MailHog's UI, see the comment; loop simulation with the auto-reply stand-in stops within one minute.
- **Local dev:** docker-compose runs MailHog for outbound (SES stub endpoint) and a small `email-in` injector script that drops `.eml` files into LocalStack S3 and publishes the SQS message, so the whole pipeline runs without AWS.

## 9. Risks / notes

- **Client forwarding delays or misconfiguration** can hide the alias in headers; the resolver checks four header locations and falls back to the envelope recipient from SES's `receipt.recipients`.
- **Stripping is never perfect.** The raw message is always one click away for internal users; a wrong strip loses nothing.
- **Threading depends on our root message existing.** Tickets created by email get their root from the inbound message id, so a reply threads even before any notification was sent.
- **SES sandbox in dev** limits recipients; the dev environment uses verified test addresses and MailHog.
- **DKIM for client-owned domains** requires the client to publish CNAMEs; onboarding checklists carry the records and the sender identity shows the status.
- **Migrating ServiceNow inbound addresses** is a per-account cutover step owned jointly with [Data Migration & Cutover](../data-migration/FUNCTIONAL-SPEC.md).

## 10. As-built notes

To be filled during the build; graduates into `WHAT-WAS-DONE.md`.
