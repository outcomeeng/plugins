---
id: 01a1e087-aab5-7169-b654-98c842648440
---

# Plugin Build

PROVIDES authored plugin files with deterministic agent-harness-native emission for Claude Code and Codex
SO THAT plugin authors and the marketplace
CAN maintain skills and thin agents as one canonical source while delivering native outputs for each coding agent.

## Assertions

### Audit: naming and configuration

- naming-relation: ALWAYS: published skills and agent definitions use the same distribution-owned naming relation: flat roles are `<plugin>_<unchanged-authored-role>` and native namespaced dispatch is `<plugin>:<authored-role>`, including authored roles that already begin with the plugin name, per [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md).
- own-agent-guides: ALWAYS: generated instruction surfaces address only their own agent.
- profile-configuration: ALWAYS: agent definitions, configuration examples, and descriptions derive their complete native configuration from the central Standard, Strong, Thorough, or Fast profile selected under [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md); each harness keeps its own reasoning controls, and authored sources select profiles rather than independently selecting model and effort fields.

### Test.Mapping: [agent-token-ownership](tests/test_agent_token_ownership.mapping.l1.py)

The build loads the coding-agents agent-token module by path, and each row maps a part of the toolchain to the agent tokens it holds.

| Case              | Part of the toolchain        | Agent tokens                         |
| ----------------- | ---------------------------- | ------------------------------------ |
| loaded-tokens     | the tokens the build loads   | the tokens the owner module declares |
| target-values     | each generated-output target | the owner token of the same name     |
| toolchain-modules | each toolchain module        | none declared                        |

### Test.Mapping: [agent-token-rendering](tests/test_agent_token_rendering.mapping.l1.py)

The build renders the agent tokens into a data file beside each product-tree script that reads them, and each row maps a rendered file property to what it holds in every target tree.

| Case      | Property                   | Holds                                                 |
| --------- | -------------------------- | ----------------------------------------------------- |
| placement | where the data file stands | beside each product-tree script that reads the tokens |
| content   | what the data file holds   | the declaration it renders, unchanged                 |

### Test.Mapping: [agent-target-keys](tests/test_agent_target_keys.mapping.l1.py)

Each of the build's per-agent tables keys each agent by its `Target` member, and every generated-tree path derives from a `Target` value.

| Case                | Table                                   | Key                 |
| ------------------- | --------------------------------------- | ------------------- |
| capability-registry | the agent capability registry           | the `Target` member |
| prompt-fields       | the configured-agent prompt-field table | the `Target` member |
| terms               | the configured-agent term table         | the `Target` member |
| catalog-paths       | the marketplace catalog paths           | the `Target` member |
| generated-trees     | each generated-tree path                | a `Target` value    |

### Test.Compliance: build products

- [dist-traces-src](tests/test_plugin_build.compliance.l1.py): ALWAYS: every committed file under `dist/` traces to a `src/` ancestor through the build — every committed generated artifact is a build product.

### Test.Property: build

- [build-determinism](tests/test_plugin_build.property.l1.py): For every `src/` content, the build produces byte-identical `dist/claude/` and `dist/codex/` outputs across machines and time.
- [build-idempotence](tests/test_plugin_build.property.l1.py): For every build, running it twice in succession produces no changes on the second run.
