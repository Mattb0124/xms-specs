# Functional Spec: ServiceNow Sync

**Status:** Draft, Brookfield facts pending (Vini, due 2026-09-25)
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Data Migration & Cutover](../data-migration/FUNCTIONAL-SPEC.md), [Platform Integrations](../integrations/FUNCTIONAL-SPEC.md), [Decision Log](../../00-overview/DECISION-LOG.md) (ADR-06)
**Requirements covered:** SN-01, SN-02, SN-03, SN-04, SN-05, SN-06, SN-07, SN-08, SN-09
**Repos affected:** `backend/src/worker`, `backend`, `frontend`, `backend/src/domain`, `backend/src/db`, `infra`

---

## 1. Problem

Some XMS clients run their own ServiceNow and expect Hackett to work inside it: Brookfield raises cases in its instance, expects Hackett's updates to appear there, and expects Hackett to see its updates. Today that works because Hackett is also on ServiceNow. After the replacement, XMS must keep that relationship alive without asking the client to change anything.

The hard parts are not the HTTP calls. They are: two systems with different state models that must agree on what a ticket is doing; updates that echo back and forth forever if nobody stops them; two parties editing the same field with no rule for who wins; internal work notes that must never cross into the client's public journal; attachments that are too big for one side; and several clients whose instances differ in schema, version and authentication, all running at once. On top of that, the first release must be able to run read-only, both as a safe start and as the position to fall back to when write-back has to be suspended.

## 2. Current state (what exists today)

- **No sync engine exists in AIX** (verified 2026-09-04): no field mapping, state translation, loop prevention, DLQ or replay anywhere in app-api, workers or the studio. The MCP `resolve-session` contract in app-api returns unreachable servers as `skipped` rather than failing, which is the one degradation idea this module keeps.
- **A read-side ServiceNow MCP module exists** in `aix-mcp/app/modules/servicenow_ams_mcp/` with its source on another branch (only compiled files are present on the current checkout). Its client (`snow_client.py`) is the starting point for the read calls; nothing about ongoing sync exists there.
- **The XMS POC** has no external references on tickets beyond a free-text contact; the `source` vocabulary reserved `api`, not `sync`. XMS adds `sync` as a source and an `external_ref` on every ticket (ADR-10).
- **The connector framework** ([Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md)) supplies outbox, inbox, DLQ, replay and kill switch. This module adds only what is ServiceNow-specific.
- **Brookfield facts are unknown**: flows, mappings, auth, volumes, error handling and ownership are an open decision (assessment appendix B, Vini). This spec states its assumptions in §8 and the technical spec so the build can start on the stand-in.

## 3. Goals

1. **A client's ServiceNow and XMS tell the same story.** A case raised in the client instance appears in XMS with the right type, priority and requester; Hackett's public updates appear in the client's case; state changes translate both ways (SN-01, SN-02, SN-05).
2. **Configuration, not code, per instance.** An administrator maps fields and states for a new instance in XMS Web, validates the mapping against sample payloads, and activates it (SN-01, SN-08).
3. **Nothing loops and nothing is silently overwritten.** Every crossing change carries a correlation id and watermark; reflections are dropped; each field has a declared system of record (SN-03, SN-04).
4. **Internal stays internal.** Work notes sync only to work notes, comments only to comments, and a client instance configured for public-only never receives a work note (SN-05).
5. **Attachments travel, within limits.** Files under the size limit sync both ways; larger ones become a link and a note (SN-06).
6. **The operator can see and fix sync problems** without a developer: health per instance, failed messages with their error, one-click replay or discard (SN-07).
7. **Read-only is a first-class mode.** An instance starts in ingest-only, can be promoted to bidirectional, and can be dropped back to ingest-only in one click with nothing lost (SN-09).

## 4. Non-goals / out of scope

- **Historical import.** Loading open and closed history from ServiceNow CSM before cutover is owned by [Data Migration & Cutover](../data-migration/FUNCTIONAL-SPEC.md). This module owns ongoing sync, including the shadow-sync period that migration relies on.
- **Syncing Hackett's own ServiceNow.** Hackett's instance is being decommissioned; it is a migration source, not a sync target.
- **Custom ServiceNow development on the client side.** XMS uses the standard Table API and Attachment API. A Business Rule webhook is optional and improves latency; polling is the baseline so no client change is required.
- **Syncing knowledge articles, CIs or time entries.** Only tickets, their journals and attachments sync in Phases 1 to 3. CI linking and knowledge sharing are Phase 4 candidates.
- **Other ITSM tools** (Jira Service Management, Zendesk). The framework supports them; only ServiceNow is specified.
- **Automatic mapping inference.** Mappings are authored by a person from the instance's schema; Axel may suggest mappings in Phase 4.

