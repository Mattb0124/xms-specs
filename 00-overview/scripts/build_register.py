"""Build the DMS requirements register and traceability matrix from the workbook.

Usage (from the xms repo root, any Python 3.10+ with openpyxl):

    python 00-overview/scripts/build_register.py "<path to DMS_Ticketing_System_Requirements.xlsx>"

Outputs (overwritten):
    00-overview/requirements.csv
    00-overview/requirements.json
    00-overview/REQUIREMENTS-TRACEABILITY.md

IDs are `<category prefix>-<nn>` in workbook order within each category, so they
are stable as long as rows are only appended. The module and phase mappings
below are the single place to change where a requirement lands; never hand-edit
the generated markdown (ADR-00 in the Decision Log).
"""
from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "00-overview"

PREFIX = {
    "Ticket Management": "TM",
    "Time Tracking & Budget": "TB",
    "Team Allocation & Capacity": "CAP",
    "Client Portal": "CP",
    "Email Intake": "EM",
    "Dashboard & Reporting": "DR",
    "ServiceNow Integration": "SN",
    "AI Functionality": "AI",
    "Data Migration": "DM",
    "Integrations": "INT",
}

CATEGORY_MODULE = {
    "Ticket Management": "ticket-management",
    "Time Tracking & Budget": "time-and-budget",
    "Team Allocation & Capacity": "capacity-and-allocation",
    "Client Portal": "client-portal",
    "Email Intake": "email-intake",
    "Dashboard & Reporting": "dashboard-and-reporting",
    "ServiceNow Integration": "servicenow-integration",
    "AI Functionality": "ai-functionality",
    "Data Migration": "data-migration",
    "Integrations": "integrations",
}

# Requirement name -> primary module when it differs from the category default.
MODULE_OVERRIDE = {
    "Multi-tenant data isolation": "accounts-and-administration",
    "Per-client business calendars and timezones": "accounts-and-administration",
    "Assignment groups": "accounts-and-administration",
    "Identity provider integration (internal)": "accounts-and-administration",
    "SSO via SAML / OIDC": "client-portal",
    "Knowledge base with per-client article visibility": "knowledge-base",
    "Similar-ticket retrieval and KB suggestion": "knowledge-base",
    "Auto-resolution of allowlisted request types": "knowledge-base",
    "CMDB / lightweight asset register": "knowledge-base",
    "Ticket templates": "knowledge-base",
    "Rate cards by client, contract and role": "time-and-budget",
    "Renewal and contract expiry alerting": "time-and-budget",
    "Finance / billing system export interface": "time-and-budget",
    "Budget burn anomaly detection": "ai-functionality",
    "Weekly report narrative generation": "ai-functionality",
    "Priority detection from email content": "ai-functionality",
}

MODULE_TITLE = {
    "accounts-and-administration": "Accounts & Administration",
    "ticket-management": "Ticket Management",
    "knowledge-base": "Solution Knowledge Base",
    "time-and-budget": "Time, Contracts & Budget",
    "capacity-and-allocation": "Capacity & Allocation",
    "client-portal": "Client Portal",
    "email-intake": "Email Intake & Outbound",
    "dashboard-and-reporting": "Dashboards & Report Packs",
    "servicenow-integration": "ServiceNow Sync",
    "ai-functionality": "Axel AI Functionality",
    "data-migration": "Data Migration & Cutover",
    "integrations": "Platform Integrations",
    "audit-and-analytics": "Audit Log & User Analytics",
    # Modules introduced by the functional RTM revision 3 (2026-09-09).
    "resolution-ladder": "Resolution Ladder & Routing",
    "measurement-and-calibration": "Measurement & Calibration",
    "account-health": "Account Health & Experience",
    "time-certification": "Time Certification",
    "collaboration-signal": "Collaboration Signal",
    "configuration-governance": "Configuration Governance",
    "outcomes": "Outcomes",
}

# F = Foundations, P = Focused pilot, O = Operational replacement, L = Later.
PHASE = {
    "Multi-tenant data isolation": "F", "Immutable audit trail": "F",
    "Identity provider integration (internal)": "F", "Strict data scoping": "F",
    "Attachments with virus scanning": "F", "Dedicated inbound address": "F",
    "Outbound email threading and branding": "F", "Assignment groups": "F",
    "Per-client AI disable switch": "F", "AI actions logged and attributable": "F",
    "No training on client data; DPA and residency compliance": "F",
    "Ticket types with distinct workflows": "P", "Configurable state machine": "P",
    "Priority / impact matrix": "P", "SLA engine": "P",
    "SLA clock pause with reason logging": "P", "Parent / child and related ticket linking": "P",
    "Public comments vs internal work notes": "P", "Full-text search and saved filters": "P",
    "Time entry at ticket level": "P", "Mandatory time entry before resolution": "P",
    "Activity type taxonomy": "P", "Billable classification": "P",
    "Contract object with multiple commercial models": "P",
    "Budget burn-down per client per period": "P", "Per-ticket hours breakdown": "P",
    "Resource roster": "P", "Ticket submission with dynamic forms": "P",
    "Ticket status tracking and comment threads": "P", "Attachment upload from portal": "P",
    "Budget / consumption visibility toggle": "P",
    "Knowledge base with per-client article visibility": "P",
    "Thread matching on message headers": "P", "Reply-to-update on existing tickets": "P",
    "Attachment and inline image extraction": "P", "Signature and quoted-reply stripping": "P",
    "Loop protection and auto-responder suppression": "P", "Unknown-sender quarantine queue": "P",
    "Internal operational view": "P", "Client-facing view": "P",
    "Export to Excel / CSV on all views": "P",
    "Auto-generated weekly report pack (PPTX / PDF)": "P", "One-way ingest mode": "P",
    "Auto-categorisation and priority suggestion": "P", "Long-thread summarisation": "P",
    "Similar-ticket retrieval and KB suggestion": "P", "Human-in-the-loop by default": "P",
    "Confidence thresholds with human fallback": "P", "Feedback capture on AI suggestions": "P",
    "Historical import from ServiceNow CSM": "P", "Duplicate detection with merge suggestion": "P",
    "Near-real-time dashboard refresh": "P",
    "Per-client business calendars and timezones": "O", "Grouping under project or change window": "O",
    "Ability to flag out-of-scope / over-budget work": "O",
    "Rate cards by client, contract and role": "O", "Forecast to period end": "O",
    "Threshold alerts": "O", "Adjustment and write-off workflow": "O",
    "After-hours and weekend flagging": "O", "Billing export": "O",
    "Available capacity calculation": "O", "Planned allocation per person per client per period": "O",
    "Planned vs actual variance reporting": "O", "Overallocation detection": "O",
    "Skills matrix with single-point-of-failure flagging": "O", "SSO via SAML / OIDC": "O",
    "CSAT survey on ticket close and every quarter end": "O",
    "Scheduled email delivery of report packs": "O", "Historical trend retention": "O",
    "Bidirectional sync with configurable field mapping": "O", "State machine translation": "O",
    "Loop prevention": "O", "Conflict resolution policy": "O", "Comment and work note sync": "O",
    "Attachment sync": "O", "Sync health monitoring and dead-letter queue": "O",
    "Multiple concurrent client instances": "O", "Draft response generation": "O",
    "Weekly report narrative generation": "O", "Time entry assistance": "O",
    "Contract and budget history import": "O", "Reconciliation report post-migration": "O",
    "Parallel run period": "O", "Finance / billing system export interface": "O",
    "Renewal and contract expiry alerting": "O", "Budget burn anomaly detection": "O",
    "PTO and holiday calendar": "L", "Forward demand from pipeline": "L", "Non-ticket time capture": "L",
}
PHASE_LABEL = {
    "F": "1 Foundations",
    "P": "2 Focused pilot",
    "O": "3 Operational replacement",
    "L": "4 Later releases",
    # Revision 3 intake. The functional RTM carries no phases and no priorities by
    # design, so every row it introduced lands here until it is triaged. This is a
    # holding pen, not a phase: see 00-overview/CLARIFICATIONS-NEEDED.md item C-02.
    "U": "0 Unscoped (revision 3 intake)",
}

