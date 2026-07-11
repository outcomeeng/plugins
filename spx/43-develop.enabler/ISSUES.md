# Issues: Develop Plugin

Current develop-plugin follow-ups. Coordination note; not spec truth.

## 1. Audit-skill skeleton sweep

The canonical auditor shape lives in `src/plugins/develop/skills/skill-standards/references/auditor-skeleton.md`: verdict-shaped `<objective>`, `<audit_workflow>`, `<verdict_format>`, `<failure_modes>`, soundness `<success_criteria>`, and no `<quick_start>`.

Open work: sweep the remaining `audit-*` skills onto that skeleton. Keep the post-collapse composition exception: generic composing auditors that invoke language audits require `Skill` in `allowed-tools`.

Before starting, reconcile this work with:

- `spx/21-spec-tree.enabler/32-decisions.enabler/ISSUES.md` for the artifact-type auditor family.
- `spx/21-spec-tree.enabler/16-verification.enabler/PLAN.md` for the run-journal migration.
- Any active structural-conformance session touching the same audit-skill family.

Gate changed skills with `develop:skill-auditor`, then `just build-skills`, `just check-skills`, and `just docs-check`.

## 2. `<quick_start>` policy enforcement on reference skills

`skill-standards` already requires foundation, gate, validator, reference, and auditor skills to omit `<quick_start>`. The remaining live violation class is reference-skill enforcement: `src/plugins/typescript/skills/typescript-standards/SKILL.md` still carries a `<quick_start>` block.

Required handling:

- Update `audit-skills` enforcement if reference-skill `<quick_start>` detection is not already mechanical.
- Sweep reference skills for `<quick_start>` blocks and remove any abbreviated path that contradicts their foundation/reference role.
- Preserve legitimate `<quick_start>` blocks on on-demand tool skills.

Gate changed skills with `develop:skill-auditor`.

## 3. Verification-run row taxonomy

Verdict-emitting skills use different row taxonomies while claiming a shared audit evidence envelope. For example, `audit-skills` uses `keep-these-aspects` / `worth-improving` / `must-fix`, while `audit-subagents` uses `critical-issues` / `recommendations` / `strengths` / `quick-fixes`.

Required handling: decide whether the SPX verification-run payload contract mandates a uniform row taxonomy or treats row names as free-form labels inside a fixed envelope. This decision affects rendered audit surfaces and any auditor agent that indexes on row names.

Govern with `spx/15-audit-result-delivery.pdr.md` and the audit nodes before editing individual skills.

## 4. Audit-skills eval coverage

`audit-skills` now exposes observable flags with no eval suite proving detection, including objective-shape and command-capability findings:

- `actor_or_activity_objective`
- `objective_criteria_duplication`
- `auditor_skeleton_violation`
- `orphaned_argument`
- `missing_argument_hint`
- `argument_capture_regression`
- `overbroad_allowed_tools`
- `irrelevant_dynamic_context`
- `codex_rendering_assumption`

Required handling: author the first develop-plugin eval suite for `audit-skills`, add matching `[eval]` assertions, and run the eval harness before using the auditor as the gate for marketplace-wide objective or argument-syntax sweeps.

## 5. Remaining `uv run` command policy

`inspect-github-actions` no longer invokes bundled helper scripts through `uv`, but other plugin surfaces still document `uv run` for consumer toolchains or vendored local workflows. The remaining cases require a product decision per plugin surface: consumer-project tool invocation, local marketplace tooling, or shipped script execution.

Required handling: classify each remaining `uv run` occurrence by execution environment before changing it. Shipped plugin scripts stay `python3` and stdlib-only; consumer project commands may remain runtime-specific when the language plugin explicitly delegates to the consumer's toolchain.

## 6. Cross-plugin architect objective subject

Architect skills must use one objective-subject policy across Python, Rust, and TypeScript. The architect objectives and nearby body prose mix imperative output wording, artifact-shaped objective wording, and architect-skill subject claims across the three language plugins.

Required handling: decide whether objective statements may use the artifact subject `the skill` or must name `Claude` for this output claim, update `skill-standards` / `agent-prompt-standards` if the rule needs clarification, then sweep the architect skills consistently. Gate changed skills with `develop:skill-auditor`.
