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
