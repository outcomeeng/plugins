# Marketplace PR Rules

Loaded by `/open-pr` when working in this repository. Marketplace-specific additions to the base PR workflow.

## Pre-flight additions

In addition to `/open-pr`'s branch hygiene, verify before opening:

| Check                                                                                                       | If failing                                                           |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| The touched-scope deterministic verification selected by `spx/local/merging.md` and root `AGENTS.md` passes | STOP. Fix the failing touched-scope lane first.                      |
| Plugin manifest version bumped when the change warrants it                                                  | STOP. Bump per `spx/local/commit-changes.md`.                        |
| Both marketplace catalogs updated when adding or removing a plugin                                          | STOP. Run the catalog or manifest command named by root `AGENTS.md`. |
| `AGENTS.md` skills, commands, and agents tables updated to match the change                                 | STOP. New or removed artifacts must appear in the catalog.           |
| `update-instruction-block/templates/instruction-block.md` updated when skill structure changes              | STOP. New projects inherit this template.                            |

## Required body sections

Append to the default template from `/open-pr`:

```text
## Versioning

- <plugin>: <old> → <new> (<MAJOR | MINOR | PATCH>)

## Validation

- [ ] Touched-scope deterministic verification passes
- [ ] `/reload-plugins` confirms the change loads in a running session
```

Drop the **Versioning** section only when no `plugin.json` files changed.
