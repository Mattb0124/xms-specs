# Go-Live Plan: build, parallel run, cutover

**Status:** Draft for approval
**Owner:** Matt Brown
**Last updated:** 2026-09-11
**Related:** [Roadmap](./ROADMAP.md), [Implementation Plan](./IMPLEMENTATION-PLAN.md), [Test Strategy](./TEST-STRATEGY.md), [TODO](./TODO.md), [Requirements Traceability](../00-overview/REQUIREMENTS-TRACEABILITY.md), [Clarifications needed](../00-overview/CLARIFICATIONS-NEEDED.md)

---

## 1. The shape of it

| Phase | Dates | What happens |
|---|---|---|
| **Build** | Mon 14 Sep to Fri 16 Oct 2026 (4 working weeks) | The twelve outstanding Must Have rows close. Feature complete for the replacement |
| **Parallel run and training** | Mon 19 Oct to Fri 27 Nov 2026 (5 weeks) | DM-04. Both systems carry the same work. People are trained on the real product with real data |
| **Cutover** | Fri 27 Nov to Mon 30 Nov 2026 | Final migration delta, reconciliation, sign-off |
| **Go live** | Tue 1 Dec 2026 | ServiceNow is read-only. XMS is the system of record |

## 2. What "outstanding" actually means

The register carries **94 rows that are not Built**. That number is misleading as a plan input, and the split is what makes mid-October achievable:

| Group | Rows | In this plan |
|---|---|---|
| Must Have, still outstanding | **12** | **Yes. This is the build phase** |
| Nice to Have, phases 3 and 4 | 17 | No. After go-live |
| Revision 3 intake, unassessed | **65** | **No. See section 6** |

**The 65 revision 3 rows are not in scope for the replacement.** They are the operating-model programme: the resolution ladder, measurement and calibration, account health, time certification, collaboration signal, configuration governance and outcomes. They were never phased, most are blocked on open clarifications, and none of them is needed to switch ServiceNow off. Treating them as go-live scope is the single easiest way to miss December.

## 3. The build phase: twelve rows, four weeks

### 3.1 One piece of work unblocks eight of them

Eight of the twelve Must Haves are Axel AI: **AI-01, AI-02, AI-03, AI-04, AI-05, AI-06, AI-07, AI-14**. They are not eight separate builds.

Five are already coded and sitting behind one switch. The adapter, the SSE client, the capability builders for classify, prioritise, duplicate, summarise and draft_reply all exist and are tested. Three things stop them working:

1. `HARNESS_BASE_URL` is unset, and `.env.example` says to leave it empty to run without AI.
2. `NullHarnessClient` throws, so nothing has run end to end against a real harness.
3. The UI entry points were deliberately removed. "Ask Axel and Draft with Axel are out. Both opened a surface that is held" (frontend `c9c3225`).

So **AI-01, AI-02, AI-03, AI-04 and AI-07 are a wiring and validation job, not a build.** AI-05, AI-06 and AI-14 are genuinely unbuilt: their capability builders are explicitly `undefined` in `capabilities.ts`.

| Week | Work |
|---|---|
| W1 (14 to 18 Sep) | Point `HARNESS_BASE_URL` at the harness dev environment. Prove one turn end to end. Restore the Axel panel entry points |
| W2 (21 to 25 Sep) | AI-01 to AI-04 and AI-07 validated against real responses: confidence thresholds, withholding, the per-account switch, redaction before egress |
| W3 (28 Sep to 2 Oct) | AI-05 report narrative and AI-14 burn anomaly. Both are new capability builders on an adapter that now works |
| W4 (5 to 9 Oct) | AI-06 time entry assistance, narrowed to normalisation and gap detection |

### 3.2 The other four, in parallel

| Row | Work | Risk |
|---|---|---|
| **CP-01** SSO via SAML / OIDC | Clerk enterprise connections, one organisation per account. The Phase 1 spike in Security section 2.1 confirms licensing and the per-organisation SAML topology | **Highest risk item in the plan.** If Clerk cannot do it, the fallback is an XMS-owned portal realm behind the same principal interface. Start week 1, not week 3 |
| **TB-02** Composite resolution gate | Resolution code, notes completeness, article prompt. Ships without the TC-01 certification source, which is out of scope | Low |
| **TM-23** Account ownership and team construct | One named primary owner per account, audited changes, teams | **Blocked on C-01.** Revision 3 has ownership drive default routing, which contradicts the group routing already shipped |
| **DM-04** Parallel run period | Not a build. This is phase 2 of this plan | None |

### 3.3 Also closing in the build phase

The fourteen Partial rows each carry a named gap in the register. Nine are the AI rows above. The rest are Nice to Have (TM-17, TB-15, CAP-09, EM-09, AI-18) or unassessed knowledge-base rows (KB-03, KB-04, KB-05) and **do not block go-live**. KB-03 is worth pulling forward anyway: the generalise flow ships today with no AI-23 consent gate behind it, so content can be promoted to global with no consent check.

