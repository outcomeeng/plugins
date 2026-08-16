# Changelog — contribute plugin

Contributions to repositories you do not control.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.2.0

### Breaking

- **Four skills are renamed from `parent` to `upstream`.** `/open-parent-pr`, `/manage-parent-pr`, `/open-parent-issue`, and `/manage-parent-issue` become `/open-upstream-pr`, `/manage-upstream-pr`, `/open-upstream-issue`, and `/manage-upstream-issue`. The old names no longer resolve. `parent` is what the GitHub API calls the repository a fork came from, and it stays in the resolver that reads that field; `upstream` is the word a developer uses for the same relationship, so it is the word the invocation surface carries. `/sync-fork` keeps its name.
- **The resolver's classifications are renamed and extended.** `parent-contribution` becomes `upstream-contribution`, and `head-ambiguous` is new. A skill or overlay branching on the old value must read the new one.

### Added

- **`/upstream` resolves the contribution target once per contribution.** It runs the resolver and emits an `<UPSTREAM_TARGET>` marker carrying `base`, `head`, `permission`, and `classification`; the five workflow skills read that marker and invoke `/upstream` only when none is live. Invoked on its own it answers what the contribution target is and whether you can push to it.
- **An existing fork is found instead of assumed absent.** Working from a clone of the upstream is ordinary, and the checkout then supplies no head. Resolution now searches the authenticated account and its organizations for a fork of the resolved base, matching without regard to case because GitHub preserves a repository's case and matches it without one. One match becomes the head and the contribution proceeds where it previously dead-ended; several stop as `head-ambiguous` with every match named, because choosing among them is yours; none yields `fork-absent`, which now means verified absent rather than inferred from the checkout — so the `gh repo fork` command it reports is one GitHub will accept.

- **Four skills carry a worked end-to-end example.** `/open-upstream-issue`, `/manage-upstream-issue`, `/manage-upstream-pr`, and `/sync-fork` each show one realistic case worked through to the text it produces — a defect report with its negative control, a maintainer's question and the reply that answers it, a two-finding review where one confirms and one does not, and a diverged fork's commit-by-commit report. A run compares its draft against the example instead of deriving the shape from prose alone.

### Removed

- **The five per-skill resolver copies are gone.** Each workflow skill shipped a byte-identical `scripts/resolve_target.py` whose only job was reaching the shared resolver. The resolver now lives in `/upstream` alone, and no other skill carries a `scripts/` directory or grants a resolver path.

## 0.1.1

### Fixed

- **The outward-text review rule states a rationale the prose plugin still supports.** It justified dispatching `prose-auditor` by claiming that plugin produces a verdict only in a dispatched verifier context. The prose plugin no longer asserts that exclusivity, so the rule now names the reason that holds: the verdict comes from a separate verifier agent session rather than the session that wrote the text.

## 0.1.0

### Added

- **`/open-parent-pr`** — opens one pull request against a repository you do not control, after resolving the base and head repositories and your permission, obtaining authorization in that turn, cutting the branch from the base repository's default branch, and running that repository's own declared checks.
- **`/manage-parent-pr`** — reads an open pull request's state once, verifies each review finding against the branch, appends the revision, and posts one comment stating what changed. The comment is the re-request; requesting a reviewer is a maintainer-side action a contributor's permission does not reach.
- **`/open-parent-issue`** — files one issue carrying tool versions, the base commit observed against, the exact command, and a negative control.
- **`/manage-parent-issue`** — reads a thread once and answers the maintainer's question with evidence.
- **`/sync-fork`** — brings a fork's default branch current with its parent's, distinguishing behind from diverged and never discarding commits.
- **`contribution-standards`** — the invariants every artifact obeys, loaded by the five workflow skills. It ships the target resolver those skills run before their first write.

### Requires

- `git`, the GitHub CLI (`gh`) authenticated, and a Python interpreter. No other plugin and no methodology CLI.
