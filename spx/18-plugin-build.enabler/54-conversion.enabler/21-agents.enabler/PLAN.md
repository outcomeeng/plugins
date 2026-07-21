# Plan

Governing decisions: `spx/12-marketplace-state.adr.md` (marketplace state ownership) and
`spx/18-plugin-build.enabler/15-build-architecture.adr.md` (build architecture).

## Defect this plan closes

A consumer whose agent harness cannot declare agents in a plugin manifest receives skills and zero
agents. That harness's plugin manifest declares only skills, its runtime reads agents from a
checkout or user-scope agent directory, and nothing converts or places the agent definitions that
plugin installation already copies into the consumer's plugin cache — verified: the installed plugin
cache holds each plugin's agent directory today. Every marketplace agent is therefore absent for
those consumers, and any methodology step that dispatches one fails. Because the converted
definitions were declared gitignored, every agent environment that resolves only committed
repository files is left without agents as well.

## Target model

1. **The build emits each target's native agent artifact.** A target's generated tree carries its
   agent artifact in the format that target reads and never an artifact it cannot read. Conversion is
   a pure function of the agent source, so it runs once at build time under the existing `dist/`
   drift gate and every consumer receives byte-identical definitions.
2. **Naming renders the namespaced identity.** A target whose agent namespace is flat receives the
   plugin name as slug prefix, `<plugin>_<agent>`, rendering the namespaced `<plugin>:<agent>`
   identity; a target that namespaces plugin agents carries the bare name. An agent-harness policy
   matching on name can then whitelist the marketplace's agents and deny arbitrary subagent
   spawning, with the prefix set derived from the marketplace catalog.
3. **Delivery rides the existing install path.** Plugin installation already carries each plugin's
   agent directory to consumers, so the built artifact reaches them with no new transport.
4. **The checkout's agent directory is committed.** An agent environment resolving only committed
   repository files has no installation to consult, so the committed definitions are the sole
   delivery for it. The SPX CLI places and keeps that directory current from the installed plugins,
   prunes stale generated entries, and offers a `--check` mode the gates read.
5. **`agents.py` is the interim placer** until that CLI capability is published and the version floor
   advances. It also installs to an explicitly named user-scope agent home so the marketplace's
   agents are available while the capability is built in the `@outcomeeng/spx` repository.
6. **Per-target capability values live in the registry**, not in the decisions: agent format,
   filename shape, and namespace behavior resolve from the source-owned per-target registry, so a
   new agent harness is a registry entry rather than a decision amendment.

## Declarations this supersedes

- `spx/12-marketplace-state.adr.md`: converted agent files install under a *gitignored* checkout
  directory.
- This node: `NEVER: agent conversion writes generated agents into published plugin manifest
  content`. Generated artifacts become published plugin *tree* content; the manifest simply declares
  no agents.
- `spx/18-plugin-build.enabler/54-conversion.enabler/conversion.md`: conversion outputs stay scoped
  to local installation orchestration.

## Plan to merge

### Phase 1 — Decisions and specs

- Revise `spx/12-marketplace-state.adr.md` and
  `spx/18-plugin-build.enabler/15-build-architecture.adr.md` to capability-keyed principles. *(applied)*
- Align this node and `spx/18-plugin-build.enabler/54-conversion.enabler/conversion.md`. *(applied)*
- Align `spx/13-infrastructure.enabler/32-installation.enabler` for coherence over the committed set.
- ADR 12's per-agent config-path enumeration stays as authored in this changeset. It is tracked in
  `spx/ISSUES.md` as the `coding-agents` decomposition: one child node per agent declaring that
  agent's capabilities and configuration, with the decision collapsing to capability assertions. That
  is a structural change routed through `/decompose`, out of scope here.

### Phase 2 — Capability registry

- Add agent-capability values to the source-owned per-target registry in
  `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`:
  native agent format, filename shape, and whether the target's agent namespace is flat.
- Align that node's spec with the added capability kind.

