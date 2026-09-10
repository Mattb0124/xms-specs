# Technical Spec: Resolution Ladder & Routing

**Status:** Draft, not yet verified in code. Blocked on [C-01](../../00-overview/CLARIFICATIONS-NEEDED.md)
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [AI Integration](../../01-architecture/AI-INTEGRATION.md), [Measurement & Calibration](../measurement-and-calibration/TECHNICAL-SPEC.md)
**Requirements covered:** RL-01 to RL-09

---

## 1. Why this is a draft

The module has no code. Unlike the specs written against the built product, nothing here is verified in code, and it must not be read as if it were. It fixes the shape the build should take and names what has to be decided first.

**Blocking:** RL-03 says the classified path "drives routing". [C-01](../../00-overview/CLARIFICATIONS-NEEDED.md) has not settled what routing is, because the workbook and revision 3 disagree about whether assignment groups route at all. Building the classifier against the wrong routing model is the expensive mistake here.

## 2. Data model

All tables are account scoped, carry `account_id NOT NULL`, and get `FORCE ROW LEVEL SECURITY` with operator and portal policies in the same migration ([Data Model](../../01-architecture/DATA-MODEL.md) section 3). They are picked up by the generated isolation suite automatically.

| Table | Holds |
|---|---|
| `acct.ticket_paths` | One row per ticket: `classified_path`, `classified_at`, `classified_by` (model or person), `confidence`, `actual_path`, `actual_derived_at`, `derivation_reason`. Both paths nullable, neither overwrites the other |
| `acct.path_proposals` | Append-only. Every proposal Axel made with its confidence, and the override that followed it with actor and reason. RL-03 requires the proposal to survive the override |
| `acct.request_type_access` | Per account and request type: `requires_credentialed_access`, `requires_expertise`, owner, effective date. This is the RL-04 marking, and it is a CG-01 registered parameter |
| `acct.resolution_profiles` | The RL-02 profile per account and request type: volumes, who resolved, access and expertise signals, last rebuilt. Derived, rebuildable from source |
| `acct.self_service_events` | RL-06 and RL-07: what was asked, what was returned, satisfaction, and `fallback_ticket_id` where the attempt became a ticket |

`path` is `text` with a `CHECK` over `0`, `1`, `2`, `3` and a matching TypeScript union, never a Postgres enum ([Data Model](../../01-architecture/DATA-MODEL.md)).

## 3. Domain rules (`backend/src/domain`)

Pure, no database, reused by the worker:

- **Actual path derivation.** From the ownership trail and TM-21 participants at close. Path 2 requires a participant event with a validation touch type while the assignee never changed. Insufficient trail returns underived with a reason, never a default.
- **Credential gate.** A request type marked `requires_credentialed_access` for that account cannot yield a classified path of 1. Enforced in the domain, so neither the classifier nor a human override can produce the forbidden combination.
- **Profile aggregation.** Deterministic from closed records, so a rebuild produces the same profile.

## 4. Classification path

Intake calls the Axel adapter through the single egress ([AI Integration](../../01-architecture/AI-INTEGRATION.md)). The adapter checks the account AI switch first: with AI off, no call is made and the ticket routes to a human unclassified. AI-09 thresholds are applied before the proposal is stored as actionable.

The profile is retrieval input, and it is subject to the AI-23 two-scope consent rule: an account that has not opted in to cross-account contribution never has its profile content reach another account's classification or RL-08 guidance. This is enforced in the data layer, not in the prompt.

## 5. Ordering

1. `acct.resolution_profiles` and the RL-02 aggregation over migrated history (DM-01). No UI, no classification.
2. `acct.ticket_paths` and `acct.path_proposals` with silent classification. Paths stamped, nothing routed.
3. RL-04 markings and the credential gate.
4. Routing effect. **Gated on C-01 and on MC-04/MC-05 accuracy.**
5. RL-08 guidance, then RL-09 candidates.
6. RL-06 and RL-07 alongside the portal's self-service surface.

## 6. Testing

Per [Test Strategy](../../03-delivery/TEST-STRATEGY.md):

- Domain units for derivation across every trail shape, including the path 2 case and the underivable case.
- A test that a credential-marked type cannot reach path 1 by classification **or** by human override.
- A test that an override leaves the original proposal readable.
- Isolation suite coverage for all five tables, both roles.
- An AI switch-off test: no HTTP call is made when the account has AI disabled.

## 7. Risks

- **Classifier drives routing before it is trustworthy.** Mitigated by the silent phase and by gating on measured accuracy.
- **Path 2 defined too loosely.** Any engineer comment counting as a validation touch inflates the front-desk figure MC-02 depends on. The touch type is explicit for this reason.
- **Profile leakage across accounts.** The AI-23 rule is a data-layer control, and a prompt-level filter would not satisfy it.
- **Historical profile quality.** RL-02 is only as good as DM-01, and a thin corpus produces a confident classifier with nothing behind it.
