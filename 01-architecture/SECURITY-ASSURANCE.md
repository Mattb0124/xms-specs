# Security Assurance: built to pass audits

**Status:** Draft
**Owner:** Matt Brown
**Last updated:** 2026-09-05
**Related:** [Security & Tenancy](./SECURITY-AND-TENANCY.md), [Audit Log and User Analytics](./AUDIT-AND-ANALYTICS.md), [Data Model](./DATA-MODEL.md), [Platform & Operations](./PLATFORM-AND-OPERATIONS.md), [Test Strategy](../03-delivery/TEST-STRATEGY.md), [Thirty-Day Build](../03-delivery/THIRTY-DAY-BUILD.md), the `xms-security-first` skill (`.claude/skills/xms-security-first/SKILL.md`)
**Requirements covered:** XA-05 (security assurance), and the evidence side of TM-01, TM-12, TM-13, TM-14, CP-01, CP-02, AI-08, AI-10, AI-11, AI-12

Matt's direction (2026-09-05): the solution must be security tight and everything must be developed around passing security audits. This document is the assurance programme: which audits XMS must pass, the control catalogue mapped to them, the evidence each control produces automatically, the secure development gates that enforce the controls on every change, and the operating rhythm that keeps the evidence current.

---

## 1. The audits XMS is built for

| Audit | Why | What they will ask for |
|---|---|---|
| ISO 27001 (the operator's existing certification; the assessment's mitigation is "reuse existing ISO 27001 controls") | XMS becomes a certified system in the operator's scope | Statement of applicability coverage for the Annex A controls XMS touches, risk register entries, evidence of access control, logging, cryptography, supplier management, secure development |
| SOC 2 Type II (Security, Availability, Confidentiality) | Clients such as Brookfield ask for it | Control descriptions with evidence over a period: change management, logical access, monitoring, incident response, availability, data classification and handling |
| Client security questionnaires (SIG, CAIQ, bespoke; the Rio Tinto questionnaire in the workspace is the shape) | Every onboarding | Answers with pointers to evidence: isolation, encryption, retention, sub-processors, AI processing, breach notification |
| Penetration test (annual, plus after major changes) | Contractual and SOC 2 expectation | Scope, findings, remediation with retest |
| Internal architecture and code review (Juan, Security) | The isolation ruling (ADR-02) | Policies, guard, tests, this document |

## 2. Control catalogue with evidence

Each row: the control XMS implements, where it lives, the audit criteria it maps to (ISO 27001:2022 Annex A, SOC 2 trust services criteria, OWASP ASVS 4.0 level 2), and the evidence it produces without manual work.

### 2.1 Identity and access

| Control | Where | Maps to | Evidence |
|---|---|---|---|
| Internal users authenticate through the THG IdP via the XMS Clerk application; portal users through the account's IdP or MFA-protected local accounts | Security §2 | A.5.15, A.5.16, A.8.5; CC6.1, CC6.2; ASVS V2, V3 | Clerk configuration export; `auth.*` security events; invitation and acceptance events |
| One Principal resolved once per request with `authorizedParties`, 60-second skew, distinct audience for long-lived agent tokens | Security §2.2 | A.8.5; CC6.1; ASVS V3.5 | Guard unit tests; auth rejection suite report; `auth.token.rejected` events |
| Permission catalogue in code with transitive implications, global guard, route-and-permission snapshot | Security §3 | A.5.15, A.8.3; CC6.3; ASVS V4 | Snapshot file in the repository; failing build on drift |
| Account grants explicit, role assignments in PostgreSQL only, last-administrator protection | Accounts & Administration | A.5.18; CC6.3 | `admin.user.*` security events; quarterly access review export (§4) |
| API clients with scopes, hashed lookup, operator ownership, expiry | Security §2.3 | A.5.17; CC6.1 | `auth.apikey.*` events; key inventory export |
| Realm separation between portal and internal | Security §2.2 | A.8.3; CC6.1 | `authz.realm.denied` events; realm test suite |

### 2.2 Data isolation and protection