# Requirements added by XMS beyond the workbook (Matt, 2026-09-04). They live in the
# register with their own prefix so they are traceable like every workbook row.
EXTRA_REQUIREMENTS = [
    ("Security audit log", "Every authentication, authorisation, administration, data-movement, abuse and AI decision is recorded as an append-only security event with actor, principal kind, request and trace ids; searchable and exportable.", "F"),
    ("User analytics", "Screen views, named actions, searches, Axel decisions and API requests are captured as usage events (no ticket, email or article content), per role and per account, with portal capture governed by an account setting.", "F"),
    ("Audit and usage reporting", "Admin screens for audit search over all three streams, a security dashboard and a usage dashboard (active users, feature adoption, core-loop funnel, knowledge gaps, Axel acceptance, portal deflection), with exports and an analyst SQL surface.", "P"),
    ("Security assurance and audit readiness", "Every change passes the security definition of done (isolation, visibility, realm, evidence, egress) with the required tests and a completed checklist; controls are mapped to ISO 27001, SOC 2 and OWASP ASVS with evidence produced automatically; monthly access reviews, quarterly runbook rehearsals, annual penetration test.", "F"),
    ("Tamper evidence and retention", "Append-only event tables, nightly Parquet archive to an Object Lock bucket, chained daily digests with weekly verification, retention per stream and per account DPA, pseudonymisation for erasure requests.", "O"),
]
EXTRA_CATEGORY = "XMS additions"
EXTRA_PREFIX = "XA"
EXTRA_MODULE = "audit-and-analytics"
MODULE_LINK = {"audit-and-analytics": "../01-architecture/AUDIT-AND-ANALYTICS.md"}

# Build status, established by inspecting `frontend` and `backend` on 2026-09-09:
# explicit requirement-id references in source, the feature modules and migrations
# present, the AI capability builders in backend/src/modules/ai/capabilities.ts,
# and the as-built layout notes in each application's CLAUDE.md.
#
# This is a read of the code, NOT an acceptance result. "Built" means the capability
# is present and wired, not that anyone has signed it off against its acceptance
# note, and not that it satisfies the revision 3 wording where revision 3 widened
# the row. Anything not listed here is "Not started".
BUILT = {
    "TM-01", "TM-02", "TM-03", "TM-04", "TM-05", "TM-06", "TM-07", "TM-08", "TM-09",
    "TM-10", "TM-11", "TM-12", "TM-13", "TM-14", "TM-15", "TM-16", "TM-18", "TM-19",
    "TM-21", "TM-25",
    "TB-01", "TB-03", "TB-16", "TB-04", "TB-05", "TB-06", "TB-07", "TB-08", "TB-09", "TB-10",
    "TB-11", "TB-12", "TB-13", "TB-14",
    "CAP-01", "CAP-02", "CAP-03", "CAP-04", "CAP-05", "CAP-06", "CAP-07", "CAP-08",
    "CP-02", "CP-03", "CP-04", "CP-05", "CP-06", "CP-07", "CP-08",
    "DR-01", "DR-02", "DR-03", "DR-04", "DR-05", "DR-06", "DR-07", "DR-08", "DR-09",
    "EM-01", "EM-02", "EM-03", "EM-04", "EM-05", "EM-06", "EM-07", "EM-08",
    "SN-01", "SN-02", "SN-03", "SN-04", "SN-05", "SN-06", "SN-07", "SN-08", "SN-09",
    "INT-01", "INT-02", "INT-03", "INT-05",
    "AI-08", "AI-09", "AI-10", "AI-11", "AI-12", "AI-13",
    "DM-01", "DM-02", "DM-03",
    "XA-01", "XA-02", "XA-03", "XA-04", "XA-05",
    "KB-01", "KB-02",
}

