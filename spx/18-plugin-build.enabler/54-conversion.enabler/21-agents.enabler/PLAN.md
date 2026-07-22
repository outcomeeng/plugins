# Plan

Governing decisions: `spx/12-marketplace-state.adr.md` (marketplace state ownership) and
`spx/18-plugin-build.enabler/15-build-architecture.adr.md` (build architecture).

## Defect this plan closes

A consumer whose agent harness cannot declare agents in a plugin manifest receives skills and zero
agents. Verified against the agent harness documentation: that runtime loads custom agents only from
a project-scoped agent directory (highest precedence) or the user's global one, and its plugin
manifest declares `skills`, `mcpServers`, `apps`, `hooks`, and `interface` — no agents. Its plugin
component layout has no agent directory either. So no installation path delivers a plugin's agents,
every marketplace agent is absent for those consumers, and any methodology step that dispatches one
fails. The definitions were additionally declared gitignored, leaving environments where nobody runs
a materialization step without agents as well.

## Target model

1. **The build emits each target's native agent artifact.** A target's generated tree carries its
   agent artifact in the format that target reads and never an artifact it cannot read. Conversion is
   a pure function of the agent source, so it runs once at build time under the existing `dist/`
   drift gate and every consumer receives byte-identical definitions.
2. **Naming renders the namespaced identity.** A target whose agent namespace is flat receives the
   plugin name as slug prefix, `<plugin>_<agent>`, rendering the namespaced `<plugin>:<agent>`
   identity. The prefix is applied to the agent's `name` field, which the runtime treats as the
   identity source of truth, and the filename follows it by convention. The prefix is also the
   ownership boundary for idempotent placement, and it keeps a plugin's agent from shadowing a
   built-in agent of the same bare name.
3. **Agent artifacts ship inside a declared plugin surface.** Each plugin carries a lifecycle skill,
   and the agent artifacts live within that skill's own directory, so delivery rides a component the
   manifest declares rather than an undeclared directory that merely survives the install copy.
4. **Every plugin carries a lifecycle skill** — `/{plugin}-plugin` — generated per plugin from one
   authored source with the slug substituted, emitted for every target. It is the plugin's
   consumer-side lifecycle surface, not an agent installer: `help` and `version` are the floor for
   every plugin; `init`, `upgrade`, and `check` manage a plugin's footprint where it has one;
   `tutorial` and `diagnose` extend it later. `version` reports the version the session actually
   resolved rather than a manifest read off disk, because those diverge. `upgrade` migrates the
   plugin's footprint across versions, including pruning definitions a later version retired.
5. **Placement is a file copy.** The lifecycle skill's script overwrites and prunes within the
   namespace its plugin owns, leaving developer-authored and other plugins' definitions untouched.
   The mapping stays at build time, so the shipped script carries no test-bearing logic.
6. **Per-target capability values live in the registry**, not in the decisions: agent format,
   filename shape, and namespace behavior resolve from the source-owned per-target registry, so a
   new agent harness is a registry entry rather than a decision amendment.

## Declarations this supersedes

- `spx/12-marketplace-state.adr.md`: converted agent files install under a *gitignored* checkout
  directory.
- This node: `NEVER: agent conversion writes generated agents into published plugin manifest
  content`. Generated artifacts become published plugin *tree* content within a declared surface.
- `spx/18-plugin-build.enabler/54-conversion.enabler/conversion.md`: conversion outputs stay scoped
  to local installation orchestration.

## Plan to merge

### Phase 1 — Decisions and specs

- Revise both governing decisions to capability-keyed principles. *(applied)*
- Align this node and `spx/18-plugin-build.enabler/54-conversion.enabler/conversion.md`. *(applied)*
- Align `spx/13-infrastructure.enabler/32-installation.enabler` for coherence over the committed set.
- Align `spx/18-plugin-build.enabler/43-target-emission.enabler`, whose two `[test]`-backed
  compliance assertions the planned emission falsifies: one authored lifecycle-skill source fans out
  to many outputs per target rather than exactly one, and the flat-namespace agent artifact is
  placed by the build rather than mirroring its source subtree. Re-declare both to admit
  source-to-many fan-out and build-directed placement, and carry
  `tests/test_target_emission.compliance.l1.py` with them. This node is a lower-index sibling of
  conversion, so it constrains this work directly.
- ADR 12's per-agent config-path enumeration stays as authored; it is tracked in `spx/ISSUES.md` as
  the `coding-agents` decomposition, routed through `/decompose`.

### Phase 2 — Capability registry