| Control | Where | Maps to | Evidence |
|---|---|---|---|
| Forced row-level security on every account-scoped table, session binding in one place, portal role revokes, no cross-account foreign keys | Data Model §3 | A.8.3, A.8.4; CC6.1, C1.1; ASVS V4.2 | Generated isolation suite report on every build; migration files; `authz.isolation.filtered` events |
| Dedicated isolation tier per account | Data Model §3 | A.8.3; C1.1 | Account record; Terraform module state |
| Encryption in transit (TLS 1.2+ at the ALB, TLS to RDS and S3) and at rest (RDS, S3 with KMS, Secrets Manager) | Platform §1 | A.8.24; CC6.7; ASVS V9 | Terraform state; AWS Config rules |
| Attachments: presigned POST with size and type limits, malware scan gating download, quarantine | Security §6 | A.8.7; CC6.8; ASVS V12 | Scan state on rows; `data.attachment.*` events; GuardDuty findings |
| Visibility: work notes as a separate table with no portal grant; typed client-visible view models for templates, exports and sync | Security §5 | A.8.3, A.5.12; C1.1 | Portal timeline view definition; compile-time checks; portal suite |
| Data classification and retention per stream and account DPA; offboarding with pseudonymisation and purge | Platform §7, Audit & Analytics §8 | A.5.12, A.5.34, A.8.10; C1.2, P (where applicable) | Retention jobs' audit events; offboarding step events; lifecycle rules in Terraform |
| Backups with point-in-time recovery, restore drills | Platform §6 | A.8.13; A1.2 | Drill runbook entries with dates |

### 2.3 Logging, monitoring and evidence

| Control | Where | Maps to | Evidence |
|---|---|---|---|
| Domain audit, security events and usage events, append-only, one envelope | Audit & Analytics | A.8.15, A.8.16; CC7.2; ASVS V7 | The tables themselves; Admin audit search; exports |
| Tamper evidence: nightly Parquet archive to Object Lock, chained digests, weekly verification | Audit & Analytics §6 | A.8.15; CC7.2 | `integrity.*` events; the digest files |
| Alarms on security signals (failed sign-ins, isolation probes, bad signatures, digest mismatch) | Audit & Analytics §7.3 | A.8.16; CC7.3 | CloudWatch alarm definitions; alarm history |
| Structured logs with request and trace ids, no content, no secrets | Platform §5 | A.8.15; CC7.2 | Log samples; secrets scan in the pipeline |

### 2.4 Secure development and change management

| Control | Where | Maps to | Evidence |
|---|---|---|---|
| Security definition of done on every change (the `xms-security-first` skill and the pull request checklist) | Skill §4 | A.8.25, A.8.28; CC8.1; ASVS V1 | Pull request history with completed checklists |
| Pipeline gates: lint, type-check, unit, integration, isolation suite, dependency audit, secrets scan, Terraform plan; no suppression flags | Test Strategy §5 | A.8.29, A.8.31; CC8.1 | Pipeline run history and artefacts |
| ZAP baseline on every dev deploy of the portal; annual penetration test | Test Strategy §2 | A.8.29; CC4.1 | ZAP reports; pen test reports and retests |
| Dependency management: single lockfile, audit in the gate, no known-vulnerable dependency merged | Platform §2 | A.8.8; CC7.1 | Audit reports |
| Infrastructure as code with least privilege and reviewed plans; no console changes | Platform §1 | A.8.9, A.8.32; CC8.1 | Terraform repository history; AWS CloudTrail for drift |
| Separation of environments; production deploys only from tagged releases | Platform §3 | A.8.31; CC8.1 | Pipeline configuration |

### 2.5 Third parties and AI processing

| Control | Where | Maps to | Evidence |
|---|---|---|---|
| Sub-processor register: AWS, Clerk, the Axel harness (Bedrock); no new vendors | Platform, ADR-03, ADR-04 | A.5.19, A.5.20, A.5.21; CC9.2 | Register maintained in this document's appendix |
| AI egress only through the adapter with per-account switch, opt-ins, redaction, audit; no training on client data; residency check | AI Integration, Security §8 | A.5.34, A.8.10; C1.1; P | `ai.*` events; AI settings on the account record; harness owners' written confirmations |
| Connector credentials in Secrets Manager, HMAC-verified webhooks, fixed egress IP, kill switches | Integration Patterns §5 | A.5.14, A.8.20; CC6.6, CC6.7 | Connector instance records; `abuse.webhook.*` events |
| Email: DKIM and SPF per sending identity, bounce handling, loop guard | Email Intake | A.5.14; CC6.6 | SES configuration in Terraform; `abuse.email.*` events |

### 2.6 Operations and resilience

