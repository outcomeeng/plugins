# Execution Policy

PROVIDES deterministic Codex execution-policy derivation from one rendered plugin agent definition
SO THAT converted agents and Codex consumers
CAN preserve enforceable restrictions while surfacing unsupported source semantics for review

## Assertions

### Mappings

- Source `permissionMode` values with supported Codex equivalents map to `sandbox_mode`, and unsupported values map to manual-review guidance in `developer_instructions` ([test](tests/test_execution_policy.mapping.l1.py))
- Source tool allowlists that omit web-capable tools map to `web_search = "disabled"`, while absent `tools` frontmatter, the `all` tool sentinel, and allowlists that include any web-capable tool leave web search unset for runtime defaults ([test](tests/test_execution_policy.mapping.l1.py))
- Source file-read-only and web-capable-only tool allowlists map to `sandbox_mode = "read-only"` when no explicit `permissionMode` is present; absent `tools` frontmatter, script-capable allowlists, write-capable allowlists, the `all` tool sentinel, and explicit unmapped `permissionMode` values leave sandbox mode unset for runtime defaults plus manual-review guidance ([test](tests/test_execution_policy.mapping.l1.py))

### Compliance

- ALWAYS: converted agents keep manual-review guidance for source fields whose Codex semantics remain prompt guidance rather than hard execution boundaries — `disallowedTools` and command-level meanings inside `tools` do not restrict commands executed through allowed shell tools, and `skills.config` enables named skills without proving spawn-time preload behavior ([test](tests/test_execution_policy.compliance.l1.py))
