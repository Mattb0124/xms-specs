# Technical Spec: Collaboration Signal

**Status:** Draft, not yet verified in code. Blocked on [C-05](../../00-overview/CLARIFICATIONS-NEEDED.md)
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Security & Tenancy](../../01-architecture/SECURITY-AND-TENANCY.md), [Audit & Analytics](../../01-architecture/AUDIT-AND-ANALYTICS.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Ticket Management](../ticket-management/TECHNICAL-SPEC.md)
**Requirements covered:** CL-01 to CL-05

---

## 1. Why this is blocked, and why that matters more here than elsewhere

CL-05 says no interface, export **or audit view** can resolve an anonymised concern to its author. XA-01 says every action is recorded as an append-only security event with actor and principal kind. These are in direct conflict, and [C-05](../../00-overview/CLARIFICATIONS-NEEDED.md) has not resolved it.

This is not a blocker that can be worked around later. **A concern written with an actor id is unfixable afterwards**: the association exists in the table, in the WAL, in every backup and in the audit stream. Deleting the column later does not undo it. The mechanism has to exist before the first concern is captured.

Two candidate resolutions, neither chosen:

1. **Pseudonymisation at write.** The concern stores a per-subject-per-window pseudonym; the mapping lives in a table no application role can read, held for the minimum needed to enforce one-concern-per-contributor. The audit event records that a concern was written, by a pseudonym, never by whom.
2. **Documented audit exemption.** Concern authoring is exempt from actor capture, recorded as a deliberate, signed-off gap in [Security Assurance](../../01-architecture/SECURITY-AND-TENANCY.md) terms.

Option 1 satisfies both requirements. Option 2 is cheaper and trades an audit hole for it. The choice is a security decision, not an engineering preference, and it wants an ADR.

## 2. Data model (subject to C-05)

| Table | Holds |
|---|---|
| `acct.collaboration_grades` | CL-01. Ticket, participant subject, grade, optional comment, grader, graded at. Positive signal is attributable |
| `acct.client_relayed_feedback` | CL-02. Subject person, the client contact it came from, the CSM who relayed it, date, content |
| `acct.concerns` | The anonymised half. Subject, window, content, and an author reference whose shape C-05 decides |
| `rpt.collaboration_quadrant` | CL-04 per person per account per period, computed |

Grades and concerns are separate tables on purpose. One table with a nullable author is how an anonymity guarantee gets broken by a later feature.

## 3. Domain rules

- **Minimum contributor count** (CL-05) is checked at read time and the response carries neither the count nor a direction below it. Returning "withheld, 2 of 3" leaks in a small team.
- **Quadrant placement** is pure over peer signal and client satisfaction. Where they disagree, client satisfaction governs placement, and the disagreement is carried as its own field rather than being resolved away.
- **No chasing** (CL-03) is a build constraint: no reminder job, no unread state, no completion percentage exposed to a manager.

## 4. Ordering

1. TM-21 and TM-22 in Ticket Management. Prerequisites.
2. **Resolve C-05 and build the anonymity mechanism.** Nothing below starts first.
3. CL-01 positive path with concerns disabled, which is safe under either resolution.
4. Concerns, with the minimum contributor count registered in CG-01.
5. CL-02, then CL-04 once both sides carry volume.
6. CL-03 digest.

## 5. Testing

- **The test that matters:** an anonymised concern cannot be resolved to its author through any API response, export, report pack, audit query or direct table read available to an application role. Written against the database, not only the API, because the API is not where this leaks.
- Below-minimum concerns return withheld, with no count and no direction.
- A single-participant ticket produces no grading prompt.
- Skipping CL-01 or CL-03 produces no follow-up job, message or notification.
- Isolation suite coverage on all three account-scoped tables, both roles. None of them is portal readable.

## 6. Risks

- **The anonymity guarantee is the product.** If people believe a concern is traceable, they stop giving them and the module produces a flattering, useless signal. This is a trust property, and one leak ends it permanently.
- **Small teams.** With four people, "anonymised and aggregated" is thin cover regardless of mechanism. The minimum contributor count must be set with that in mind, and it may mean concerns are simply not available on small accounts.
- **Scope creep into appraisal.** The functional spec rules it out; the risk is organisational rather than technical, and the asymmetric design is the mitigation.
