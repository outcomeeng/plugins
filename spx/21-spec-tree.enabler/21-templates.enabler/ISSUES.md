# Issues: Templates

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The lean PDR template describes no extension for normative-heavy decisions

The lean PDR template `src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.pdr.md` prescribes a four-section shape (opening statement, `## Rationale`, `## Product properties`, `## Verification`) and a one-to-two-sentence Rationale. A normative-heavy decision needs decision-body sections between the opening statement and `## Rationale` and a longer Rationale, and the template describes no extension for them. [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md), approved by `/audit-pdr` after the operator's content-preservation review, stands as a documented deviation.

**Settlement condition.** The template describes an extension for normative-heavy decisions, naming that PDR as the reference. The decision side of this entry is in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/ISSUES.md`.
