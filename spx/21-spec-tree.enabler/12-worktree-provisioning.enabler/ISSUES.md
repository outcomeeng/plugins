# Issues: Worktree Provisioning

## Provisioner extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/init-worktrees/scripts/init_worktrees.py` runs to
476 lines — three-layout classification (single tree, compliant bare-repo pool,
non-compliant), pool provisioning, the push of every local ref to the remote,
and the carry-across of a prior checkout's gitignored state. Past fifty lines
`spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves
into the SPX CLI once the script proves its value; the provisioner has proven
its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository. The same dependency
gates the waiter and the instruction-block generator, tracked in
`spx/13-infrastructure.enabler/13-host-readiness.enabler/ISSUES.md` and
`spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.

**Resolution shape**: port layout classification and pool provisioning into the
SPX CLI, publish it, advance the floor, and reduce the shipped skill to its
instruction with no script. Revisit when the capability publishes.

## Four universal Compliance assertions rest on scenario-typed evidence

Four `### Compliance` assertions in `worktree-provisioning.md` state universal
`ALWAYS` rules yet link `tests/test_worktree_provisioning.scenario.l1.py`: the
origin-derived main-checkout name, the push of every local ref, the refusal on a
non-gitignored `.spx/`, and the container-basename requirement. A universal is
never a scenario — a scenario proves one case and cannot establish an
always-true rule — so each needs `compliance` evidence exercising violating
fixtures.

The coupling itself is sound: the test-evidence audit traced every one of the
four to test functions that reach the governing source. The defect is the
declared evidence type, not the coverage.

**Resolution shape**: add `tests/test_worktree_provisioning.compliance.l1.py`,
move the violating-fixture tests that carry these four rules into it — the
refusal and fail-fast cases plus the origin-URL derivation cases — and re-point
the four assertion links. The scenario file keeps its genuinely existential
cases. Route the work through `/test`, which owns assertion typing and level
selection.

## The property test declares Hypothesis settings the harness owns

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
places property-run execution configuration — seed selection, run counts, replay
input, and failure diagnostics — in a property-test harness.
`tests/test_worktree_provisioning.property.l1.py` declares `@settings(...)`
Hypothesis configuration in the test file instead. The replayable-property
wrapper pattern exists in `outcomeeng_testing/harnesses/gate.py`
(`selected_gate_property`); a shared wrapper in `outcomeeng_testing/harnesses/`
can serve this node and the two others carrying the same pattern (each tracked
in its own `ISSUES.md`).

**Resolution shape**: route the property test through a harness-owned wrapper
that owns the Hypothesis profile and replay diagnostics, then re-run
`test-evidence-auditor` over the node.

**Evidence**: surfaced by the test-evidence audit on PR #549 as the same
pattern used identically in this file.

## The node's remaining obligations await the published worktree lifecycle

The worktree lifecycle — creating a pool worktree on demand, archiving it, restoring it, disposing of it — is `spx worktree` behavior, and `spx` is a separate product with its own spec tree. `spx/21-spec-tree.enabler/19-worktree-occupancy.enabler` records the boundary: how `spx` manages a worktree is `spx`'s concern, and a node here specifies only the plugins' use of that capability. The published `@outcomeeng/spx` 0.7.2 exposes `spx worktree claim`, `status` and `release` only, and no decision in this repository declares the lifecycle design.

What the node owes once `spx` decides and publishes the lifecycle:

- The plugins' use of the published verbs, which skill invokes them and when, as assertions here; the verbs stay specified in the `spx` tree.
- If the lifecycle populates the live set on demand, provisioning keeps only its migration role: classify, push every local ref, bare-clone, place the main checkout, carry gitignored state, hand off the husk. The `init-worktrees` skill's pool-name gathering, its `--worktree` flag and the tests that request N worktrees and assert N exist follow that change.
- Renaming this node and the skill to match a migration-only role is a `/refactor` operation, not an edit.

Provisioning a fresh pool needs no migration: a bare clone and one `git worktree add` for the main checkout, with no husk, no ref push and no gitignored carry. The provisioner exists for the retrofit case, and its extraction is the entry above.

**Settlement condition.** `spx` publishes the lifecycle, the repository floor and the CI pin advance to that release per `CLAUDE.md`, and the assertions, the skill and the tests follow it. No skill or script here invokes a lifecycle verb before then.

**Related.** `outcomeeng/changes#206` declares the worktree lifecycle every conforming pool follows in a decision.
