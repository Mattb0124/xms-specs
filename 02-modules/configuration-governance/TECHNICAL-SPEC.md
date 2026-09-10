# Technical Spec: Configuration Governance

**Status:** Draft, not yet verified in code
**Owner:** Matt Brown
**Last updated:** 2026-09-09
**Related:** [Functional Spec](./FUNCTIONAL-SPEC.md), [Data Model](../../01-architecture/DATA-MODEL.md), [Audit & Analytics](../../01-architecture/AUDIT-AND-ANALYTICS.md), [Accounts & Administration](../accounts-and-administration/TECHNICAL-SPEC.md), [Dashboards & Report Packs](../dashboard-and-reporting/TECHNICAL-SPEC.md)
**Requirements covered:** CG-01 to CG-04

---

## 1. What already exists

This module governs a store that is already built. `frontend` ships an account Configuration tab over six catalogs with an effective source, version history, a JSON body editor, and override or remove under `admin:config`. The backend carries the catalog config with versions.

What is missing is ownership, reason, effective date, staleness and change markers. This module adds those around the existing store rather than replacing it.

## 2. Data model

| Table | Holds |
|---|---|
| `op.config_parameters` | The CG-01 register: parameter key, scope (operator or account), plain-language description, owner, review cadence, last reviewed. One row per parameter the system reads |
| `op.config_changes` | CG-02: parameter, scope target, old value, new value, reason, effective date, actor, changed at. Append-only, raise-on-update-or-delete trigger |

The register is **operator scoped** and describes parameters. The per-account values stay where they already live, in the catalog store. A parameter overridden on twelve accounts is one register row, and the twelve values are in the config store, which is the open question the functional spec raises.

`op.config_changes` joins the append-only family with the same trigger pattern as `acct.audit_events`.

## 3. Registration is generated, not maintained

CG-01 says a parameter with no owner is visible as unowned. That only holds if the register is populated from the parameters themselves.

Every configurable parameter declares itself in `backend/src/contracts` alongside the permission catalog, and the register is derived from that declaration. A parameter added in code without a declaration fails the build, the same way an unknown permission key does and the same way a new account-scoped table missing from the isolation suite does.

This is the mechanism that stops the register rotting, and it is the reason the module is worth building rather than being a spreadsheet.

## 4. Change markers (CG-03)

A trend or scorecard line spanning a change renders a marker. The read model for any trend takes the window and returns the changes whose **effective date** falls inside it, alongside the series. The marker travels with the data rather than being fetched separately, so a chart cannot render without its markers by omission.

Effective date, not changed-at, is what decides marker placement. A threshold changed on the 9th and effective from the 1st marks the 1st.

## 5. Domain rules

- A change with no reason is refused. Not saved with an empty string.
- Reviewing without changing is recorded, so still-correct is distinguishable from never-looked-at.
- Staleness (CG-04) is evaluated by the worker against the cadence, surfacing to the owner and then to the support director.

## 6. Ordering

1. `op.config_parameters` with declaration in `src/contracts` and the build check, populated over the six existing catalogs. Most rows land unowned, and that list is the useful first output.
2. Ownership assignment. A people exercise the register enables, not a build step.
3. `op.config_changes` extending the existing version history with reason and effective date.
4. CG-03 markers, once there is change history to mark.
5. CG-04 cadence and staleness.

## 7. Testing

- A test that fails when a configurable parameter exists in code without a register declaration. Same shape as the isolation-suite schema check.
- A parameter with no owner renders as unowned rather than being absent.
- A change without a reason is refused.
- `op.config_changes` rejects update and delete at the database level.
- A trend spanning a change returns its marker with the series, placed on the effective date.

## 8. Risks

- **The register becomes a second source of truth.** It must describe parameters, never hold their values. Two places holding a threshold is worse than no register.
- **Declaration friction.** If declaring a parameter is tedious, people will avoid adding parameters or route around the mechanism. The declaration needs to be a few lines beside the parameter.
- **Markers in client-facing packs.** CG-03 marking a client deck invites a question that may be better handled internally. Open in the functional spec.
