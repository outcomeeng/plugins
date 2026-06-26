# PLAN: Land SPX-CLI context enumeration

## Status

The architecture is decided in
`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`:
context loading derives a target's read-set from `spx spec context --json`, the
deterministic tree walk living in the SPX CLI as a trusted third party per
`spx/12-shipped-scripting.adr.md`. `context-loading.md` is re-founded on that ADR.

What remains is implementation, and it is BLOCKED: the CLI capability does not yet
exist, and the published-floor rule (`AGENTS.md`;
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`)
forbids the consuming skill or its tests from depending on an unpublished `spx`
capability. No manual fallback in the skill closes this gap — the ADR's NEVER
rules forbid reconstructing the read-set outside the CLI.

## The data already exists in spx

`spx spec status --json` already emits both inputs the derivation needs:

- `nodes` — the full tree: each node's full-path `id`, `kind`, `order`, `state`,
  and `children`.
- `decisions` — a flat array of every ADR/PDR with its full-path `id`, `kind`,
  `order`, `slug`.

From those two structures the read-set for any target is a pure function: walk
`nodes` to the target for the ancestor chain; for each ancestor and the target,
take its `{id}/{slug}.md` spec, the `decisions` whose `id` sits directly in that
directory, and the lower-`order` sibling specs at that level; add product spec,
coordination notes, and local overlays. No new traversal is needed — only the
derivation.

## Target capability (spx repo `~/Code/outcomeeng/spx/`)

Add `spx spec context <path> --json` emitting the ordered read-set for a target.
`spx spec --help` currently exposes only `status` and `next`; this is a new
sibling subcommand, a thin derivation over the existing `spec status` internals.

Output contract (ordered, top-down — the read order `/contextualize` follows):

```text
{
  "version": 1,
  "target": "spx/{path}",
  "read_order": [
    {"path": "spx/{product}.product.md", "role": "product-spec"},
    {"path": "spx/{adr-or-pdr}", "role": "decision", "level": "product"},
    ...                                  # every product-level ADR/PDR
    {"path": "spx/{ancestor}/{slug}.md", "role": "ancestor-spec"},
    {"path": "spx/{ancestor}/{adr-or-pdr}", "role": "decision", "level": "{ancestor}"},
    {"path": "spx/{ancestor}/{lower-index-sibling}/{slug}.md", "role": "lower-index-sibling"},
    ...                                  # repeated per level down to the target
    {"path": "spx/{target}/{slug}.md", "role": "target-spec"},
    {"path": "spx/{target}/{adr-or-pdr}", "role": "decision", "level": "target"},
    {"path": "spx/{target}/PLAN.md", "role": "coordination-note"},
    {"path": "spx/{target}/ISSUES.md", "role": "coordination-note"}
  ],
  "siblings_listed_not_read": {
    "same_index": ["spx/{...}"],
    "higher_index": ["spx/{...}"]
  },
  "guides": ["spx/CLAUDE.md", "spx/{ancestor}/CLAUDE.md"],
  "local_overlays": ["spx/local/{...}.md"],
  "bootstrap": false
}
```

Contract specifics:

- **Read order is deterministic and total**: product → each ancestor top-down →
  target; within a level, spec before its decisions before its lower-index
  siblings. Entries sharing an `order` index are tie-broken by `slug`, so the same
  tree and target always produce byte-identical `read_order` even where indices
  repeat.
- **All decisions at a level are emitted** — never filtered by title or by the
  lower-index rule. Decision ordering within a level follows `order`, then `slug`.
- **Lower-index siblings only** carry their spec; same-index and higher-index
  siblings go to `siblings_listed_not_read`, never into `read_order`.
- **Coordination notes** (`PLAN.md`/`ISSUES.md`) present at any level on the path
  are emitted with `role: coordination-note`.
- **Guides and overlays sit outside `read_order`**: the product guide
  (`spx/CLAUDE.md` plus any subdirectory guide on the path) is emitted in `guides`
  and the local overlays in `local_overlays`. Guides are read outside the
  `read_order` loop; among `local_overlays`, only the lifecycle overlay
  (`spx/local/merging.md`) is read, and the rest are listed for the skills that
  consume them. The skill rewrite preserves the current product-guide and
  `merging.md` reads rather than dropping them, and does not start reading the
  other overlays.
- **Bootstrap**: a not-yet-existing target under an authoring operation returns
  `read_order` of the product spec only and `bootstrap: true`.
- **Missing required spec** (an ancestor directory with no `{slug}.md`) is a
  non-zero exit with the missing path on stderr — the CLI surfaces the abort the
  skill currently raises.

## Plugins-side consumption (BLOCKED on publish + floor advance)

This slice cannot ship until:

1. `spx spec context` is released to npm.
2. `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) is advanced to
   that release.
3. CI `SPX_VERSION` (`.github/workflows/check.yml`) is bumped to a published
   version at or above the floor.

Once unblocked:

- Rewrite `src/plugins/spec-tree/skills/contextualize/SKILL.md` Steps 1–3: replace
  the per-level "glob ADRs/PDRs, read every one, count must match" prose with
  "run `spx spec context <target> --json`; read every path in `read_order`, then
  read the `guides` and the lifecycle overlay (`spx/local/merging.md`) outside the
  `read_order` loop while listing the remaining `local_overlays` without reading
  them; the `<SPEC_TREE_CONTEXT>` manifest enumerates exactly those paths."
  Preserving the guide and `merging.md` reads keeps the product guide and
  lifecycle overlay in every context load without pulling in unrelated skill
  overlays. The agent no longer eyeballs the file set, so the skip and the
  read-higher-index-sibling failures become structurally impossible.
- Retag the read-completeness, lower-index-sibling, and determinism assertions in
  `context-loading.md` from `[audit]` to `[test]` against the CLI output — the
  enumeration is now code, so the determinism claim gains a real grader. This is
  the node's first `[test]` evidence; until the capability publishes, the ADR's
  rules and these assertions stay `[audit]`.
- `just build-skills`, then `develop:skill-auditor` on the edited skill plus the
  spec and test-evidence auditor gates.

## Hand-off

The CLI capability is spec-tree-methodology work in the external spx repo, the
same shape as the spx-CLI hand-offs tracked under
`spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md`. Build and test
`spx spec context` there against the contract above; return here for the
consumption slice once it is published and the floor is advanced.

## Done in this changeset

- Authored `spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`
  deciding the SPX-CLI enumeration architecture and forbidding any manual
  read-set reconstruction.
- Re-founded `context-loading.md` on the ADR: the read-set is derived from
  `spx spec context`, and the "read every ADR/PDR" assertion no longer names the
  agent-glob mechanism.
