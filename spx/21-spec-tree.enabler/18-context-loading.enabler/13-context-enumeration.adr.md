# Context Enumeration via the SPX CLI

Context loading derives a target's complete read-set — product spec, ancestor specs, every ancestor- and target-level decision record, lower-index sibling specs, coordination notes, guides, and local overlays — from the structured output of the `spx spec context --json` CLI capability, with the deterministic tree walk and per-target derivation living in the SPX CLI as a trusted third-party component per `spx/12-shipped-scripting.adr.md`. The read order is total and a pure function of the tree and target. Agent-executed glob-and-count enumeration is not a context-loading mechanism, and the read-set is a function of tree structure alone, never of references scanned out of coordination-note prose.

## Rationale

Agent-executed enumeration — glob each level, read every file, self-report that the glob count equals the read count — places the completeness guarantee in instructions the same context both follows and attests, so a skipped decision record passes its own check and the manifest's counts still hold. Deriving the read-set in the SPX CLI moves the tree walk into a component tested in its own right and consumed as structured output, so completeness, ordering, and determinism are properties of code rather than of agent diligence — the shipped-scripting lifecycle's "proven complexity belongs in the SPX CLI, consumed as a trusted third party" applied to context enumeration. The substrate exists: `spx spec status --json` emits the full node tree and the flat decision set from which a target's read-set is a pure derivation, the same "spx parses, the plugin consumes structured output" boundary the pickup claim verifier consumes through `spx session show --json`.

Restricting the read-set to structural derivation keeps it a pure function of tree position. Loading governing references named inside coordination-note prose is a distinct concern this decision does not adopt: a prose scan reintroduces the heuristic the structural derivation exists to remove, and a coordination note is a stale-prone input reconciled against product truth, never an authority that steers the read-set.

## Invariants

- The read order is total and byte-identical for the same tree and target.
- Read order is product spec, then each ancestor top-down, then the target; within a level, the spec precedes its decision records, which precede its lower-index sibling specs; decision records and sibling specs that share an index are ordered by slug, so the order is total even where indices repeat.
- Every decision record at a level is in the read-set, ordered by index, never filtered by title.
- A lower-index sibling carries its spec into the read-set; same-index and higher-index siblings are listed, not read.
- Coordination notes (`PLAN.md`, `ISSUES.md`) present at any level on the path are in the read order, after that level's decision records.
- Guides — the active root harness guide file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex), plus any on-path subdirectory guide file with that harness's guide filename, in path order from the root — are enumerated as a distinct set outside the ordered read order. The root guide's managed Spec Tree Guide section carries the product-root methodology guide; obsolete `spx/CLAUDE.md` and `spx/AGENTS.md` are not guide inputs.
- Local overlays are enumerated as a distinct set, not interleaved into the ordered read order.

## Verification

### Audit

- ALWAYS: `/contextualize` derives a target's read-set from the structured output of `spx spec context --json`, reads the ordered read-order paths in their enumerated order, reads the guides and the lifecycle overlay (`spx/local/merging.md`) outside that order, and lists the remaining local overlays without reading them — those are consumed by the skills they configure ([audit])
- ALWAYS: the deterministic tree walk and per-target read-set derivation live in the SPX CLI, consumed by context loading as a trusted third-party component per `spx/12-shipped-scripting.adr.md` ([audit])
- NEVER: context loading enumerates its read-set by agent-executed globbing with a self-reported read-count check, or by any manual fallback that reconstructs the read-set outside the CLI ([audit])
- NEVER: context loading scans coordination-note prose for governing references — the read-set is a function of tree structure alone ([audit])
