# Issues — sync-base

## An untracked file that collides with a base addition still maps to `conflict`

The dirty-tree precondition check excludes untracked files
(`git status --porcelain --untracked-files=no`), because an untracked file
generally does not block a rebase. One narrow case is an exception: when the
base advance adds a path the working tree already holds as an untracked file,
`git rebase` refuses to start to avoid overwriting it — the same "untracked
working tree file would be overwritten" guard `git checkout` applies.

In that case sync-base falls through to the rebase, the rebase exits non-zero
before replaying, and the existing mapping reports `conflict` with conflict
details. That is a precondition the caller clears (remove or commit the
colliding untracked file), not a content conflict to resolve — so the reported
outcome is imprecise, and the ADR's "untracked files do not block a rebase"
holds only for the non-colliding case.

Scope: narrow edge case, no regression — before the `dirty_tree` change this
same case also surfaced `conflict`. Resolving it needs a new detection step
(parse the rebase's pre-flight refusal, or pre-check the base diff against
untracked paths) distinct from the tracked-file dirty check, plus an ADR/spec
refinement of the untracked-file claim. Tracked rather than fixed in the
introducing change because it is a separable detection mechanism, not a bounded
edit to the current diff.

## Synchronizer extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` runs to 785 lines
— base-ref and remote-tracking resolution, behind-base detection, the
attached-branch rebase and the detached-head advance, the dirty-tree
precondition, structured conflict reporting, and the readiness-preservation
proof. Past fifty lines [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) makes a shipped script
debt whose logic moves into the SPX CLI once the script proves its value; the
synchronizer has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port base movement, conflict structuring, and the
preservation proof into the SPX CLI, publish it, advance the floor, and reduce
the shipped skill to its instruction with no script. The derivation this script
shares with its siblings extracts with the primitives tracked in
`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/ISSUES.md`.
Carry the rebase-never-reset invariant and the untracked-collision gap above
into the ported surface rather than leaving either behind. Revisit when the
capability publishes.

## `/sync-base` has no read-only form a Verifier could select

A Verifier's context load runs `/sync-base`, which fetches, rebases the audited branch onto its base and resolves conflicts, while other Verifiers dispatched against the same committed head are still running. `/sync-base` offers no form that reports a branch behind its base without moving the checkout.

**Evidence.** Rollout `agent-a4cedd803fc1a5758.jsonl` of the test-evidence audit dispatched against head `f07db1bbaf225ec031d7a777f02c166daa588871` on 2026-09-16 rebased the branch to `15d4309e69c26804cd1b04676248a529fd0235b9`; implementation-audit run `2026-09-16_12-40-04-694-a2e206a2d753` then found its sealed head superseded.

**Settlement condition.** `/sync-base` reports behind-base without moving the checkout when the caller selects it, or the context load reads the committed subject without calling it; the decision lives with the entry in `spx/21-spec-tree.enabler/18-context-loading.enabler/ISSUES.md`.

## The conflict handoff to a superior meets the node's audit rule and fails `/skill-standards` caller independence

**Evidence.** Skill-auditor run `2026-10-08_23-39-23-724-b13324f3337e` rejected the `sync-base` skill on the conflict handoff in `<conflict_reconciliation>` of `src/plugins/spec-tree/skills/sync-base/SKILL.md`, which defines a superior as whoever assigned the work and sends that superior an assessment. That text follows the ALWAYS `[audit]` assertion in `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md` that the skill sends its superior an assessment with a recommended route and acts on the superior's decision, and the `### Audit` rule of [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) that names the same handoff. `/skill-standards` rejects the same text as a dependency on the caller.

**Impact.** No wording of the conflict handoff satisfies both the node's declarations and the skill standard, so every typed skill audit of the `sync-base` skill rejects either the handoff the spec and ADR require or the skill text that omits it.

**Settlement condition.** The spec and the ADR, or `/skill-standards`, change so the two agree on how the skill addresses the party that decides a conflict route.

## `_CHANGESET_SCOPE_PATH` meets the provider-import decisions and fails the `/skill-standards` bundled-file-reference rule

**Evidence.** Skill-auditor run `2026-10-08_23-39-23-724-b13324f3337e` flagged `_CHANGESET_SCOPE_PATH` in `src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py`, which resolves `scope-changeset/scripts/changeset_scope.py` relative to `__file__` across the skill directory boundary, as a cross-skill file path. [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) requires a consumer to reach a provider skill's shared logic from its own `scripts/` entrypoint by a `__file__`-relative import, and [`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md) requires sync-base to reach the changeset primitives only by import from that one script. `/skill-standards` flags that one file-relative load.

**Impact.** The load the two decisions require is the reference the skill standard rejects, so every typed skill audit of the `sync-base` skill reports a bundled-file-reference finding that no repair inside the skill can clear without violating a decision.

**Settlement condition.** The two decisions, or `/skill-standards`, change so the two agree on how a consumer skill's script loads its provider skill's script.

## The missing-provider-script case has no `[test]` assertion

**Evidence.** When `scripts/changeset_scope.py` of the scope-changeset skill is absent beside the sync-base skill, `src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` raises `ChangesetScopeUnavailableError` at load and, run as a script, prints a result with status `git_failure` and a `detail` naming the expected path, then exits 1. No assertion in `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md` states that case, and no linked test under `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/tests/` exercises it.

**Impact.** The primitive's contract that every run yields a structured status holds for this case only by implementation; a change that turns it back into a traceback or another exit code passes every linked test.

**Settlement condition.** `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md` carries an assertion for the missing-provider-script case with a linked test.
