# Methodology 4.0 migration log

## 2026-10-04

- **Notes retired**: All 31 `PLAN.md` files and `spx/ISSUES.md` left the tree (Change [#158](https://github.com/outcomeeng/changes/issues/158)). Each item took one of three dispositions: dropped where a commit, decision, spec or open Change realizes or carries it; an `ISSUES.md` entry with a settlement condition on the node it concerns where it is a defect, contradiction or gap; a Proposed Change where it is pending work.
- **Proposed Changes**: The design-tests proposals became [#353](https://github.com/outcomeeng/changes/issues/353), the role-vocabulary sweep became [#356](https://github.com/outcomeeng/changes/issues/356), the prose-grep validation gate became [#354](https://github.com/outcomeeng/changes/issues/354), and the browser interface plan became [#358](https://github.com/outcomeeng/changes/issues/358).
- **Authoring skills**: The `/bootstrap` and `/decompose` skills, the router template, the delivery-lifecycle skills and decisions, and the bootstrapping, decomposing, aligning and refactoring specs still instruct creating or writing to `PLAN.md` notes; `spx/21-spec-tree.enabler/54-bootstrapping.enabler/ISSUES.md` records the gap and its settlement condition.
- **Verification subtree**: The `31-verification` notes became `ISSUES.md` entries on the verification, agentic-verification, Claude and Codex invocation, conformance, eval-verification, eval-harness and test-verification nodes. PR #448 and PR #454 were closed unmerged and superseded by [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) and [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md); the per-assertion-type standards programme landed in the `test-evidence-standards` skill, and two decomposition dispositions became test-verification entries. The `/verify` routing of the untagged rules in [`spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/15-skill-instrumentation.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/15-skill-instrumentation.pdr.md), [`spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md) and [`spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md) is the gap the `31-verification` entry on untyped Verification rules records.
- **Spec Tree subtree**: The three-PR evidence refactor was realized by `/verify`, `/test` and the shared standard, and the `/eval` and `/eval-skill` surfaces are exposed by Declared nodes. The verification slice for `audit-implementation` was realized, and its later slices are carried by Changes #330 and #327. The merge lifecycle rewrite was realized by [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md), the merging standards and the overlay, and PR #447 was closed. The readiness record was realized and dropped.
- **Spec Tree entries**: Worktree provisioning, agent environment, context loading, the instruction block, apply, audit, changeset coherence, direct push and diagnostics took entries for their open work. The `ISSUES.md` files of `13-agent-environment`, `32-direct-push` and `79-diagnostics` are new.
- **Language subtrees**: The TypeScript, Python tests, Rust, skills, HDL and work notes became entries on their nodes, including the TypeScript source-laundering delta, the Rust credential level and the Python tests overlay.
- **Build and distribution**: The runtime parameterization plan was settled: its first phase and the field, term and file work are complete, and the front matter strip is an entry on `target-emission`. The eval harness plan became three entries, and the distribution, installation and bump nodes took the changelog, agent-specific decision and `AssertionError` entries.
- **Root notes**: The 16 `spx/ISSUES.md` entries moved to the nodes they concern: the architecture template, the Lean PDR template, agent terminology, 19 oversized reference files, absent `failure_modes`, the non-interactive git guard, agent-specific decisions, changelog titles, verifier collisions, harness `AssertionError`, the allowed-tools token, verifier rebases, the merging decision and implementation audit against changeset review. Two entries, Product-level assertions without tags and the thirty-three `PLAN.md` files, were dropped. The 4.0 migration refinement was dropped because the foundation shipped on 2026-09-08 and Changes #185, #321, #328 and #334 carry the rest. The installation governance split was dropped because Changes #14 and #48 carry it.
- **Browser interface**: The browser plan became Proposed Change [#358](https://github.com/outcomeeng/changes/issues/358); the prototype stays at `prototypes/interview-live/`.

## 2026-09-19

- **Change records**: The Change record accepted 4.0 patch declarations of the form `4.0.N` (`65a4267e3`, `1fee92b30`; PR #590).

## 2026-09-18

- **Lifecycle**: The Lifecycle skills claim, release and close replaced the pickup, handoff and issue skills (`3f0b83de3`).
- **Vocabulary**: The agent terminology cited the 4.0 Change chapter for Change, Output and Activity (`1ea6cf863`; PR #581).

## 2026-09-08

- **Foundation**: The `/understand` foundation stated methodology 4.0 (`3bf828913`; PR #564), and the sibling skills read the 4.0 kinds and templates.
- **Declaration**: `spx.config.yaml` declared methodology 4.0, and the skills recognized the prior 3.x forms unconditionally (`f8f7c51e5`; PR #565).

## 2026-09-07

- **Exclusion**: `spx/EXCLUDE` and its pytest collection filter were retired (`95c1cc5f7`), and the exclusion-path plans moved into `ISSUES.md` entries (`ef5b48f98`).
- **Planning**: `spx/PLAN.md` recorded the role-vocabulary sweep and the 4.0 migration refinement (`497c82bfa`).

## 2026-08-17

- **Coordination**: `spx/local/coordination.md` declared the store where the repository's Changes live (`b7a3388a8`).

## 2026-07-29

- **Declaration**: `spx.config.yaml` first declared the methodology version the repository follows (`0339a5650`).
