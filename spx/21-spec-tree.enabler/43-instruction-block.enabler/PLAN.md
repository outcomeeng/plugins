# Plan: Instruction Block

## Absorb the personal project-instruction file into the block

`~/Code/.claude/CLAUDE.md` (the operator's project-level instruction file, outside this repository) is to be deleted. Its sections were reviewed one by one against the router block and the `/understand` foundation, and each was dispositioned. This entry records those decisions so the migration can be executed as its own changeset.

Three sections need no action: `<recording>`, `<no_origin_distinction>`, and `<touched_file_debt>` are already carried by the foundation's `<imperfection_protocol>`, whose wording is broader — debt the change causes, surfaces, or invalidates is fix-now wherever it lives — and which additionally carries `<expense_ceiling>`.

### Into the router template

| Section                           | Placement                                | Shape                                                                                                                                          |
| --------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `<self_reference_policy>`         | near Autonomy Boundary                   | operational artifacts never name the agent identity; the authored-skill-content exception stated explicitly in the same rule                   |
| `<skill_failure_no_substitution>` | stop trigger under When to Invoke Skills | a failed invocation is diagnosed and reported, never substituted by reading the skill file, pre-compaction context, or memory                  |
| `<actionable_waits>`              | bullets under `### Operator questions`   | a blocked report carries the exact command, what it does, what stays blocked, and an offer — restated in full on every check                   |
| `<findings_vs_expected_state>`    | classification half only                 | classify an observation before calling it a finding; expected state is never a finding. The Known/Likely/Investigate/Fix vocabulary is dropped |

The `<self_reference_policy>` placement also resolves a dangling citation: the product's root instruction file references that section by name while the router carries no such rule, so deleting the personal file without this move breaks the reference.

### Into `/wait-for-load`

`<check_load_before_flake_classification>` belongs beside the load reading it depends on rather than in the router: no failure is classified flaky, intermittent, or pre-existing before consulting the waiter's observation, because sustained load above capacity starves short-budgeted operations and produces starvation rather than flakiness.

### Dropped

`<no_until_polling>`, `<no_gh_run_watch>`, `<memory_scope>`, the `<closing_protocol>` three-option template, and `<why_perfection_matters>`. The closing-protocol template is dropped because the foundation already governs closing and its touched-file-debt rule is stricter than that template's track-and-proceed option allowed, so carrying both would ship a contradiction.

### Sequencing

The four router additions total roughly thirteen lines. The node's `ISSUES.md` records that the router block carries no size ceiling and that every methodology advance grows an eager per-session cost for every consumer; this migration adds to that cost with no offsetting removal, so it is the natural changeset in which to settle the budget question rather than compound it silently.
