# PLAN: Land SPX-CLI context enumeration

## Status

The architecture is decided in
`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`:
the target architecture derives a target's complete read-set from
`spx spec context --json`, with the deterministic tree walk and
cited-governance decision resolver living in the SPX CLI as a trusted third
party per `spx/12-shipped-scripting.adr.md`. The current `/contextualize` skill
keeps structural enumeration locally until the published CLI capability satisfies
that contract, while it already reads cited full-path ADR/PDR governance decisions
from loaded specs and decisions.

`spx spec context` is published in `spx` 0.6.16, while the repository floor plus
CI pin remain 0.6.15. The publication gate is clear; the consuming floor has not
advanced to the observed release. Consumption also remains BLOCKED because the
published JSON contract does not yet satisfy
`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`:
it emits `documents`, `methodology`, `productDir`, `siblings`, and `target`, but
omits a cited governance decision observed for this node and exposes no
citation provenance, guides, local overlays, bootstrap flag, or schema version.
The current skill-level cited-decision read therefore remains necessary while
the dependency contract is completed.

## The data already exists in spx

`spx spec status --json` already emits both inputs the derivation needs:

- `nodes` — the full tree: each node's full-path `id`, `kind`, `order`, `state`,
  and `children`.
- `decisions` — a flat array of every ADR/PDR with its full-path `id`, `kind`,
  `order`, `slug`.

