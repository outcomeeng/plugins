# Issues — Bump

Known follow-ups for the bump node. Coordination note; not spec truth.

## A version advances with no changelog entry, and nothing detects it

`just bump` writes the next version into every changed plugin's manifests. Nothing requires that plugin's `CHANGELOG.md` to gain a matching entry, and no gate step compares the two. The requirement exists only in each changelog's own preamble — "An entry appears when a change alters what a consumer can rely on, must do, or must know" — which no spec assertion declares and no command checks.

The result is silent: `spec-tree` shipped 0.88.3 through 0.88.6 with the changelog stopping at 0.88.2, and the gap surfaced only because a reviewer noticed one missing entry on one pull request.

**Why backfilling is the wrong repair.** A changeset reconstructing another release's entry from commit messages and diffs is guessing at what that release's consumers must know, and the author who knew is not in the room. It also attaches an unbounded obligation to whichever branch is open: each base advance brings another release to document. A gap is closable only by the author of the change that left it, who is recording rather than inferring.

**Resolution shape**: decide whether the bump surface enforces this and how. Candidates, in rising cost: a `bump --check` extension that fails when a changed plugin's manifest version has no matching `## <version>` heading in that plugin's `CHANGELOG.md`; a gate step that applies the same comparison over the changed-plugin set; or an explicit opt-out for a release whose changes are genuinely consumer-invisible. Whichever is chosen, the check belongs where the version is written, so the failure arrives while the author is still holding the change.

**Also decide**: whether the existing gaps are filled by their authors, left as gaps with the note the changelog now carries, or closed by declaring the entries start at the version the check first covers. Reconstruction by someone who did not make the change is not among the options.

**Revisit condition**: before the next release-process change touching `outcomeeng/distribution/bump.py` or the `bump-check` gate wiring.

Surfaced on the release-overlay changeset. That changeset backfilled 0.88.3, 0.88.5, and 0.88.6 — releases it did not author — and one entry carried fabricated content before a verification pass caught it; all three were withdrawn. It kept the 0.88.4 entry, whose release it did author, so that entry is a record of known consumer impact rather than a reading of someone else's diff.
