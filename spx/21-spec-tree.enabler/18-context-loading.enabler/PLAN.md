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

## Keep named verification dispatch context-free

### Problem

The authoring agent session already holds exact committed refs and recorded
scope coordinates when it reaches an agentic verification gate. Passing those
coordinates to a verifier agent session currently risks being classified as
discussion of the governed node, which forces the authoring session to reload
the live `<SPEC_TREE_FOUNDATION>` marker and complete node context before it can
dispatch. The verifier agent session must load its own context to produce an
independent verdict, so author-side preloading duplicates work and consumes the
context needed to act on the result.

### Operational-continuation requirement

Extend the existing operational-continuation enumeration in
`spx/21-spec-tree.enabler/spec-tree.md` and the managed router with one
harness-neutral operation. Keep `/understand` independently invocable and
limited to product-content classification plus foundation-marker output:

> Dispatching a named verifier or reviewer role from recorded scope
> coordinates, collecting its result, rendering its returned token or
> projection, and recording its verdict and findings touches no product content
> and triggers neither `/understand` nor `/contextualize`.

The operation has these requirements:

- A named role is an audit or review role with a role-task contract in the
  managed instruction block. Add a path-only managed contract for
  `spec-tree:changeset-coherence-auditor` so this isolated audit role shares the
  boundary with the other auditor roles. The operation excludes implementation
  runners such as `spec-tree:applier`, simplifier agents, updater agents,
  general-purpose workers, explorers, and arbitrary delegated reads.
- Scope coordinates are operational data recorded before dispatch in a source
  the authoring agent session may read without the foundation marker: the exact
  commit and its `Refs:` trailer, the session store, or sealed journal scope
  events. After compaction, the authoring agent session never derives a governing
  node by searching product content. An absent recorded coordinate makes that
  derivation product-content access and activates the normal gates.
- Every named role-task contract accepts path-only coordinates. Assertion text,
  producer artifacts, language-scope classification, and
  owning-plugin classifications are resolved by the verifier agent session from
  those paths after it establishes its own live `<SPEC_TREE_FOUNDATION>` marker
  and contextualized-node set. The authoring agent session neither preloads nor
  relays content-bearing fields.
- The verifier agent session invokes `/contextualize --at <full-head-oid>` for
  each governing node. Exact-commit mode requires the checkout HEAD to equal the
  recorded subject and skips `/sync-base`; a mismatch blocks before product
  access, so concurrent verifiers never rebase or advance the authoring checkout.
- `spx journal` and `spx verification` read, list, and render operations are
  operational commands under the same boundary as `spx session`,
  `spx worktree status`, and `spx diagnose`. Following any path from their
  output into product content activates the normal gates.
- Compaction clears the authoring agent session's live foundation marker,
  contextualized-node set, and remembered deterministic-verification result. A
  post-compaction agentic dispatch re-establishes deterministic passing evidence
  for the exact committed subject by rerunning the declared deterministic
  command and reading its tool output. A compaction summary or prior-run claim
  does not establish that precondition.
- A returned token, projection, verdict, finding location, or finding record is
  operational data while the authoring agent session handles it without opening
  a referenced product artifact or making a product judgment.

### Product-content re-entry and finding disposition

- Before the authoring agent session first reads, searches, lists, or edits
  product content for any purpose after dispatch, it establishes a live
  `<SPEC_TREE_FOUNDATION>` marker and contextualizes every governing node needed
  by that access.
- Accepting a finding as recorded and placing it in the conversation-local
  imperfection ledger for fix-now handling is operational.
- Rejecting, downgrading, dropping as unbacked, or deferring a finding is a
  product judgment. The authoring agent session establishes the live foundation
  marker and contextualizes the finding's governing node before making that
  decision.
- Writing a deferral to `PLAN.md` or `ISSUES.md` is product-content access under
  the same gates. A bounded valid finding remains fix-now, and a valid finding's
  defect class is swept across the touched nodes as required by
  `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`.