| Control | Where | Maps to | Evidence |
|---|---|---|---|
| Availability and recovery objectives, Multi-AZ, DLQs, readiness checks | Platform §6 | A.8.14; A1.2, A1.3 | Uptime report from the ALB metrics; drill records |
| Runbooks for deploy, rollback, DLQ replay, email loop, kill switch, offboarding, secrets rotation, restore, isolation incident; rehearsed quarterly | Platform §8 | A.5.24 to A.5.28, A.8.13; CC7.4, CC7.5 | Runbook files with rehearsal dates; incident records |
| Incident response with client notification timelines per DPA | Platform §8 | A.5.26; CC7.4 | Incident template; the security dashboard |

## 3. Secure development lifecycle (how every change passes)

1. **Design.** The threat note (the five failures in the skill) is written before code; identity, isolation, egress and infrastructure changes are reviewed by Matt at design time.
2. **Build.** Controls first, then features: the policy, the permission, the events, the redaction; tests from the skill's section 3 exist before the code they prove.
3. **Gate.** The pipeline runs the isolation suite, the snapshot test, the auth rejection suite, dependency audit and secrets scan on every pull request; a red gate cannot be skipped.
4. **Review.** The pull request carries the completed security checklist; the stream owner reviews; Matt reviews the sensitive categories.
5. **Deploy.** Terraform plan reviewed; production only from a tagged release; migration dry-run against a snapshot.
6. **Verify.** ZAP on dev; alarms confirmed; the security dashboard checked after each release.
7. **Record.** Every step leaves the artefacts in §2; nothing is produced for the auditor by hand.

## 4. Operating rhythm

| Cadence | Activity | Output |
|---|---|---|
| Every pull request | Security checklist, gates | Checklist in the PR; pipeline artefacts |
| Every release | Security dashboard review, alarm check | Release note entry |
| Weekly | Digest verification job; DLQ and alarm review | `integrity.*` events; operations log |
| Monthly | Access review export (users, roles, grants, API clients, portal users per account), dependency review | Signed review record |
| Quarterly | Runbook rehearsal (one per quarter, all within the year), restore drill, retention job audit, sub-processor register review | Rehearsal records |
| Annually | Penetration test and retest, ISO internal audit contribution, questionnaire answer bank refresh | Reports |
| On every account onboarding | DPA register entry (AI allowed, residency, retention, isolation tier), questionnaire answered from the evidence map | Account record settings |

## 5. Questionnaire answer bank (the pointers)

| Typical question | Answer source |
|---|---|
| How is our data isolated from other clients? | Data Model §3, isolation suite report, the account's isolation tier |
| Who can access our data and how is it reviewed? | Security §2 and §3, the monthly access review export |
| Is data encrypted? | §2.2 encryption row, Terraform state |
| How are files scanned? | Security §6, scan-state evidence |
| Is our data used to train AI? | AI Integration §6, the harness owners' written confirmation, the account's AI switch and opt-ins |
| Where is data processed and stored? | Platform §1 region, the account's residency setting, the sub-processor register |
| How long is data retained and how is it deleted? | Platform §7, Audit & Analytics §8, offboarding events |
| How are changes tested and deployed? | §3, pipeline history |
| How would we be notified of a breach? | Platform §8 incident runbook, the DPA timeline |
| Can we get audit logs of activity on our data? | Audit & Analytics §7, account-owner audit view and export |

## 6. Sub-processor register

| Sub-processor | Purpose | Data | Controls |
|---|---|---|---|
| Amazon Web Services (us-east-1; other regions per residency) | Hosting, storage, queues, email, malware scanning, model inference through Bedrock | All | AWS DPA, encryption, IAM least privilege |
| Clerk | Identity for internal and portal users | Names, emails, authentication metadata | Clerk DPA, enterprise connections, MFA |
| The Axel harness (operator-run, `os-aixelerator-studio`, Bedrock in AWS) | AI suggestions and narrative | Redacted ticket and knowledge context for accounts with AI enabled | Adapter switch, redaction, audit, no-training confirmation |

## 7. What is deliberately not done

- No third-party analytics, error tracking or logging vendors (evidence stays in AWS and the product).
- No customer content in logs, telemetry, error reports or AI prompts beyond what the adapter redacts and the account allows.
- No production access by developers outside break-glass with a security event and a runbook.
- No control is "planned for later" if it protects isolation, visibility, realm, evidence or egress: those exist from the first migration and the first route, including in the one-month build.