## 4. Parallel run and training: 19 Oct to 27 Nov

This is DM-04, and it is the phase that earns the go-live decision.

### 4.1 What parallel means here

Both systems carry the same work for five weeks. ServiceNow stays the system of record until 1 December; XMS is written to in earnest, not rehearsed.

- **Every new ticket is raised in both.** Email intake points at XMS; the ServiceNow record is created by the connector, which already ships (SN-01 to SN-09, all Built).
- **Time is logged in XMS only.** Running two time ledgers guarantees they disagree, and the XMS one is the one being trusted in December.
- **Reporting runs from both, weekly, and the numbers are compared.** A WSR pack from each, side by side, is the most honest test the product gets.
- **The migration delta is re-run weekly** so the gap at cutover is days, not months.

### 4.2 Training

| Week | Audience | Content |
|---|---|---|
| W1 (19 to 23 Oct) | Service desk | Queue, record, transitions, time, resolution discipline |
| W2 (26 to 30 Oct) | Engineers | Record, work notes, scope flags, change windows, connectors |
| W3 (2 to 6 Nov) | CSMs and leads | Accounts, budget, report packs, dashboards, portal admin |
| W4 (9 to 13 Nov) | Client pilot | One or two accounts on the portal. Real requests, real feedback |
| W5 (16 to 27 Nov) | Everyone | Running on XMS with support to hand. No new material |

Training on the real product with real migrated data, not a sandbox. People trained on fixtures do not trust the system when their own accounts look wrong.

### 4.3 Exit criteria, decided Fri 27 Nov

Go-live is a decision, not a date. It needs all of:

- [ ] Reconciliation (DM-03) signed off: record counts and hour totals match, source against target
- [ ] Zero P1 defects open; no P2 defect older than five working days
- [ ] Every operator has completed their training week and worked a full day in XMS
- [ ] The portal pilot accounts have raised, tracked and closed real requests
- [ ] Weekly report packs from both systems agree, or every difference is explained
- [ ] The isolation suite, the full gate and the ZAP baseline are green on the release build
- [ ] Security ruling on ADR-02 received (Security & Tenancy, pending)
- [ ] Rollback rehearsed at least once

Any unmet, the date moves. Section 7 says what that costs.

## 5. Cutover: 27 to 30 Nov

1. **Fri 27 Nov, close of business.** ServiceNow goes read-only for the migrating accounts.
2. **Fri evening.** Final delta migration, then reconciliation (DM-03) against the frozen source.
3. **Sat 28 Nov.** Sign-off on the reconciliation. Rollback decision point: if it fails, ServiceNow reopens Monday and the date moves.
4. **Sun 29 Nov.** Inbound email cut to XMS. Connector switched to one-way ingest (SN-09) so ServiceNow keeps receiving but never writes back.
5. **Mon 30 Nov.** Quiet day. Smoke tests, seeded checks, support on hand.
6. **Tue 1 Dec.** Go live. XMS is the system of record.

The connector staying in ingest-only mode rather than being switched off is deliberate: it keeps a read path back to ServiceNow for the first weeks without any risk of a write loop.

## 6. Explicitly out of scope

**The 65 revision 3 rows**, in seven modules with specs written but not scheduled. They are a separate programme, and they carry their own blockers: C-01 (does a group route?), C-02 (nothing triaged into a phase), C-05 (anonymised concerns against the audit trail).

**The 17 Nice to Have rows** in phases 3 and 4, including multi-currency (TB-15), scenario planning (CAP-10), the custom report builder (DR-10), Slack and Teams (INT-04) and autonomous triage (AI-19).

Neither group is needed to switch ServiceNow off. Both are worth doing afterwards, and the register already tracks them.

## 7. Risks, and what each one costs

| Risk | Impact | Mitigation |
|---|---|---|
| **Clerk cannot do per-account SAML** (CP-01) | Portal go-live slips. Internal go-live does not | Spike in week 1. The fallback realm sits behind the same principal interface, so nothing above the guard changes |
| **The harness is not available** to point at in week 1 | Eight Must Haves stall at once | The single largest dependency in the plan. Confirm harness dev access before 14 Sep |
| **C-01 is not answered** | TM-23 cannot be built, and the routing model stays ambiguous through the parallel run | Needs a decision this week. It is one question |
| **Parallel run reveals a data problem** | Cutover slips by the time it takes to fix and re-reconcile | Weekly delta re-runs mean the problem surfaces in October, not on 27 November |
| **Training does not finish** | People fall back to ServiceNow after go-live and the record splits | Five weeks is generous. The risk is attendance, not duration |
| **A second session is editing the same tree** | Work is lost or silently reverted | Already happening. Worktrees per workstream |

## 8. What this plan assumes

- Four people, as today.
- Harness dev environment available from 14 September.
- No new Must Have requirements between now and go-live. Anything added displaces something, and the register is where that trade is recorded.
- The Security ruling on ADR-02 arrives before the exit-criteria review.
- Brookfield, or whichever account is first, agrees to the portal pilot in week 4 of the parallel run.
