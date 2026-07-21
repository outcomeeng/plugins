# Plan: eval-verification placeholder

This node and its harness child are declared placeholders: the opening declarations exist, and no decision records, assertions, tests, or implementation exist yet. Pending work:

- **Adapter-derived-evals ADR** — supersede `spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`: evals invoke the real runtime with the real installed plugin through the adapter contract provided by `spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler`, rather than materializing producer text into prompts. The producer-file/producer-section/producer-files resolution modes, the placeholder contract, and `--check` drift detection are compensations for not crossing the runtime boundary; the superseding decision removes the compensation layer.
- **Eval-harness vocabulary** — suite, case, trial, verdict, grading, trace policy, and run-record semantics land under `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/21-eval-harness.enabler` once the adapter-contract ADR exists.
- **Implementation cutover** — the shipped harness under `outcomeeng_evals/` and the governing specs under `spx/13-infrastructure.enabler/25-eval-harness.enabler` re-home into this subtree; the old node carries a relocation pointer in its `PLAN.md` and stays authoritative for the shipped harness until the cutover completes, after which it retires.
- **CLI surface** — an eval-CLI surface node is deferred pending the product-root projection; none exists until that projection lands.
- **Skills-update gate** — the python and test skills are updated before any harness implementation; implementation code in this subtree is blocked until that gate clears.