# Partly built, with the specific gap named. A partial with no named gap is a
# guess, so every entry here says what is missing.
PARTIAL = {
    # The five capability builders (classify, prioritise, duplicate, summarise,
    # draft_reply) are real code against a real SSE client, and the adapter commit
    # of 2026-09-07 claims AI-09 to AI-13 only. Three things stop these being built:
    # HARNESS_BASE_URL is optional and unset (.env.example says to leave it empty to
    # run without AI), NullHarnessClient throws HarnessUnavailableError, and the UI
    # entry points were deliberately removed. "Ask Axel and Draft with Axel are out.
    # Both opened a surface that is held, and a control that opens nothing is not a
    # control" (frontend c9c3225, 2026-09-08), then "Axel is out of the bar: the
    # panel behind it is held" (2026-09-09). The panel frame survives; the turn
    # surface behind it does not.
    "AI-01": "The classify and prioritise builders exist behind the adapter; the harness is unconfigured and the suggestion has no confirmed surface at intake",
    "AI-02": "The duplicate builder exists; unexercised while the harness is unconfigured, and no merge-proposal surface is reachable",
    "AI-03": "The summarise builder exists; Ask Axel was removed from the record and the bar on 2026-09-08 and 2026-09-09 because the turn surface is held",
    "AI-04": "The draft_reply builder exists; Draft with Axel was removed from the composer on 2026-09-08 because the surface behind it is held",
    "AI-07": "Retrieval and the solutions rail ship; ranking depends on embeddings the harness produces, and the harness is unconfigured",
    "TM-17": "Schema only; one reference in the backend and no authoring or apply surface",
    "TB-02": "The time-or-exemption gate ships. Revision 3 makes it composite (resolution code, notes completeness, article prompt, certification-sourced time), and that is not built",
    "TB-15": "Currency is carried on rate cards and amounts; no FX conversion for consolidated views",
    "CAP-09": "A rota exists in the backend; no desk surface, no coverage-gap detection, and it drives no routing",
    "AI-18": "The allowlist configuration exists; no end-to-end auto-resolution path",
    "KB-03": "The generalise flow with its findings sheet ships; the AI-23 cross-account consent gate that must block it does not exist",
    "KB-04": "Staleness and reuse signals exist on articles; the coverage report listing high-volume patterns with no article does not",
    "KB-05": "Author and improver are recorded per version; the per-person and per-account aggregation is not built",
    "EM-09": "The prioritise capability exists and is wired to tickets, not to email intake",
}

STATUS_ORDER = ["Built", "Partial", "Not started"]


def build_status(rid: str) -> tuple[str, str]:
    if rid in BUILT:
        return "Built", ""
    if rid in PARTIAL:
        return "Partial", PARTIAL[rid]
    return "Not started", ""


# Triage of the revision 3 intake (C-02), one category at a time.
#
# A row leaves phase "U" only when somebody has decided where it belongs, so
# this map is the decision and the register is its output. Anything not named
# here is still Unassessed and still unscheduled, which is the point of the
# holding pen.
#
# The rule applied, so the next category is triaged the same way: Must Have
# means ServiceNow cannot be switched off without it, which is what phase 3
# is for. Valuable work that the replacement does not depend on is Nice to
# Have in phase 4, however much anyone wants it.
#
# Ticket Management, triaged 2026-09-10 with Matt:
#
#   TM-21 participant record   3 / Must Have. DMS uses ServiceNow's watchers
#         and collaborators today, and TM-22 has nowhere to write an invitation
#         without it. A join table is far cheaper now than retrofitted.
#   TM-22 invite a collaborator 3 / Must Have. The day-in-the-life analysis
#         found people transferring a ticket to ask a question and never
#         getting it back. Parity, not improvement.
#   TM-23 ownership and teams  3 / Must Have. The owner half exists; the
#         audited change, the team construct and report authorship do not.
#         C-01 is still open and still blocks the routing half of this row:
#         ownership-driven routing contradicts the assignment-group routing
#         already shipped, and that is a decision, not a build.
#   TM-24 ranked queue          4 / Nice to Have. The queue works and sorts on
#         the tightest clock. A weighted stall score is an optimisation over
#         something that already does its job.
#   TM-26 outcome coverage      4 / Nice to Have. It cannot start before the
#         Outcomes module exists (OC-01), which is itself unbuilt and, as of
#         today, itself untriaged.
#   TM-27 container detection   3 / Nice to Have. Cheap now that TM-11 keeps a
#         real decision record: a threshold, a flag and a notification. The
#         replacement does not depend on it, since a consultant can still flag
#         a container case by hand.
#   TM-28 shift handover        4 / Nice to Have. An operating-model
#         improvement rather than parity: ServiceNow does not do this either,
#         and today the handover is verbal.
TRIAGE: dict[str, tuple[str, str]] = {
    "TM-21": ("O", "Must Have"),
    "TM-22": ("O", "Must Have"),
    "TM-23": ("O", "Must Have"),
    "TM-24": ("L", "Nice to Have"),
    "TM-26": ("L", "Nice to Have"),
    "TM-27": ("O", "Nice to Have"),
    "TM-28": ("L", "Nice to Have"),
}


