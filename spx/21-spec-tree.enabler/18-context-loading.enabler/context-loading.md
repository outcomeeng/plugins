# Context Loading

PROVIDES deterministic context loading that walks the tree from product root to target, collecting all ancestor specs, lower-index sibling specs, ADRs/PDRs, coordination notes, guides, and local overlays
SO THAT all implementation and authoring skills
CAN operate with complete, verified context before any work begins

## Assertions

### Compliance

- ALWAYS: bring a behind-base branch current through sync-base (`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md`) before reading product or spec context, so loaded context reflects current product truth rather than a stale branch ([audit])
- ALWAYS: when sync-base reports `dirty_tree` during context loading — uncommitted tracked changes block the rebase so the branch may still be behind — surface that loaded context may be stale and proceed; context loading never commits or stashes the operator's in-progress work, distinguishing it from the merge lifecycle, which commits then re-syncs ([audit])
- ALWAYS: derive the target read-set from the deterministic enumeration decided in `spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`, reading the ordered read-set in its enumerated order, reading the guides and the lifecycle overlay outside that order, and listing the remaining local overlays without reading them ([audit])
- ALWAYS: abort with the missing file path and remediation guidance when a required ancestor spec is absent ([audit])
- ALWAYS: return an empty bootstrap manifest when authoring against an empty tree with only a product spec ([audit])
- ALWAYS: read lower-index sibling specs as target constraints and list same-index or higher-index siblings without reading them as constraints ([audit])
- ALWAYS: produce the same context manifest for the same tree structure and target ([audit])
- ALWAYS: read every ADR/PDR in the target read-set — do not filter by title relevance ([audit])
- ALWAYS: list target spec test links and co-located test files without reading test file bodies — test-body inspection belongs to `/test`, `/audit-tests`, and `/apply` ([audit])
- ALWAYS: emit node, ADR, PDR, test, and coordination-note references as full paths from `spx/` — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([audit])
- ALWAYS: emit lifecycle continuation state in the context manifest — local lifecycle overlays read, default-branch completion boundary, the governed next workflow, a progress verdict rule, and a continuation action when a changeset is destined for the default branch — so context loading carries the merge obligation into the workflow that follows ([audit])
- NEVER: proceed with partial context — abort if any required document is missing ([audit])
- NEVER: infer implementation state from test imports during context loading — implementation state is unknown unless another workflow establishes it ([audit])
