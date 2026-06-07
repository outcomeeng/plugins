# Update spx/

PROVIDES detection and rendering of a product's `spx/CLAUDE.md` from the installed spec-tree template, scoped to the project's enabled languages
SO THAT all spec-tree projects
CAN stay current with methodology changes without manual template tracking

## Assertions

### Scenarios

- Given a template with language-conditional blocks, when the guide is scaffolded with an enabled-language set, then the rendered output contains exactly the enabled languages' blocks ([test](tests/test_update_spx.scenario.l1.py))
- Given a guide recording an enabled-language set and a newer template that adds a section, when the guide is updated, then the re-rendered guide contains the new section and still carries the recorded enabled languages ([test](tests/test_update_spx.scenario.l1.py))
- Given the CLI edge, `--check` reports `absent`, `stale`, or `current` for a missing, version-behind, or version-current guide, and reports `stale` when `--languages` is supplied and differs from the guide's recorded set; `--write` without `--product` exits non-zero; and `--write` creates the guide file ([test](tests/test_update_spx.scenario.l1.py))
- Given a guide whose `template_version` is not parseable as dotted integers, when staleness is checked, then it is treated as stale rather than raising, so a re-render normalizes it to the installed version ([test](tests/test_update_spx.scenario.l1.py))
- Given an update of a guide that records no `languages` frontmatter key, the update refuses without a supplied `--languages` rather than silently emptying the guide's language sections, and renders when a language set is supplied ([test](tests/test_update_spx.scenario.l1.py))

### Mappings

- Over the languages the template defines blocks for, a language's block appears in the rendered guide when the language is in the guide's recorded `languages` and is omitted otherwise ([test](tests/test_update_spx.mapping.l1.py))

### Properties

- After a scaffold or an update, the `template_version` in the output equals the installed template version ([test](tests/test_update_spx.property.l1.py))
- Every rendered guide ends with exactly one trailing newline ([test](tests/test_update_spx.property.l1.py))
- Staleness ordering matches dotted-numeric version order: a product version is stale exactly when it is numerically below the installed template version ([test](tests/test_update_spx.property.l1.py))

### Compliance

- ALWAYS: `/understanding` detects the project's enabled languages and flags the guide stale when its recorded `languages` or `template_version` fall behind the detected languages or the installed template — staleness detection runs once per session ([audit])
- ALWAYS: `/handoff` checks for the staleness marker emitted by `/understanding` and includes it in the persistence proposal ([audit])
- NEVER: the render substitutes a product-specific string into the guide body — a brace-delimited token in the template passes through unchanged ([test](tests/test_update_spx.compliance.l1.py))
- NEVER: an update keeps an unmodeled hand-prose edit to the guide body — a re-render reflects only the template and the recorded enabled languages ([test](tests/test_update_spx.compliance.l1.py))
