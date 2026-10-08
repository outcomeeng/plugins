# Issues: Eval verification

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## Three routed rules carry no evidence

[`spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md) and this node's assertions are routed, and the case-shape conformance rule, the producer-declaration compliance rule and the withheld-plugin eval have no evidence. The case format they constrain does not exist until the harness vocabulary lands in `21-eval-harness.enabler`.

**Settlement condition.** The harness vocabulary — suite, case, trial, verdict, grading and run record, the arm semantics (every skill eval matrix carries a no-skill baseline arm beside the prior and candidate versions, realizing the withheld-plugin invariant), the layered evidence model (routing, workflow conformance, behavioral quality, final-state assertions, cost) and multi-run aggregation and stability reporting — lands, and the three rules carry evidence. `knowledge/oe-skill-eval-brief.md` is background input for that vocabulary and carries no authority.

## The shipped harness has not crossed into this subtree

The shipped harness under `outcomeeng_evals/` and the specs under `spx/13-infrastructure.enabler/25-eval-harness.enabler` stay authoritative for it until its cutover, when they re-home into this subtree with the execution machinery consumed from the external component [`spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md) names. The shipped eval-evidence auditor `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-eval-evidence.enabler` aligns to the adapter-invoked coupling model in the same cutover; its producer-coupling verdict model is superseded by the adapter-derived decision and recorded in that node's `ISSUES.md`.

**Settlement condition.** The harness and the auditor move together: the cutover completes, the old node retires, and the auditor judges the coupling mode the harness produces.

## No eval CLI surface node exists

An eval CLI surface node is deferred behind the product-root projection.

**Settlement condition.** The projection lands and the surface node is authored.