From those two structures the structural read-set for any target is a pure
function: walk `nodes` to the target for the ancestor chain; for each ancestor
and the target, take its `{id}/{slug}.md` spec, the `decisions` whose `id` sits
directly in that directory, and the lower-`order` sibling specs at that level;
add product spec, coordination notes, and local overlays. The CLI then resolves
full-path ADR/PDR citations from the loaded specs and decisions, adding cited
methodology-governance decisions to the read-set once with citing-file
provenance. Coordination notes never drive citation loading.

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
    {
      "path": "spx/{governance}/{adr-or-pdr}",
      "role": "cited-governance-decision",
      "cited_by": "spx/{citing-spec-or-decision}"
    },
    {"path": "spx/{target}/PLAN.md", "role": "coordination-note"},
    {"path": "spx/{target}/ISSUES.md", "role": "coordination-note"}
  ],
  "siblings_listed_not_read": {
    "same_index": ["spx/{...}"],
    "higher_index": ["spx/{...}"]
  },
  "guides": ["CLAUDE.md", "spx/{ancestor}/CLAUDE.md"],
  "local_overlays": ["spx/local/{...}.md"],
  "bootstrap": false
}
```

Contract specifics:

- **Read order is deterministic and total**: product → each ancestor top-down →
  target; within a level, spec before its decisions before its lower-index
  siblings. Entries sharing an `order` index are tie-broken by `slug`, so the same
  tree contents and target always produce byte-identical `read_order` even where
  indices repeat.
- **All decisions at a level are emitted** — never filtered by title or by the
  lower-index rule. Decision ordering within a level follows `order`, then `slug`.
- **Lower-index siblings only** carry their spec; same-index and higher-index
  siblings go to `siblings_listed_not_read`, never into `read_order`.
- **Coordination notes** (`PLAN.md`/`ISSUES.md`) present at any level on the path
  are emitted with `role: coordination-note`.
- **Cited governance decisions** are emitted when a loaded spec or decision names
  a full `spx/.../*.adr.md` or `spx/.../*.pdr.md` path to a methodology
  governance decision outside the structural ancestry. They are ordered by first
  citation in the already-derived read order, de-duplicated by path, and carry
  `cited_by`. `PLAN.md`, `ISSUES.md`, and other coordination notes never add
  cited decisions.
- **Guides and overlays sit outside `read_order`**: the active runtime's product
  guide (`CLAUDE.md` for Claude Code or `AGENTS.md` for Codex, plus any
  same-runtime subdirectory guide on the path) is emitted in `guides` and the
  local overlays in `local_overlays`. Guides are read outside the
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

## Plugins-side structural-enumeration consumption (BLOCKED on contract completion)

This slice cannot ship until:

1. A published `spx spec context` release satisfies the output contract above,
   including cited-governance provenance and guide, overlay, bootstrap, and
   schema-version metadata.
2. `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) is advanced to
   that release.
3. CI `SPX_VERSION` (`.github/workflows/check.yml`) is bumped to the same
   published version or newer.

Once unblocked:

- Rewrite `src/plugins/spec-tree/skills/contextualize/SKILL.md` Steps 1–3: replace
  the per-level "glob ADRs/PDRs, read every one, count must match" prose with
  "run `spx spec context <target> --json`; read every path in `read_order`, then
  read the `guides` and the lifecycle overlay (`spx/local/merging.md`) outside the
  `read_order` loop while listing the remaining `local_overlays` without reading
  them; the `<SPEC_TREE_CONTEXT>` manifest enumerates exactly those paths and
  cited-governance provenance."
  Preserving the guide and `merging.md` reads keeps the product guide and
  lifecycle overlay in every context load without pulling in unrelated skill
  overlays. The agent no longer eyeballs the file set, so the skip and the
  read-higher-index-sibling failures become structurally impossible.
- Retag the read-completeness, lower-index-sibling, and determinism assertions in
  `context-loading.md` from `[audit]` to `[test]` against the CLI output — the
  enumeration is now code, so the determinism claim gains a real grader. Until
  the complete contract publishes, those CLI-output assertions and the governing
  ADR's rules stay `[audit]`; the node's foundation-manifest assertions carry
  their own `[test]` evidence independently of this consumption slice.
- `just build-skills`, then `instructions:skill-auditor` on the edited skill plus the
  spec and test-evidence auditor gates.

## Hand-off

SPX dependency session `2026-07-13_13-20-53` records the observed published
contract gap. Complete and publish `spx spec context` against the contract above;
return here for the consumption slice once the satisfying release exists and the
floor is advanced to it.

## Keep isolated verification dispatch context-free

### Problem

Operational verification dispatch passes exact committed refs, spec-node paths,
and artifact paths to configured isolated auditors and reviewers. Those values
are scope coordinates for the isolated session. Treating their transmission as
discussion of the governed node forces the main conversation to load the product
foundation and the node's complete context even when it will neither inspect nor
change product content. The extra loading increases latency and context use while
duplicating work that the isolated verifier must perform in its own session.

### Requirements

- The main conversation passes committed heads, ref ranges, node paths, and
  artifact paths unchanged to configured isolated auditors and reviewers as
  opaque scope inputs without loading the product foundation or contextualizing
  the named nodes.
- The exemption applies to every configured isolated audit and review role. It
  does not extend to general-purpose workers, explorers, or arbitrary delegated
  file reads.
- Spawning the isolated role, collecting and closing its handle, rendering its
  returned run or journal token, and recording its verdict and findings remain
  operational continuation. These actions do not count as product-content
  access or node discussion.
- Each isolated auditor or reviewer loads the foundation and node context its
  own workflow requires inside its isolated session. The main conversation does
  not preload or relay that content.
- A returned token, projection, verdict, finding location, or rejection remains
  operational data while the main conversation handles it without opening the
  referenced product artifacts.
- Before the main conversation first reads, searches, lists, or edits referenced
  product content to investigate or repair a finding, it establishes a live
  foundation and contextualizes every governing node required by that access.
- Compaction clears any product foundation and contextualized-node state held by
  the main conversation. It does not prevent context-free operational dispatch
  or result collection after compaction.

### Boundaries

- The exemption grants no product-file read or write authority.
- Rejecting or accepting a verifier finding without inspecting product content
  does not trigger context loading.
- Product-content access after dispatch follows the existing foundation and
  contextualization gates, including the post-compaction reset.
- The change preserves verifier role definitions, isolation, output contracts,
  handle lifecycle, and gate authority.

### Acceptance evidence

- A focused compliance case starts after compaction with a clean committed
  changeset, dispatches each configured isolated audit or review role from exact
  scope coordinates, and proves that the main conversation performs no product
  context load before dispatch or result collection.
- A focused compliance case receives a rejection or finding token and proves
  that recording and routing the result remains operational until the main
  conversation attempts product-content access.
- A focused compliance case attempts to open a referenced product path and
  proves that foundation loading and node contextualization become mandatory at
  that boundary.
- Generated Claude and Codex instruction surfaces express the same exemption and
  re-entry boundary.
- Focused tests, skill checks, documentation checks, instruction checks, and SPX
  validation pass for the exact committed changeset.

### Intended implementation order

1. Amend the context-loading spec and any governing decision needed to define
   opaque verification scope and the product-content re-entry boundary.
2. Align the authored instruction template and the `/contextualize` skill with
   the new operational exemption.
3. Add focused compliance coverage for opaque scope transmission,
   verifier-owned context loading, compaction behavior, and product-file
   re-entry.
4. Regenerate derived instruction surfaces and advance the plugin version.
5. Run the affected spec, skill, test-evidence, implementation, and changeset
   review gates.

### Interview decisions

- Desired behavior: context-free dispatch.
- Covered roles: all configured isolated verification roles.
- Reload boundary: immediately before main-conversation product-file access.
- Deliverable: requirements only in this PLAN; implementation remains a later
  slice.

## Done in this changeset

- Authored `spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`
  deciding the SPX-CLI structural enumeration target and the cited-governance
  decision loading rule.
- Re-founded `context-loading.md` on the ADR: the read-set includes cited
  methodology-governance decisions, while full structural enumeration through
  `spx spec context` remains blocked on the published CLI capability.
- Updated `src/plugins/spec-tree/skills/contextualize/SKILL.md` so the current
  runtime reads explicit full-path ADR/PDR citations from loaded specs and
  decisions before emitting `<SPEC_TREE_CONTEXT>`.
