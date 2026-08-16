# Issues — Bump

Known follow-ups for the bump node. Coordination note; not spec truth.

## The include-directive grammar has two implementations

`outcomeeng/distribution/build.py` owns the authoritative directive grammar — `_DIRECTIVE_RE`, `_DIRECTIVE_BODY_RE`, `_is_jinja_control_block`, `_directive_argument`, the `Directive` types, and `DirectiveSyntaxError` — together with the authored-source filter `plugin_source_files` and `_is_authored_source_file`. `outcomeeng/distribution/bump.py`'s `_real_include_index_probe` re-derives both: a local `_INCLUDE_DIRECTIVE` regex over the shared block delimiters, and a local ignored-directory and ignored-suffix filter.

Bump cannot import the build to reach them. `build.py` imports Jinja2, and `spx/32-distribution.enabler/21-bump.enabler/15-bump-shape.adr.md` forbids this module a third-party dependency, so importing the build would take Jinja2 into bump's graph through the back door.

Two implementations of one grammar drift. The local regex already had to grow a second quote branch to match the literal `format_directive` emits through `repr()`, and any future directive-syntax change reaches only one of the two.

**Resolution shape**: move the directive grammar, the `Directive` types, and the authored-source filter into the stdlib-only `outcomeeng/distribution/contracts.py`, which both modules already import, and have `build.py` and `bump.py` consume them from that one owner. `DirectiveSyntaxError` needs a home that does not subclass `BuildError`, or the error hierarchy needs splitting.

**Why this is larger than the bump changeset**: the move restructures the core of `build.py` and lands on `spx/18-plugin-build.enabler`, whose spec and `15-build-architecture.adr.md` both describe the directive system as build-owned. Aligning that node's declarations is the substance of the work, and it belongs to a changeset scoped to the build node rather than riding on a bump attribution fix.

**Evidence**: `implementation-auditor` run `2026-08-16_14-37-36-503-a91d084361f9`, two debt findings against `outcomeeng/distribution/bump.py`.

## A version advances with no changelog entry, and nothing detects it

`just bump` writes the next version into every changed plugin's manifests. Nothing requires that plugin's `CHANGELOG.md` to gain a matching entry, and no gate step compares the two. The requirement exists only in each changelog's own preamble — "An entry appears when a change alters what a consumer can rely on, must do, or must know" — which no spec assertion declares and no command checks.

The result is silent: `spec-tree` shipped 0.88.3 through 0.88.6 with the changelog stopping at 0.88.2, and the gap surfaced only because a reviewer noticed one missing entry on one pull request.

**Why backfilling is the wrong repair.** A changeset reconstructing another release's entry from commit messages and diffs is guessing at what that release's consumers must know. It also attaches an unbounded obligation to whichever branch is open: each base advance brings another release to document. Git author identity does not bound it either — every bump commit in this repository carries the same author, so "I wrote that release" licenses backfilling any gap at all.

The bound that holds is topical: a changeset may record a prior release whose change its own diff modifies or reverses, because the entry is then checkable against the diff carrying it, and it names that release's commit. Every other gap stays open until the changeset that fills it has that relationship to it.

**Resolution shape**: decide whether the bump surface enforces this and how. Candidates, in rising cost: a `bump --check` extension that fails when a changed plugin's manifest version has no matching `## <version>` heading in that plugin's `CHANGELOG.md`; a gate step that applies the same comparison over the changed-plugin set; or an explicit opt-out for a release whose changes are genuinely consumer-invisible. Whichever is chosen, the check belongs where the version is written, so the failure arrives while the author is still holding the change.

**Also decide**: whether the existing gaps are filled by the changesets that next touch what those releases changed, left as gaps with the note the changelog now carries, or closed by declaring the entries start at the version the check first covers. Reconstruction with no topical relationship to the release is not among the options.

**Revisit condition**: before the next release-process change touching `outcomeeng/distribution/bump.py` or the `bump-check` gate wiring.

Surfaced on the release-overlay changeset, which backfilled 0.88.3, 0.88.5, and 0.88.6 and had one entry carry fabricated content before a verification pass caught it; all three were withdrawn. It kept the 0.88.4 entry and first justified that by authorship, until a skill audit established that every bump commit in this repository carries the same author identity, so the criterion separated nothing. The entry stands on the checkable relationship instead: 0.88.7 reverses what `dbd7b429cdc3744f7288553d1be8a4e91b76ab40` shipped.
