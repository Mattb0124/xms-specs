# Implementation Plan: XMS to go-live, ordered work breakdown

**Status:** Draft for approval. Supersedes the 2026-09-04 [Implementation Plan](./IMPLEMENTATION-PLAN.md) from 2026-09-14 onward; that document remains the record of how Phases 0 and 1 were built
**Owner:** Matt Brown
**Last updated:** 2026-09-11
**Related:** [Go-Live Plan](./GO-LIVE-PLAN.md), [Roadmap](./ROADMAP.md), [TODO](./TODO.md), [Test Strategy](./TEST-STRATEGY.md), [Requirements Traceability](../00-overview/REQUIREMENTS-TRACEABILITY.md), [Clarifications needed](../00-overview/CLARIFICATIONS-NEEDED.md)

The [Go-Live Plan](./GO-LIVE-PLAN.md) is the phase view and the gantt. This is the work behind it: what gets built, in what order, what each item depends on, and what proves it done.

---

## 1. What changed since the 2026-09-04 plan

That plan was written for a six-month build from an empty repository. Seven days later the position is different enough that the sequence no longer describes the work.

| Then (2026-09-04) | Now (2026-09-11) |
|---|---|
| Nothing built | **96 of 190 requirements Built**, 14 Partial, 80 Not started |
| 12 module spec pairs | 19, after the functional RTM revision 3 |
| 115 requirements | 190, after 75 were merged in |
| Phases 1 to 4 over six months | Build to 16 Oct, parallel to 27 Nov, live 1 Dec |

**The register is the input to this plan**, and the number that matters is not 94 outstanding. It is **12 Must Have**. Everything else is either Nice to Have or the revision 3 intake, and section 7 says why neither is in scope.

## 2. How to read this plan

**Item format.** `GL<phase>.<week>.<n>` followed by the outcome, then **Depends on**, **Spec**, **Owner**, **Done when**. Requirement ids appear in brackets where an item closes one. Ids in this series do not collide with the `P` series in the superseded plan.

**Streams.** `INF` infrastructure and pipeline; `BE` backend; `FE` frontend; `AI` Axel adapter and harness; `DATA` migration and ServiceNow; `OPS` training, parallel run, cutover. Owners map to [Roadmap §4](./ROADMAP.md).

**Sequencing rules.** The six rules in the superseded plan still hold: migration then worker then API then frontend; nothing merges without its test line green; shared-contract changes land as their own item first; two developers never edit the same module in the same week; weekly sprints with a named exit demo; every item under the security definition of done (ADR-16, the `xms-security-first` skill).

**One rule added, learned this week.** Concurrent sessions and developers work in **separate git worktrees**, one per workstream. Two agents editing one tree has already cost a broken build and a typecheck error that appeared and fixed itself mid-run.

## 3. Week 0: the three answers (by Fri 18 Sep)

These are not work. They are decisions that gate work, and two of them gate a lot of it.

- **GL0.0.1** **C-01 answered: do assignment groups route?** **Depends on** nothing. **Spec** [Clarifications needed](../00-overview/CLARIFICATIONS-NEEDED.md) C-01. **Owner** Matt with Sofi. **Done when** the answer is an ADR in the Decision Log, and TM-08, TM-23 and CAP-09 read consistently. **Blocks** GL1.3.1.
- **GL0.0.2** **Harness dev environment confirmed reachable** with a `HARNESS_BASE_URL` the API can use and a session secret. **Depends on** nothing. **Spec** [AI Integration](../01-architecture/AI-INTEGRATION.md). **Owner** Matt. **Done when** a curl against the harness chat stream returns frames from the XMS dev network. **Blocks** eight Must Have rows at once.
- **GL0.0.3** Security ruling on ADR-02 requested with a date. **Owner** Matt with Juan. **Done when** a response date is committed. **Blocks** the go-live gate, not the build.
- **GL0.0.4** Portal pilot account agreed, with a named client contact. **Owner** Matt. **Done when** the account and contact are recorded here. **Blocks** GL2.4.1.

## 4. Phase GL1: Build (Mon 14 Sep to Fri 16 Oct)

### Week 1 (14 to 18 Sep): the harness, and the riskiest unknown

- **GL1.1.1** The Axel adapter reaches a real harness: `HARNESS_BASE_URL` configured in dev, one interactive turn streaming end to end, `NullHarnessClient` no longer the path taken. **Depends on** GL0.0.2. **Spec** AI Integration §2. **Owner** AI. **Done when** a ticket summarise turn returns frames and persists a suggestion row.
- **GL1.1.2** The Axel panel entry points come back: Ask Axel on the record, Draft with Axel on the composer, the panel in the bar. They were removed in `c9c3225` because the surface was held. **Depends on** GL1.1.1. **Spec** User Experience §11. **Owner** FE. **Done when** a consultant opens the panel from the record and receives a streamed answer.
- **GL1.1.3** **CP-01 spike: can Clerk do per-account SAML?** One enterprise connection on one organisation, one federated test sign-in. **Depends on** nothing. **Spec** [Security & Tenancy](../01-architecture/SECURITY-AND-TENANCY.md) §2.1. **Owner** Matt. **Done when** a federated portal user signs in, or the spike fails and GL1.2.4 starts instead. **This is the highest-risk item in the plan and it runs first for that reason.**
- **GL1.1.4** Worktree per workstream, and the dev server run outside any agent session. **Owner** INF. **Done when** each stream has its own worktree and `git worktree list` shows no shared checkout.

