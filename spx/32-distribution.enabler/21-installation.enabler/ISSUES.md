# Issues: Installation

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## Agent-specific behavior is enumerated inside product-level decisions

Product-level decisions carry per-agent facts inline, so adding an agent harness edits decisions whose subject is not that harness. `spx/12-marketplace-state.adr.md` enumerates each agent's committed marketplace catalog, plugin-selection boundary and configuration location: Codex's `.agents/plugins/marketplace.json` and caller-selected `CODEX_HOME` beside Claude Code's `.claude-plugin/marketplace.json` and project-scope `.claude/settings.json`. A third agent harness churns a decision that governs state ownership rather than agent identity. The build decision `spx/18-plugin-build.enabler/15-build-architecture.adr.md` now resolves per-target agent format, filename shape and namespace behavior from the source-owned per-target registry, so a new target is a registry entry; the catalog and state-boundary enumeration in the marketplace-state decision is the remaining per-agent coupling.

**Settlement condition.** A `coding-agents` node, placed through `/decompose`, has one child per agent, each declaring its own agent's capabilities and configuration locations: whether its plugin manifest can declare agents, whether its agent namespace is flat, its native agent format and filename shape, and the committed configuration it reads. The marketplace-state decision then collapses to capability assertions of the form "each agent declares capability X, verified by that agent's node" and "agent-specific behavior is decided only in that agent's node", so a new harness adds a child.

**Revisit condition.** Resolve before a third agent harness ships, since that is the change the coupling taxes. The agent-harness terminology sweep in `spx/18-plugin-build.enabler/ISSUES.md` can share the decomposition.
