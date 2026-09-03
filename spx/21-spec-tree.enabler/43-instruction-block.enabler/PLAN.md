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

The four router additions total roughly thirteen lines. The render model declares the 32768-byte project-doc ceiling and the gate measures every render against it, so these additions land against a measured budget; the remaining router-reduction units below own the room they spend into.

## Codex project-doc budget: remaining units of Change #7

The 32768-byte combined Codex project-doc budget is the given ceiling — no consumer setting is raised. The ceiling declaration and measurement (render-model ADR amendment, spec assertions, generator `--check` and gate report) are the first unit. The remaining units, coordinated in `https://github.com/outcomeeng/changes/issues/7` under its recorded constraints:

1. Router reduction: relocate dispatch-time guidance — the per-role role-task contracts and the subagent lifecycle mechanics — out of the router into content authored once and build-injected into every skill whose flow dispatches a verifier or reviewer. Injection ships before or with removal; no released plugin version lacks the guidance in both places; the spec assertions and `outcomeeng/distribution/instruction_block.py` `*_POLICY_REQUIREMENTS` tuples pinning router sections move in the same changesets; dispatch behavior after the relocation carries `[eval]` evidence.
2. Repository fit: this repository's own root instruction content shrinks until the rendered `AGENTS.md` fits the ceiling, and the gate flips from report to fail for fitting surfaces.

## Render a Go language block once the go plugin ships

Governing declarations: `spx/43-go.enabler/go.md` and `spx/43-go.enabler/15-go-testing.adr.md` declare the Go evidence cell `<subject>.<evidence>.<level>[.<runner>]_test.go`, and `spx/21-spec-tree.enabler/17-audit.adr.md` requires every language plugin to ship `audit-go-code`, `audit-go-tests`, and `audit-go-architecture`.

The router renders no Go block: `LANGUAGE_BY_EXTENSION` in `src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` maps only `py`, `ts`, and `rs`, and `templates/instruction-block.md` declares only `lang:python`, `lang:typescript`, and `lang:rust` blocks. A Go product therefore renders an empty language list and no Go test-naming row.

Steps, carried by the plugin lane of `https://github.com/outcomeeng/changes/issues/10` in the same change that ships `src/plugins/go/`, because the audit-skill table the block introduces names skills that exist only then:

1. Add `go` to `LANGUAGE_BY_EXTENSION`; the mapping test over that source-owned domain covers the new entry.
2. Add a `lang:go` block to each of the three per-language groups in the template: the Claude and Codex audit-skill tables naming `/audit-go-code`, `/audit-go-architecture`, and `/audit-go-tests`, and the Go row of the test-naming convention.
3. Update a `*_POLICY_REQUIREMENTS` tuple in `outcomeeng/distribution/instruction_block.py` only where a pinned section changes; run `just build-skills`, `just build-instructions`, `just instructions-check`, and `just test spx/21-spec-tree.enabler/43-instruction-block.enabler/tests/`.
