# Issues: Reviewing Changes Enabler

## 1. Caller-narrowing prompt-content assertion is `[review]`, could be `[test]` (FOLLOW-UP)

The assertion added to `reviewing-changes.md` —

> ALWAYS: the review prompt instructs the reviewer to review the whole diff against the whole shared taxonomy using the repository's own instructions, and to treat any caller-supplied scope, severity pre-filter, or emphasis as non-authoritative — the local reviewer runs at parity with the CI reviewer per `spx/15-agent-pr-authority.pdr.md`

carries `[review]` evidence. Its subject is a static, observable property of `references/review-prompt.md`: the file contains a Scope section whose text rejects caller-supplied scope, severity pre-filter, and emphasis. That is the same class of prompt-content property the sibling assertion at `reviewing-changes.md` already verifies with `[test]` — "the swappable review prompt template lives at `…/review-prompt.md`" → `tests/test_reviewing_changes.compliance.l1.py`.

A compliance test in the style of the existing `test_reviewing_changes.compliance.l1.py` checks (a prompt-content presence assertion) would make this verifiable without human inspection on every PR, removing the `[review]`/`[test]` evidence-strength inconsistency between two assertions about the same file.

Required handling when a test-evidence sweep happens on this node:

- Add a compliance test asserting `review-prompt.md` contains the Scope section with the caller-narrowing rejection text (whole-diff/whole-taxonomy, no caller-supplied scope/severity-filter/emphasis).
- Retag the assertion from `[review]` to `[test](tests/test_reviewing_changes.compliance.l1.py)`.

Split out of the parity-contract change (PR `feat/local-review-parity`) because it adds a new test class beyond that change's blast-radius.

## 2. Local review may resolve its base from a stale local ref, not `origin/<base>`

During the `fix/sessions-test-hermeticity` work, the `changes-reviewer` agent (driving the `reviewing-changes` skill) twice surfaced findings about code **already merged to `main`** — verification-taxonomy (#103) and merging-review (#104) changes that were not part of the changeset under review. The reviewer was invoked with base `origin/main`, yet its diff included those merged commits.

The symptom correlated with the local `main` ref being stale: `main` pointed at `e880a61` while `origin/main` had advanced past #103/#104. Force-updating `git branch -f main origin/main` before each review made the false findings disappear. This points at a candidate defect: the diff base appears to resolve from the local `main` branch ref (or a merge-base computed against it) rather than from `origin/<base>` or the explicitly-passed base ref. In a multi-worktree checkout — where `main` is intentionally kept unattached and can lag `origin/main` — that reviews a superset diff and yields false findings against already-merged work.

Required handling (investigate before fixing):

- Invoke `/understanding` then `/contextualizing spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`.
- Inspect how `reviewing-changes` computes its diff base (the `git diff <base>...<head>` resolution and any merge-base step).
- Confirm whether it dereferences a local branch ref (e.g., `main`) or uses `origin/<base>` (fetched) and the explicit base the caller passes.
- If it keys off a local ref, resolve the base against `origin/<base>` (fetch first) or honor the caller-passed base verbatim, so a stale local ref cannot widen the reviewed diff. Add evidence that a stale local `main` does not change the reviewed diff.

Until then, agents running the local review in this multi-worktree repo keep `main` synced (`git branch -f main origin/main`) before invoking the reviewer.

Surfaced during the `fix/sessions-test-hermeticity` change review (PR #105).
