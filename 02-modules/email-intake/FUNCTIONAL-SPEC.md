# Functional Spec: Email Intake & Outbound

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Client Portal](../client-portal/FUNCTIONAL-SPEC.md), [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md), [Integration Patterns](../../01-architecture/INTEGRATION-PATTERNS.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md)
**Requirements covered:** EM-01, EM-02, EM-03, EM-04, EM-05, EM-06, EM-07, EM-08, EM-09 (nice to have, delivered through Axel)
**Repos affected:** `backend/src/worker`, `backend`, `frontend`, `backend/src/domain`, `backend/src/db`, `infra`

---

## 1. Problem

Most client requests to XMS arrive by email, and most client replies to a ticket arrive by email. ServiceNow handles this today with its inbound actions and notification engine; when it goes, XMS needs its own answer to five things that are hard to get right:

1. **Keeping the addresses clients already know.** Every account has a support address printed in runbooks and saved in contacts. Those addresses must keep working on day one.
2. **Recognising a reply as a reply.** A client answering a notification must land on the existing ticket as a comment, not create a duplicate. Mail clients mangle subjects, so matching cannot depend on the subject line.
3. **Readable threads.** Signatures, legal disclaimers and twelve levels of quoted history turn a ticket conversation into noise. The comment must contain what the person wrote, with inline screenshots preserved.
4. **Never looping with a client mail system.** An auto-reply answering our notification, which we answer with another notification, is a severity-1 event with a client. Detection must be automatic, suppression must be immediate, and the operator must be alarmed.
5. **Not letting strangers create work.** Mail from an unknown sender cannot become a ticket on a client's contract without a person looking at it.

Outbound is the other half: notifications must thread correctly in the client's mail client, carry the account's branding, and be signed so they are not spam-foldered.

## 2. Current state (what exists today)

- **Nothing inbound exists in AIX.** Verified 2026-09-04: no SES receipt rules, no IMAP, no MIME parsing in app-api, workers or the studio. The XMS POC reserved `email` in its ticket `source` vocabulary (`web-ui/components/aix-v3/xms/vocab.ts`) and deliberately made email intake the last planned phase because it is the hardest single feature.
- **Outbound in AIX is a fire-and-forget Lambda** (`app-api/src/api/v1/email/email.service.ts`) with templates outside the repos and a personal Gmail address as the default sender. XMS does not copy it; templates live in the XMS repo and are versioned and tested.
- **The studio XMS module's `notify.py`** shows the one discipline worth keeping: notification producers never let a failure propagate into the ticket mutation that triggered them, and comment bodies never leave the ticketing domain in a notification payload.
- **AIX notification design** (`app-api/src/api/v3/notifications`) supplies the in-app side: recipient as identity key, collapse keys, mute-not-delete subscriptions. In-app notifications are owned by [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md); this module owns their email delivery.

## 3. Goals

1. **Every existing client address keeps working.** An account can have any number of inbound aliases, and a message to any of them lands on that account (EM-01).
2. **Replies always land on the right ticket.** Header-based matching plus a token in our own addresses makes a reply-to-update reliable even when the subject is rewritten (EM-02, EM-03).
3. **Comments read like what the person typed.** Signatures and quoted history are stripped, attachments are on the ticket, inline images stay in place (EM-04, EM-05).
4. **Loops cannot happen twice.** Auto-responders are suppressed, a detected loop disables the alias and pages the operator within a minute (EM-06).
5. **Unknown senders wait for a human.** A quarantine queue in the standard list grammar, with three decisions and an audit trail (EM-07).
6. **Outbound mail looks like the account's mail and threads correctly.** Per-account sender identity, branding and DKIM; every notification carries the headers that make the next reply match (EM-08).
7. **Email is a first-class ticket source.** Tickets created by email are indistinguishable from portal tickets in SLA, audit and reporting except for their `source`.

## 4. Non-goals / out of scope

- **Reading a shared mailbox over IMAP or Graph.** Intake is by forwarding or MX to the XMS inbound domain. Accounts that cannot change MX forward their existing address to the alias. Revisit only if a client refuses forwarding.
- **Email as a chat channel for agents.** Consultants reply from XMS Web; a consultant's email reply to a notification is treated like any inbound message from a known internal sender (appended as a public comment) but is not the intended workflow.
- **Rich HTML composition inside XMS.** Outbound bodies are template-driven plus the comment text; no WYSIWYG editor in Phases 1 to 3.
- **Marketing or bulk mail.** One-to-one and small distribution lists only (report packs go to a distribution list, but as individual messages).
- **Slack or Teams intake.** INT-04 is a Phase 4 item in [Platform Integrations](../integrations/FUNCTIONAL-SPEC.md).
- **Priority detection from content in Phases 1 to 3** (EM-09). It arrives as an Axel suggestion through [Axel AI Functionality](../ai-functionality/FUNCTIONAL-SPEC.md) in Phase 4, human-confirmed like every other suggestion.