- Add native agent format, filename shape, and flat-versus-namespaced agent namespace to a
  source-owned per-target agent-capability registry, declared in
  `spx/18-plugin-build.enabler/43-target-emission.enabler` together with the assertion realignment
  above. That node owns per-target output emission; the registry parameterizes emission and belongs
  with it.
- Not `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`,
  whose registry and every assertion govern rendering a divergent **name** into authored text through
  a template token. An emission parameter is not a name substituted into content, and its values are
  not tokens the source-layer guard could forbid in prose, so it does not belong to that node's
  registry or its kind-keyed structure.

### Phase 3 — Lifecycle skill and build emission

- Author one lifecycle-skill source that the build fans out per plugin with the slug substituted,
  for every target. Floor verbs `help` and `version`; `init`, `upgrade`, and `check` where the plugin
  has a footprint.
- The build renders each plugin's agent definitions into every target's native agent artifact inside
  that plugin's lifecycle-skill directory, applying the slug prefix for flat-namespace targets and
  omitting any artifact a target cannot read.
- Reuse the existing conversion functions rather than duplicating mapping logic; update every reader
  the markdown-consumer sweep identifies.
- Add the repair routing rule to the instruction-block template in
  `src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md`, so it
  renders into this product's root guides and ships to every consumer that updates its block. The
  rule is failure-triggered and capability-keyed: when a plugin's agents are missing, run that
  plugin's `/{plugin}-plugin init`. It never fires in a healthy session, so it adds no per-session
  check and no per-session output. Writing the rule into a root guide directly reaches no consumer
  and is overwritten by the next render.

### Phase 4 — Placement and the committed agent directory

- The lifecycle skill's script places and prunes the checkout's agent directory within its plugin's
  namespace. Stdlib-only, invoked through the skill-directory variable, no dependency installation.
- Keep that script at or under fifty raw lines. `spx/12-shipped-scripting.adr.md` declares a longer
  shipped script to be debt awaiting extraction into the SPX CLI, so scope it to placement and
  namespace-bounded pruning with the mapping already resolved at build time, and keep verb behavior
  that needs no code as skill instruction. Exceeding the cap is an explicit extraction decision.
- Un-gitignore the checkout agent directory and commit the placed definitions.
- Add the drift check that fails a commit when the committed directory diverges from what the
  lifecycle skill would place.

### Phase 5 — Sync cutover fold-in

- The build and the lifecycle skill own agent production and placement, so sync's agent-install step
  is removed and the user-scope cache and reconciliation machinery is deleted with its tests and
  harnesses. Correct `spx/32-distribution.enabler/21-sync.enabler` and its `PLAN.md`.

### Phase 6 — Surfaces, overlays, and versions

- Correct `spx/local/merging.md` where it describes the superseded gitignored agent install.
- Re-render the root guides with `just build-instructions` after the template gains the repair
  routing rule, then verify with `just instructions-check`. The managed blocks are generated; never
  hand-edit them.
- Update `CLAUDE.md` and `AGENTS.md` product-owned content, outside the managed block, where it
  describes agent installation or sync steps.
- Advance plugin manifest versions in lockstep per the bump investigation's finding.

### Phase 7 — Evidence

Route each new assertion through `/verify`, then the selected specialist. Cover: the build emits each
target's native artifact and no unreadable artifact; the slug prefix on the identity field; the
lifecycle skill's floor verbs; placement and namespace-bounded pruning; the drift check; and sync
performing no agent install.

### Phase 8 — Deterministic verification

Focused lanes first, then `just check-full` once on the clean committed head, after the agentic gates
converge — never before them, never inside an agent, never concurrently with another heavy command.

### Phase 9 — Agentic verification

Dispatch in isolated verifier contexts on the committed changeset: `adr-auditor` for both revised
decisions, `spec-auditor` for aligned nodes, `implementation-auditor`, `test-evidence-auditor`,
`changes-reviewer`, and `skill-auditor` for the new lifecycle skill, which the changeset reviewer
does not cover. Run `changeset-coherence-auditor` to decide whether the changeset needs a
dependency-ordered split. Fix each valid finding as a defect class.

### Phase 10 — Commit and merge

Commit by concern through `/commit-changes`, then `/merge` drives `VERIFY -> PREVIEW -> MERGE ->
DEPLOY -> RELEASE -> CLOSE` against the four gates, with the canonical-checkout diagnosis before the
first merge mutation and the marketplace-source refresh at `RELEASE_READINESS`.

## Resolved dependencies

The lifecycle skill removes the SPX CLI dependency this plan previously carried: placement ships with
the plugin, so no published-capability gate, version-floor advance, or interim placer stands between
the decision and delivery.
