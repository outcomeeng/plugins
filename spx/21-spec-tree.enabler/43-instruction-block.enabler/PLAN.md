# Plan: Instruction Block

## Absorb the personal project-instruction file into the block

The operator's project-level instruction file, outside this repository, is deleted. Its sections were reviewed one by one against the router block and the `/understand` foundation, and each was dispositioned. Every retained rule therefore exists nowhere until it lands in the home recorded below.

Three sections need no action: `<recording>`, `<no_origin_distinction>`, and `<touched_file_debt>` are already carried by the foundation's `<imperfection_protocol>`, whose wording is broader — debt the change causes, surfaces, or invalidates is fix-now wherever it lives — and which additionally carries `<expense_ceiling>`.

### Into the router template

| Section                           | Placement                                | Shape                                                                                                                                          |
| --------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `<self_reference_policy>` — done  | Autonomy Boundary                        | landed as `### Agent identity in generated artifacts`; both product-content citations now name that rule                                       |
| `<skill_failure_no_substitution>` | stop trigger under When to Invoke Skills | a failed invocation is diagnosed and reported, never substituted by reading the skill file, pre-compaction context, or memory                  |
| `<actionable_waits>`              | bullets under `### Operator questions`   | a blocked report carries the exact command, what it does, what stays blocked, and an offer — restated in full on every check                   |
| `<findings_vs_expected_state>`    | classification half only                 | classify an observation before calling it a finding; expected state is never a finding. The Known/Likely/Investigate/Fix vocabulary is dropped |

That first row is applied. The deletion left both root files citing a rule that existed nowhere and the ban itself unenforced, so it was fixed by the changeset that observed it rather than deferred. The three remaining rows are cited by nothing, so their absence is quiet — they are simply unenforced until their own pass runs.

### Into `/wait-for-load`

`<check_load_before_flake_classification>` belongs beside the load reading it depends on rather than in the router: no failure is classified flaky, intermittent, or pre-existing before consulting the waiter's observation, because sustained load above capacity starves short-budgeted operations and produces starvation rather than flakiness.

### Dropped

`<no_until_polling>`, `<no_gh_run_watch>`, `<memory_scope>`, the `<closing_protocol>` three-option template, and `<why_perfection_matters>`. The closing-protocol template is dropped because the foundation already governs closing and its touched-file-debt rule is stricter than that template's track-and-proceed option allowed, so carrying both would ship a contradiction.

### Sequencing

The four router additions total roughly thirteen lines. The node's `ISSUES.md` records that the router block carries no size ceiling and that every methodology advance grows an eager per-session cost for every consumer; this migration adds to that cost with no offsetting removal, so it is the natural changeset in which to settle the budget question rather than compound it silently.

## Codex project-doc budget for the managed root instruction surface

Codex injects the root instruction file only up to its `project_doc_max_bytes` budget (32 KiB by default, combined across the instruction-file chain), so a root `AGENTS.md` above that size reaches a Codex session truncated — the router block survives, the product's own phase commands and conventions below it do not. The render model in `spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md` rests on the root file being read whole, and the `ISSUES.md` entry "The router block carries no size ceiling" records that nothing measures the surface against any budget.

Steps, in order:

1. Amend `spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md` to state the size budget the managed surface is rendered against and what a breach requires; align the first affected assertions in `spx/21-spec-tree.enabler/43-instruction-block.enabler/instruction-block.md` (a rendered-size measurement per harness, a `--check` report on breach) and `spx/21-spec-tree.enabler/54-bootstrapping.enabler/bootstrapping.md` (bootstrap declares the budget for a new product).
2. `/update-instruction-block`: measure each rendered root file against the budget and report a breach with the exact size and the Codex setting to raise; `/bootstrap`: write the repository Codex configuration `project_doc_max_bytes` for a new product so a consumer inherits the budget without discovering the truncation.
3. This repository: set `project_doc_max_bytes = 131072` in `.codex/config.toml`, the setting Codex honors from the repository configuration.
4. Regenerate the shipped trees and both root instruction blocks, bump the plugin, and gate with `spec-auditor`, `adr-auditor`, and `instructions:skill-auditor` before `/merge`.

Sequenced after the reload-timing change (PR #532) at the operator's direction so the budget lands as its own reviewable changeset.
