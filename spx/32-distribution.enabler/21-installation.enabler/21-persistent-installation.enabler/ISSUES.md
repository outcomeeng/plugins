# Installation evidence gaps

## Cross-plugin agent-home cleanup is reachable only through the maintainers' installer

`spx/32-distribution.enabler/21-installation.enabler/12-installation-state.pdr.md` separates a plugin's namespace-bounded
placement from marketplace-scope reconciliation — the pass that prunes
definitions of plugins later removed or renamed from the catalog under the
marketplace's recorded ownership. The shipped `place_agents.py` implements only
its own plugin's namespace; the marketplace-scope pass lives in
`outcomeeng/distribution/installation.py` and is reachable solely through
`just install-marketplace` in this repository. An ordinary consumer whose
`$CODEX_HOME/agents/` carries a definition for a plugin the catalog no longer
publishes has no shipped path to prune it: the definition stays until the
consumer removes it by hand.

The retired plan for this node proposed embedding a committed-catalog snapshot,
stamped with a deterministic catalog revision, in each plugin's shipped tree so
any single plugin's lifecycle skill could run the marketplace-scope pass. That
mechanism was not built; the ownership record shipped instead, which lets the
maintainers' installer prune safely but gives a shipped script no view of the
current catalog.

**Resolution shape**: either ship the consumer-reachable marketplace-scope pass —
an embedded catalog snapshot the shipped script consults, or an `spx` command
that reads the marketplace source directly — or narrow the decision's
reconciliation invariant to the maintainers' installer and say so where the
consumer would look for the missing prune.

**Revisit condition**: before a plugin is removed or renamed in the catalog,
since that is the event that leaves a stale owned definition in consumer homes.

**Evidence**: raised by changeset review `2026-08-17_01-03-44-668-0ddd9fe582a1`.
