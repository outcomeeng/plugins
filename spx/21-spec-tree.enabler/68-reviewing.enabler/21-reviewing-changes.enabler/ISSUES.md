# Issues: Reviewing Changes Enabler

## 1. Local census markers diverge from the GitHub CI clean-review message

The local `review-changes` render emits a per-severity census for the no-findings state:

```text
BLOCKING: none
DEBT: none
```

The GitHub-hosted `spec-tree-review` workflow in `outcomeeng/gh-actions` emits a single composite clean-review line:

```text
No BLOCKING or DEBT findings.
```

`spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md` says the local and hosted surfaces should share the rendered shape. The no-findings state violates that.

Required handling:

- Decide the canonical clean-review representation.
- Align both surfaces: the local render templates in this repo and the `spec-tree-review` workflow in `outcomeeng/gh-actions`.
- Until both surfaces converge, any clean-review detection that reads both surfaces recognizes both forms.

## 2. Live review passes do not meet the per-pass exhaustiveness assertion

`reviewing-changes.md` declares:

> each pass against a given changeset surfaces every finding the changeset exhibits in that single pass - there is no cross-pass continuity, and a finding missed on this pass has no second chance unless the diff itself changes.

Live runs have missed findings present in the same diff. On `outcomeeng/plugins` PR #148, five `changes-reviewer` passes over the reference-portability node surfaced roughly one finding per pass while missing other defects already present in the first committed diff.

The design is intentionally stateless, so the remedy is to make each pass more exhaustive, not to add cross-pass memory.

Required handling:

- Add a completeness procedure to `references/review-prompt.md`: enumerate the changeset's spec assertion -> evidence link -> implementation chains and every changed file before emitting findings.
- Consider adding a review-result coverage manifest listing visited files and assertions. A new top-level field requires a `SCHEMA_VERSION` bump in `review_result.py` plus coordinated updates to validation, rendering, and consumers.
- Consider changing the current `[review]` evidence to `[eval]` with cases that contain several independent defects and require all of them to be surfaced in one pass.
