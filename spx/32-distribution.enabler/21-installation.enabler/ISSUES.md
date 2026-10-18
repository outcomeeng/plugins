# Issues: Installation

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## Agent-specific behavior is enumerated inside product-level decisions

Product-level decisions carry per-agent facts inline, so adding an agent harness edits decisions whose subject is not that harness. [`spx/12-marketplace-state.adr.md`](spx/12-marketplace-state.adr.md) enumerates each agent's committed marketplace catalog, plugin-selection boundary and configuration location: Codex's `.agents/plugins/marketplace.json` and caller-selected `CODEX_HOME` beside Claude Code's `.claude-plugin/marketplace.json` and project-scope `.claude/settings.json`. A third agent harness churns a decision that governs state ownership rather than agent identity. The build decision [`spx/18-plugin-build.enabler/15-build-architecture.adr.md`](spx/18-plugin-build.enabler/15-build-architecture.adr.md) now resolves per-target agent format, filename shape and namespace behavior from the source-owned per-target registry, so a new target is a registry entry; the catalog and state-boundary enumeration in the marketplace-state decision is the remaining per-agent coupling.

**Settlement condition.** A `coding-agents` node, placed through `/decompose`, has one child per agent, each declaring its own agent's capabilities and configuration locations: whether its plugin manifest can declare agents, whether its agent namespace is flat, its native agent format and filename shape, and the committed configuration it reads. The marketplace-state decision then collapses to capability assertions of the form "each agent declares capability X, verified by that agent's node" and "agent-specific behavior is decided only in that agent's node", so a new harness adds a child.

**Revisit condition.** Resolve before a third agent harness ships, since that is the change the coupling taxes. The agent-harness terminology sweep in `spx/18-plugin-build.enabler/ISSUES.md` can share the decomposition.

## DEBT [evidence]: installation mapping and compliance tests leave inputs unvaried (f-003, f-004)

Two filed findings (severity FILED) on tests under
`spx/32-distribution.enabler/21-installation.enabler/tests/`, numbered as in the
test-evidence audit verdict on this node at head
`18ad3df27fa85898687bfc3c196ff7c9901db240`:

- f-003 at `test_installation.mapping.l1.py` (alignment, remediation target
  harness): the mapping never drives the scope, project-path, or marketplace
  filter of the reported inventory. The verdict's message reads: "Standing
  defect. The mapping never drives the scope, project-path, or marketplace
  filter of the reported inventory. observe_persistent_catalog_subset_plans
  feeds _plugin_listing_payload, which lists only project-scope records at the
  invocation checkout. generated_claude_listing_entries, which varies scope and
  path, is not used here. The diff touches this function only to rename Agent to
  Target, so no changed basis is named." Its `baseRefEvidence` is
  `b9e1245462c8f5e345beb67140cd0eedab28861c..HEAD`.
- f-004 at `test_installation.compliance.l1.py` (oracle independence,
  remediation target independent-oracle): the selected homes are compared with
  values production computes. The verdict's message reads: "Standing defect.
  Each command's CODEX_HOME is compared with plan.roots.codex_home, and the
  isolated state root with plan.roots.state. Production computes both, so a
  mutation that ignores the caller-selected home passes. The diff touches these
  test functions only for the Agent to Target rename, so no changed basis is
  named." Its `baseRefEvidence` is
  `b9e1245462c8f5e345beb67140cd0eedab28861c..HEAD`.

The verdict carries no sealed run token.

**Resolution shape**: for f-003, drive the mapping with
`generated_claude_listing_entries` and `generated_codex_listing_entries`, as the
child repository-installation mapping test does. For f-004, expose the
harness-chosen homes in the observation and compare each command's
`CODEX_HOME` and the isolated state root with them.

**Evidence that the text lies outside the change.** The verdict names no changed
basis for either finding: against `b9e1245462c8f5e345beb67140cd0eedab28861c..HEAD`
the changeset touches the cited test functions only for the rename from Agent to
Target. The cited tests and the filter and home comparisons they leave unvaried
predate the changeset.

**Invalidation check.** The changeset renames Agent to Target in
`outcomeeng/distribution/installation.py`,
`outcomeeng_testing/harnesses/installation.py`,
`outcomeeng_testing/generators/installation.py`, and the cited tests, and
repairs two other findings of the same verdict (f-001 and f-002) in those tests.
The rename changes identifiers only. It changes neither the scope, project-path,
and marketplace filtering that `installed_plugin_names` performs, nor the
derivation of `plan.roots.codex_home` and `plan.roots.state`, so the cited text
neither cites, restates, nor depends on a change that falsifies it.

**Settlement condition**: the mapping rejects an inventory that stops filtering
on scope, project path, or marketplace, and the compliance test rejects a plan
that ignores the selected `CODEX_HOME` or isolated state root.