**Exit demo.** A summarise turn, live, from the record. A federated sign-in, or a written decision to build the fallback realm.

### Week 2 (21 to 25 Sep): the five that were already coded

- **GL1.2.1** **AI-01, AI-02** proven against real responses: categorisation and priority on intake, duplicate detection with a merge a human accepts or rejects. **Depends on** GL1.1.1. **Spec** AI Integration §4. **Owner** AI. **Done when** both return suggestions above threshold and withhold below it, with the account switch honoured. `[AI-01, AI-02]`
- **GL1.2.2** **AI-03, AI-04** proven: long-thread summarisation and draft reply, neither able to send without a human. **Depends on** GL1.1.2. **Owner** AI with FE. **Done when** a draft is produced with its confidence and the AI-22 outcome (sent unchanged, light edit, heavy edit, discarded) is recorded. `[AI-03, AI-04]`
- **GL1.2.3** **AI-07** retrieval proven: embeddings generated for the corpus, similar tickets and articles ranked on the Solutions rail, AI-23 scope rules enforced at the data layer. **Depends on** GL1.1.1. **Owner** AI with BE. **Done when** a rail on a seeded ticket ranks real comparables and an opted-out account contributes nothing. `[AI-07]`
- **GL1.2.4** **CP-01 build**, on whichever path GL1.1.3 chose. **Depends on** GL1.1.3. **Owner** Matt with BE. **Done when** a portal user federates in and lands scoped to exactly their account. `[CP-01]`
- **GL1.2.5** **TB-02 composite resolution gate**: resolution code, notes completeness, article prompted then warned on. Ships without the TC-01 certification source, which is out of scope. **Depends on** nothing. **Spec** Ticket Management. **Owner** BE with FE. **Done when** a ticket cannot reach Resolved without the gate satisfied or an exemption logged with its reason. `[TB-02]`

**Exit demo.** Intake suggests a category and a priority, the rail ranks real neighbours, and a portal user signs in through their own IdP.

### Week 3 (28 Sep to 2 Oct): the three genuinely unbuilt capabilities

- **GL1.3.1** **TM-23 account ownership and team construct**: one named primary owner per account, changes audited, teams grouping accounts and people. **Depends on** GL0.0.1. **Spec** Accounts & Administration. **Owner** BE with FE. **Done when** every account has exactly one owner, a change writes an audit event, and the routing behaviour matches whatever C-01 decided. `[TM-23]`
- **GL1.3.2** **AI-05 report narrative**: the `wsr_narrative` capability builder, replacing `templatedNarrative` in the pack. **Depends on** GL1.1.1. **Spec** AI Integration §4. **Owner** AI. **Done when** a WSR pack renders an Axel narrative, a human can edit it before send, and the unedited rate is recorded. `[AI-05]`
- **GL1.3.3** **AI-14 budget burn anomaly**: the `burn_anomaly` builder, flagging an account materially off its run rate to the owner. **Depends on** GL1.1.1. **Owner** AI with BE. **Done when** a seeded account tracking 40 percent above run rate raises to its owner and the suggestion is auditable. `[AI-14]`
- **GL1.3.4** **KB-03 consent gate**: the generalise flow refuses promotion to global unless the source account has opted in to cross-account contribution. **Depends on** nothing. **Spec** Solution Knowledge Base, AI-23. **Owner** BE. **Done when** promotion from a non-opted-in account is refused at the data layer, proven by test. **Not a Must Have, pulled forward because the flow ships today with no gate behind it.** `[KB-03 partial]`

**Exit demo.** A weekly pack with a written narrative, and a burn alert on a seeded account.

### Week 4 (5 to 16 Oct): the last capability, then hardening

- **GL1.4.1** **AI-06 time entry assistance**, narrowed to description normalisation and unlogged-time gap detection. The daily flow is TC-01 and is out of scope. **Depends on** GL1.1.1. **Owner** AI. **Done when** an unlogged gap is surfaced as a specific figure and a description normalises. `[AI-06]`
- **GL1.4.2** Full-gate hardening pass: lint, type-check, unit, integration, isolation suite and ZAP baseline green on the release build, with no suppressions. **Depends on** every GL1 item. **Spec** [Test Strategy](./TEST-STRATEGY.md) §5. **Owner** INF. **Done when** the pipeline is green end to end on a tagged build.
- **GL1.4.3** Seed and demo data refreshed for training: two accounts with contrasting calendars, contracts of each model, tickets across every state, articles at each visibility. **Depends on** nothing. **Owner** DATA. **Done when** `seed:dev` produces the training environment in one command.
- **GL1.4.4** Training material written against the built product, not the spec. **Depends on** GL1.4.3. **Owner** OPS with Matt. **Done when** each of the four audience decks exists and has been walked once.

