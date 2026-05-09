# Template Update Engine

## Purpose

This decision governs how Spec Tree updates project-local `spx/CLAUDE.md` guides from the installed plugin template.

## Context

**Business impact:** Spec Tree projects keep methodology guidance current without requiring developers to compare template files by hand.

**Technical constraints:** The updater runs inside agent-controlled repositories where `spx/CLAUDE.md` may be a symlink, may contain project-specific product names, and may have language rows deleted by the project. Claude Code and Codex expose skills and commands as markdown prompt artifacts, while deterministic merge behavior needs automated test evidence.

## Decision

Template synchronization uses a skill-local Python update engine with a small CLI boundary, while `/understanding`, `/handoff`, and `/update-spx` remain prompt surfaces that delegate detection, persistence messaging, and execution to that engine.

## Rationale

A skill-local Python engine gives tests direct access to version parsing, template rendering, symlink handling, and merge behavior. Keeping command and skill markdown as thin surfaces preserves plugin ergonomics across Claude Code and Codex, and avoids duplicating merge rules in prompt text. A repo-root helper module would couple installed plugins to marketplace checkout layout, while a skill-local script ships with the spec-tree plugin itself.

## Trade-offs accepted

| Trade-off                                                          | Mitigation / reasoning                                                                                 |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| The skill directory contains executable support code               | The script is local to `/updating-spx`, has a narrow CLI, and is covered by co-located spec-tree tests |
| Prompt surfaces depend on marker text emitted by the update engine | The marker names are documented in the ADR and tested through markdown wiring checks                   |

## Compliance

### Recognized by

A `plugins/spec-tree/skills/updating-spx/` skill containing `SKILL.md` and `scripts/update_spx.py`, plus `/update-spx` command and `spx-updater` agent prompt surfaces that invoke the skill.

### MUST

- The update engine accepts explicit project guide and template paths as parameters — enables `l1` tests with temporary directories and no global filesystem assumptions ([review])
- The update engine preserves project-specific product names and deleted language sections while replacing managed methodology sections from the template — keeps local customization intact ([review])
- The update engine emits stable staleness markers that `/understanding` and `/handoff` can reference — enables prompt surfaces to coordinate without reimplementing merge logic ([review])
- The update engine resolves `spx/CLAUDE.md` symlinks to the real file before writing — supports projects whose Codex and Claude instructions share one guide ([review])

### NEVER

- Shell out to compare or patch guide files — subprocess output would make `l1` evidence brittle and harder to diagnose ([review])
- Read plugin manifests as the source of template content — the bootstrapping `spx-claude.md` template is the update authority ([review])
- Overwrite sections the project deleted from the Quick Reference or Test Naming tables — deleted rows and language sections are project customization ([review])
