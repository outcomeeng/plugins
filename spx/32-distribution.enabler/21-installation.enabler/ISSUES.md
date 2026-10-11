# Issues: Installation

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## Agent-specific behavior is enumerated inside product-level decisions

Product-level decisions carry per-agent facts inline, so adding an agent harness edits decisions whose subject is not that harness. [`spx/12-marketplace-state.adr.md`](spx/12-marketplace-state.adr.md) enumerates each agent's committed marketplace catalog, plugin-selection boundary and configuration location: Codex's `.agents/plugins/marketplace.json` and caller-selected `CODEX_HOME` beside Claude Code's `.claude-plugin/marketplace.json` and project-scope `.claude/settings.json`. A third agent harness churns a decision that governs state ownership rather than agent identity. The build decision [`spx/18-plugin-build.enabler/15-build-architecture.adr.md`](spx/18-plugin-build.enabler/15-build-architecture.adr.md) now resolves per-target agent format, filename shape and namespace behavior from the source-owned per-target registry, so a new target is a registry entry; the catalog and state-boundary enumeration in the marketplace-state decision is the remaining per-agent coupling.

**Settlement condition.** A `coding-agents` node, placed through `/decompose`, has one child per agent, each declaring its own agent's capabilities and configuration locations: whether its plugin manifest can declare agents, whether its agent namespace is flat, its native agent format and filename shape, and the committed configuration it reads. The marketplace-state decision then collapses to capability assertions of the form "each agent declares capability X, verified by that agent's node" and "agent-specific behavior is decided only in that agent's node", so a new harness adds a child.

**Revisit condition.** Resolve before a third agent harness ships, since that is the change the coupling taxes. The agent-harness terminology sweep in `spx/18-plugin-build.enabler/ISSUES.md` can share the decomposition.

## DEBT [evidence]: installation mapping and compliance tests leave inputs unvaried (f-001, f-002, f-003)

Two findings (both REJECT) on tests under
`spx/32-distribution.enabler/21-installation.enabler/tests/`, and one warning on
the generator that feeds them:

- f-001 at `test_installation.mapping.l1.py` (alignment): the mapping never
  drives the scope and marketplace filter of the reported inventory. Every
  listing the harness feeds (`_plugin_listing_payload`) carries only
  project-scope records at the invocation checkout, or Codex entries of the
  product's own marketplace, so `installed_plugin_names` could stop filtering on
  scope, project path, or marketplace and the test would still pass.
- f-002 at `test_installation.compliance.l1.py` (oracle independence): the
  selected homes are never compared with the values the caller selected. Each
  command's `CODEX_HOME` is compared with `plan.roots.codex_home`, which
  production computes, and the isolated state root with the plan's own
  `roots.state`. A mutation that ignores the selected `CODEX_HOME` passes.
- WARNING f-003 at `outcomeeng_testing/generators/installation.py:111`:
  `generated_valid_catalog_subsets` and `generated_invalid_catalog_subsets`
  produce one rotating-window subset per size class, with no recorded rationale
  and no complete enumeration.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run
token.

**Resolution shape**: for f-001, drive the mapping with
`generated_claude_listing_entries` and `generated_codex_listing_entries`, as the
child repository-installation mapping test does. For f-002, expose the
harness-chosen homes in the observation and compare each command's
`CODEX_HOME` and the isolated state root with them. For f-003, record the
rationale for the rotating window in the generator, or enumerate the subsets
completely.

**Evidence that the text lies outside the change.**
`git diff -U0 origin/main...HEAD` reports no hunk in the cited tests, harness,
or generator, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py` (model prices, `UsageTokenClass`,
`UnpricedModelError`, `resolve_model_price`; no existing symbol changes), adds
the model-price and profile-binding generators, harnesses, and tests, and
narrows the configuration guard in
`outcomeeng/validation/profile_configuration.py`. The cited tests drive
`outcomeeng/distribution/installation.py`, which the changeset does not change.

**Settlement condition**: the mapping rejects an inventory that stops filtering
on scope, project path, or marketplace; the compliance test rejects a plan that
ignores the selected `CODEX_HOME`; and the catalog-subset generators either
enumerate every subset or state why one subset per size class suffices.