**Phase gate GL1, Fri 16 Oct.** Signed when: all twelve Must Have rows are Built in the register; the register was regenerated and committed; the full gate is green; no open security finding; training material exists.

## 5. Phase GL2: Parallel run and training (Mon 19 Oct to Fri 27 Nov)

- **GL2.0.1** Parallel run starts: email intake points at XMS, the connector creates the ServiceNow record, time is logged in XMS only. **Depends on** GL1 gate. **Spec** [Go-Live Plan](./GO-LIVE-PLAN.md) §4.1. **Owner** OPS with DATA. **Done when** a ticket raised by email exists in both systems and its time exists only in XMS. `[DM-04]`
- **GL2.0.2** Weekly migration delta re-run and reconciled, every Friday. **Depends on** GL2.0.1. **Owner** DATA with Vini. **Done when** each Friday's reconciliation report is signed and the gap is under one day of records. `[DM-03]`
- **GL2.0.3** Weekly report packs generated from both systems and compared. **Depends on** GL2.0.1. **Owner** OPS. **Done when** each week's differences are either zero or explained in writing.
- **GL2.1.1** Training week 1, service desk: queue, record, transitions, time, resolution discipline. **Owner** OPS. **Done when** every agent has worked a full day in XMS.
- **GL2.2.1** Training week 2, engineers: record, work notes, scope flags, change windows, connectors. **Owner** OPS.
- **GL2.3.1** Training week 3, CSMs and leads: accounts, budget, report packs, dashboards, portal admin. **Owner** OPS.
- **GL2.4.1** Training week 4, client portal pilot on the agreed account. **Depends on** GL0.0.4. **Owner** Matt with the account CSM. **Done when** the client has raised, tracked and closed a real request.
- **GL2.5.1** Weeks 5 and 6: everyone running on XMS with support to hand, no new material. Defect burn-down to the exit criteria. **Owner** OPS.
- **GL2.5.2** Exit criteria review, Fri 27 Nov, against the eight criteria in [Go-Live Plan](./GO-LIVE-PLAN.md) §4.3. **Owner** Matt. **Done when** every criterion is met or the date moves.

**Phase gate GL2, Fri 27 Nov.** The go-live decision. Any criterion unmet and the date moves rather than the criterion.

## 6. Phase GL3: Cutover (Fri 27 to Mon 30 Nov) and go live

- **GL3.0.1** ServiceNow read-only for the migrating accounts, Friday close of business. **Owner** DATA with Vini.
- **GL3.0.2** Final delta migration against the frozen source, then reconciliation. **Depends on** GL3.0.1. **Owner** DATA. **Done when** counts and hour totals match and the report is signed. `[DM-03]`
- **GL3.0.3** Rollback decision point, Saturday. **Depends on** GL3.0.2. **Owner** Matt. **Done when** either sign-off is recorded or ServiceNow reopens Monday and the date moves.
- **GL3.0.4** Inbound email cut to XMS; connector switched to one-way ingest so ServiceNow keeps receiving and never writes back. **Depends on** GL3.0.3. **Owner** DATA. `[SN-09]`
- **GL3.0.5** Quiet Monday: smoke tests, seeded checks, support on hand. **Owner** everyone.
- **GL3.0.6** **Go live Tue 1 Dec.** XMS is the system of record.

## 7. Out of scope, and why

**The 65 revision 3 rows**, in seven modules with specs written but never phased: resolution ladder, measurement and calibration, account health, time certification, collaboration signal, configuration governance, outcomes. They carry their own blockers (C-01, C-02, C-05) and none is needed to switch ServiceNow off. They are the operating-model programme and want their own plan after go-live.

**The 17 Nice to Have rows** in phases 3 and 4: multi-currency (TB-15), scenario planning (CAP-10), the custom report builder (DR-10), Slack and Teams (INT-04), autonomous triage (AI-19), ticket templates (TM-17), the shift rota (CAP-09), email priority detection (EM-09), auto-resolution (AI-18).

**The remaining knowledge-base partials** KB-04 and KB-05, which are article health reporting and contribution aggregation. Neither blocks the replacement.

## 8. Gate checklists

**GL1, feature complete.** Twelve Must Have rows Built and regenerated into the register; full gate green on a tagged build; no open security finding; seed refreshed; training material walked once.

**GL2, go-live decision.** The eight exit criteria in [Go-Live Plan](./GO-LIVE-PLAN.md) §4.3, in full.

**GL3, cutover.** Reconciliation signed; rollback rehearsed; email cut; connector in ingest-only; smoke tests green.
