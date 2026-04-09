# Field Extraction Strategy

## Purpose

This decision governs how the set of valid SKILL.md frontmatter fields is determined. Consistent field discovery prevents validation drift as the Claude Code CLI evolves its accepted fields.

## Context

**Business impact:** Skill authors whose frontmatter is rejected by Claude Code but passes local validation lose trust in the validation pipeline. Authors whose frontmatter is accepted by Claude Code but rejected locally are blocked from committing valid work. Both failure modes stem from a drift between local validation and the authoritative field set.

**Technical constraints:** The Claude Code CLI is distributed as a compiled binary that embeds JavaScript source. The source parses frontmatter via property access patterns (`var["field-name"]`, `var.field`), so the accepted field set is inspectable by scanning the binary for these patterns. The Agent Skills open standard defines a smaller floor set of universally recognized fields.

## Decision

The set of valid SKILL.md frontmatter fields is the union of the Agent Skills open standard floor and the field set extracted from the installed Claude Code CLI binary at validation time.

## Rationale

Two extremes fail:

- **Hardcoded field list** — drifts from reality the moment Claude Code adds a field. Requires a maintenance step that is always late.
- **Only the open standard floor** — rejects Claude Code-specific fields that are legitimate, blocking skill authors from using features the CLI actually supports.

Extracting fields from the installed binary at validation time keeps the ceiling current without a maintenance step. The open standard provides a floor that applies even when binary extraction fails (e.g., unusual install locations, permissions issues), preserving forward compatibility with any Agent Skills runtime.

The extraction reads property access patterns from the binary's embedded JavaScript. The extraction logic is coupled to the CLI's parser representation; any change in that representation requires a corresponding change in the extraction patterns.

Binary location and binary reading are performed through injectable callables so that the fallback logic is verifiable at Level 1 without filesystem coupling or process monkeypatching. Tests supply lambdas that return `None` to exercise the fallback path; production callers use the default resolvers.

## Trade-offs accepted

| Trade-off                                                                  | Mitigation / reasoning                                                                                           |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Extraction depends on an internal parser pattern in the Claude Code binary | The open standard floor provides a safe fallback when the pattern fails to match                                 |
| Validation results depend on the locally installed Claude Code version     | Validation is a developer tool; differences between local environments produce actionable diagnostics, not drift |
| Extraction fails silently when the binary is missing                       | The open standard floor serves as the result, still catching malformed frontmatter                               |

## Compliance

### Recognized by

The `validate_skill_frontmatter.py` script computes valid fields at runtime from the installed binary plus the open standard floor. No committed constant lists Claude Code-specific fields.

### MUST

- Derive Claude Code-specific fields from the installed binary at runtime — the authoritative source is the CLI, not a committed list ([review])
- Fall back to the Agent Skills open standard floor when binary extraction fails — validation never fully breaks on a missing or unreadable binary ([review])
- Binary location accepts an injected callable that returns the binary path or `None` — the fallback branch is verifiable at Level 1 without filesystem coupling ([review])
- Binary field extraction accepts an injected callable that returns the extracted field set or `None` — the fallback branch is verifiable at Level 1 without process execution ([review])

### NEVER

- Hardcode Claude Code-specific fields in source or configuration — any field the CLI may accept changes between releases and hardcoding creates drift ([review])
- Use `unittest.mock.patch` on filesystem or subprocess operations in tests for this module — the injectable callables are the sanctioned seam ([review])
- Call `shutil.which`, `Path.read_bytes`, or `subprocess.run` outside the injected resolver and reader boundaries — direct calls bypass the testability contract ([review])
