# Update spx/

PROVIDES detection and rendering of a product's `spx/CLAUDE.md` from the installed spec-tree template and the guide's declared customization config
SO THAT all spec-tree projects
CAN stay current with methodology changes without manual template tracking

## Assertions

### Scenarios

- Given a template carrying the `{product-name}` placeholder and language-conditional blocks, when the guide is scaffolded with a product name and an enabled-language set, then the rendered output substitutes the product name and contains exactly the enabled languages' blocks ([test](tests/test_update_spx.scenario.l1.py))
- Given a guide whose config enables a language set and a newer template that adds a section, when the guide is updated, then the re-rendered guide contains the new section and still carries the config's product name and enabled languages ([test](tests/test_update_spx.scenario.l1.py))
- Given the CLI edge, `--check` reports `absent`, `stale`, or `current` for a missing, version-behind, or version-current guide; `--write` without `--product` exits non-zero; and `--write` creates the guide file ([test](tests/test_update_spx.scenario.l1.py))
- Given an update of a guide that predates the config schema (no `product_name` frontmatter), the update refuses without a supplied name rather than discarding the body-held name, and migrates when a name and languages are supplied ([test](tests/test_update_spx.scenario.l1.py))

### Mappings

- Over the languages the template defines blocks for, a language's block appears in the rendered guide when the language is in the config's `languages` and is omitted otherwise ([test](tests/test_update_spx.mapping.l1.py))

### Properties

- After a scaffold or an update, the `template_version` in the output equals the installed template version ([test](tests/test_update_spx.property.l1.py))
- Every rendered guide ends with exactly one trailing newline ([test](tests/test_update_spx.property.l1.py))
- Staleness ordering matches dotted-numeric version order: a product version is stale exactly when it is numerically below the installed template version ([test](tests/test_update_spx.property.l1.py))

### Compliance

- ALWAYS: `/understanding` compares the product guide's frontmatter `template_version` against the installed template in the understanding skill's `templates/` — staleness detection runs once per session ([audit])
- ALWAYS: `/handoff` checks for the staleness marker emitted by `/understanding` and includes it in the persistence proposal ([audit])
- NEVER: an update keeps an unmodeled hand-prose edit to the guide body — a re-render reflects only the template and the guide's declared config ([test](tests/test_update_spx.compliance.l1.py))
