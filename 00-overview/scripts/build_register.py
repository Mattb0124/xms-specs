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
PHASE_LABEL = {"F": "1 Foundations", "P": "2 Focused pilot", "O": "3 Operational replacement", "L": "4 Later releases"}

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
        })
    return out


def module_link(m: str) -> str:
    return MODULE_LINK.get(m, f"../02-modules/{m}/FUNCTIONAL-SPEC.md")


def write_matrix(reqs: list[dict]) -> None:
    lines: list[str] = []
    add = lines.append
    add("# Requirements Traceability Matrix: XMS Ticketing\n")
    add("**Status:** Draft\n**Owner:** Matt Brown\n**Last updated:** 2026-09-04\n"
        "**Source:** `Copy of DMS_Ticketing_System_Requirements.xlsx` (sheet `Requirements`, 110 rows). "
        "Machine-readable copies: [requirements.csv](./requirements.csv), [requirements.json](./requirements.json). "
        "Four XMS-added rows (prefix `XA`, category \"XMS additions\") cover the audit log and user analytics capability.\n"
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
    prio_count = collections.Counter(r["priority"] for r in reqs)
    add("## 2. Summary\n")
    add("| Phase | Must Have | Nice to Have |\n|---|---|---|")
    by_phase: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in reqs:
        by_phase[r["phase"]][r["priority"]] += 1
    for ph in sorted(by_phase):
        add(f"| {ph} | {by_phase[ph]['Must Have']} | {by_phase[ph]['Nice to Have']} |")
    add(f"| **Total** | **{prio_count['Must Have']}** | **{prio_count['Nice to Have']}** |\n")
    add("| Module spec | Rows | Must Have |\n|---|---|---|")
    by_mod: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in reqs:
        by_mod[r["module"]][r["priority"]] += 1
    for m, title in MODULE_TITLE.items():
        add(f"| [{title}]({module_link(m)}) | {sum(by_mod[m].values())} | {by_mod[m]['Must Have']} |")
    add("")
    add("## 3. Matrix by workbook category\n")
    current = None
    for r in reqs:
        if r["category"] != current:
            current = r["category"]
            add(f"\n### {current}\n")
            add("| ID | Requirement | Priority | Module spec | Phase | Acceptance notes (from workbook) |\n|---|---|---|---|---|---|")
        add(f"| {r['id']} | {r['requirement']} | {r['priority']} | [{MODULE_TITLE[r['module']]}]({module_link(r['module'])}) "
            f"| {r['phase']} | {r['description'].replace('|', '/')} |")
    add("\n## 4. Matrix by module spec\n")
    for m, title in MODULE_TITLE.items():
        add(f"\n### {title} (`{module_link(m).replace('../', '').rsplit('/', 1)[0]}/`)\n")
        add("| ID | Requirement | Priority | Phase |\n|---|---|---|---|")
        for r in reqs:
            if r["module"] == m:
                add(f"| {r['id']} | {r['requirement']} | {r['priority']} | {r['phase']} |")
    add("\n## 5. Maintenance rule\n\nThis file is generated from the workbook by "
        "`00-overview/scripts/build_register.py` (ADR-00 in the Decision Log). Edit the workbook or the "
        "`phase`/`module` mapping in the script, regenerate, and commit both; never hand-edit the tables, or the CSV "
        "and this page will diverge.\n")
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
