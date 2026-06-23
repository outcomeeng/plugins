# Update spx/

PROVIDES deterministic generation of a product's two spx-level guide files — `spx/CLAUDE.md` for Claude Code and `spx/AGENTS.md` for Codex — from one installed template, scoped to the project's enabled languages and rendered per agent runtime
SO THAT every agent working a spec-tree project
CAN read its own runtime's guidance, kept current by a gate without manual template tracking or agent judgment

## Assertions

### Scenarios

- Given a template with language blocks and per-runtime blocks, when the guide is generated for an enabled-language set, then both `spx/CLAUDE.md` and `spx/AGENTS.md` are written, each containing exactly the enabled languages' blocks and only its own runtime's blocks ([test](tests/test_update_spx.scenario.l1.py))
- Given the `CLAUDE.md` and `AGENTS.md` outputs of one generation, when they are compared, then they share every line except the runtime-divergent spans — the auditor-subagent mandate, the runtime tool names, and the guide's own filename ([test](tests/test_update_spx.scenario.l1.py))
- Given a newer template that adds a section, when the guide is updated, then both re-rendered files contain the new section and still carry the recorded enabled languages ([test](tests/test_update_spx.scenario.l1.py))
- Given the CLI edge, `--check` reports `absent`, `stale`, or `current` for a missing, version-behind, or version-current guide, reports `stale` when the detected language set differs from the recorded set, and `--write` creates both guide files ([test](tests/test_update_spx.scenario.l1.py))
- Given a guide whose `template_version` is not parseable as dotted integers, when staleness is checked, then it is treated as stale rather than raising, so a re-render normalizes it to the installed version ([test](tests/test_update_spx.scenario.l1.py))

### Mappings

- Over the languages the template defines blocks for, a language's block appears in a rendered guide when the language is in the detected enabled set and is omitted otherwise ([test](tests/test_update_spx.mapping.l1.py))
- A test-file extension present under `spx/**/tests/` maps to the language it denotes, and the detected enabled-language set is the set of those mappings ([test](tests/test_update_spx.mapping.l1.py))

### Properties

- After generation, each output file's `template_version` equals the installed template version ([test](tests/test_update_spx.property.l1.py))
- Every rendered guide file ends with exactly one trailing newline ([test](tests/test_update_spx.property.l1.py))
- Staleness ordering matches dotted-numeric version order: a product version is stale exactly when it is numerically below the installed template version ([test](tests/test_update_spx.property.l1.py))

### Compliance

- ALWAYS: generation writes both `spx/CLAUDE.md` and `spx/AGENTS.md`, never one without the other — each agent reading the same repository gets its own runtime's guide ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: a gate regenerates both guide files and fails on drift, keeping them current without an agent invocation ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: the enabled-language list is detected from the product's `spx/**/tests/` test-file extensions, with no agent input ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: the render substitutes a product-specific string into a guide body — a brace-delimited token in the template passes through unchanged ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: an update keeps an unmodeled hand-prose edit to a guide body — a re-render reflects only the template, the recorded enabled languages, and the runtime ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: the canonical spx-level guide template instructs agents to add, maintain, or require a `result` session frontmatter property — session archival follows the sessions model without that field ([test](tests/test_update_spx.compliance.l1.py))
