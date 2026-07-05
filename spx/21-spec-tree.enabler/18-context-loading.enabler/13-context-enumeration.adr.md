# Context Enumeration via the SPX CLI

Context loading derives a target's complete read-set — product spec, ancestor specs, every ancestor- and target-level decision record, lower-index sibling specs, coordination notes, explicit full-path methodology-governance decisions cited by loaded specs or decisions, guides, and local overlays — from the structured output of the `spx spec context --json` CLI capability, with the deterministic tree walk and per-target derivation living in the SPX CLI as a trusted third-party component per `spx/12-shipped-scripting.adr.md`. The read order is total and a pure function of the tree, target, and citations in loaded spec or decision files. Agent-executed glob-and-count enumeration is not a context-loading mechanism, and the read-set never follows references scanned out of coordination-note prose.

## Rationale

Agent-executed enumeration — glob each level, read every file, self-report that the glob count equals the read count — places the completeness guarantee in instructions the same context both follows and attests, so a skipped decision record passes its own check and the manifest's counts still hold. Deriving the read-set in the SPX CLI moves the tree walk into a component tested in its own right and consumed as structured output, so completeness, ordering, and determinism are properties of code rather than of agent diligence — the shipped-scripting lifecycle's "proven complexity belongs in the SPX CLI, consumed as a trusted third party" applied to context enumeration. The substrate exists: `spx spec status --json` emits the full node tree and the flat decision set from which a target's read-set is a pure derivation, the same "spx parses, the plugin consumes structured output" boundary the pickup claim verifier consumes through `spx session show --json`.

Restricting the structural read-set to deterministic derivation keeps context loading predictable while still allowing specs and decisions to declare cross-tree methodology governance by full path. A cited methodology-governance ADR or PDR is a durable declaration in product truth, unlike a coordination note; the CLI resolves those citations from already-loaded specs and decisions and emits the cited decisions with explicit provenance. Loading governing references named inside coordination-note prose remains excluded: a prose scan reintroduces the heuristic the structural derivation exists to remove, and a coordination note is a stale-prone input reconciled against product truth, never an authority that steers the read-set.

## Invariants

- The read order is total and byte-identical for the same tree contents and target.
- Read order is product spec, then each ancestor top-down, then the target; within a level, the spec precedes its decision records, which precede its lower-index sibling specs; decision records and sibling specs that share an index are ordered by slug, so the order is total even where indices repeat.
- Every decision record at a level is in the read-set, ordered by index, never filtered by title.
- A lower-index sibling carries its spec into the read-set; same-index and higher-index siblings are listed, not read.
- Coordination notes (`PLAN.md`, `ISSUES.md`) present at any level on the path are in the read order, after that level's decision records.
- Full `spx/.../*.adr.md` and `spx/.../*.pdr.md` citations in specs or decision records add cited methodology-governance decisions to the read-set exactly once, ordered by first citation in the already-derived read order.
- Instruction files — the active root harness instruction file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex), plus any on-path subdirectory instruction file with that harness's instruction filename, in path order from the root — are enumerated as a distinct set outside the ordered read order. The root instruction file's managed Spec Tree instruction block carries the product-root methodology instructions; obsolete `spx/CLAUDE.md` and `spx/AGENTS.md` are not instruction inputs.
- Local overlays are enumerated as a distinct set, not interleaved into the ordered read order.

## Verification

### Audit

- ALWAYS: `/contextualize` derives a target's read-set from the structured output of `spx spec context --json`, reads the ordered read-order paths in their enumerated order, reads the guides and the lifecycle overlay (`spx/local/merging.md`) outside that order, and lists the remaining local overlays without reading them — those are consumed by the skills they configure ([audit])
- ALWAYS: the deterministic tree walk and per-target read-set derivation live in the SPX CLI, consumed by context loading as a trusted third-party component per `spx/12-shipped-scripting.adr.md` ([audit])
- ALWAYS: `spx spec context --json` includes explicit full-path methodology-governance ADR/PDR citations from loaded specs and decisions in the read-set, with provenance that names the citing file ([audit])
- NEVER: context loading enumerates its read-set by agent-executed globbing with a self-reported read-count check, or by any manual fallback that reconstructs the read-set outside the CLI ([audit])
- NEVER: context loading scans coordination-note prose for governing references — coordination notes do not affect the read-set ([audit])
