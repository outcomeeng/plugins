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

`src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` runs to 1548 lines
— base-ref and remote-tracking resolution, behind-base detection, the
attached-branch rebase and the detached-head advance, the dirty-tree
precondition, structured conflict reporting, the readiness-preservation
proof, and the stack record with its restack and topology derivation. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script
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
Carry the rebase-never-reset invariant, the stack record and restack contract
(`branch.<name>.stackPredecessor` and `branch.<name>.stackTip`, the predecessor
states, topology derivation, and the `--onto` replay), and the
untracked-collision gap above into the ported surface rather than leaving any
behind. Revisit when the capability publishes.

## A missing sibling script fails the synchronizer with a traceback, not a JSON result

`src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` loads the changeset-scope primitives
from the sibling `scope-changeset` skill at module import. When that sibling is absent from the
installed plugin tree, the load raises before `main` runs, so the failure reaches the caller as a
Python traceback rather than the structured `git_failure` result every other outcome honors; the
skill body tells Claude how to act on that shape.

**Impact.** A split or partial plugin installation is diagnosable from the traceback, which names the
expected path, but not from the JSON contract a caller parses.

**Settlement condition.** The module loads the sibling lazily, or the entry point catches the import
failure and emits a `git_failure` result naming the path. Either restructures the module's load
order, which the extraction of the synchronizer into the SPX CLI (recorded above) supersedes; carry
the requirement into the ported surface, or settle it here if the extraction stalls.

Surfaced by the skill audit on head `003cf8d2b18b94dbb3d2daf4b802fe79ef32d7b6`.

## The shipped `scripts/__init__.py` is cited by no skill content

`src/plugins/spec-tree/skills/sync-base/scripts/__init__.py` is an empty file that ships into both
generated runtime trees. Four of the fourteen script directories in the spec-tree plugin carry one;
the others do not. The test harness loads the synchronizer by file path, so the file serves no
documented consumer or test role.

**Impact.** A consumer reading the installed skill sees a bundled file whose purpose nothing states.

**Settlement condition.** One convention across the plugin's script directories, decided with the
type-checker configuration that may rely on package markers to disambiguate same-named modules;
then either every script directory carries the marker with its role stated, or none does.

Surfaced by the skill audit on head `003cf8d2b18b94dbb3d2daf4b802fe79ef32d7b6`.
