# Issues — Bump

Known follow-ups for the bump node. Coordination note; not spec truth.

## A version advances with no changelog entry, and nothing detects it

`just bump` writes the next version into every changed plugin's manifests. Nothing requires that plugin's `CHANGELOG.md` to gain a matching entry, and no gate step compares the two. The requirement exists only in each changelog's own preamble — "An entry appears when a change alters what a consumer can rely on, must do, or must know" — which no spec assertion declares and no command checks.

The result is silent: `spec-tree` shipped 0.88.3 through 0.88.6 with the changelog stopping at 0.88.2, and the gap surfaced only because a reviewer noticed one missing entry on one pull request.

**Why backfilling is the wrong repair.** A changeset reconstructing another release's entry from commit messages and diffs is guessing at what that release's consumers must know. It also attaches an unbounded obligation to whichever branch is open: each base advance brings another release to document. Git author identity does not bound it either — every bump commit in this repository carries the same author, so "I wrote that release" licenses backfilling any gap at all.

The bound that holds is topical: a changeset may record a prior release whose change its own diff modifies or reverses, because the entry is then checkable against the diff carrying it, and it names that release's commit. Every other gap stays open until the changeset that fills it has that relationship to it.

**Resolution shape**: decide whether the bump surface enforces this and how. Candidates, in rising cost: a `bump --check` extension that fails when a changed plugin's manifest version has no matching `## <version>` heading in that plugin's `CHANGELOG.md`; a gate step that applies the same comparison over the changed-plugin set; or an explicit opt-out for a release whose changes are genuinely consumer-invisible. Whichever is chosen, the check belongs where the version is written, so the failure arrives while the author is still holding the change.

**Also decide**: whether the existing gaps are filled by the changesets that next touch what those releases changed, left as gaps with the note the changelog now carries, or closed by declaring the entries start at the version the check first covers. Reconstruction with no topical relationship to the release is not among the options.

**Revisit condition**: before the next release-process change touching `outcomeeng/distribution/bump.py` or the `bump-check` gate wiring.

Surfaced on the release-overlay changeset, which backfilled 0.88.3, 0.88.5, and 0.88.6 and had one entry carry fabricated content before a verification pass caught it; all three were withdrawn. It kept the 0.88.4 entry and first justified that by authorship, until a skill audit established that every bump commit in this repository carries the same author identity, so the criterion separated nothing. The entry stands on the checkable relationship instead: 0.88.7 reverses what `dbd7b429cdc3744f7288553d1be8a4e91b76ab40` shipped.

## A shared-fragment change bumps no plugin at the documented invocation order

`_plugin_from_changed_path` in `outcomeeng/distribution/bump.py` attributes a changed path to a plugin only under `src/plugins/<name>/`, `dist/claude/<name>/`, or `dist/codex/<name>/`. A change confined to `src/_shared/<scope>/<topic>/` matches none of them, so it attributes to no plugin.

The root guide orders the two commands as bump, then build — "`just bump` (run before `just build-skills` so `dist/` carries the bumped version)". At that moment the shared fragment has changed and no `dist/` output has, so every plugin whose shipped surface the fragment renders into stays at its old version. Running the documented order once leaves the consuming plugin unbumped and reports nothing; the version only advances if the author happens to run `just bump` a second time after building.

**Evidence**: a change to `src/_shared/agentic-execution/configured-verifier-contracts/fragment.md` renders into `dist/claude/spec-tree/skills/update-instruction-block/templates/instruction-block.md` and both `dist/codex` equivalents. `just bump` before `just build-skills` left `spec-tree` at `0.89.1`; the same command after the build wrote `0.89.2`. Observed on PR #524.

**Resolution shape**: attribute a `src/_shared/` change to every plugin whose generated output it reaches, or make the ordering safe — either by having bump consult the build's source-to-output relation rather than path prefixes, or by declaring the shared-fragment consumers where `spx/local/generated-sources.toml` already records the relation. A path-prefix rule cannot express a many-to-many source-to-output mapping, which is what the shared tree is.

**Revisit condition**: with the changelog-enforcement decision above, since both change where and how `bump` reads a changeset.
