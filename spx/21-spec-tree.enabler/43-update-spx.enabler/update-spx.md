# Update spx/

PROVIDES deterministic generation of a managed Spec Tree section in a product's root agent-harness guide files — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — from the rendered harness templates committed under `dist/`, scoped to the project's enabled languages and rendered per agent harness
SO THAT every agent working a spec-tree project
CAN retain Spec Tree routing guidance across compaction while preserving the product's own root instructions

## Assertions

### Scenarios

- Given a template with language blocks and per-harness blocks, when the managed root guide section is generated for an enabled-language set, then both `CLAUDE.md` and `AGENTS.md` are written, each preserving root content outside the managed section and containing exactly the enabled languages' blocks and only its own harness's blocks inside the managed section ([test](tests/test_update_spx.scenario.l1.py))
- Given the `CLAUDE.md` and `AGENTS.md` outputs of one generation, when they are compared, then they share every line except the per-harness blocks the template marks; the two files differ only there and in their own filename, which is the output path, not a span of the shared body ([test](tests/test_update_spx.scenario.l1.py))
- Given a newer template that adds a section, when the managed root guide section is updated, then both re-rendered sections contain the new section and still carry the recorded enabled languages ([test](tests/test_update_spx.scenario.l1.py))
- Given the CLI edge, `--check` reports `absent`, `stale`, or `current` for a missing, version-behind, or version-current guide, reports `stale` when the detected language set differs from the recorded set, and `--write` creates both guide files ([test](tests/test_update_spx.scenario.l1.py))
- Given a guide whose `template_version` is not parseable as dotted integers, when staleness is checked, then it is treated as stale rather than raising, so a re-render normalizes it to the installed version ([test](tests/test_update_spx.scenario.l1.py))
- Given root `CLAUDE.md` is a symlink to `AGENTS.md`, when `--write` updates the managed Spec Tree section, then `CLAUDE.md` becomes a regular file copy and both root guides preserve the shared root body outside their harness-specific managed sections ([test](tests/test_update_spx.scenario.l1.py))

### Mappings

- Over the languages the template defines blocks for, a language's block appears in a rendered managed section when the language is in the detected enabled set and is omitted otherwise ([test](tests/test_update_spx.mapping.l1.py))
- A test-file extension present under `spx/**/tests/` maps to the language it denotes, and the detected enabled-language set is the set of those mappings ([test](tests/test_update_spx.mapping.l1.py))

### Properties

- After generation, each managed section's `template_version` equals the installed template version ([test](tests/test_update_spx.property.l1.py))
- Every rendered managed section ends with exactly one trailing newline ([test](tests/test_update_spx.property.l1.py))
- Staleness ordering matches dotted-numeric version order: a product version is stale exactly when it is numerically below the installed template version ([test](tests/test_update_spx.property.l1.py))

### Compliance

- ALWAYS: generation writes managed sections in both root `CLAUDE.md` and root `AGENTS.md`, never one without the other — each agent reading the same repository gets its own harness guide in the root instruction file it retains across compaction ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: product guide generation reads the harness-specific guide templates from `dist/claude/` and `dist/codex/`, so the guide update surface consumes the same rendered output this product ships as installed plugin trees ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: guide writing is exposed to agents through the repository Justfile recipe `just build-guides`; `just guide-check` is the drift gate over the same writer ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: the guide drift gate reports missing root guide paths as drift and marks only existing generated guide paths with `--intent-to-add`, so deleted obsolete `spx/` guide paths are reported by `git diff` without causing a missing-path failure ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: the root-guide refresh workflow regenerates skill output and root guide sections, then opens or updates a pull request only when git drift exists ([test](tests/test_update_spx.compliance.l1.py))
- ALWAYS: regenerating a drifted guide overwrites the drift — a re-render restores the template's content over any hand-edit, the basis of the regenerate-and-diff gate that keeps both files current without an agent invocation ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: the render substitutes a product-specific string into a managed section body — a brace-delimited token in the template passes through unchanged ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: an update keeps an unmodeled hand-prose edit inside the managed section — a re-render reflects only the template, the recorded enabled languages, and the harness, while root content outside the managed section is preserved ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: any rendered guide output contains the session-result archive instruction token or the `result` session frontmatter field token ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: guide generation writes output from a harness template that still contains unresolved build-template delimiters such as `{{! ... !}}` ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: `spx/CLAUDE.md` or `spx/AGENTS.md` remain after guide generation — the root managed section is the canonical guide surface ([test](tests/test_update_spx.compliance.l1.py))