## 5. User-facing behavior

### 5.1 Vocabulary

| Set | Values | Notes |
|---|---|---|
| Instance mode | off, ingest_only, bidirectional | `off` stops dispatch and apply; `ingest_only` applies inbound, never sends; `bidirectional` does both |
| Kill switch | armed, tripped | Tripped by an administrator or automatically after a configured error rate; equivalent to `off` without losing the configured mode |
| Sync direction (per field) | in, out, both, none | Declared in the field map |
| System of record (per field) | xms, external, newest, merge | Conflict policy; `newest` only for free-text; `merge` only for journals |
| Sync link state | linked, pending_external, pending_xms, conflict, unlinked | A ticket may be created on either side first |
| Health | healthy, degraded, failing, tripped | Derived from recent runs, backlog and DLQ depth |
| Run outcome | success, retried, dead_lettered, skipped_reflection, skipped_policy | Every attempt is a run |
| Journal kind | comments (public), work_notes (internal) | ServiceNow's names, kept for administrator familiarity |

### 5.2 Onboarding an instance (administrator)

On the account record, the **Integrations** tab lists connector instances. "Add ServiceNow instance" opens a full-screen record in the standard grammar:

1. **Connection**: instance URL, authentication kind (OAuth client credentials, or basic), credential reference (the secret is entered once and stored in the secrets store; the record shows only a name and a "test connection" button), the table to sync (`sn_customerservice_case` for CSM instances, `incident` for ITSM instances, or another table name), polling interval, optional webhook secret.
2. **Field map**: a two-column grid, ServiceNow field on the left and XMS field on the right, with direction, transform (none, lookup table, template) and system of record per row. Required XMS fields are highlighted until mapped. A "load sample" button pulls five recent records from the instance so the administrator can see real values while mapping.
3. **State map**: one grid per ticket type: ServiceNow state values to XMS states inbound, and XMS states to ServiceNow values outbound. Unmapped values are listed in red.
4. **Journals and attachments**: which journal receives XMS public comments (default `comments`), whether work notes sync at all (default no), attachment size limit (default 10 MB), and what to do above the limit (link or skip).
5. **Validate**: runs the mapping against the sample records and the instance's own metadata (`sys_dictionary`), reporting every unmapped required field and every unmapped state. Validation must pass before activation.
6. **Activate** in `ingest_only`. The instance starts polling from a chosen watermark (default: now, or a date for a shadow-sync backfill).

Every step is an audit event. Mapping versions are kept; the active version is shown, and an older version can be restored.

### 5.3 What consultants see

- A synced ticket shows a **Linked record** card in the related-info rail: instance name, the external number (`CS0012345` on the client side), last inbound and last outbound time, and a link to open the record in the client instance. Sync state and any conflict show as a pill.
- Comments that arrived from the instance carry a "via ServiceNow" chip and the client-side author name. Work notes that arrived through a work-note sync carry the same chip and stay internal.
- A conflict (both sides changed a field whose policy is `xms` or `external` in the same window) is shown on the ticket as a yellow banner: the field, both values, which one was kept by policy, and a "review" link to the sync run. The consultant cannot resolve a conflict by hand in Phases 1 to 3; policy resolves it and the banner records it.
- When an instance is `ingest_only`, the ticket rail says "Updates are not sent to ServiceNow" so nobody assumes the client saw a comment.
- Ticket creation from the client side follows the account's intake rule for type and the state map for state; the requester is matched to a contact by email or created as a contact.

### 5.4 Sync health screen (operator)

Reached from Admin, Integrations. One row per instance across all accounts the user can see: account, instance, mode, health, last success, inbound backlog, outbound backlog, dead letters, error rate (last hour), and a kill-switch control. Clicking a row opens the instance record with:

- **Runs**: the standard list, filterable by outcome and time, each run showing direction, the ticket, the external id, the attempt, the outcome and the error text.
- **Dead letters**: the retained failures with payload preview, error, first and last failure, attempt count; actions "Replay" (re-enqueue with the original payload) and "Discard" (requires a reason). Bulk replay for a selected set after a fix.
- **Watermarks**: the current inbound polling watermark and the option to rewind it (for example after a client outage) with a preview of how many records that will re-fetch.

### 5.5 Kill switch and fallback