## 5. User-facing behavior

### 5.1 Vocabulary

| Set | Values | Notes |
|---|---|---|
| Inbound disposition | created, appended, quarantined, suppressed, rejected | What happened to a received message; shown on the message row and in the ticket audit |
| Suppression reason | auto_submitted, auto_response_header, bulk_precedence, own_message_id_in_references, sender_rate, subject_burst, bounce, complaint, alias_disabled | Why a message was not processed; each has a short human explanation |
| Sender resolution | known_contact, known_internal, portal_user, unknown | Drives quarantine |
| Alias state | active, disabled_by_admin, disabled_by_loop_guard | A loop-guard disable requires an admin to re-enable |
| Quarantine decision | create_contact_and_ticket, create_ticket_once, discard, mark_spam | `create_contact_and_ticket` adds the sender to the account's contacts so later mail flows straight through |
| Outbound kind | ticket_created, ticket_comment, ticket_state, ticket_assigned, sla_warning, csat_invite, report_pack, portal_invite, quarantine_digest | The template catalog; each kind lists the fields it may render |
| Delivery state | queued, sent, delivered, bounced, complained, failed | From SES events |

### 5.2 Addresses and aliases

- Each environment has one inbound domain, for example `support.xms.<domain>`. Every account gets a canonical address `<account key>@support.xms.<domain>`.
- An account administrator adds **aliases**: any address the account already uses (for example `onestream-support@client.com`, which the client forwards). An alias is verified by sending a token to it and seeing it arrive.
- Outbound mail from an account is sent **from** the account's chosen sender identity (a XMS-owned address on the inbound domain by default, or a client-owned domain the client has authorised with DKIM records). Replies come back to a per-ticket address of the form `<account key>+<ticket token>@support.xms.<domain>` so the token is a second matching key.
- The alias list, sender identity and DKIM status live on the account record's **Email** tab. A sender identity that is not yet DKIM-verified shows an amber "unverified: mail will send from the default identity" notice.

### 5.3 Inbound processing (what a consultant sees)

A message that becomes a new ticket:

- Ticket type defaults from the account's **email intake rule** (default Incident; an alias can override, for example an alias named `changes@` defaults to Change).
- Requester is the resolved contact; CC recipients that are known contacts become watchers.
- The comment body is the stripped message text; inline images appear where they were; attachments show on the ticket with a "scan pending" badge until the virus scan completes.
- The ticket audit shows "Created from email" with the sender, the alias it arrived on, and a link to the original message (raw view, internal only).
- SLA clocks start at the received time (the SES receipt time), not at processing time, so a worker backlog never shortens a clock.

A message that appends to an existing ticket:

- The comment is public, authored by the resolved contact, with a small "via email" chip.
- If the ticket is Resolved or Closed, a reply within the account's reopen window reopens it (per the ticket type's state machine); after the window, a new ticket is created linked as "related" to the old one, and the comment says so.
- A reply from an internal user appends as a public comment; internal users are told in the notification footer that email replies are public.

### 5.4 Quarantine queue

- Reached from the sidebar under Intake. Standard list grammar: columns Received, Sender, Alias (account), Subject, Reason (unknown sender, suspicious content, scan quarantined), Age. Sorted oldest first. Count badge on the sidebar item.
- Opening a row shows the stripped body, the attachment list (unscanned attachments are not downloadable), and the four decisions. Every decision writes an audit event with the reviewer.
- "Create contact and ticket" pre-fills the new ticket form in the standard full-screen record grammar with the message content.
- Empty state: "Nothing waiting for review."
- Items older than 14 days are auto-discarded with a digest email to the account's operator group (configurable).

### 5.5 Loop protection and suppression

- Every message gets a loop score before any ticket write. Signals: auto-submitted headers, auto-response suppression headers, bulk or list precedence, our own outbound message id appearing in the References chain more than once, more than N messages from one sender to one alias in a window, and identical-subject bursts.
- **Suppressed** messages are stored, shown in the account's Email log with their reason, and never create a comment or a ticket. Nobody is notified for a suppressed message except in the daily digest.
- **Loop detected** (score above the hard threshold, or more than a configured number of suppressions from one sender in ten minutes): the alias moves to `disabled_by_loop_guard`, outbound notifications to that sender pause, an operations alarm fires, and the account owner sees a red banner on the account record. An administrator re-enables the alias after fixing the cause. This is treated as a severity-1 operational event per the workbook.
- Out-of-office replies are suppressed silently; the ticket shows nothing.

