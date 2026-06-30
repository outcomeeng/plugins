# ISSUES - review-changes

Known issues for `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`.

## 1. Review nodes use gerunds

`spx/21-spec-tree.enabler/68-reviewing.enabler` and `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` use gerund slugs. The nodes must be `review` and `review-changes`.

Required handling:

- Use `/refactor` to rename the nodes and update spec filenames, links, and references.
- Preserve the verification-kind vocabulary: `review` is the verification type and `review-changes` is the skill surface.
- Regenerate derived plugin, runtime, catalog, and guide artifacts that carry the node paths or names.

## 2. Review-changes tests violate testing governance

The tests under `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/` are not acceptable evidence for this node. They violate the testing skill, Python test standards, and this product's testing ADR/PDR rules.

Required handling:

- Rewrite the test evidence through `/test` and run the required test-evidence audit before accepting it.
- Align the evidence chain with `spx/15-test-infrastructure.pdr.md`, `spx/15-test-language.adr.md`, and the Python test standards.
- Keep `tests/` limited to typed assertion files; move harness, generator, fixture, and source-owned vocabulary responsibilities to their governed homes.

## 3. Review finding validation belongs in SPX

The stop-gap runner appends review findings through the shared run journal without review-specific validation for required finding fields, severity and concern values, or citation shape. `spx journal append` validates the journal event boundary, but it does not yet enforce the review finding contract.

Required handling:

- Add review-specific finding validation to the SPX verification or journal boundary that owns review runs.
- Validate the finding shape before a review run can be sealed or projected.
- Keep the skill runner as a thin command surface; do not restore per-finding schema or citation validation to the skill path as a durable fix.

## 4. Review runner loses journal run after opening it

Running the `changes-reviewer` agent against `5f54d7602e6b35140b6971b649d9d8db655a0784..e0631e7bd73cc1ddbce1e29e8acdb3cef09d5cea` opens a review journal, appends the initial `verification.scope.entered` event, then blocks because later `append-scope` and `append-finding` calls fail with `journal run not found; open the run before operating on it`.

Observed evidence:

- Agent id: `019f1760-e04f-7022-8335-d61b334fcf26`
- Run token in runner state: `2026-06-30_07-14-37-776-937336422d13`
- Raw journal file: `/Users/shz/Code/outcomeeng/plugins/.spx/branch/e0631e7bd73cc1ddbce1e29e8acdb3cef09d5cea-7c4e3988/review/runs/run-2026-06-30_07-14-37-776-937336422d13.jsonl`
- The raw journal contains exactly one event and has no `.sealed` marker.

Required handling:

- Diagnose the mismatch between the namespace used by `spx journal open` and the namespace used by later `spx journal append`, `read`, and `seal` calls.
- Preserve a single stable run token and backend namespace across all runner subcommands.
- Add regression coverage that starts a real run, appends scope after a separate runner invocation, and seals the same run.
