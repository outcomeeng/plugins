# Issues: Instructions Plugin

Current instructions-plugin follow-ups. Coordination note; not spec truth.

## 1. Audit-skill skeleton sweep

The canonical auditor shape lives in `src/plugins/instructions/skills/skill-standards/references/auditor-skeleton.md`: verdict-shaped `<objective>`, `<audit_workflow>`, `<verdict_format>`, `<failure_modes>`, soundness `<success_criteria>`, and no `<quick_start>`.

Open work: sweep the remaining `audit-*` skills onto that skeleton. Keep the post-collapse composition exception: generic composing auditors that invoke language audits require `Skill` in `allowed-tools`.

`audit-prose` and `audit-internal-docs` are the furthest from the skeleton: they carry `<essential_principles>` and `<workflow>` instead of `<constraints>`/`<audit_workflow>`/`<verdict_format>`, and no `<constraints>` block stating the read-only boundary. Their descriptions are also the only two audit-skill descriptions that use directive `ALWAYS invoke` wording rather than the passive `X audit methodology — judges Y` form the standard prescribes at `<descriptions>`. That divergence is not a plain violation: unlike the agent-composed language audits, no auditor agent composes these two, so description-match is their sole entry point and a passive description would not activate them. Resolve the description convention for agentless user-facing audit skills — a `skill-standards` carve-out for description-match audit entry points, or a rewrite — as part of this sweep rather than one skill at a time, since the answer governs both prose auditors together.

Before starting, reconcile this work with:

- `spx/21-spec-tree.enabler/32-decisions.enabler/ISSUES.md` for the artifact-type auditor family.
- `spx/21-spec-tree.enabler/16-verification.enabler/PLAN.md` for the run-journal migration.
- Any active structural-conformance session touching the same audit-skill family.

A concrete instance for the sweep: `audit-skill/SKILL.md` and `audit-subagent/SKILL.md` both carry a
`<validation>` checklist (Completeness, Precision, Accuracy, Actionability, Fairness, Context,
Examples) restating ground `<success_criteria>` already covers, and the auditor skeleton carries no
such block. Both instances are the same defect, so fold each checklist item not already stated in
`<success_criteria>` into that section and drop the rest across the family in one pass rather than
per skill.

Gate changed skills with `instructions:skill-auditor`, then `just build-skills`, `just check-skills`, and `just docs-check`.

## 2. `<quick_start>` policy enforcement on reference skills

`skill-standards` already requires foundation, gate, validator, reference, and auditor skills to omit `<quick_start>`. No reference or standards skill currently carries a `<quick_start>` block; the sweep of authored reference skills is complete. The remaining open work is enforcement mechanization.

Required handling:

- Add a mechanical `audit-skill` flag for a `<quick_start>` block on a foundation, gate, validator, or reference skill, so a reintroduced block is caught the way `auditor_skeleton_violation` catches it on an `audit-*` skill.
- Preserve legitimate `<quick_start>` blocks on on-demand tool skills.

Gate changed skills with `instructions:skill-auditor`.

## 3. Verification-run row taxonomy

Verdict-emitting skills use different row taxonomies while claiming a shared audit evidence envelope. For example, `audit-skill` uses `keep-these-aspects` / `worth-improving` / `must-fix`, while `audit-subagent` uses `critical-issues` / `recommendations` / `strengths` / `quick-fixes`.

Required handling: decide whether the SPX verification-run payload contract mandates a uniform row taxonomy or treats row names as free-form labels inside a fixed envelope. This decision affects rendered audit surfaces and any auditor agent that indexes on row names.

Govern with `spx/15-audit-result-delivery.pdr.md` and the audit nodes before editing individual skills.

## 4. Audit-skill eval coverage

`audit-skill` now exposes observable flags with no eval suite proving detection, including objective-shape and command-capability findings:

- `actor_or_activity_objective`
- `objective_criteria_duplication`
- `auditor_skeleton_violation`
- `caller_coupling`
- `orphaned_argument`
- `missing_argument_hint`
- `argument_capture_regression`
- `overbroad_allowed_tools`
- `irrelevant_dynamic_context`
- `codex_rendering_assumption`

Required handling: author the first instructions-plugin eval suite for `audit-skill`, add matching `[eval]` assertions, and run the eval harness before using the auditor as the gate for marketplace-wide objective or argument-syntax sweeps.

## 5. Remaining `uv run` command policy

`inspect-github-actions` no longer invokes bundled helper scripts through `uv`, but other plugin surfaces still document `uv run` for consumer toolchains or vendored local workflows. The remaining cases require a product decision per plugin surface: consumer-project tool invocation, local marketplace tooling, or shipped script execution.

Required handling: classify each remaining `uv run` occurrence by execution environment before changing it. Shipped plugin scripts stay `python3` and stdlib-only; consumer project commands may remain runtime-specific when the language plugin explicitly delegates to the consumer's toolchain.