### 5.6 Outbound notifications

- Notification kinds and their audience are configured per account (for example, the client sees `ticket_created`, `ticket_comment` for public comments, `ticket_state` for client-visible states, `csat_invite`; internal users see everything they watch).
- Every message carries `In-Reply-To` and `References` pointing at the ticket's root message so mail clients thread the whole ticket; the subject is `[CS0001234] <title>` and stays stable for the life of the ticket.
- Branding: the account's logo and accent colour in the header band, the operator's footer, a plain-text alternative always included.
- Templates render only client-visible fields; a work note cannot be referenced by any template, by construction.
- Each ticket record has an **Email** tab: every outbound message with recipient, kind, delivery state and a rendered preview; every inbound message with disposition and a link to the raw message (internal only).
- Bounces mark the contact's address as bouncing; complaints suppress the address until an administrator clears it. Both appear on the contact record.

### 5.7 Edge cases

- A message to an alias of an account whose portal is disabled still creates tickets; email is independent of the portal.
- A message with only an attachment and no body creates a ticket titled from the subject with the body "See attachment".
- Messages over the size limit (25 MB total by default) are rejected with a bounce that explains the limit; the rejection is logged.
- Encrypted or signed mail (S/MIME) is stored raw and quarantined with reason "unsupported content".
- Two messages with the same Message-ID are processed once (the second is recorded as a duplicate delivery).

## 6. Rollout

1. **Phase 1 (Foundations):** inbound domain, SES receipt rules, raw storage, one canonical alias per account, outbound sender identities with DKIM, template engine with the `ticket_created` and `ticket_comment` kinds, bounce and complaint handling, threading headers. Depends on the account model and the ticket service (EM-01, EM-08). Exit: a message to the seed account's alias creates a ticket in dev and the notification threads in a real mail client.
2. **Phase 2 (Focused pilot):** thread matching, reply-to-update, stripping parser with the corpus, attachment and inline image extraction with scan gating, loop protection and suppression, quarantine queue, alias verification, Email tabs on ticket and account, daily digest (EM-02 to EM-07). Depends on the attachment pipeline in Ticket Management.
3. **Phase 3 (Operational replacement):** client-owned sender domains, per-account notification matrix, report pack and CSAT delivery, suppression list administration, migration of existing ServiceNow inbound addresses as aliases with a forwarding cutover checklist.
4. **Phase 4:** priority suggestion from content (EM-09) through Axel, Slack and Teams intake in Platform Integrations.

## 7. Success criteria

- A client replies to a notification from Outlook, Gmail and Apple Mail with the subject edited; all three land as comments on the original ticket and none creates a new ticket.
- The corpus of 40 sample messages is stripped so that each comment contains the new text and not the signature, disclaimer or quoted history, verified by exact expected output.
- An out-of-office auto-reply to a notification produces no comment, no notification and one suppressed row.
- A simulated loop (a stand-in mailbox that auto-replies to every message) is stopped within one minute: the alias is disabled, an alarm fires, and no more than five messages were exchanged.
- A message from an unknown sender never creates a ticket without a reviewer decision, and the decision is in the audit trail.
- Notifications for one ticket thread as one conversation in the three mail clients, show the account's logo, and pass DKIM and SPF checks.
- An attachment with the EICAR test string arrives in quarantine, is never downloadable, and the ticket shows a placeholder.
- SLA clocks on an email-created ticket start at the SES receipt time even when the worker was paused for ten minutes.

## 8. Open questions

- **Who owns the client-side forwarding change?** Default assumption: the XMS account owner drives it with a per-account cutover checklist; XMS provides the alias and the verification token.
- **Reopen window after Resolved.** Default assumption: 5 business days on the account calendar, per ticket type, configurable per account.
- **Should internal consultants be able to reply to tickets by email at all?** Default assumption: yes, appended as a public comment, with a footer warning; can be turned off per operator group.
- **Digest cadence and recipients.** Default assumption: daily at 08:00 account time to the account's operator group.
- **Client-owned sender domains in the pilot.** Default assumption: no; pilot sends from the XMS domain; client domains are a Phase 3 onboarding step.
