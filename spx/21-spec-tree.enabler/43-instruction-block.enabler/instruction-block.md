# Instruction Block

PROVIDES deterministic generation of a managed Spec Tree instruction block in a product's root agent-harness instruction files — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — from the rendered harness templates committed under `dist/`, scoped to the project's enabled languages and rendered per agent harness
SO THAT every agent working a spec-tree project
CAN retain the Spec Tree routing instructions across compaction while preserving the product's own root instructions

## Assertions

### Scenarios

- Given a template with language blocks and per-harness blocks, when the managed root instruction block is generated for an enabled-language set, then both `CLAUDE.md` and `AGENTS.md` are written, each preserving root content outside the instruction block and containing exactly the enabled languages' blocks and only its own harness's blocks inside the instruction block ([test](tests/test_instruction_block.scenario.l1.py))
- Given the `CLAUDE.md` and `AGENTS.md` outputs of one generation, when they are compared, then they share every line except the per-harness blocks the template marks; the two files differ only there and in their own filename, which is the output path, not a span of the shared body ([test](tests/test_instruction_block.scenario.l1.py))
- Given a newer template that adds a section, when the managed root instruction block is updated, then both re-rendered instruction blocks contain the new section and still carry the recorded enabled languages ([test](tests/test_instruction_block.scenario.l1.py))
- Given the CLI edge, `--check` reports `absent`, `stale`, or `current` for a missing, version-behind, or version-current instruction block, reports `stale` when the detected language set differs from the recorded set, and `--write` creates both instruction files ([test](tests/test_instruction_block.scenario.l1.py))
- Given a `--template` argument that is a symlink or does not resolve to an existing regular file, when the CLI runs, then the path is validated and rejected before any read, so a faulty argument cannot escape into an unintended file ([test](tests/test_instruction_block.scenario.l1.py))
- Given an instruction block whose `template_version` is not parseable as dotted integers, when staleness is checked, then it is treated as stale rather than raising, so a re-render normalizes it to the installed version ([test](tests/test_instruction_block.scenario.l1.py))
- Given root `CLAUDE.md` is a symlink to `AGENTS.md`, when `--write` updates the managed Spec Tree instruction block, then `CLAUDE.md` becomes a regular file copy and both root instruction files preserve the shared root body outside their harness-specific instruction blocks ([test](tests/test_instruction_block.scenario.l1.py))
- Given a root instruction file contains a markerless generated Spec Tree instruction block from the retired full-file surface, when `--write` updates the managed Spec Tree instruction block, then the generated legacy body is replaced rather than preserved ahead of the instruction block ([test](tests/test_instruction_block.scenario.l1.py))
- Given a root instruction file carries a managed block delimited by the retired marker naming, when staleness is checked, then it reports `stale`, and when `--write` updates the managed Spec Tree instruction block, then the legacy-marker block is replaced in place with the current marker rather than duplicated ([test](tests/test_instruction_block.scenario.l1.py))

### Mappings

- Over the languages the template defines blocks for, a language's block appears in a rendered instruction block when the language is in the detected enabled set and is omitted otherwise ([test](tests/test_instruction_block.mapping.l1.py))
- A test-file extension present under `spx/**/tests/` maps to the language it denotes, and the detected enabled-language set is the set of those mappings ([test](tests/test_instruction_block.mapping.l1.py))

### Properties

- After generation, each instruction block's `template_version` equals the installed template version ([test](tests/test_instruction_block.property.l1.py))
- Every rendered instruction block ends with exactly one trailing newline ([test](tests/test_instruction_block.property.l1.py))
- Staleness ordering matches dotted-numeric version order: a product version is stale exactly when it is numerically below the installed template version ([test](tests/test_instruction_block.property.l1.py))

### Compliance

- ALWAYS: generation writes instruction blocks in both root `CLAUDE.md` and root `AGENTS.md`, never one without the other — each agent reading the same repository gets its own harness instruction block in the root instruction file it retains across compaction ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: instruction-block generation reads the harness-specific instruction-block templates from `dist/claude/` and `dist/codex/`, so the instruction-block update surface consumes the same rendered output this product ships as installed plugin trees ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: instruction-block writing is exposed to agents through the repository Justfile recipe `just build-instructions`; `just instructions-check` is the drift gate over the same writer ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: the instruction-block drift gate reports missing root instruction-file paths as drift and marks only existing generated instruction-file paths with `--intent-to-add`, so deleted obsolete `spx/` instruction files are reported by `git diff` without causing a missing-path failure ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: the instruction-block refresh workflow regenerates skill output and root instruction blocks, then opens or updates a pull request only when git drift exists ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: the instruction-block refresh workflow checks out the default branch `main`, so its regeneration and drift comparison run against the published tree ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: the instruction-block refresh workflow verifies the pinned `just` download against its recorded SHA-256 checksum before installing it, so a tampered or moved release fails the run rather than executing ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: the instruction-block refresh workflow provisions `dprint` before regenerating skill output, because `just build-skills` formats generated `dist/` output with `dprint` and fails without it ([test](tests/test_instruction_block.compliance.l1.py))
- ALWAYS: regenerating a drifted instruction block overwrites the drift — a re-render restores the template's content over any hand-edit, the basis of the regenerate-and-diff gate that keeps both files current without an agent invocation ([test](tests/test_instruction_block.compliance.l1.py))
- NEVER: the render substitutes a product-specific string into an instruction-block body — a brace-delimited token in the template passes through unchanged ([test](tests/test_instruction_block.compliance.l1.py))
- NEVER: an update keeps an unmodeled hand-prose edit inside the instruction block — a re-render reflects only the template, the recorded enabled languages, and the harness, while root content outside the instruction block is preserved ([test](tests/test_instruction_block.compliance.l1.py))
- NEVER: any rendered instruction-block output contains the session-result archive instruction token or the `result` session frontmatter field token ([test](tests/test_instruction_block.compliance.l1.py))
- NEVER: instruction-block generation writes output from a harness template that still contains unresolved build-template delimiters such as `{{! ... !}}` ([test](tests/test_instruction_block.compliance.l1.py))
- NEVER: `spx/CLAUDE.md` or `spx/AGENTS.md` remain after instruction-block generation — the root managed instruction block is the canonical instruction surface ([test](tests/test_instruction_block.compliance.l1.py))
