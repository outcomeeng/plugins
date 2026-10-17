# Execution Policy

PROVIDES deterministic Codex execution-policy derivation from one rendered plugin agent definition
SO THAT converted agents and Codex consumers
CAN preserve enforceable restrictions while surfacing unsupported source semantics for review

## Assertions

- ALWAYS: a generated Codex implementation auditor composes every installed concern skill selected for its changed files through the `Use skill` instruction, without searching for a dedicated skill-invocation tool.
- ALWAYS: Codex enforces no denial of launching a subagent or of asking the operator, so a source agent that denies either declares the denial for Claude Code alone, its Codex artifact carries neither a restriction nor guidance that presents the denial as enforced, and the attested observation of the deployed Codex child is the evidence that the child keeps within the denial ([audit])

### Mappings

- Source `permissionMode` values with supported Codex equivalents map to `sandbox_mode`, and unsupported values map to manual-review guidance in `developer_instructions` ([test](tests/test_execution_policy.mapping.l1.py))
- Source tool allowlists that omit web-capable tools map to `web_search = "disabled"`, while absent `tools` frontmatter, the `all` tool sentinel, and allowlists that include any web-capable tool leave web search unset for runtime defaults ([test](tests/test_execution_policy.mapping.l1.py))
- Source file-read-only and web-capable-only tool allowlists map to `sandbox_mode = "read-only"` when no explicit `permissionMode` is present; absent `tools` frontmatter, script-capable allowlists, write-capable allowlists, the `all` tool sentinel, and explicit unmapped `permissionMode` values leave sandbox mode unset for runtime defaults plus manual-review guidance ([test](tests/test_execution_policy.mapping.l1.py))
- Each rendered source-tool set over the source-owned tool universe maps to manual-review guidance that names exactly the tools in that set, so a tool absent from the set never reappears as guidance ([test](tests/test_execution_policy.mapping.l1.py))

### Compliance

- ALWAYS: converted agents keep manual-review guidance for rendered source fields whose Codex semantics remain prompt guidance rather than hard execution boundaries — `disallowedTools` and command-level meanings inside rendered `tools` do not restrict commands executed through allowed shell tools, and `skills.config` enables named skills without proving spawn-time preload behavior ([test](tests/test_execution_policy.compliance.l1.py))