## 6. Cross-plugin architect objective subject

Architect skills must use one objective-subject policy across Python, Rust, and TypeScript. The architect objectives and nearby body prose mix imperative output wording, artifact-shaped objective wording, and architect-skill subject claims across the three language plugins.

Required handling: decide whether objective statements may use the artifact subject `the skill` or must name `Claude` for this output claim, update `skill-standards` / `agent-prompt-standards` if the rule needs clarification, then sweep the architect skills consistently. Gate changed skills with `instructions:skill-auditor`.

## 7. Skill auditor remediation must preserve runtime terminology

`skill-auditor` rejected the phrase "the agent" under the prompt-voice rule, then prescribed "the configured agent" as an acceptable replacement. That remediation bypasses the runtime terminology layer: `configured_agent` is an authoring-time key used through `{{! term('configured_agent') !}}`, which renders as `subagent` for Claude and `custom agent` for Codex. The governing prompt standard prefers imperative, subject-free instructions but does not yet forbid the literal phrase "configured agent", and `src/plugins/instructions/skills/audit-subagent/SKILL.md:65,68` still uses that literal phrase. The auditor recommendation and those existing occurrences expose the same unresolved cross-runtime terminology rule.

Required handling:

- Declare that cross-runtime skill prose uses imperative, subject-free wording or the canonical terminology expression; the literal internal key name is forbidden.
- Require auditor remediation for banned-subject findings to follow that rule instead of recommending an internal terminology key as prose.
- Sweep the existing literal occurrences in `src/plugins/instructions/skills/audit-subagent/SKILL.md` onto imperative wording or `{{! term('configured_agent') !}}` as appropriate.
- Add an auditor eval case where "the agent" is rejected and "the configured agent" is also rejected as its replacement.

## 8. Auditor agent model declaration convention

The auditor agents declare their model two ways. `src/plugins/instructions/agents/skill-auditor.md`, `src/plugins/instructions/agents/subagent-auditor.md`, and `src/plugins/spec-tree/agents/implementation-auditor.md` use the build-time term `model: "{{! term('configured_agent_auditor_model') !}}"`, which renders `sonnet` for Claude and the Codex standard model for Codex. The five remaining spec-tree auditor agents hardcode `model: sonnet`, which reaches Codex as the literal `sonnet` and is translated to the Codex standard model at install time by `MODEL_MAPPINGS` in `outcomeeng/distribution/agents.py`. Both forms select the same model on both runtimes, so neither is broken; the divergence is which layer owns the per-runtime mapping — the build or the install-time converter.

The divergence is invisible in the authored files: an author copying a hardcoded auditor as a template gets the literal form, and an author copying a term-form auditor gets the term form, with nothing naming either as canonical.

Required handling: decide which layer owns per-runtime model selection for agent frontmatter, record it in the agent-authoring standards, then sweep the eight auditor agents onto the chosen form. Deciding one agent at a time reproduces the divergence, so this is not a per-file edit. Gate changed agents with `instructions:subagent-auditor`.

## 9. Python-parity standards subtree

The instructions node lacks the standards subtree the Python plugin models. `spx/43-python.enabler` groups its standards under `spx/43-python.enabler/25-python-standards.enabler/` with facet children — architecture, tests, and the `29-python-code.enabler` workflow child that carries the language's workflow assertions. `spx/43-instructions.enabler` carries only the two meta-skill cluster children (`21-skills.enabler`, `21-subagents.enabler`), so the instruction-artifact workflow assertion lives in the plugin-level spec `spx/43-instructions.enabler/instructions.md` for lack of a workflow child.

**Required handling**: restructure via `/decompose spx/43-instructions.enabler` toward the Python model — a standards subtree with a workflow child — and move the spec-first instruction-artifact workflow assertion from `spx/43-instructions.enabler/instructions.md` into that workflow child. Structural change (node creation and assertion relocation), not a text edit.

## 10. Audit-skill target-argument declaration convention

The audit skills declare their target input two ways. `src/plugins/instructions/skills/audit-subagent/SKILL.md` declares `argument-hint` and `arguments` and substitutes the named argument through its body. `src/plugins/instructions/skills/audit-skill/SKILL.md`, `src/plugins/spec-tree/skills/audit-adr/SKILL.md`, and `src/plugins/spec-tree/skills/audit-pdr/SKILL.md` declare no argument and take their target from the invoking prompt, so `/` autocomplete offers no signal about the expected input. `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md` requires `argument-hint` when a skill takes arguments, which does not settle whether an audit target is an argument or prompt context.

Required handling: decide whether an audit skill's target is a declared argument, then apply the answer across the audit-skill family rather than one file at a time — the answer changes each skill's input contract and its `missing_argument_hint` exposure under `audit-skill`'s own anti-pattern list. Reconcile with entry 1's skeleton sweep, which rewrites the same frontmatter. Gate changed skills with `instructions:skill-auditor`.
