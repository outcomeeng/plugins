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
