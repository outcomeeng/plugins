# Execution Policy

PROVIDES deterministic Codex execution-policy derivation from one rendered plugin agent definition
SO THAT converted agents and Codex consumers
CAN preserve enforceable restrictions while surfacing unsupported source semantics for review

## Assertions

- ALWAYS: a generated Codex implementation auditor composes every installed concern skill selected for its changed files through the `Use skill` instruction, without searching for a dedicated skill-invocation tool.
- ALWAYS: Codex enforces no denial of launching a subagent or of asking the operator, so a source agent that denies either declares the denial for Claude Code alone, its Codex artifact carries neither a restriction nor guidance that presents the denial as enforced, and the attested observation of the deployed Codex child is the evidence that the child keeps within the denial ([audit])

### Declarations

The source tool vocabulary is the authoring platform's own, and each tool belongs to exactly one class:

| Class          | Member tools                    |
| -------------- | ------------------------------- |
| file-read-only | `Glob`, `Grep`, `Read`          |
| web-capable    | `WebFetch`, `WebSearch`         |
| script-capable | `Bash`, `Skill`                 |
| write-capable  | `Edit`, `NotebookEdit`, `Write` |

The source `permissionMode` values map to Codex sandbox modes by these rows, where unmapped is manual-review guidance:

| `permissionMode`    | Codex `sandbox_mode` |
| ------------------- | -------------------- |
| `default`           | unmapped             |
| `acceptEdits`       | `workspace-write`    |
| `auto`              | unmapped             |
| `dontAsk`           | unmapped             |
| `bypassPermissions` | unmapped             |
| `plan`              | `read-only`          |

- ALWAYS: the converter's class constants hold exactly the member tools the table declares, and its `permissionMode` mapping holds exactly the rows the table declares ([audit:declared-values-match-converter])

### Mappings

- Source `permissionMode` values with a declared Codex equivalent map to `sandbox_mode`, and values the declared rows leave unmapped map to manual-review guidance in `developer_instructions` ([test](tests/test_execution_policy.mapping.l1.py))
- For every subset of the source tool universe, an allowlist that holds no web-capable tool maps to `web_search = "disabled"` and one that holds a web-capable tool leaves web search unset, while absent `tools` frontmatter, the `all` tool sentinel, and allowlists that include any web-capable tool leave web search unset for runtime defaults ([test](tests/test_execution_policy.mapping.l1.py))
- For every subset of the source tool universe, an allowlist that holds only file-read-only and web-capable tools maps to `sandbox_mode = "read-only"` when no explicit `permissionMode` is present; absent `tools` frontmatter, script-capable allowlists, write-capable allowlists, the `all` tool sentinel, and explicit unmapped `permissionMode` values leave sandbox mode unset for runtime defaults plus manual-review guidance ([test](tests/test_execution_policy.mapping.l1.py))
- Each rendered source-tool set over the source-owned tool universe maps to manual-review guidance that names exactly the tools in that set, so a tool absent from the set never reappears as guidance ([test](tests/test_execution_policy.mapping.l1.py))

### Compliance

- ALWAYS: converted agents keep manual-review guidance for rendered source fields whose Codex semantics remain prompt guidance rather than hard execution boundaries — `disallowedTools` and command-level meanings inside rendered `tools` do not restrict commands executed through allowed shell tools, and `skills.config` enables named skills without proving spawn-time preload behavior ([test](tests/test_execution_policy.compliance.l1.py))
