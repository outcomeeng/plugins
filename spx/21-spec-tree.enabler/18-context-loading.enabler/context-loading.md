# Context Loading

PROVIDES deterministic context loading that walks the tree from product root to target, collecting all ancestor specs, lower-index sibling specs, and ADRs/PDRs
SO THAT all implementation and authoring skills
CAN operate with complete, verified context before any work begins

## Assertions

### Compliance

- ALWAYS: read all ancestor specs, lower-index sibling specs, and governing ADRs/PDRs for a target with a complete ancestor chain ([review])
- ALWAYS: abort with the missing file path and remediation guidance when a required ancestor spec is absent ([review])
- ALWAYS: return an empty bootstrap manifest when authoring against an empty tree with only a product spec ([review])
- ALWAYS: read lower-index sibling specs as target constraints and list same-index or higher-index siblings without reading them as constraints ([review])
- ALWAYS: produce the same context manifest for the same tree structure and target ([review])
- ALWAYS: read every ADR/PDR returned by globs — do not filter by title relevance ([review])
- ALWAYS: list target spec test links and co-located test files without reading test file bodies — test-body inspection belongs to `/test`, `/audit-tests`, and `/apply` ([review])
- ALWAYS: emit node, ADR, PDR, test, and coordination-note references as full paths from `spx/` — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([review])
- ALWAYS: emit lifecycle continuation state in the context manifest — local lifecycle overlays read, default-branch completion boundary, the governed next workflow, a progress verdict rule, and a continuation action when a changeset is destined for the default branch — so context loading carries the merge obligation into the workflow that follows ([review])
- NEVER: proceed with partial context — abort if any required document is missing ([review])
- NEVER: infer implementation state from test imports during context loading — implementation state is unknown unless another workflow establishes it ([review])
