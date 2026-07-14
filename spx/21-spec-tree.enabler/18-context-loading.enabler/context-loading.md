# Context Loading

PROVIDES deterministic context loading that walks the tree from product root to target, collecting all ancestor specs, lower-index sibling specs, ADRs/PDRs, cited methodology-governance decisions, coordination notes, guides, and local overlays
SO THAT all implementation and authoring skills
CAN operate with complete, verified context before any work begins

## Assertions

### Properties

- Produces the same context manifest for the same tree contents and target ([audit])

### Compliance

- ALWAYS: bring a behind-base branch current through sync-base (`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md`) before reading product or spec context, so loaded context reflects current product truth rather than a stale branch ([audit])
- ALWAYS: when sync-base reports `already_current` or `rebased` during context loading, record the sync status only as context-load state and continue directly to locating the same target before answering or doing branch lifecycle work; loading the skill and completing sync-base are prerequisites, not context ([audit])
- ALWAYS: when sync-base reports `dirty_tree` during context loading — uncommitted tracked changes block the rebase so the branch may still be behind — surface that loaded context may be stale and proceed; context loading never commits or stashes the operator's in-progress work, distinguishing it from the merge lifecycle, which commits then re-syncs ([audit])
- ALWAYS: before any filesystem lookup, accept a target only when it is the canonical product-root address `spx/` or a full repository-relative node address whose segments each match `{index}-{slug}.{enabler|outcome}`; reject a missing target, traversal segment, empty segment, or malformed node segment before deriving the read-set ([audit])
- ALWAYS: derive the target read-set from the deterministic enumeration decided in `spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`, reading the ordered read-set in its enumerated order, reading the guides and the lifecycle overlay outside that order, and listing the remaining local overlays without reading them ([audit])
- ALWAYS: abort with the missing file path and remediation guidance when a required ancestor spec is absent ([audit])
- ALWAYS: when the canonical product-root target `spx/` is contextualized against a tree with one product spec and no node directories, emit the product-root context manifest with `bootstrap=true`; a missing node target aborts, and new-node authoring contextualizes the existing parent ([audit])
- ALWAYS: read lower-index sibling specs as target constraints and list same-index or higher-index siblings without reading them as constraints ([audit])
- ALWAYS: read every ADR/PDR in the target read-set — do not filter by title relevance ([audit])
- ALWAYS: include full-path methodology-governance ADR/PDR citations from loaded specs and decisions in the target read-set, so specs outside the methodology subtree can depend on governance decisions that are not structural ancestors ([audit])
- ALWAYS: list target spec test links and co-located test files without reading test file bodies — test-body inspection belongs to `/test`, `/audit-tests`, and `/apply` ([audit])
- ALWAYS: emit node, ADR, PDR, test, and coordination-note references as full paths from `spx/` — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([audit])
- ALWAYS: emit lifecycle continuation state in the context manifest — local lifecycle overlays read, default-branch completion boundary, the governed next workflow, a progress verdict rule, and a continuation action when a changeset is destined for the default branch — so context loading carries the merge obligation into the workflow that follows ([audit])
- ALWAYS: treat the `SPEC_TREE_FOUNDATION` marker as absent after every compaction event until `/understand` re-emits it in the resuming conversation ([audit])
- ALWAYS: require a live `SPEC_TREE_FOUNDATION` marker before direct filesystem access to any path under `spx/`, or before reading, searching, listing, or changing source or test files; operational-state commands under `spx session`, `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology remain available without the marker until their output is followed into product content ([audit])
- NEVER: proceed with partial context — abort if any required document is missing ([audit])
- NEVER: add a cited governance decision to the read-set from `PLAN.md`, `ISSUES.md`, or any other coordination-note prose ([audit])
- NEVER: accept a `SPEC_TREE_FOUNDATION` mention in a compaction summary, session file, handoff note, prior-run description, or statement that `/understand` ran as evidence that the marker is live ([audit])
- NEVER: infer implementation state from test imports during context loading — implementation state is unknown unless another workflow establishes it ([audit])
