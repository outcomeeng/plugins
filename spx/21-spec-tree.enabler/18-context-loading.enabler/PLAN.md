# PLAN: Route context read-set enumeration to the spx CLI

## Why this plan exists

`/contextualize` enumerates its read-set — product spec, ancestor specs, every
ancestor-level ADR/PDR, lower-index sibling specs, coordination notes, local
overlays — by agent-executed prose: the workflow globs each level and tells the
agent to "read every file" with a self-reported "glob count == read count"
check. Nothing forces it at runtime, so an agent can skip decision records and
the manifest's counts still pass (the manifest is written by the same agent that
was supposed to read). `context-loading.md` already declares the correct behavior
(read all ancestor specs and governing ADRs/PDRs; read every ADR/PDR returned by
globs; produce the same manifest for the same tree and target), but every one of
those assertions is `[audit]` — verified by reading the skill body, not by a
deterministic gate. A skip is the failure mode this work removes.

The fix routes the deterministic part — the tree walk and the per-target
read-set derivation — to the spx CLI, consumed by the plugins product as a
trusted third party per `spx/12-shipped-scripting.adr.md` ("once proven, that
logic belongs in the SPX CLI"). The complexity that resists isolated testing as
agent prose becomes a tested CLI capability.

## The data already exists in spx

`spx spec status --json` already emits both inputs the derivation needs:

- `nodes` — the full tree: each node's full-path `id`, `kind`, `order`, `state`,
  and `children`.
- `decisions` — a flat array of every ADR/PDR with its full-path `id`, `kind`,
  `order`, `slug`.

From those two structures the read-set for any target is a pure function: walk
`nodes` to the target to get the ancestor chain; for each ancestor and the
target, take its `{id}/{slug}.md` spec, the `decisions` whose `id` sits directly
in that directory, and the lower-`order` sibling specs at that level; add
product spec, coordination notes, and local overlays. No new traversal is
needed — only the derivation.

The precedent is already shipping: `spx session show --json` (consumed by the
pickup verifier) landed the same "spx parses, the plugin consumes structured
output" pattern. This plan applies it to context enumeration.

## Target capability (spx repo `~/Code/outcomeeng/spx/`)

Add `spx spec context <path> --json` emitting the ordered read-set for a target.
`spx spec --help` currently exposes only `status` and `next`; this is a new
sibling subcommand, a thin derivation over the existing `spec status` internals.

Output contract (ordered, top-down — the read order `/contextualize` must follow):

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
  "local_overlays": ["spx/local/{...}.md"],
  "bootstrap": false
}
```

Contract specifics:

- **Read order is deterministic and total**: product → each ancestor top-down →
  target; within a level, spec before its decisions before its lower-index
  siblings. The same tree and target always produce byte-identical `read_order`
  (satisfies `context-loading.md`'s determinism assertion as code, not prose).
- **All decisions at a level are emitted** — never filtered by title or by the
  lower-index rule. Decision ordering within a level follows `order`.
- **Lower-index siblings only** carry their spec; same-index and higher-index
  siblings go to `siblings_listed_not_read`, never into `read_order`.
- **Coordination notes** (`PLAN.md`/`ISSUES.md`) present at any level on the path
  are emitted with `role: coordination-note`.
- **Bootstrap**: a not-yet-existing target under an authoring operation returns
  `read_order` of the product spec only and `bootstrap: true`.
- **Missing required spec** (an ancestor directory with no `{slug}.md`) is a
  non-zero exit with the missing path on stderr — the CLI surfaces the abort the
  skill currently raises.

## Plugins-side consumption (BLOCKED on publish + floor advance)

The published-floor rule (`AGENTS.md`; `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`)
forbids depending on an unpublished spx capability. This slice cannot ship until:

1. `spx spec context` is released to npm.
2. `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) is advanced to
   that release.
3. CI `SPX_VERSION` (`.github/workflows/check.yml`) is bumped to a published
   version at or above the floor.

Once unblocked:

- Rewrite `src/plugins/spec-tree/skills/contextualize/SKILL.md` Steps 1–3: replace
  the per-level "glob ADRs/PDRs, read every one, count must match" prose with
  "run `spx spec context <target> --json`; read every path in `read_order`; the
  `<SPEC_TREE_CONTEXT>` manifest enumerates exactly those paths." The agent no
  longer eyeballs the file set, so the skip and the read-higher-index-sibling
  failures become structurally impossible.
- Add a `[test]`-backed assertion to `context-loading.md`: the read-set is the
  ordered output of `spx spec context --json` and is a deterministic function of
  the tree and target. This is the node's first `[test]` evidence — the
  enumeration is now code, so the determinism claim (currently `[audit]`) gains a
  real grader. The "read every ADR/PDR" and "lower-index siblings only"
  assertions retag from `[audit]` to `[test]` against the CLI output.
- `just build-skills`, then `develop:skill-auditor` on the edited skill plus the
  spec/test-evidence auditor gates.

## Hand-off

The CLI capability is spec-tree-methodology work in the external spx repo, the
same shape as the spx-CLI hand-offs tracked under
`spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md`. Build and test
`spx spec context` there against the contract above; return here for the
consumption slice once it is published and the floor is advanced.

## Done as part of this plan's changeset

- `context-loading.md` assertions migrated from the legacy `[review]` tag
  spelling to `[audit]`.
