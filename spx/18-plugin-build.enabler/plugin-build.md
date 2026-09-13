# Plugin Build

PROVIDES authored plugin files with deterministic agent-harness-native emission for Claude Code and Codex
SO THAT plugin authors and the marketplace
CAN maintain skills and thin agents as one canonical source while delivering native outputs for each coding agent.

## Assertions

- ALWAYS: published skills and agent definitions use the same distribution-owned
  naming relation: flat roles are `<plugin>_<unchanged-authored-role>` and native
  namespaced dispatch is `<plugin>:<authored-role>`, including authored roles that
  already begin with the plugin name, per `spx/15-subagent-execution.pdr.md` ([audit]).
- ALWAYS: generated instruction surfaces address only their own agent ([audit]).
- ALWAYS: agent definitions, configuration examples, and descriptions derive
  their complete native configuration from the central Standard, Strong, or Fast
  profile selected under `spx/15-subagent-execution.pdr.md`; each harness keeps
  its own reasoning controls, and authored sources select profiles rather than
  independently selecting model and effort fields ([audit]).

### Compliance

- ALWAYS: every committed file under `dist/` traces to a `src/` ancestor through the build — every committed generated artifact is a build product ([test](tests/test_plugin_build.compliance.l1.py))

### Properties

- Build determinism: same `src/` content always produces byte-identical `dist/claude/` and `dist/codex/` outputs across machines and time ([test](tests/test_plugin_build.property.l1.py))
- Build idempotence: running the build twice in succession produces no changes on the second run ([test](tests/test_plugin_build.property.l1.py))
