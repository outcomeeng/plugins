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