# Requirements introduced by the functional RTM revision 3 (2026-09-09), which
# folds in the gap analysis, the day-in-the-life analysis and the operating model
# session. That document carries no phases and no priorities by design, so every
# row here lands in phase "U" as Unassessed until it is triaged; see
# CLARIFICATIONS-NEEDED.md item C-02. IDs are explicit rather than counted,
# because they continue the workbook's own numbering (TM stops at 19 in the
# workbook and resumes at 21 here) and must not shift when a row is inserted.
# (id, category, requirement, description, module)
NEW_REQUIREMENTS = [
    # --- Resolution ladder & routing -------------------------------------------------
    ("RL-01", "Resolution Ladder & Routing", "Path as a first-class ticket attribute", "Every ticket carries a classified path (0 client self-service, 1 front-desk resolved, 2 front-desk owned and engineer-validated, 3 engineer-owned) stamped at intake, and an actual path derived from the ownership and participant trail at close. Both are stored, neither overwrites the other, and both are reportable.", "resolution-ladder"),
    ("RL-02", "Resolution Ladder & Routing", "Historical profiling layer", "Closed historical records are profiled by client, request type, complexity, who resolved them, and whether resolution required credentialed access or genuine expertise. Queryable per client and per request type, and the classifier's prior from day one.", "resolution-ladder"),
    ("RL-03", "Resolution Ladder & Routing", "Path classification at intake", "Axel proposes a path from the profile and the request content, with confidence, subject to AI-08 and AI-09. The proposed path drives routing. A human can override, and the override is recorded against the proposal.", "resolution-ladder"),
    ("RL-04", "Resolution Ladder & Routing", "Credential-blocked action taxonomy", "Request types are marked where resolution requires client-side access or elevated permission. A marked type cannot classify to path 1 and routes to path 3 or path 0. The marking is maintained per client, since access varies by account.", "resolution-ladder"),
    ("RL-05", "Resolution Ladder & Routing", "Path 2 validation touch", "An engineer records a validation, certification or coordination touch on a ticket the agent still owns. The touch is a TM-21 participant event carrying a touch type, the assignee is unchanged, and the actual path resolves to 2 rather than 3.", "resolution-ladder"),
    ("RL-06", "Resolution Ladder & Routing", "Path 0 stays on platform", "A client resolving through self-service produces a record without a Hackett touch: what was asked, what was returned, and whether the experience satisfied. The record attaches to the account and feeds AH-03.", "resolution-ladder"),
    ("RL-07", "Resolution Ladder & Routing", "Path 0 fallback capture", "A self-service attempt abandoned into a raised ticket links to that attempt, and fallback rate is reportable by request type and account.", "resolution-ladder"),
    ("RL-08", "Resolution Ladder & Routing", "Guided resolution for the front desk", "Where the profile holds a known-good path, Axel walks a non-technical resolver through it step by step against the current corpus. Where the profile says expertise or access is required, Axel proposes path 2 or path 3 instead of guidance.", "resolution-ladder"),
    ("RL-09", "Resolution Ladder & Routing", "Self-service candidate surfacing", "Request types resolved repeatedly at path 1 without engineer involvement surface as path-0 candidates, ranked by volume and consistency of resolution, on a surface the service desk lead owns.", "resolution-ladder"),
    # --- Measurement & calibration ---------------------------------------------------
    ("MC-01", "Measurement & Calibration", "Intake mix by path", "The share of intake landing at each of the four paths reports per account, per period, with trend, and rolls up to the portfolio.", "measurement-and-calibration"),
    ("MC-02", "Measurement & Calibration", "Front-desk resolution rate, paths 1 and 2", "Computed over tickets whose classified path was 1 or 2. A ticket classified 3 is absent from the denominator regardless of outcome, and no configuration can move it in. Reported at team and account level only; no screen, export or report resolves it to an individual.", "measurement-and-calibration"),
    ("MC-03", "Measurement & Calibration", "Engineer resolution rate, path 3", "Computed over tickets whose classified path was 3, reported at account and practice level only; no screen, export or report resolves it to an individual. Individual coaching signal comes from MC-07 cause tags and CL-04.", "measurement-and-calibration"),
    ("MC-04", "Measurement & Calibration", "Automatic misroute detection", "Where classified path and actual path disagree, a misroute is raised without anyone reporting it, and its direction is derived from the ownership trail.", "measurement-and-calibration"),
    ("MC-05", "Measurement & Calibration", "Under-routing and over-routing reported separately", "Under-routing (classified low, escalated) and over-routing (classified high, resolvable at the front desk) report as distinct rates, never as one accuracy figure.", "measurement-and-calibration"),
    ("MC-06", "Measurement & Calibration", "First-move-to-resolver measure", "First-contact resolution is defined and computed as the ticket reaching its final resolver on the first move, not as the service desk having solved it. The legacy first-level figure remains available during transition and is labelled as such.", "measurement-and-calibration"),
    ("MC-07", "Measurement & Calibration", "Misroute review queue with cause tagging", "Misroutes queue for the technical manager on a weekly cadence. Each is tagged model was wrong or person was wrong with a short reason. Unreviewed misroutes age visibly and surface to the support director past a configured age.", "measurement-and-calibration"),
    ("MC-08", "Measurement & Calibration", "Tags feed classifier improvement", "Cause tags are retained as labelled training signal, are reportable by cause, account and manager, and a model-was-wrong volume trend is visible beside the classifier's accuracy.", "measurement-and-calibration"),
    ("MC-09", "Measurement & Calibration", "Tag sampling by the support director", "The director can sample a manager's tags, record agreement or disagreement per sampled item, and see disagreement rate per manager. Sampling is visible to the manager.", "measurement-and-calibration"),
    ("MC-10", "Measurement & Calibration", "Cross-manager variance view", "Calibration quality, ladder mix, misroute rate and certification completeness compare between managers and between service desk teams, not only within accounts, on a surface the support director and service desk lead own.", "measurement-and-calibration"),
    # --- Account health & experience -------------------------------------------------
    ("AH-01", "Account Health & Experience", "Continuous account activity record", "Every touch on an account, any path, any shift, any person, any reporting line, lands in one account-level record the account owner sees without running a report, including work done by people who do not report to them.", "account-health"),
    ("AH-02", "Account Health & Experience", "Patterns, not a feed", "The account view surfaces recurring requests, repeated themes, commitments made to the client and precedents set, as patterns over a rolling window, not only as a chronological list.", "account-health"),
    ("AH-03", "Account Health & Experience", "Readiness trajectory", "A per-account trajectory composed of front-desk share, path-0 volume and fallback rate, profile maturity and knowledge coverage, calibrated against that account's own historical mix rather than a global target. Rising front-desk share reads as readiness, not as risk.", "account-health"),
    ("AH-04", "Account Health & Experience", "Experience trajectory", "A per-account trajectory composed of CSAT, responsiveness, expectation-management signal and perception notes. No surface renders AH-03 without AH-04 beside it.", "account-health"),
    ("AH-05", "Account Health & Experience", "Ranked account surface", "The CSM, the technical manager, the CSM lead and the director land on accounts ranked by attention need, computed server-side from health movement, exposure, consumption position and open divergences, never on an alphabetical or portfolio-order list.", "account-health"),
    ("AH-06", "Account Health & Experience", "Flexible perception capture", "Meeting transcripts, forwarded emails, typed notes and voice notes attach to the account record, are attributable and timestamped, are searchable, and feed AH-04. Voice notes transcribe.", "account-health"),
    ("AH-07", "Account Health & Experience", "Crystallised prior at cutover", "An account can be seeded with a dated starting assessment (owner's read of health, known fragility, key relationships, continuity risk) recorded as a stated prior. Later movement renders against the prior rather than against an empty history, and the prior remains readable and attributable.", "account-health"),
    ("AH-08", "Account Health & Experience", "Service-line seam", "The account-health object holds more than one service line. Support is the only line populated at launch; adding a second requires configuration, not schema change, and no surface hard-codes support as the only line.", "account-health"),
    ("AH-09", "Account Health & Experience", "Account touch cadence", "Direct account conversations log against the account with date and participant. Rolling coverage per account is visible, a per-account target interval is configurable, and accounts past their interval surface on AH-05.", "account-health"),
    # --- Time certification ----------------------------------------------------------
    ("TC-01", "Time Certification", "Daily certification flow", "Every role from agent to director completes a card-based end-of-day wrap-up in under a minute. It is available on any device and does not require opening a ticket.", "time-certification"),
    ("TC-02", "Time Certification", "System-proposed activity", "The first card proposes the day's activities from ticket, comment, time-entry and calendar signals for confirmation. The person confirms, removes or corrects; nothing is entered from a blank screen.", "time-certification"),
    ("TC-03", "Time Certification", "Off-system capture by text or voice", "One prompt asks whether anything else happened, answerable by typing or by speaking. Spoken input is transcribed into a candidate entry the person confirms.", "time-certification"),
    ("TC-04", "Time Certification", "Effort estimation against placeholders", "Each confirmed activity gets one card for effort. Duration fields show a placeholder and are never pre-filled with a computed actual; the person supplies the figure.", "time-certification"),
    ("TC-05", "Time Certification", "Catch-all bucket", "An other bucket accepts effort without forcing a ticket, an account or an activity type, so no one is blocked from completing the wrap-up.", "time-certification"),
    ("TC-06", "Time Certification", "Other-bucket guardrail, weekly", "The size of other is policed weekly, never daily. Crossing a role-configurable threshold raises to the person and their manager, and the threshold and its owner appear in the CG-01 register.", "time-certification"),
    ("TC-07", "Time Certification", "Completeness tracking, not content grading", "A missed evening is permitted; the next login shows outstanding wrap-ups. Completeness is reportable per person and per period and may drive enforcement. No report, screen or export renders certification magnitude as a performance measure of a person, and this is enforced rather than conventional.", "time-certification"),
    # --- Collaboration signal --------------------------------------------------------
    ("CL-01", "Collaboration Signal", "Closure grading of collaborators", "At closure the ticket owner grades each TM-21 participant on a short scale with optional comment. Skipping is permitted and the skip rate is reportable.", "collaboration-signal"),
    ("CL-02", "Collaboration Signal", "CSM grading from client-relayed feedback", "A CSM records feedback about a named person as relayed from the client, attributed to the client source and dated, feeding the client side of CL-04.", "collaboration-signal"),
    ("CL-03", "Collaboration Signal", "Weekly collaboration digest", "Once a week a person is shown who they worked with and invited to comment. It is skippable, takes under a minute, and never chases.", "collaboration-signal"),
    ("CL-04", "Collaboration Signal", "Peer-and-client quadrant view", "Peer signal renders against client satisfaction in four quadrants per person and per account. Client satisfaction governs where the two disagree, and the disagreement is itself the reported signal.", "collaboration-signal"),
    ("CL-05", "Collaboration Signal", "Asymmetric visibility", "Positive feedback is attributable and visible to its subject. Concerns are aggregated and anonymised, never rendered attributably, and are withheld from display until a configured minimum contributor count is reached. No interface, export or audit view can resolve an anonymised concern to its author.", "collaboration-signal"),
    # --- Configuration governance ----------------------------------------------------
    ("CG-01", "Configuration Governance", "Configuration register with named owners", "Every configurable parameter appears in one register with a named owner and a plain-language description of what it affects: path rules and credential markings, classifier and queue weights, all thresholds, the TC-06 guardrail, activity and outcome taxonomies, auto-resolution allowlists, consent flags, CL-05 aggregation minimums, and coverage floors. A parameter with no owner is visible as unowned.", "configuration-governance"),
    ("CG-02", "Configuration Governance", "Audited change with reason and effective date", "Changing a parameter records who, when, old value, new value, a reason and an effective date. Prior values remain readable, and no interface edits or deletes the history.", "configuration-governance"),
    ("CG-03", "Configuration Governance", "Change visible where it moves a number", "A trend or scorecard line spanning a configuration change renders a marker for that change, so a step is never read as behaviour when it was a setting.", "configuration-governance"),
    ("CG-04", "Configuration Governance", "Review cadence and staleness", "Each parameter carries a review cadence; parameters past it surface to their owner and, unactioned, to the support director.", "configuration-governance"),
    # --- Outcomes --------------------------------------------------------------------
    ("OC-01", "Outcomes", "Outcome object above the ticket", "An outcome carries name, stated business result, owner, period, status, type, client visibility, linked tickets and linked contract. The type taxonomy is configurable per client from a maintained default list, each type carrying a default client-visibility setting that can be overridden per instance and is audited when it is.", "outcomes"),
    ("OC-02", "Outcomes", "Outcome-framed client reporting", "The client-facing report leads on business result with tickets and hours as supporting evidence, and shows only client-visible outcome types.", "outcomes"),
    # --- Solution knowledge base -----------------------------------------------------
    ("KB-01", "Solution Knowledge Base", "Authoring, lifecycle, ownership, versioning", "An article moves draft to review to published to retired, has a named owner, and prior versions remain readable.", "knowledge-base"),
    ("KB-02", "Solution Knowledge Base", "Candidate queue and promotion", "A candidate submitted at resolution appears in the queue and can be promoted, merged, or rejected with a reportable reason.", "knowledge-base"),
    ("KB-03", "Solution Knowledge Base", "Client-to-global promotion with sanitisation", "Promoting to global forces a review for client identifiers and configuration detail, and is blocked unless the source account has explicitly opted in to cross-account contribution (AI-23).", "knowledge-base"),
    ("KB-04", "Solution Knowledge Base", "Article health and coverage", "Each article shows reuse count and last-validated date, stale articles flag against the review cadence, and a report lists high-volume patterns with no article.", "knowledge-base"),
    ("KB-05", "Solution Knowledge Base", "Contribution attribution", "Author and improver are recorded per version and aggregate per person and per account.", "knowledge-base"),
    ("AI-23", "Solution Knowledge Base", "Two-scope knowledge contribution consent", "Contribution within the originating account is on by default and can be switched off per account. Contribution across accounts is off by default and requires explicit opt-in recorded in account configuration. Both are enforced at the data layer, honoured by KB-02, KB-03, AI-07, RL-08 and any historical backfill, and independent of the AI-11 processing switch.", "knowledge-base"),
    # --- Ticket management -----------------------------------------------------------
    ("TM-21", "Ticket Management", "Ticket participant record", "People appear on a ticket in roles other than assignee, with joined and left timestamps and who invited them; contributor count is queryable.", "ticket-management"),
    ("TM-22", "Ticket Management", "Invite a collaborator without transferring ownership", "A named person or skill group is invited, accepts or declines, is notified, and the assignee is unchanged throughout.", "ticket-management"),
    ("TM-23", "Ticket Management", "Account ownership and team construct", "Every account has exactly one named primary owner; changing it is audited; teams group accounts and people; ownership drives default routing and report authorship.", "accounts-and-administration"),
    ("TM-24", "Ticket Management", "Ranked work queue with stall weighting", "The landing queue orders by a server-computed score over client priority, severity, breach proximity, shift context and, weighted at least as heavily, time since last movement, age against expected duration for that ticket type, and time since last client contact. An administrator changes a weight and the order changes.", "ticket-management"),
    ("TM-25", "Ticket Management", "Default active-work view", "Resolved, closed and transferred tickets are absent from the default view and require a deliberate action to reach.", "ticket-management"),
    ("TM-26", "Ticket Management", "Ticket-to-outcome association with coverage measure", "A ticket can be attached to and detached from an outcome, and the outcome lists it. Linkage coverage, the share of tickets and of delivered hours carrying an outcome, is reportable per account, per engineer and per period, and accounts below a configured coverage floor surface to the account owner and the support director.", "ticket-management"),
    ("TM-27", "Ticket Management", "Container-case detection", "A ticket crossing the configured time-entry, elapsed-day or effort threshold raises TM-11 and notifies the account owner.", "ticket-management"),
    ("TM-28", "Ticket Management", "Shift handover", "At the close of a coverage window the outgoing owner produces a handover for the incoming one covering open work, items at risk of breach, commitments made to clients, and anything awaiting a third party. The incoming owner acknowledges it. Unacknowledged handovers are visible to the technical manager. Drafted by Axel (AI-25) and editable before it is passed; retained and searchable against the ticket.", "ticket-management"),
    # --- Time, contracts & budget ----------------------------------------------------
    ("TB-17", "Time Tracking & Budget", "Commercial model as a configurable type", "A new model type is added with its own consumption rules and the finance export still resolves it to hours and value with no interface change.", "time-and-budget"),
    # --- Capacity & allocation -------------------------------------------------------
    ("CAP-11", "Team Allocation & Capacity", "Account concentration detection with owned response", "Any account where one person holds more than the configured share of delivered hours in a rolling window raises an alert to the technical manager, escalating to the support director if unactioned within a configured period. The alert carries a state (acknowledged, mitigation planned, accepted as risk, resolved) with the reason recorded, and open alerts are visible on the portfolio and AH-05 views.", "capacity-and-allocation"),
    ("CAP-12", "Team Allocation & Capacity", "Absence-aware routing", "A person recorded as absent cannot be assigned a ticket, invited as a collaborator, or placed on the triage rota for that period without an explicit recorded override. Work already assigned at the point absence begins is surfaced for reassignment, and the ranked queue excludes them from scoring.", "capacity-and-allocation"),
    # --- Dashboards & report packs ---------------------------------------------------
    ("DR-12", "Dashboard & Reporting", "Client self-service measure", "The client sees how many issues they resolved without raising a ticket, and which articles they used.", "dashboard-and-reporting"),
    ("DR-13", "Dashboard & Reporting", "Collaboration and contribution measures", "Median time to first response, contributors per ticket, and share of tickets first touched by a principal engineer. The first-touch figure reports beside MC-05 over-routing, since over-routing is its mechanism.", "dashboard-and-reporting"),
    ("DR-14", "Dashboard & Reporting", "Renewal exposure view", "For every contract approaching expiry, one view shows contracted value, delivered value, forecast consumption at expiry, the resulting undelivered exposure, and the account's health score, sortable by exposure and filterable by expiry window. Exposure totals roll up to the portfolio.", "dashboard-and-reporting"),
    ("DR-15", "Dashboard & Reporting", "Portfolio scorecard surface", "The scorecard exists in the product, read quarterly, organised as four movements: is the ladder shifting downward, is the classifier getting braver safely, is knowledge compounding, is the conversation flipping from effort to value. Each line carries baseline, current, direction and target, and names the decision it informs. Ticket volume and MTTR cannot be added to it.", "dashboard-and-reporting"),
    ("DR-16", "Dashboard & Reporting", "Capture-rate gate on the scorecard", "Time-capture rate renders at the top of DR-15. Every value-derived line displays as provisional, and is labelled as such on screen and in export, until capture rate passes its configured threshold.", "dashboard-and-reporting"),
    ("DR-17", "Dashboard & Reporting", "Two pillar scorecards from one dataset", "An operational scoping for the support director and a commercial scoping for the customer experience lead render from the same underlying data with no divergent figures; a number appearing on both is identical.", "dashboard-and-reporting"),
    ("DR-18", "Dashboard & Reporting", "Service desk team view", "Team resolution rate within paths 1 and 2, early-escalation pattern, path mix and certification completeness, on a surface the service desk lead owns. Per-person detail is limited to MC-07 cause tags and CL-04; the team rate does not decompose to an individual figure.", "dashboard-and-reporting"),
    # --- Axel AI ---------------------------------------------------------------------
    ("AI-21", "AI Functionality", "Confidence persisted and calibratable", "The confidence value is stored, and a calibration report compares stated confidence against realised outcome.", "ai-functionality"),
    ("AI-22", "AI Functionality", "Draft outcome capture", "Within the AI-13 stream, a draft records sent unchanged, light edit, heavy edit or discarded, with edit distance.", "ai-functionality"),
    ("AI-24", "AI Functionality", "Resolution note drafting", "On close, Axel drafts resolution notes from the thread, work notes and time entries, and proposes a resolution code. The draft satisfies the TB-02 completeness rule only once a human confirms it. Confirmation without edit is recorded distinctly from edited confirmation, and the unedited rate is reported.", "ai-functionality"),
    ("AI-25", "AI Functionality", "Shift handover summary", "At the end of a coverage window Axel drafts the TM-28 handover (open work, breach risk, client commitments, third-party waits) from ticket state and activity, editable before it is passed.", "ai-functionality"),
    # --- Data migration & cutover ----------------------------------------------------
    ("DM-05", "Data Migration", "Knowledge corpus backfill", "The existing knowledge corpus is imported and is governed by the AI-23 two-scope contribution rule; nothing crosses an account boundary without recorded opt-in.", "data-migration"),
]



