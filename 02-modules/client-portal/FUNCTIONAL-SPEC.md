# Functional Spec: Client Portal

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-04
**Related:** [Technical Spec](./TECHNICAL-SPEC.md), [Product Vision](../../00-overview/PRODUCT-VISION.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Design System](../../01-architecture/DESIGN-SYSTEM.md), [Ticket Management](../ticket-management/FUNCTIONAL-SPEC.md), [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md), [Time, Contracts & Budget](../time-and-budget/FUNCTIONAL-SPEC.md), [Email Intake & Outbound](../email-intake/FUNCTIONAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md), [Accounts & Administration](../accounts-and-administration/FUNCTIONAL-SPEC.md)
**Requirements covered:** CP-01, CP-02, CP-03, CP-04, CP-05, CP-06, CP-07
**Repos affected:** `frontend`, `backend`, `backend/src/worker`, `backend/src/domain`, `backend/src/db`, `backend/src/contracts`

---

## 1. Problem

Clients of the DMS practice today reach the team by email and, for Brookfield, through their own ServiceNow. They cannot see the status of what they asked for without asking again, they cannot see how many contracted hours are left, they receive no structured way to say whether the work was good, and they cannot help themselves with a documented fix. The operator, in turn, has no controlled surface to give a client: every visibility question becomes an email, and every "who at the client is allowed to ask for what" is tribal knowledge.

The portal is the client-facing half of the product. It must cover:

1. **Getting in.** Client users sign in with their own company identity (SAML or OIDC), or with a local account when their company has no federation (CP-01).
2. **Seeing only their own organisation.** Enforced on the server and proven by automated tests, not by hiding links (CP-02).
3. **Asking for something.** A request form whose fields depend on the request type, with required fields enforced (CP-03).
4. **Following it.** Status, the public conversation, and public updates only, never internal work notes (CP-04).
5. **Attaching evidence.** Screenshots and logs with the same scanning and limits as internal uploads (CP-05).
6. **Seeing consumption when allowed.** A per-account switch decides whether hours and budget appear (CP-06).
7. **Saying how it went.** A survey on ticket close and a relationship survey every quarter, both feeding reporting (CP-07).
8. **Finding a fix first.** The knowledge base, scoped to what the account may see (CP-08, owned by [Solution Knowledge Base](../knowledge-base/FUNCTIONAL-SPEC.md)).

## 2. Current state (what exists today)

- **XMS proof of concept:** internal only. `NewTicketPage.tsx` has a "Caller" free-text field and `vocab.ts` reserves `source: portal`, but there is no external user, no external route, and `client_contact` is a string on the ticket. The POC audit called the portal "the biggest cut and the most likely fast-follow".
- **AIX external access:** nothing reusable. AIX uses Clerk only for internal staff (verified 2026-09-04 in `app-api/src/authtentication/*`; no organisation creation, invitation or SSO-connection code exists). The only external-user mechanism is a hand-rolled HMAC token for discovery share links (`app-api/src/services/jwt/simple-jwt.service.ts`) which this product does not copy (ADR-03).
- **Studio `xms_ticketing`:** comment `visibility` is a column on one table. This product uses two tables so a portal query cannot return a work note by mistake ([Domain Model §4](../../01-architecture/DOMAIN-MODEL.md)).
- **Not built anywhere:** portal identity, dynamic forms, consumption view, CSAT, portal notifications.

## 3. Goals

1. **Clients sign in with their own identity.** Federation per account, with a supported fallback for accounts that have none, and an onboarding flow the account can run itself.
2. **A client sees their organisation, completely and only.** Tickets, threads, attachments, consumption (if allowed), CSAT, articles: all theirs, nothing else, enforced below the application.
3. **Submitting a request is guided and short.** Solutions first, then a form shaped by the request type, with the required fields the practice actually needs to start work.
4. **Following a ticket needs no email.** Status, public comments, attachments and notifications are in one place; replying by email still works and lands in the same thread.
5. **Consumption is transparent when the contract says so.** Hours used, hours left, forecast and the period end, matching the internal numbers to the minute.
6. **Feedback is structured.** CSAT on close and quarterly, low friction, visible in the client's dashboard and report pack.
7. **The portal is accessible and safe.** WCAG 2.1 AA, rate limited, behind a web application firewall, with no internal vocabulary leaking through.

## 4. Non-goals / out of scope

