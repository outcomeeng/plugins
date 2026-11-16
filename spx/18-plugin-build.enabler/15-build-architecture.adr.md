# Build Architecture

CONSTRAINS the build that turns authored plugin sources into the plugin trees each coding agent installs
TO one Python module that expands a single agent-neutral source tree under `src/` through Jinja2 into committed generated agent trees at `dist/claude/` and `dist/codex/`
SO THAT every coding agent reads native plugin content rendered from one authored source, with no coding agent privileged as the canon

## Verification

### Test.Compliance: agent emission

- agent-native-format: ALWAYS: the build renders each plugin's agent definitions into the native agent format of every target the definition's `targets` field lists — every registered target when the field is absent — and no generated target tree carries an agent artifact that target cannot read.
- flat-namespace: ALWAYS: a target whose agent namespace is flat receives agent filenames and names carrying the plugin as slug prefix, `<plugin>_<agent>`, rendering the namespaced `<plugin>:<agent>` identity; a target that namespaces plugin agents carries the bare agent name.
- capability-registry: ALWAYS: each target's agent format, filename shape, and namespace behavior resolve from a source-owned per-target agent-capability registry, distinct from the agent-specific token registry because it parameterizes emission rather than rendering a name into authored text — adding a target adds a registry entry rather than amending this decision.
- dist-traces-src: ALWAYS: every committed `dist/` file traces to a `src/` ancestor through the build — no orphan dist content.

### Audit: tokens and profiles

- agent-token-owner: ALWAYS: the build derives its targets, `claude` and `codex`, from the coding-agents agent-token module, which owns the tokens `claude`, `codex`, and `pi` and which the toolchain loads by path, and renders its tokens beside each product-tree script that reads them; no toolchain module and no authored product-tree script declares an agent token.
- model-identifier-once: ALWAYS: define each model identifier once in the Python configuration owner, which also owns the Standard, Strong, Thorough, and Fast profiles selected in [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md); profiles reference that identity and keep each harness's complete native settings together, with distinct harness-specific types for reasoning controls rather than a shared effort scale.
- profile-prices: ALWAYS: the configuration owner holds the prices of the model identities it prices, for every usage token class, so the profiles stay the one model inventory.
- one-profile-unit: ALWAYS: render native agent definitions, examples, and descriptions from one selected complete profile; template callers cannot independently request or override individual model or reasoning values.
- no-translated-profile: NEVER: resolve a destination profile by translating another harness's model or effort, passing through an unknown value, or selecting a fallback.
- no-native-fields: NEVER: an authored agent input or skill frontmatter carries a native configuration field; an unknown profile, an independent override, or an incompatible configuration fails before any output write.
- explicit-boundary: ALWAYS: accept profile definitions explicitly at the pure resolution boundary so propagation and rejection evidence can exercise real resolution with typed inputs without replacing process globals.
- guard-vocabulary: ALWAYS: derive the source guard's model vocabulary and native configuration fields from the configuration owner; reject configuration assignments while leaving ordinary prose words unrestricted.
- guard-scope: ALWAYS: the source guard rejects literal model identifiers and authored assignments of native model and reasoning controls throughout `src/`, including conditional blocks and otherwise ignored files; a field bound to an expression that reads a value, and a field bound to an interpolation placeholder, are no configuration assignment, and every other binding, an unquoted value included, is an authored assignment.

### Audit: per-agent variation

- agent-name-registry: ALWAYS: render each agent-specific name (the skill-directory variable, tool names, frontmatter field names, concept terms, per-agent filenames such as the agent guide) into the target's native name from a source-owned agent-specific token registry — no coding agent's names are the privileged source language.
- token-kinds: ALWAYS: key the agent-specific token registry by token kind (`tool`, `field`, `term`, `file`), each kind exposed as its own template global and declaring whether the source-layer guard enforces its names — `tool`, `field`, and `file` names are unique tokens the guard forbids raw, `term` concept terms are common-word and review-covered, so a new kind opts into or out of guard enforcement explicitly rather than every registered name being forbidden.
- symmetric-strip: ALWAYS: strip a frontmatter field absent from a target's schema for that target, applied symmetrically in either direction — the schema decides what survives, not one privileged agent.
- portable-fields: ALWAYS: portable skill capability fields such as `argument-hint` and `allowed-tools` survive in both generated agent trees.
- targets-field-stripped: ALWAYS: the build strips an agent source's `targets` field from every output.
- conditional-blocks: ALWAYS: author a claim whose truth differs by agent as a per-agent conditional block, never as a single statement true for only one target.
- directive-bodies: ALWAYS: `{!% include %!}` and `{!% require_skill %!}` directives expand to identical bodies in both targets.
- raw-token-guard: NEVER: a raw agent-specific unique token (`AskUserQuestion`, `ScheduleWakeup`, `CLAUDE.md`, `AGENTS.md`, and the like) appears in authored `src/plugins/` or `src/_shared/` content outside the explicit ignore-list — a divergent reference is a registry token, a conditional, or a tracked exemption, enforced by a source-layer guard derived from the lint-enforced kinds (`tool`, `field`, `file`) that covers every authored file the build renders or inlines by default; common-English-word tool names together with the `term` kind's concept terms are covered by the frontmatter schema and review instead.

### Audit: templating and layout

- jinja-delimiters: ALWAYS: use Jinja2 with custom delimiters (`{!% %!}` and `{{! !}}`) for template processing — collision-free syntax in the presence of meta-skill content.
- source-homes: ALWAYS: place every plugin source under `src/plugins/<plugin>/` and all canonical shared content under `src/_shared/<scope>/<topic>/` — a single home for each shared fragment.
- every-target-output: ALWAYS: emit committed outputs into every registered target's generated tree for every plugin published to that target's marketplace catalog — a new target is covered by this rule rather than by rewriting it.
- lefthook-gate: ALWAYS: run `just build-skills` from a lefthook pre-commit hook that fails the commit when `dist/` would change — stale dist is the failure mode this decision prevents.
- no-hand-edit: NEVER: edit `dist/claude/` or `dist/codex/` by hand — the build, `outcomeeng/distribution/build.py`, is the only writer; manual edits desynchronize the source-output contract.
- no-execution-injection: NEVER: use `!`cat ${CLAUDE_SKILL_DIR}/...`` execution-time injection in built output — shared content reaches both outputs via build-time fan-out.
- codex-skill-dir: NEVER: emit unescaped `${CLAUDE_SKILL_DIR}` references into `dist/codex/` outputs — Codex output uses `${SKILL_DIR}`; source lines carrying the rewrite-escape directive are the explicit exception.
- one-build-adr: NEVER: add separate ADRs for individual build concerns (template engine, source layout, output layout, orchestration) — these decisions are interdependent and belong in this single ADR.
- no-plugins-distribution: NEVER: distribute downstream-repo content from `plugins/` — `distribute_skills.py` reads from `dist/claude/`, the canonical home of Claude Code plugin content.

### Audit: formatter boundary

- formatter-injection: ALWAYS: external formatter discovery and execution in the build accept dependency-injected collaborators typed as Python Protocols, with controlled implementations limited to `/test` Stage 5 exception 1 (failure simulation) for unavailable or failing formatters and exception 2 (interaction protocols) for recording the command shape, so tests cover missing-tool and formatter-failure behavior without patching global process APIs.
- no-formatter-mocks: NEVER: framework mocks replace formatter discovery, execution, or the build behavior under verification; injected collaborators preserve the real boundary and expose observations for predicates owned by the linked tests.