def load(xlsx: Path) -> list[dict]:
    ws = openpyxl.load_workbook(xlsx, data_only=True)["Requirements"]
    rows = [r for r in ws.iter_rows(values_only=True) if r[0] and r[0] != "Category"]
    counters: collections.Counter = collections.Counter()
    out = []
    for cat, req, desc, prio in rows:
        counters[cat] += 1
        name = req.strip()
        module = MODULE_OVERRIDE.get(name, CATEGORY_MODULE[cat])
        prio = prio.strip()
        phase = PHASE.get(name, "L" if prio.startswith("Nice") else "O")
        out.append({
            "id": f"{PREFIX[cat]}-{counters[cat]:02d}",
            "category": cat,
            "requirement": name,
            "description": (desc or "").strip(),
            "priority": prio,
            "module": module,
            "phase": PHASE_LABEL[phase],
            "source": "Workbook",
            "status": build_status(f"{PREFIX[cat]}-{counters[cat]:02d}")[0],
            "gap": build_status(f"{PREFIX[cat]}-{counters[cat]:02d}")[1],
        })
    for i, (name, desc, phase) in enumerate(EXTRA_REQUIREMENTS, 1):
        out.append({
            "id": f"{EXTRA_PREFIX}-{i:02d}",
            "category": EXTRA_CATEGORY,
            "requirement": name,
            "description": desc,
            "priority": "Must Have",
            "module": EXTRA_MODULE,
            "phase": PHASE_LABEL[phase],
            "source": "XMS addition",
            "status": build_status(f"{EXTRA_PREFIX}-{i:02d}")[0],
            "gap": build_status(f"{EXTRA_PREFIX}-{i:02d}")[1],
        })
    for rid, cat, name, desc, module in NEW_REQUIREMENTS:
        phase_key, priority = TRIAGE.get(rid, ("U", "Unassessed"))
        out.append({
            "id": rid,
            "category": cat,
            "requirement": name,
            "description": desc,
            "priority": priority,
            "module": module,
            "phase": PHASE_LABEL[phase_key],
            "source": "Functional RTM r3",
            "status": build_status(rid)[0],
            "gap": build_status(rid)[1],
        })
    # Group by category without disturbing order inside a category: the workbook rows
    # keep workbook order, revision 3 rows join the end of their category block, and a
    # category revision 3 introduced appears after every category that existed before.
    seen: dict[str, int] = {}
    for r in out:
        seen.setdefault(r["category"], len(seen))
    out.sort(key=lambda r: seen[r["category"]])
    return out