- **A public website or anonymous request form.** Every portal action is by an authenticated user of a known account. Unknown senders use email and land in the quarantine queue.
- **Client-side approval workflows for changes.** A client approver can be a required field on a Change ticket (Ticket Management), but there is no multi-step client approval engine in the target solution.
- **Client-managed SLAs or contracts.** The portal shows, it never edits, commercial terms.
- **Client access to internal time detail, rate cards, roster, AI suggestions or work notes.** Never shown, by database role, not by UI choice.
- **Chat, Slack or Teams for clients.** Nice to Have INT-04 concerns internal Slack and Teams; client chat is not planned.
- **Client-authored knowledge articles.** Feedback only (see Knowledge Base non-goals).
- **Mobile applications.** The portal is responsive; there is no native app.
- **Per-client custom domains** in Phases 1 to 3. One `portal.<domain>` host with the account's branding; custom domains are a later option.

## 5. User-facing behavior

### 5.1 Vocabulary (fixed sets)

| Set | Values | Notes |
|---|---|---|
| Portal role | Requester, Account admin, Read-only | Account admin can also do everything a Requester can and manages the account's portal users |
| Identity mode (per account) | Federated (SAML), Federated (OIDC), Local fallback | Set by the operator's administrator on the account; local fallback may coexist with federation for named exceptions |
| Local account credential | Email plus password with mandatory MFA, or magic link | Chosen per account |
| Request types shown | Incident, Service Request, Change (when the account's forms enable them) | Problem and Project Task are internal types; a client never creates them |
| Ticket status as shown to clients | Submitted, Being worked, Waiting on you, Waiting on third party, Resolved, Closed, Cancelled | A display mapping from the internal state machine; internal states such as Dispatch or In review collapse into these seven |
| Consumption view | Off, Summary, Detailed | Summary shows hours used and remaining per contract period; Detailed adds per-ticket hours and the forecast |
| CSAT survey kind | Ticket close, Quarterly relationship | Ticket close is one question plus a comment; quarterly is five questions |

### 5.2 Getting in

- **Invitation.** An operator administrator (or an Account admin at the client) enters a name and email. The person receives a branded invitation from the account's sending identity. Federated accounts: the link sends the user to their company sign-in; on first return the portal user is created and bound to the account. Local accounts: the link sets a password and enrols MFA, or enables magic links, per the account's setting.
- **Sign-in page** at `portal.<domain>`: email first; the domain decides the route (federation redirect, or password and MFA). A user whose account is not enabled for the portal sees "Your organisation's portal is not active; contact your account owner" and nothing else.
- **Session.** Eight hours of inactivity ends the session; a federated account's IdP can end it sooner. Sign-out everywhere is available from the profile menu.
- **Account admin user management.** Account admins see their organisation's users: invite, change role (Requester or Read-only), deactivate. They cannot see or manage users of any other account, and they cannot grant Account admin without the operator's confirmation.
- **Fallback when federation breaks.** An operator administrator can switch the account to local fallback for a named user for a limited period; the switch is an audit event and the user must enrol MFA.

### 5.3 Information architecture

| Page | Contents | Empty state |
|---|---|---|
| Home | Greeting with the account name and branding, a "Find a solution or make a request" search box, open tickets awaiting the user's reply ("Waiting on you") pinned at the top, recent updates, consumption tiles when the account allows, common requests (client-visible templates), a pending CSAT prompt if any | "No open requests. Search for a solution or make a request." |
| My tickets | The user's own tickets, filters by status and date, search by key or words, export to CSV | "You have not made any requests yet." |
| Organisation tickets | Every ticket of the account, when the user's role allows (Account admin always; Requester if the account setting "requesters see organisation tickets" is on) | Same as above |
| New request | Solution search first, then request type, then the form for that type | Not applicable |
| Ticket | Key, title, status, priority as shown to clients, requester, assigned team (group name only, no individual by default), configuration item, dates, the public thread, attachments, "Reply" composer, "Mark resolved" for the requester when the account allows | Not applicable |
| Consumption | Per contract period: hours contracted, used, remaining, carried over, projected at period end, days left; per-ticket hours when Detailed; downloadable statement | "Consumption is not shared for your organisation" (only reachable when Off is set and the user follows an old link) |
| Knowledge | Published, visible articles by category, search, feedback | "No articles yet for your organisation." |
| Surveys | Pending and completed CSAT surveys | "No surveys pending." |
| Profile | Name, email, time zone, notification preferences, sign-out everywhere | Not applicable |

The navigation shows Consumption only when the setting is Summary or Detailed, Organisation tickets only when permitted, and Users only for Account admins.

### 5.4 New request

1. **Search first.** The user types the problem; matching solutions appear ([Knowledge Base §5.7](../knowledge-base/FUNCTIONAL-SPEC.md)). "Follow these steps" opens the article; "Request this" continues to the form pre-filled from the article's template. "None of these, continue" goes to step 2.
2. **Request type.** Cards for the types the account's forms enable, each with a one-line description and the response target the client can expect for a typical priority (from the contract's SLA policy, as plain text).
3. **Form.** The account's current form version for that type. Field kinds: short text, long text, choice, multi-choice, date, configuration item picker, contact picker, urgency (from the client's point of view), impact, attachment. Required fields are marked and block submission with inline messages. Conditional fields appear when a controlling choice is made. A form change by the operator applies to new requests only; a request in progress keeps the version it started with.
4. **Attachments.** Drag or pick files; per-file and per-request limits shown; a file is accepted as "scanning" and becomes downloadable when clean; a quarantined file is removed from the request with a notice to the user and the assignee.
5. **Submit.** Confirmation shows the key (`CS0012345`), the expected first-response window in the user's time zone, and a link to the ticket. The ticket is created with source Portal, requester the user, priority derived server-side from impact and urgency (per-account matrix), and the client-facing status Submitted.

