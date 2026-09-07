# Functional Spec: Platform Integrations

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [ServiceNow Sync](../servicenow-integration/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Roadmap](../../03-delivery/ROADMAP.md)
**Requirements covered:** INT-04, INT-05; delivery mechanism for INT-02 (content owned by Time, Contracts & Budget); registry and health surface for every connector (SN-07 shared); INT-01 and INT-03 are owned elsewhere and only cross-referenced
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`, `infra`

---

## 1. Problem

XMS does not live alone. Finance needs the locked billing data delivered as a structured interface rather than a file someone emails (INT-02). Clients and future tooling need a supported way to read and write tickets without screen-scraping, and to be told when something changes. The team works in Microsoft Teams and Outlook and wants ticket events, ticket creation and time logging where they already are (INT-04), and change windows on their calendars (INT-05). Axel reaches XMS through an MCP server that has to be operated like any other integration. Every one of these needs the same things: a registry that says which integrations exist and how they are configured, a health view that says whether they are working, and the plumbing guarantees from the [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md) framework.

This module covers the cases that no other module owns:

1. **The connector registry and health overview** shared by every connector (ServiceNow, email, finance, reports, webhooks, chat, calendar, MCP).
2. **The finance connector**: how the export produced by Time & Budget is delivered and acknowledged.
3. **The public XMS API and outbound webhooks** for clients and integrators.
4. **Microsoft Teams (then Slack)**: notifications to channels, create-from-message, time logging by command.
5. **Calendar push** of change windows and scheduled work to Outlook.
6. **The XMS MCP server** as an operated integration.

## 2. Current state (what exists today)

- **AIX has an MCP catalog and connection store** in `app-api/src/api/v3/mcp/` (catalog rows, per-opportunity credentials, OAuth refresh with mark-invalid-on-failure, and a `resolve-session` contract that returns unreachable servers as `skipped` instead of failing the run). That degradation idea is adopted for the XMS registry; the catalog itself is AIX's, and XMS only needs one row in it for the XMS MCP server.
- **AIX API keys** (`app-api/src/security/`) are user-owned, unscoped, and validated by scanning bcrypt hashes; the XMS API client design in [Security §2.3](../../01-architecture/SECURITY-AND-TENANCY.md) fixes all three.
- **No webhook receivers or senders, no Slack or Teams integration, no calendar integration** exist anywhere in `app-api`, `web-ui`, `workers` or the studio (verified 2026-09-04). ClickUp exists only as a Claude Code tool for the developers, not as a product integration.
- **Finance export today** is manual file handling out of ServiceNow and spreadsheets; there is no interface.
- **The XMS MCP server** is specified in [AI Integration §4](../../01-architecture/AI-INTEGRATION.md) and built on the `aix-mcp` scaffolding; its operation (health, kill switch, version) is this module's concern.

## 3. Goals

1. **One registry, one health page.** An administrator sees every integration XMS has, per account where relevant, with its mode, last success, backlog and dead letters, and can pause any of them with one switch.
2. **Finance gets a feed, not a file.** Locked billing exports are delivered to the agreed destination automatically, acknowledged, and visible as delivered or failed in XMS.
3. **A supported API.** Integrators and clients can read and write through a versioned, documented, scoped API and subscribe to signed webhooks for changes, without asking the team for a database export.
4. **Work where people already are.** Teams channels receive the events a team cares about, and a consultant can create a ticket or log time from a message without opening XMS.
5. **Change windows on the calendar.** Scheduled work appears on the right people's Outlook calendars and updates when the window moves.
6. **Nothing bypasses the framework.** Every integration inherits idempotency, retries, dead letters, replay and the kill switch, so a failing integration degrades itself and nothing else.

## 4. Non-goals / out of scope

- **ServiceNow sync.** Owned by [ServiceNow Sync](../servicenow-integration/FUNCTIONAL-SPEC.md); it appears in the registry and health page like every other connector.
- **Email intake and outbound.** Owned by [Email Intake & Outbound](../email-intake/FUNCTIONAL-SPEC.md); same registry treatment.
- **Internal identity federation** (INT-01) is owned by [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md); **renewal alerts** (INT-03) and the content of the billing export (TB-14) by [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md).
- **Invoicing.** Finance produces invoices from the feed; XMS never generates one.
- **A general-purpose integration builder** (no-code mapping for arbitrary systems). Field and state maps exist for ServiceNow; other connectors ship with fixed contracts.
- **Slack before Teams.** Hackett runs on Microsoft; Slack ships only if a client channel requires it, and reuses the same abstraction.
- **Two-way calendar sync.** XMS pushes events; changes made in Outlook do not change the ticket group.
- **Inbound API for portal users.** Client users use the portal; API clients are issued to organisations and machines, not to individual portal users, in Phases 3 and 4.

## 5. User-facing behavior

### 5.1 Vocabulary

| Set | Values | Notes |
|---|---|---|
| Connector type | servicenow, email_inbound, email_outbound, finance_export, report_delivery, webhook, teams, slack, calendar, mcp | Registry entries; each has a scope: `account` (one instance per account) or `operator` (one instance) |
| Instance mode | off, ingest_only, bidirectional, outbound_only | Not every type supports every mode; the registry says which |
| Health | healthy, degraded, failing, paused | Degraded: retries happening or backlog above threshold; failing: dead letters or no success within the expected interval; paused: kill switch |
| API client scope | tickets:read, tickets:write, comments:write, time:read, exports:read, kb:read, webhooks:manage | Granted per client, per account set |
| Webhook event | ticket.created, ticket.updated, ticket.transitioned, comment.created, attachment.scanned, time_entry.created, billing_period.locked, report_pack.ready | Public comments only; work notes never appear |
| Delivery status | pending, delivered, retrying, dead_lettered, replayed | Per webhook delivery and per finance delivery |

### 5.2 Registry and health (all connectors)

An admin area (permission `admin:connectors`) in the ServiceNow list grammar:

1. **Connectors list.** One row per connector instance: type, account (or "Operator"), name, mode, health, last success, backlog, dead letters, kill switch toggle. Sorting defaults to failing first. Filters by type, account, health.
2. **Instance record.** Properties (mode, schedule, endpoint, credential reference shown as a name only, never a secret), a **Health** tab (success and failure counts per hour for seven days, the last ten runs with duration and outcome), a **Dead letters** tab (payload summary, error, attempts, first and last failure, Replay and Discard with a required reason), and a **Configuration** tab specific to the type (finance destination, Teams channel mapping, webhook endpoints, calendar consent status, MCP version).
3. **Kill switch.** Flipping to `off` stops dispatch and apply for the instance immediately; queued work waits; flipping back resumes in order. The change is audited with actor and reason.
4. **Alerts.** A connector that becomes `failing` notifies the operator's integrations group by XMS notification and email; the health page shows the open alert until acknowledged.

Empty state: "No connectors configured for this account. Add one from the registry." The registry offers only the types the operator has enabled.

### 5.3 Finance connector

- **What it delivers.** The billing export produced by Time & Budget when a billing period is locked (TB-14, INT-02): the file in the format finance owns, plus a manifest with period, account, checksum and row counts.
- **How.** One operator-level instance with a destination chosen from: an S3 bucket and prefix finance reads, an SFTP endpoint, or an HTTPS endpoint finance exposes. Delivery happens automatically on lock, or by an admin pressing **Deliver** on the period. Finance acknowledges either by an acknowledgement file dropped next to the manifest or by the HTTPS response; the period shows `delivered` then `acknowledged`, or `failed` with the reason and a Retry action.
- **Edge cases.** A period unlocked after delivery (a correction) produces a new delivery marked `supersedes <previous>`; finance sees both files and the manifest says which is current. Delivery never alters the export content; the checksum on the period record is the one finance received.

### 5.4 Public API and webhooks

- **API clients.** Created by an administrator for an organisation or system: name, owner contact, scopes, account set, expiry. The key is shown once. The list shows last used, expiry and a revoke action. Client accounts can be granted a key limited to their own account so their tooling can read their tickets.
- **Documentation.** The API reference is published at a fixed address per environment from the same definition the product uses, with a changelog; version `v1` is stable for the life of the product and additive changes do not bump it.
- **Webhook subscriptions.** An API client with `webhooks:manage` registers an endpoint with a list of event types and receives a signing secret once. Each delivery carries the event, the entity's public representation and a signature header; the endpoint must answer quickly and can process later. Failed deliveries retry with backoff and land in dead letters after the framework's attempts; the subscription record shows delivery health and lets the owner replay from the console or, for their own subscription, through the API.
- **Rate limits.** Per API client, with limits shown in the client record and in response headers.
- **Edge cases.** A subscription whose endpoint keeps failing for 24 hours is paused and its owner contact emailed; deleting an API client cascades to its subscriptions; a webhook payload never includes work notes, internal time detail or another account's data even when the client key spans several accounts (payloads are per account).

### 5.5 Microsoft Teams (then Slack)

- **Channel notifications.** Per account, an administrator maps XMS events (new ticket, P1 created, SLA at risk, SLA breached, assigned to a group, resolved, CSAT received) to a Teams channel via an incoming webhook or the XMS Teams app. Messages carry the ticket key, title, priority, state, assignee and a link; nothing internal beyond what the internal app shows.
- **Create from message.** A consultant uses the XMS message action on any Teams message: a small form pre-filled with the message text as description, asks for account, type and priority, and creates the ticket with origin `teams`, linking back to the message.
- **Log time by command.** `/xms time CS0001234 45m Analysis "reviewed logs"` from the XMS bot creates a time entry for the user (mapped by the same email as their XMS user); the bot replies with the entry and the ticket's hours so far; validation errors come back as the same rules the web form applies.
- **Edge cases.** A Teams user without a XMS account gets a polite refusal; a channel mapping to an account the user cannot see still posts (channels are chosen by administrators, not by the sender); Slack mirrors the same features through the same abstraction when enabled.

### 5.6 Calendar push

- **What is pushed.** Ticket groups of kind `change window` and tickets with a scheduled start and end. Attendees are the assignees and the account owner, plus optional named contacts.
- **How.** Each internal user consents once (Microsoft sign-in from their profile page) so XMS can write to their calendar; the operator registers the XMS application with Microsoft once. Events are created, updated and cancelled as the window changes; the event body carries the ticket key and a link, and the event's XMS origin is marked so re-syncs do not duplicate.
- **Edge cases.** Users who have not consented see a reminder on the change window; a window with no assignees creates nothing; time zones follow each attendee's own calendar.

### 5.7 The XMS MCP server as an integration

Appears in the registry as an operator-level connector of type `mcp`: version, endpoint, health (last successful tool call, error rate), and a kill switch that makes every tool return "XMS tools are paused" to Axel without breaking the turn. Its authentication and tool surface are defined in [AI Integration §4](../../01-architecture/AI-INTEGRATION.md).

## 6. Rollout

1. **Phase 1 (Foundations): the registry and health skeleton.** Connector types table, instance records with mode and kill switch, health computed from sync runs and dead letters, the admin list and record views. Email and the MCP server register here as soon as they exist. Depends on the connector framework tables.
2. **Phase 3 (Operational replacement): finance connector, public API v1, webhooks.** Finance delivery on period lock with acknowledgement; API clients with scopes; published reference; webhook subscriptions with signed delivery, retries, dead letters and replay. Depends on billing period locking in Time & Budget and on API client identities in Accounts & Administration.
3. **Phase 4 (Later releases): Teams, then calendar, then Slack.** Channel notifications and create-from-message first, time logging by command second, calendar push third, Slack only on demand.

## 7. Success criteria

- The connectors list shows the ServiceNow instance, the email connector, the finance connector, the report delivery connector and the MCP server with correct health, and flipping any kill switch stops its work within 30 seconds and resumes it in order when flipped back, with both actions in the audit trail.
- Locking a billing period delivers the export and manifest to the finance destination within five minutes; the period shows `acknowledged` after finance's acknowledgement; a re-lock produces a superseding delivery.
- An API client scoped to `tickets:read` on one account can list that account's tickets, receives 403 on write routes and 404 for another account's ticket, and appears with a correct "last used" time.
- A webhook subscription receives `ticket.transitioned` with a valid signature within 30 seconds of a transition; an endpoint that returns 500 five times sees the delivery in dead letters and a replay delivers it once.
- A P1 created for a mapped account posts to the mapped Teams channel; the create-from-message action produces a ticket whose description is the message text and whose origin is `teams`; the time command creates an entry visible on the ticket's hours breakdown.
- A change window with two assignees creates two calendar events, moving the window updates both, and re-running the sync creates no duplicates.
- No webhook payload, Teams message or calendar event ever contains a work note, a rate, or a different account's data (asserted by tests).

## 8. Open questions

- **Finance destination and format.** S3, SFTP or HTTPS, and the file layout. Default assumption: S3 bucket owned by finance with a prefix per period, CSV plus JSON manifest, acknowledgement file `<manifest>.ack`.
- **Who may hold API keys.** Client organisations from Phase 3, or operator systems only? Default assumption: operator systems and finance in Phase 3, client organisations on request in Phase 4.
- **Teams delivery mechanism.** Incoming webhooks only (simple, no bot) or a registered Teams app (needed for message actions and commands)? Default assumption: incoming webhooks for notifications first, the app for actions and commands when Phase 4 starts.
- **Calendar scope.** Only change windows, or every scheduled ticket? Default assumption: change windows and tickets with an explicit schedule; nothing else.
- **Webhook retry horizon.** Default assumption: the framework's five attempts over about three hours, then dead letter; auto-pause after 24 hours of continuous failure.