def module_link(m: str) -> str:
    return MODULE_LINK.get(m, f"../02-modules/{m}/FUNCTIONAL-SPEC.md")


def write_matrix(reqs: list[dict]) -> None:
    lines: list[str] = []
    add = lines.append
    add("# Requirements Traceability Matrix: XMS Ticketing\n")
    add("**Status:** Draft\n**Owner:** Matt Brown\n**Last updated:** 2026-09-09\n"
        "**Sources:** `Copy of DMS_Ticketing_System_Requirements.xlsx` (sheet `Requirements`, 110 rows); five "
        "XMS-added rows (prefix `XA`) covering the audit log, user analytics and assurance capability; and the "
        "functional RTM revision 3 of 2026-09-09, which folds in the gap analysis, the day-in-the-life analysis and "
        "the operating model session. The `source` column on every row says which. Machine-readable copies: "
        "[requirements.csv](./requirements.csv), [requirements.json](./requirements.json).\n"
        "**Open items:** [Clarifications needed](./CLARIFICATIONS-NEEDED.md) carries the questions that block rows "
        "in this register, including the TM-08 routing conflict and the triage of every revision 3 row.\n"
        "**Related:** [Product Vision](./PRODUCT-VISION.md), [Roadmap](../03-delivery/ROADMAP.md), "
        "[Architecture](../01-architecture/ARCHITECTURE.md)\n\n---\n")
    add("## 1. How to read this matrix\n")
    add("Every workbook row has a stable ID (`<category prefix>-<nn>`, numbered in workbook order within its "
        "category). Each row maps to exactly one primary module spec under `02-modules/` and to one delivery phase "
        "from the [Roadmap](../03-delivery/ROADMAP.md). Secondary modules are named in the module specs themselves. "
        "The workbook this matrix was generated from carries 110 rows (90 Must Have, 20 Nice to Have); the "
        "assessment deck of 2026-09-03 cites 111 items and 75 Must Have after a reprioritisation pass that is not in "
        "this copy. Treat the deck's 75 as the pilot-scoping source and this matrix as the full target register; the "
        "reconciliation is an open item in the [Decision Log](./DECISION-LOG.md).\n")
    add("Phases: **1 Foundations** (auth, isolation, pipeline, monitoring, email infrastructure), **2 Focused pilot** "
        "(internal beta, no external clients, no Brookfield production traffic), **3 Operational replacement** "
        "(ServiceNow can be switched off), **4 Later releases** (incremental).\n")
    add("**0 Unscoped (revision 3 intake)** is not a phase, it is a holding pen. The functional RTM carries no "
        "phases and no priorities by design, so every row it introduced sits there as Unassessed until it is "
        "triaged into a real phase. A row left there is not scheduled and is not in anyone's plan, which is the "
        "point: see [Clarifications needed](./CLARIFICATIONS-NEEDED.md) item C-02.\n")
    prio_count = collections.Counter(r["priority"] for r in reqs)
    add("## 2. Summary\n")
    add("| Phase | Must Have | Nice to Have | Unassessed |\n|---|---|---|---|")
    by_phase: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in reqs:
        by_phase[r["phase"]][r["priority"]] += 1
    for ph in sorted(by_phase):
        add(f"| {ph} | {by_phase[ph]['Must Have']} | {by_phase[ph]['Nice to Have']} | {by_phase[ph]['Unassessed']} |")
    add(f"| **Total** | **{prio_count['Must Have']}** | **{prio_count['Nice to Have']}** "
        f"| **{prio_count['Unassessed']}** |\n")
    add("| Module spec | Rows | Must Have | Unassessed |\n|---|---|---|---|")
    by_mod: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in reqs:
        by_mod[r["module"]][r["priority"]] += 1
    for m, title in MODULE_TITLE.items():
        add(f"| [{title}]({module_link(m)}) | {sum(by_mod[m].values())} | {by_mod[m]['Must Have']} "
            f"| {by_mod[m]['Unassessed']} |")
    add("")
    add("### Build status\n")
    add("Established by inspecting `frontend` and `backend` on 2026-09-09: requirement-id references in source, "
        "the feature modules and migrations present, the AI capability builders, and the as-built notes in each "
        "application's `CLAUDE.md`. **This is a read of the code, not an acceptance result.** Built means the "
        "capability is present and wired, not that it has been signed off against its acceptance note, and not "
        "that it satisfies the revision 3 wording where revision 3 widened the row. Every Partial names its gap.\n")
    st_count = collections.Counter(r["status"] for r in reqs)
    add("| Status | Rows |\n|---|---|")
    for s in STATUS_ORDER:
        add(f"| {s} | {st_count[s]} |")
    add(f"| **Total** | **{len(reqs)}** |\n")
    add("| Module spec | Built | Partial | Not started |\n|---|---|---|---|")
    by_mod_status: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in reqs:
        by_mod_status[r["module"]][r["status"]] += 1
    for m, title in MODULE_TITLE.items():
        c = by_mod_status[m]
        add(f"| [{title}]({module_link(m)}) | {c['Built']} | {c['Partial']} | {c['Not started']} |")
    add("")
    add("**Partly built, with the gap named:**\n")
    add("| ID | Requirement | What is missing |\n|---|---|---|")
    for r in reqs:
        if r["status"] == "Partial":
            add(f"| {r['id']} | {r['requirement']} | {r['gap']} |")
    add("")
    add("## 3. Matrix by category\n")
    current = None
    for r in reqs:
        if r["category"] != current:
            current = r["category"]
            add(f"\n### {current}\n")
            add("| ID | Requirement | Status | Priority | Module spec | Phase | Source | Acceptance notes |\n"
                "|---|---|---|---|---|---|---|---|")
        add(f"| {r['id']} | {r['requirement']} | {r['status']} | {r['priority']} "
            f"| [{MODULE_TITLE[r['module']]}]({module_link(r['module'])}) "
            f"| {r['phase']} | {r['source']} | {r['description'].replace('|', '/')} |")
    add("\n## 4. Matrix by module spec\n")
    for m, title in MODULE_TITLE.items():
        add(f"\n### {title} (`{module_link(m).replace('../', '').rsplit('/', 1)[0]}/`)\n")
        add("| ID | Requirement | Status | Priority | Phase | Source |\n|---|---|---|---|---|---|")
        for r in reqs:
            if r["module"] == m:
                add(f"| {r['id']} | {r['requirement']} | {r['status']} | {r['priority']} | {r['phase']} "
                    f"| {r['source']} |")
    add("\n## 5. Maintenance rule\n\nThis file is generated by `00-overview/scripts/build_register.py` (ADR-00 in "
        "the Decision Log) from three sources: the workbook, the `EXTRA_REQUIREMENTS` block and the "
        "`NEW_REQUIREMENTS` block. Edit the workbook or the relevant block in the script, regenerate, and commit "
        "the script and all three outputs together; never hand-edit the tables, or the CSV and this page will "
        "diverge.\n\nRegenerate with:\n\n```\npy 00-overview/scripts/build_register.py \"<path to "
        "Copy of DMS_Ticketing_System_Requirements.xlsx>\"\n```\n")
    (OUT / "REQUIREMENTS-TRACEABILITY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    reqs = load(Path(sys.argv[1]))
    with (OUT / "requirements.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(reqs[0].keys()))
        writer.writeheader()
        writer.writerows(reqs)
    (OUT / "requirements.json").write_text(json.dumps(reqs, indent=2), encoding="utf-8")
    write_matrix(reqs)
    print(f"{len(reqs)} requirements written")


if __name__ == "__main__":
    main()