### 5.5 Following a ticket

- **Thread.** Public comments only, oldest first, with author name (the operator's people appear with first name and team, not email), time in the user's zone, and attachments inline. Work notes, time entries, AI suggestions and internal audit events never appear; status changes appear as system lines ("Being worked, 14:02", "Waiting on you since 09:15").
- **Reply.** A composer with attachments. A reply while the ticket is "Waiting on you" resumes the SLA clock server-side (the client sees the status change to "Being worked").
- **Waiting on you.** The reason the operator recorded is shown in the client's words ("We need the export file from your side"), never the internal pause code.
- **Mark resolved.** Requesters may mark their own ticket resolved when the account setting allows; the operator still closes it.
- **Reopen.** Within the account's reopen window (default 5 business days after Resolved) a requester can reopen with a comment; after that, the portal offers "Make a related request".
- **Email parity.** Every public comment goes out by email ([Email Intake & Outbound](../email-intake/FUNCTIONAL-SPEC.md)); replying to that email appends to the same thread. The portal shows which comments arrived by email.

### 5.6 Consumption

Shown only when the account setting is Summary or Detailed. Summary: one card per active contract period with hours contracted, used, remaining, carried over, the percentage bar in the shared state colours, and the period end date. Detailed adds: hours per ticket (billable only, matching the internal billable class), non-ticket buckets shown by name only ("Governance", "QBR preparation") with hours, the projected consumption at period end, and threshold alerts the account opted into. Figures come from the same server computation as the internal Contracts screen, so they never disagree. A statement export (PDF and CSV) is available per period; locked periods are marked "Final".

### 5.7 CSAT

- **On ticket close.** When a ticket reaches Closed, the requester (and, if the account setting says so, the ticket's watchers) receives one email and one portal prompt: a single five-point question ("How satisfied are you with the handling of CS0012345?") with an optional comment. One reminder after three business days; then the survey expires. A low score (1 or 2) notifies the account owner internally the same day.
- **Quarterly relationship survey.** On the first business day after each quarter end, Account admins and any contacts flagged "executive sponsor" receive a five-question survey (responsiveness, quality, communication, value, likelihood to recommend) plus a comment. Two reminders over three weeks.
- **Results.** Shown to the client on their dashboard as trends (their own only) and to the operator per account and portfolio ([Dashboards & Report Packs](../dashboard-and-reporting/FUNCTIONAL-SPEC.md)). Individual responses are visible to the operator with the respondent's name unless the account setting makes them anonymous.
- **Suppression.** No survey for tickets cancelled, resolved as Duplicate, or closed within 15 minutes of creation; no more than one ticket-close survey per requester per business day (the others are skipped, not queued).

### 5.8 Branding and accessibility

The portal carries the account's logo and accent colour on the header band and in email; everything else uses the product design system in light mode ([Design System §3.3 and §5](../../01-architecture/DESIGN-SYSTEM.md)). Every page meets WCAG 2.1 AA: keyboard navigable forms, visible focus, labels on every field, status colours paired with text, no information conveyed by colour alone.

### 5.9 Notifications to portal users

Email is the channel (no push, no SMS). Events: invitation, ticket created (confirmation), public comment added by the operator, status changed to Waiting on you, Resolved, Closed, CSAT prompt and reminder, quarterly survey, consumption threshold reached (when opted in). Users choose per event kind in Profile; "Waiting on you" cannot be turned off. All emails are threaded on the ticket's conversation and branded per account.

### 5.10 What the portal never shows

Work notes; internal time entries, rates, cost or roster; assignee email addresses; internal state names; AI suggestions or "drafted by Axel" markers; quarantined attachments; other accounts' anything; draft or retired articles; internal audit events. These are enforced by the portal database role and the client-facing view, not by omitting UI ([Security & Tenancy §4 and §5](../../01-architecture/SECURITY-AND-TENANCY.md)).

## 6. Rollout

1. **Phase 1 (Foundations):** identity spike outcome (ADR-03), the portal Clerk organisation model, the portal database role and `acct.ticket_timeline_public` view, the isolation suite cases for portal principals (CP-02). No user-facing portal yet.
2. **Phase 2 (Focused pilot, "controlled external access"):** invitation-only portal for one or two friendly internal-facing accounts: sign-in (local fallback and one federated test IdP), home, my tickets, new request with solution search and dynamic forms (CP-03), ticket view with public thread and attachments (CP-04, CP-05), consumption Summary behind the toggle (CP-06), knowledge page (CP-08), email notifications. Depends on Ticket Management core, Email outbound, Knowledge Base core.
3. **Phase 3 (Operational replacement):** production SSO per account with SAML and OIDC and the fallback procedure (CP-01), account-admin user management, organisation tickets, consumption Detailed with statements, CSAT on close and quarterly (CP-07), WAF and rate limits tuned on real traffic, accessibility audit. Depends on Accounts & Administration identity settings and Dashboards for CSAT reporting.
4. **Phase 4:** client-visible templates as "Common requests", custom domains, anonymous CSAT option, requester "mark resolved" and reopen window tuning per account.

## 7. Success criteria

- A portal user of account A who edits the URL to a ticket key of account B receives a not-found page, and the API logs show the row was never returned, on every environment, with the test in the isolation suite.
- The portal database role cannot select from the work notes table; a test proves it, and a new work note on a ticket never appears in the portal thread within any polling interval.
- A federated user of an account with SAML signs in through their IdP and lands on the home page bound to that account without any operator action after the invitation.
- A local-fallback user cannot complete sign-in without MFA enrolment.
- Submitting an Incident with a required "Affected item" left empty is blocked inline; filling it creates a ticket whose priority equals the internal matrix result for the chosen impact and urgency.
- A file that GuardDuty flags is removed from the request, the user sees a notice, and no download link ever existed.
- With the consumption setting Off, the Consumption page and navigation entry do not exist for that account; with Summary, the hours shown equal the internal Contracts screen for the same period to the minute.
- Closing a ticket sends exactly one CSAT prompt to the requester; a score of 1 notifies the account owner the same day; a Duplicate resolution sends none.
- On the first business day after a quarter end, each Account admin receives one relationship survey; responses appear on the account's dashboard.
- The portal passes an automated accessibility scan with no AA violations and a keyboard-only walk through New request.

## 8. Open questions

- **Do requesters see each other's tickets by default?** Default assumption: no; the account setting "requesters see organisation tickets" is off until the client asks.
- **Should the assigned person's name be shown?** Default assumption: team name only; the account setting can enable first names.
- **Reopen window length?** Default assumption: 5 business days on the account calendar.
- **Anonymous CSAT?** Default assumption: named responses; anonymity is an account setting in Phase 4.
- **Client approver on Change tickets in the portal?** Default assumption: a required contact-picker field on the Change form, with approval recorded as a public comment by that contact; no approval engine.
- **Custom portal domains?** Default assumption: not before Phase 4; one host with per-account branding.
- **Local fallback credential policy (password rules, MFA methods)?** Default assumption: Clerk defaults with MFA required, TOTP and email code; documented in the security annex.
