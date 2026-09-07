# Functional Spec: Axel AI Functionality

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md) (the harness contract), [Security & Tenancy §8](../../01-architecture/SECURITY-AND-TENANCY.md), [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md) (similar solutions, article drafts, auto-resolution AI-17), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md) (narrative host), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md) (time entries, burn), [Email Intake & Outbound](../email-intake/FUNCTIONAL-SPEC.md) (EM-09)
**Requirements covered:** AI-01, AI-02, AI-03, AI-04, AI-05, AI-06, AI-08, AI-09, AI-10, AI-11, AI-12, AI-13, AI-14 (Must Have); AI-15, AI-16, AI-18, AI-19, AI-20, EM-09 (Nice to Have). AI-07 (similar tickets and KB suggestion) and AI-17 (auto-resolution) are owned by the knowledge base module and surfaced through the same suggestion mechanics described here
**Repos affected:** `backend`, `backend/src/worker`, `frontend`, `aix-mcp/app/modules/xms_mcp`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`); `os-aixelerator-studio` and `aix-mcp` for the harness changes listed in [AI Integration §8](../../01-architecture/AI-INTEGRATION.md)

---

## 1. Problem

A support desk spends a large share of its hours on work that is not solving anything: reading a ticket to decide what it is and how urgent, checking whether it was already raised, re-reading a forty-message thread before a handover, writing the same reply for the twentieth time, turning the week's numbers into a talk track, and reconstructing on Friday what was done on Tuesday. ServiceNow gives XMS none of this, and the practice has no AI in its support workflow at all.

The workbook asks for assistance on every one of those steps (AI-01 to AI-06, AI-14) under strict conditions that make this different from bolting a chatbot on: nothing takes effect without a human unless a client has explicitly opted in (AI-08), low-confidence output is withheld rather than shown (AI-09), every AI act is in the audit trail and distinguishable from a person's (AI-10), a client can switch AI off and that switch must be enforceable at the data layer (AI-11), no client data trains a model and residency terms hold (AI-12), and every accept or reject is captured so accuracy can be measured (AI-13). The nice-to-have rows (AI-15 to AI-20) all extend the same machinery once accuracy has been measured.

The distinct cases the module must handle:

1. **At intake**: classify, prioritise, detect duplicates, and for email, suggest priority from content.
2. **While working**: summarise a thread, draft a reply, surface similar solutions (knowledge module), later estimate effort and flag sentiment.
3. **At the end of the day and week**: nudge on unlogged time and tidy descriptions; write the WSR narrative.
4. **In the background**: watch consumption for anomalies, later suggest allocations.
5. **Administratively**: switch AI on or off per client, set opt-ins and thresholds, and see how accurate it is.

## 2. Current state (what exists today)

- **The harness** (`os-aixelerator-studio`) provides everything needed to run agents: a published external-caller contract (`app/modules/ai_execution/XT_AXEL_API.md`), SSE chat, headless runs, inline agent definitions (the `xt_axel` skeleton), an MCP client, Bedrock Sonnet 5 and Haiku 4.5, prompt caching, Phoenix tracing and a secrets guard. Verified 2026-09-04 and fixed as the contract in [AI Integration](../../01-architecture/AI-INTEGRATION.md).
- **No XMS agent exists.** The XMS POC has no toolbox, no agent and no AI surface (studio research report §10: "a pure CRUD plus SLA API with no Axel surface").
- **No per-tenant AI switch exists in the harness** (no `ai_disabled`, no tenant model override). The switch must be a XMS property.
- **No suggestion, feedback or accuracy model exists anywhere** in AIX; the closest thing is the agent memory approval lifecycle (`agent_memories.status` pending/active), which is a different concept.
- **The Axel panel pattern in web-ui** (`AxelSplitPanel`, `DiscoveryChatWithPanel`, `useDiscoveryChat`) is coupled to the AIX opportunity model and eight RTK slices; XMS builds its own small panel over the streaming rules documented in the web-ui research report §4.

## 3. Goals

1. **Every suggestion is a proposal, never an action.** A consultant sees what Axel thinks, with confidence and a reason, and accepts, edits or rejects it in one click; the record changes only then.
2. **Intake gets faster without getting sloppier.** Category, priority and duplicate suggestions appear within seconds of a ticket arriving, and acceptance is measured.
3. **Handover and replies take minutes, not half-hours.** Any ticket can be summarised on demand; any public reply can start from a draft grounded in the thread and the knowledge base.
4. **The weekly narrative writes itself, and a person signs it.** The WSR narrative is generated from the pack's frozen numbers and reviewed before a client sees it.
5. **Nobody forgets their hours.** The time assistant tells each consultant where their unlogged time is and helps phrase the entries.
6. **Clients decide.** A client's AI switch, opt-ins, thresholds and residency requirement are enforced before any data leaves XMS, and the audit trail shows every AI touch.
7. **Accuracy is a number.** Acceptance rate per capability per account is visible to administrators and gates any move toward automation.

## 4. Non-goals / out of scope

- **Autonomous triage or resolution in Phases 1 to 3** (AI-20, AI-17). Auto-apply per capability is a Phase 4 account opt-in gated by the measurement plan (§5.11).
- **A general chat assistant over all of XMS.** The Axel panel is bound to the ticket, the queue or the report in view; it is not a free-form product-wide chatbot in the pilot.
- **Training or fine-tuning on client data.** Prohibited by AI-12; prompts are versioned constants and improvement happens through prompt and threshold changes, never model training.
- **AI in the client portal.** Portal users get knowledge base search (which uses embeddings) but no suggestions, drafts or summaries in Phases 1 to 3.
- **Sentiment on internal work notes.** Sentiment and escalation risk (AI-18) read public comments and email only.
- **Model selection by users.** Models are chosen per agent by the operator; accounts may restrict AI but not pick models.
- **Building a vector database service.** Embeddings live in XMS PostgreSQL and are owned by the knowledge base module.

## 5. User-facing behavior

### 5.1 Vocabulary

| Term | Meaning |
|---|---|
| Suggestion | One proposal from Axel about one record: a classification, a priority, a duplicate, a summary, a draft, a narrative, a time entry, an anomaly |
| Confidence | A 0 to 1 score returned with structured suggestions; compared against the account threshold for that capability |
| Withheld | A suggestion that fell below threshold or was blocked by a switch; stored for measurement, never shown as a suggestion, routed to a human queue where the workbook asks |
| Decision | The human response: accept, edit then accept, reject, or let expire |
| AI action | The audit event written when a decision is applied; actor kind AI, with the confirming person |
| Capability | A named use of Axel with its own switch, threshold and agent |
| Opt-in | A per-account, per-capability permission to apply suggestions automatically (Phase 4 only) |

### 5.2 Capability catalog

| Capability | Trigger | Inputs | Output | Surfaces on | Default threshold | Phase |
|---|---|---|---|---|---|---|
| Classify (AI-01) | Ticket created by any source; description edited before first assignment | Title, description, requester, account context, CI list, category taxonomy | Category, ticket type, CI tags, each with confidence | Intake chips on the ticket record and queue row | 0.70 | 2 |
| Prioritise (AI-01, EM-09) | Same as classify | Same plus impact and urgency matrix, email headers for EM-09 | Impact, urgency, derived priority, reason | Intake chips | 0.75 | 2 (EM-09 in 4) |
| Duplicate (AI-02) | Ticket created; title or description edited within first hour | New ticket text, open and recently resolved tickets of the account | Up to three candidates with similarity and a merge proposal | Intake banner "Possible duplicate of CS0001201" | 0.80 | 2 |
| Summarise (AI-03) | "Summarise" button; automatic on reassignment to a new person or group | Thread (comments, work notes for internal readers, events, time) | Summary with sections: situation, done so far, waiting on, next step, risks | Ticket record summary panel; handover notification | none (always shown, marked AI) | 2 |
| Similar solutions (AI-07, knowledge module) | Ticket opened by an assignee; description edited | Ticket text, embeddings of articles and resolved tickets | Ranked articles and tickets with reason | Related rail "Similar solutions" | 0.60 | 2 |
| Draft reply (AI-04) | "Draft reply" in the public composer | Thread, requester, tone setting, linked solution article | Draft text in the composer with citations | Composer, never sent automatically | none (always a draft) | 3 |
| WSR narrative (AI-05) | Report pack generation | Frozen measures, notable tickets, previous narrative | Narrative text with a headline sentence per section | Report review screen | none (always reviewed) | 3 |
| Time assistant (AI-06) | Daily digest at 16:00 person-local; inline when logging time | Calendar, tickets touched, events by the person, existing entries | Unlogged blocks with proposed ticket, minutes and a normalised description | Daily nudge and inline suggestion in the time widget | 0.65 for proposed entries; nudge itself unconditional | 3 |
| Burn anomaly (AI-14) | Nightly per contract | Consumption series, contract terms, period position, historical run rate | Anomaly flag with direction, magnitude, likely cause | Portfolio row badge, account owner notification | 0.70 | 3 |
| NL query (AI-15) | Question typed in the operations dashboard | Question, measure catalog, grants | A table or chart spec plus the query it ran | Dashboard answer panel | none | 4 |
| Allocation suggestion (AI-16) | Assignment picker opened | Skills, capacity, account familiarity, current load | Ranked assignees with reasons | Assignment picker | 0.60 | 4 |
| Sentiment and escalation risk (AI-18) | New public comment or email | Thread public text | Risk level and trend | Ticket badge, dispatcher rail | 0.75 | 4 |
| Effort estimate (AI-19) | Ticket classified | Similar closed tickets and their hours | Effort range with comparables | Ticket record | 0.60 | 4 |
| Auto-apply (AI-20, AI-17) | Per-capability opt-in | The suggestion | The applied change, audited as auto-applied by policy | Audit trail, admin dashboard | account-set, minimum 0.90 | 4 |

### 5.3 Suggestion lifecycle

| State | Meaning | Who moves it |
|---|---|---|
| Offered | Shown to a person with confidence at or above threshold | Axel via the adapter |
| Withheld | Stored but not shown: below threshold, switch off, capability off, redaction refusal, residency, or harness unavailable; carries the reason | Adapter |
| Accepted | Applied as proposed | Person |
| Edited and accepted | Applied with changes; the diff is kept for measurement | Person |
| Rejected | Declined, optionally with a reason from a short list (wrong, unnecessary, already done, unclear) | Person |
| Expired | Not acted on within the capability's life (intake chips expire when the ticket is assigned; drafts when the composer closes without sending) | System |
| Auto-applied | Applied by policy under a Phase 4 opt-in | System, audited as AI with the policy version |

Every accepted, edited or auto-applied suggestion produces an audit event with actor kind AI, the suggestion id, the confirming person, model, prompt version and confidence. Rejected and withheld suggestions produce no change to the record and are visible in the accuracy dashboard only.

### 5.4 Intake surfaces (AI-01, AI-02)

When a ticket arrives, the record shows a thin "Axel suggests" strip under the properties: chips for Category, Type, Impact, Urgency, derived Priority, and CI tags, each with a small confidence indicator and a reason on hover. Accept applies one chip; "Accept all" applies every chip at or above threshold; editing a field directly counts as edit-and-accept if the value differs. A duplicate banner shows the top candidate with a side-by-side preview and two actions: "Mark as duplicate of" (links the tickets and moves the new one to the duplicate state through the normal transition) or "Not a duplicate" (rejects all candidates). The queue row shows a faint "AI" marker while suggestions are pending. If the account's AI is off, the strip and the banner do not exist.

### 5.5 Working surfaces (AI-03, AI-04, AI-07)

- **Summarise**: a button on the record and an automatic summary on reassignment. The summary panel is marked "Written by Axel, 14:02, from 37 messages" and can be regenerated; it is never stored as a comment. Handover notifications include it.
- **Draft reply**: in the public composer, "Draft reply" fills the box with a draft that cites the solution article it used, in the account's tone setting (formal, plain). The person edits and sends; sending records the decision as edited-and-accepted or accepted. Nothing sends without a click.
- **Similar solutions**: the related rail lists articles and resolved tickets with a one-line reason ("same error text on the same CI type"). Opening one is neutral; "This solved it" links it as the resolution (knowledge module) and counts as accepted.

### 5.6 Time assistant (AI-06)

At 16:00 in each consultant's time zone, a nudge (in-app notification and optional email) says, for example, "You have 6 unlogged hours on Tuesday across CS0001210 and CS0001188". Opening it shows proposed entries: ticket, minutes, activity type, a normalised description built from the person's own comments and events. Each row accepts, edits or dismisses; accepted rows become time entries attributed to the person with an AI audit link. Inline, when someone logs time with a terse description, a "Tidy" action rewrites it into the house form ("Analysed consolidation failure on FCCS PROD; identified missing mapping; documented workaround") for approval. The assistant never creates a time entry on its own.

### 5.7 Narrative (AI-05)

The report pack review screen shows the narrative Axel wrote from the frozen numbers, with a headline sentence per section. The reviewer edits and approves ([Dashboards & Report Packs §5.8](../dashboard-and-reporting/FUNCTIONAL-SPEC.md)). If AI is off for the account, the pack uses the templated narrative and the review screen says so.

### 5.8 Burn anomaly (AI-14)

A nightly job flags contracts tracking materially above or below the expected run rate for their period position, with the likely cause (a P1 week, a change window, a drop in requests). The portfolio row carries a badge and the account owner gets a notification with the reasoning. Dismissing the badge records a rejection; acknowledging records acceptance. The anomaly never changes any figure.

### 5.9 The Axel panel

Any ticket, queue or report has an "Ask Axel" action that opens a docked panel on the right (resizable, remembers its width). The panel is bound to what is in view: on a ticket it can summarise, draft, find similar solutions and answer questions about the thread; on a queue it can answer "which of these are at risk of breaching before 17:00"; on a report it can explain a number. Structured results appear as suggestion cards inside the panel with the same accept and reject controls as the record. The panel shows the tools Axel used, can be cancelled mid-turn, keeps its conversation per ticket, and reads "Axel is unavailable" with every human control still working when the harness is down. Portal users never see the panel.

### 5.10 Administration

Per account, under Settings, an "AI" page with: the master switch (off by default for new accounts until the DPA register is completed), the residency requirement (read-only from the account record; if unmet the switch cannot be turned on and the reason is shown), the DPA reference, per-capability toggles, per-capability thresholds with the operator default shown, the redaction profile (standard; strict, which also masks portal user emails), the tone setting for drafts, and in Phase 4 the auto-apply opt-ins with their minimum thresholds and a required written approval reference. Every change is an audit event. Operators see a global AI page with the defaults and the ability to disable a capability everywhere at once (kill switch).

### 5.11 Accuracy dashboard and the measurement plan

An operator page shows, per capability and per account, over a chosen period: offered, accepted, edited, rejected, withheld, expired; acceptance rate (accepted plus edited over offered); edit distance for edited text; rejection reasons; confidence calibration (acceptance rate by confidence decile); latency; and harness cost per account. Threshold tuning is done here: an administrator can see what the acceptance rate would have been at a different threshold from the stored confidences.

The plan that gates AI-20 and AI-17: a capability may be offered for auto-apply to an account only when, for that account, over the trailing 8 weeks with at least 200 offered suggestions, the acceptance rate (unedited) is at least 95 percent at the proposed threshold, calibration is monotonic, and the account has signed the opt-in. Auto-applied changes remain reversible through the normal record actions and are reviewed weekly in the WSR appendix for that account.

### 5.12 Empty and edge states

- New account with AI off: no AI element renders anywhere for that account; the settings page explains what would appear.
- Harness unavailable: suggestions are withheld with reason `unavailable`; intake proceeds; the accuracy dashboard shows the outage window.
- Ticket with no text (attachment only): classify runs on extracted text if the attachment is clean and text-bearing; otherwise withheld with reason `no_content`.
- Threshold set to 1.0: everything is withheld; the settings page warns.
- A suggestion offered on a ticket that is then merged or cancelled expires.

## 6. Rollout

1. **Phase 1, Foundations:** account AI switch, residency check, audit model for AI actions, the adapter contract agreed with the Axel owners (AI Integration §8 items 1, 5 and 6), the XMS MCP server skeleton with read tools, redaction rules, no user-facing suggestion yet. Depends on Accounts & Administration.
2. **Phase 2, Focused pilot:** classify, prioritise, duplicate, summarise, similar solutions (with the knowledge module), the Axel panel on tickets and queues, feedback capture, the accuracy dashboard basics. Depends on Ticket Management core and the knowledge base embeddings.
3. **Phase 3, Operational replacement:** draft reply, WSR narrative, time assistant, burn anomaly, strict redaction profile, full accuracy dashboard and threshold tuning. Depends on Dashboards & Report Packs, Time & Budget, the harness embeddings and headless routes.
4. **Phase 4, Later releases:** EM-09, NL query, allocation suggestions, sentiment and escalation risk, effort estimates, auto-apply opt-ins under the measurement plan.

## 7. Success criteria

- A ticket created by email for an AI-enabled account shows category, priority and CI chips within 10 seconds; accepting all applies them and the audit trail shows an AI actor with the confirming user and confidence.
- The same email for an account with AI off produces a ticket with no AI element, no suggestion row, no embedding row, and no call to the harness (verified by the adapter's call log being empty for that account).
- A duplicate submitted twice within an hour shows the banner on the second ticket with the first as the top candidate; "Mark as duplicate" links them and moves the second to the duplicate state through the state machine.
- Reassigning a 40-message ticket to a new group produces a summary in the handover notification that names what is being waited on.
- A consultant with two hours unlogged on Tuesday receives the 16:00 nudge naming the tickets; accepting the proposals creates time entries attributed to the consultant with AI audit links.
- Lowering the classify threshold on the accuracy dashboard shows the recomputed acceptance rate from stored confidences without any new harness call.
- A capability that has not met the measurement plan cannot be enabled for auto-apply; the settings page shows which criterion failed.
- Every AI-originated change in the audit trail is filterable with one click ("Show AI actions") and shows model, prompt version and confidence.

## 8. Open questions

- **Threshold defaults per capability.** Default assumption: the values in §5.2, revised after the first four weeks of pilot data.
- **Should summaries include work notes for internal readers?** Default assumption: yes for internal users, never in anything client-visible; the summary panel labels which sources it read.
- **Handover summary automatically or on request?** Default assumption: automatic on reassignment to a different group or a person outside the current group; on request otherwise.
- **Time assistant email opt-out.** Default assumption: in-app always, email per user preference, default on.
- **Anomaly definition.** Default assumption: forecast at period end deviates more than 15 percent from the linear expectation for the period position, sustained for three days.
- **Harness embeddings endpoint timing.** Default assumption: the temporary direct Bedrock Titan exception in ADR-04 is used in Phase 2 and removed in Phase 3.
- **Where the DPA register lives.** Default assumption: fields on the account record maintained by administrators, with the AI switch blocked until the register is complete.