- The change preserves verifier-session isolation, output contracts, gate
  authority, and each harness's own handle-lifecycle rules. Harness-specific
  handle wording stays inside the matching generated harness region.

### Required evidence

- Add `[test]` render-compliance evidence under
  `spx/21-spec-tree.enabler/43-instruction-block.enabler`. Add a source-owned
  `NODE_CONTEXT_POLICY_REQUIREMENTS` tuple for the template's `Before working on
  a specific node` section, use `FOUNDATION_POLICY_REQUIREMENTS` for the
  `spx journal` and `spx verification` operational exemption, and use
  `SUBAGENT_DISPATCH_POLICY_REQUIREMENTS` for wording inside the `Sub-agent
  dispatch` section. Add `ROLE_TASK_CONTRACT_POLICY_REQUIREMENTS`, anchored to
  `Quick Reference: Skills and Agents`, for the managed role-task contracts.
  The test imports its expected substrings from those four tuples and fails
  when either generated harness surface omits the operational-continuation
  addition, path-only dispatch contract, or product-content re-entry boundary.
- Add `[audit]` assertions to
  `spx/21-spec-tree.enabler/18-context-loading.enabler/context-loading.md` for the
  managed router policy, path-only role contracts, verifier-owned context,
  immutable exact-commit contextualization, finding-disposition boundary, and
  post-compaction deterministic precondition.
- The new assertions cover policy design through `[audit]` and rendered policy
  presence through `[test]`. Focused SPX validation,
  render-compliance tests, skill checks, documentation checks, instruction
  checks, affected auditors, and changeset review pass on the same committed
  subject.

### Exact implementation surfaces and order

1. Amend `spx/21-spec-tree.enabler/spec-tree.md` to extend its
   operational-continuation assertion, then amend
   `spx/21-spec-tree.enabler/18-context-loading.enabler/context-loading.md` with
   the new `[audit]` assertions. Add the linking `[test]` assertion to
   `spx/21-spec-tree.enabler/43-instruction-block.enabler/instruction-block.md`,
   referencing the render-compliance test file. This refinement needs no new
   decision record.
2. Limit `src/plugins/spec-tree/skills/understand/SKILL.md` to caller-independent
   foundation output; amend the managed instruction template sections `Before
   product-content access`, `Before working on a specific node`, and `Sub-agent
   dispatch`;
   `FOUNDATION_POLICY_REQUIREMENTS`, `SUBAGENT_DISPATCH_POLICY_REQUIREMENTS`, and
   the new `NODE_CONTEXT_POLICY_REQUIREMENTS` and
   `ROLE_TASK_CONTRACT_POLICY_REQUIREMENTS` tuples in
   `outcomeeng/distribution/instruction_block.py`; and every named role-task
   contract that currently requires a content-bearing field. Add the managed
   path-only contract for `spec-tree:changeset-coherence-auditor`. Update every
   agent definition whose body restates a caller-supplied content-bearing
   contract, including `src/plugins/spec-tree/agents/adr-auditor.md` and
   `src/plugins/spec-tree/agents/pdr-auditor.md`.
3. Use `src/plugins/prose/skills/audit-prose/SKILL.md` as the current concrete
   audit-workflow model and
   `src/plugins/instructions/skills/audit-skill/SKILL.md` as the structural
   auditor-skeleton model when converting role-task contracts to path-only
   inputs.
4. Author the instruction-render compliance test from the source-owned policy
   tuples.
5. Run `just bump`, `just build-skills`, `just build-instructions`, and
   `just instructions-check` in that order.
6. Run focused deterministic verification, the affected spec, skill,
   test-evidence, and implementation audits; one `subagent-auditor` dispatch per
   changed agent configuration path; and changeset review.

### Interview decisions

- Desired behavior: context-free dispatch from recorded operational scope.
- Covered roles: every audit or review role named by a managed role-task
  contract, including `spec-tree:changeset-coherence-auditor`.
- Reload boundary: immediately before any authoring-agent-session product-content
  access or product judgment.
- Deliverable: one final requirements review, followed by prototype
  implementation.