- Tripping the switch stops dispatch to the instance immediately and pauses inbound apply; queued outbound work stays in the queue. Re-arming resumes both. Both actions are audit events and notify the account owner.
- Dropping from `bidirectional` to `ingest_only` is the documented fallback when write-back must be suspended (SN-09): outbound stops, inbound continues, and the ticket rail tells consultants.
- Automatic trip when the instance error rate exceeds the configured threshold (default 50 percent of attempts over 15 minutes with at least 10 attempts); the alarm fires and the health shows `tripped`.

### 5.6 Multiple instances

Each instance is independent: its own credentials, table, maps, mode, watermark, queue consumer and health. One account may have more than one instance (a CSM and an ITSM instance, or dev and prod during onboarding). The same XMS ticket can be linked to at most one record per instance.

### 5.7 Edge cases

- A record deleted on the client side: XMS keeps the ticket, marks the link `unlinked`, and adds a work note.
- A state on the client side with no mapping: the inbound update applies every other field and leaves the XMS state unchanged, logged as `skipped_policy` with the unmapped value; the health screen counts it.
- A XMS transition that the client's state model cannot represent (for example Pending client with a reason): the state map sends the nearest mapped value and the reason goes to the journal as a comment.
- An attachment already present on the other side (same name and size) is not sent twice.
- A comment written in XMS while the instance is tripped is sent when the switch is re-armed, in order.

## 6. Rollout

1. **Phase 2 (Focused pilot):** the connector on the framework, instance onboarding in `ingest_only` for one instance (the local stand-in in dev, a Brookfield non-production instance if available), field and state maps with validation, inbound case and journal apply, sync links on tickets, the health screen with runs and dead letters (SN-01, SN-02, SN-07, SN-08 partial, SN-09). Depends on the connector framework and the ticket service.
2. **Phase 3 (Operational replacement):** bidirectional mode with loop prevention and conflict policy, comment and work-note sync outbound, attachment sync both ways, webhook receiver, automatic trip, multiple production instances, the shadow-sync period with Data Migration, Brookfield production go-live after ownership rules are agreed (SN-03 to SN-06, SN-08).
3. **Phase 4:** Axel-suggested mappings, CI and knowledge sync, additional ITSM connectors on the same framework.

## 7. Success criteria

- An administrator onboards the stand-in instance from the XMS Web screens alone, validation catches an unmapped required field and an unmapped state, and activation succeeds only after both are fixed.
- A case created in the instance appears in XMS within one polling interval with the mapped type, priority, requester and state, and a `via ServiceNow` comment for its description.
- A public comment added in XMS in `bidirectional` mode appears in the instance's `comments` journal once; the instance's echo of that journal entry produces no second comment in XMS.
- A work note added in XMS never appears in the instance when work-note sync is off, and appears only in `work_notes` when it is on.
- Both sides change the priority in the same polling window; the field's policy decides, the losing value is recorded, the ticket shows the conflict banner, and the run log names both values.
- A 15 MB attachment on the instance becomes a link and a note in XMS when the limit is 10 MB; a 2 MB attachment is copied once.
- With the stand-in returning 500 for five minutes, no message is lost, the instance shows `failing`, the switch trips at the threshold, and after recovery a bulk replay drains the dead letters in order.
- Dropping to `ingest_only` stops outbound within one dispatch cycle and inbound keeps flowing; the ticket rail shows the notice.
- Two instances with different tables and auth kinds run concurrently against two stand-in profiles without cross-talk in runs, links or health.

## 8. Open questions

- **Brookfield table and flows.** Default assumption: CSM `sn_customerservice_case`, Hackett assigned as a vendor account, inbound on case creation and journal updates, outbound on public comments and state changes.
- **Authentication.** Default assumption: OAuth 2.0 client credentials issued by the client; basic auth supported for non-production instances.
- **Who owns which field.** Default assumption: the client instance is system of record for requester, short description and client-side priority at creation; XMS is system of record for state, assignment and everything after intake; journals merge.
- **Webhook availability.** Default assumption: none in the pilot; polling every 60 seconds; a Business Rule webhook is offered as an optimisation in Phase 3.
- **Volume.** Default assumption: under 200 case updates per day per instance.
- **Does the client see Hackett's ticket key?** Default assumption: yes, written to a mapped reference field (`correlation_id` or a `u_` custom field) so both sides can quote each other.
- **Shadow-sync duration before cutover.** Default assumption: two weeks in `ingest_only`, agreed with Data Migration.
