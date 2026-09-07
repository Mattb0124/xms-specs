# Rule: XMS is built to pass security audits

XMS holds several clients' data in one product and will face ISO 27001, SOC 2 and client security audits. Every change in `frontend/`, `backend/`, `infra/` and `xms_mcp` is made audit-ready by construction. Load the `xms-security-first` skill before designing, coding or reviewing any change, and apply these rules without exception:

* Isolation is a data-layer property: every account-scoped table ships with forced row-level security and both policies in the same migration; ids from clients are asserted in-account; no optional account parameters, no header-driven tenancy, no `default` fallbacks.
* Authorisation is server-side only: every route declares its permission or a justified `@Public()`, the route-and-permission snapshot changes with it, portal and internal realms never cross, and the browser only mirrors the server's decision.
* Evidence is mandatory: every mutation writes its audit event in the same transaction; every guard decision, admin change, export, download and AI egress writes a security event; screens and actions write usage events without content.
* Egress is controlled: nothing leaves the boundary (email, connector, harness, export, log) without the account's settings and redaction; templates and exports can only reference client-visible view models.
* Inputs are hostile: DTO validation with whitelist, size limits, untrusted parsing, verified signatures, scanned files, downloads only after a clean scan.
* Secrets live only in Secrets Manager; infrastructure lives only in Terraform with least-privilege roles.
* Tests prove it: the tests in the skill's section 3 exist before merge; a pull request carries the completed security checklist; an unticked box blocks the merge.
* The forbidden patterns in the skill's section 5 (found in AIX) must not recur.

Full checklist, tests and evidence map: `.claude/skills/xms-security-first/SKILL.md` and `01-architecture/SECURITY-ASSURANCE.md`.
