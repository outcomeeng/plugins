# Plugin Build

PROVIDES authored plugin files with deterministic agent-harness-native emission for Claude Code and Codex
SO THAT plugin authors and the marketplace
CAN maintain skills and thin agents as one canonical source while delivering native outputs for each coding agent.

## Assertions

- ALWAYS: published skills and agent definitions use the same distribution-owned
  naming relation: flat roles are `<plugin>_<unchanged-authored-role>` and native
  namespaced dispatch is `<plugin>:<authored-role>`, including authored roles that
  already begin with the plugin name, per [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) ([audit]).
- ALWAYS: generated instruction surfaces address only their own agent ([audit]).
- ALWAYS: agent definitions, configuration examples, and descriptions derive
  their complete native configuration from the central Standard, Strong, Executor, or Fast
  profile selected under [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md); each harness keeps
  its own reasoning controls, and authored sources select profiles rather than
  independently selecting model and effort fields ([audit]).
- ALWAYS: the build formats every generated file whatever repository or ignore file encloses its output directory.

### Mappings

- ALWAYS: the build loads the coding-agents agent-token module by path, every generated-output target is one of its tokens, and no toolchain module declares an agent token ([test](tests/test_agent_token_ownership.mapping.l1.py))
- ALWAYS: the build renders the agent tokens into a data file beside each spec-tree script that reads them, and the rendered file equals the declaration it renders ([test](tests/test_agent_token_rendering.mapping.l1.py))
- ALWAYS: the build's per-agent tables — the agent capability registry, the configured-agent prompt-field and term tables, and the marketplace catalog paths — key each agent by its `Target` member, and every generated-tree path derives from a `Target` value ([test](tests/test_agent_target_keys.mapping.l1.py))

### Compliance

- ALWAYS: every committed file under `dist/` traces to a `src/` ancestor through the build — every committed generated artifact is a build product ([test](tests/test_plugin_build.compliance.l1.py))

### Properties

- Build determinism: same `src/` content always produces byte-identical `dist/claude/` and `dist/codex/` outputs across machines and time ([test](tests/test_plugin_build.property.l1.py))
- Build idempotence: running the build twice in succession produces no changes on the second run ([test](tests/test_plugin_build.property.l1.py))