### Phase 3 — Build emission

- `outcomeeng/distribution/build.py` renders each plugin's agent definitions into every target's
  native agent artifact, applying the slug prefix for flat-namespace targets and omitting any
  artifact a target cannot read.
- Reuse the existing conversion functions rather than duplicating mapping logic.

### Phase 4 — Placement and committed agents

- `outcomeeng/distribution/agents.py` becomes the placer: read the built artifact, write the
  checkout's agent directory, prune stale generated entries through the generated-agent manifest,
  and accept an explicitly named user-scope target. Remove any user-home default.
- Un-gitignore the checkout agent directory and commit the generated definitions.
- Add the drift check that fails a commit when the committed directory diverges from the built
  artifact, alongside the existing `dist` drift gate.

### Phase 5 — Sync cutover fold-in

- `outcomeeng/distribution/sync.py` becomes checkout-bounded: the build owns agent production, so the
  agent-install step is removed and the `codex_cache` and user-scope reconciliation machinery is
  deleted with its tests and harnesses.
- Correct `spx/32-distribution.enabler/21-sync.enabler` and its `PLAN.md` to the reduced orchestration.

### Phase 6 — Surfaces and overlays

- Correct `spx/local/merging.md` lines 89-92, which describe the superseded gitignored agent install
  and assert no user-scope refresh is required.
- Update `CLAUDE.md` and `AGENTS.md` where they describe agent installation or the sync steps.
- `just bump` — this changeset changes plugin distribution content under `dist/`, so every changed
  plugin's manifest version advances in lockstep across both manifests.

### Phase 7 — Evidence

Route each new assertion through `/verify`, then the selected specialist. Evidence to establish:
build emits each target's native artifact and no unreadable artifact; the flat-namespace prefix;
placement into the checkout directory; stale-entry pruning; the explicitly named user-scope target;
the committed-agents drift check; and sync performing no agent install.

### Phase 8 — Deterministic verification

Focused lanes first: `just test <node test targets>`, `just fmt <changed markdown>`,
`just fmt-python <changed python>`, `just check-skills`, `just docs-check`, `spx validation markdown`.
Then `just check-full` once, on the clean committed head, after the agentic gates converge — never
before them, never inside an agent, never concurrently with another heavy command.

### Phase 9 — Agentic verification

Dispatch as agents in isolated verifier contexts, on the committed changeset, after deterministic
verification passes: `adr-auditor` for both revised decisions, `spec-auditor` for the aligned nodes,
`implementation-auditor`, `test-evidence-auditor`, and `changes-reviewer`. Run
`changeset-coherence-auditor` to decide whether the changeset is one review unit or needs a
dependency-ordered split. Fix each valid finding as a defect class across the touched nodes; defer
only a separate larger concern with a recorded reason.

### Phase 10 — Commit and merge

- Commit by concern through `/commit-changes`: decisions and spec alignment; registry; build
  emission; placement and committed agents; sync cutover; surfaces and version bump.
- `/merge` selects the transport and drives `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE`
  against the four gates. The GitHub-PR transport merges with
  `gh pr merge <pr-number> --merge --delete-branch=false`.
- Run the canonical-checkout diagnosis before the first merge mutation, per `spx/local/merging.md`.

### Phase 11 — Release and close

- `RELEASE_READINESS`: fast-forward the marketplace-source worktree's default branch and run the
  checkout-bounded sync from it, per `spx/local/merging.md`.
- Post-merge feature-worktree cleanup and remote branch deletion only after the repeated diagnosis
  passes every predicate.

### Dependency follow-up

File `/issue` into the `@outcomeeng/spx` queue for the CLI place, refresh, prune, and `--check`
capability. `agents.py` retires once that ships, an `@outcomeeng/spx` release carries it,
`REQUIRED_SPX_VERSION` advances, and the workflow pin is bumped at or above the floor — at which
point this repository consumes the mechanism it ships rather than special-casing itself.
