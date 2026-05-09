# Marketplace PR Rules

Loaded by `/opening-pr` when working in this repository. Marketplace-specific additions to the base PR workflow.

## Pre-flight additions

In addition to `/opening-pr`'s branch hygiene, verify before opening:

| Check                                                                        | If failing                                                 |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `just check` passes                                                          | STOP. Fix lint, format, and validation drift first.        |
| Plugin manifest version bumped when the change warrants it                   | STOP. Bump per `spx/local/committing-changes.md`.          |
| Both marketplace catalogs updated when adding or removing a plugin           | STOP. `just check` enforces; run it.                       |
| `AGENTS.md` skills, commands, and agents tables updated to match the change  | STOP. New or removed artifacts must appear in the catalog. |
| `bootstrapping/templates/spx-claude.md` updated when skill structure changes | STOP. New projects inherit this template.                  |

## Required body sections

Append to the default template from `/opening-pr`:

```text
## Versioning

- <plugin>: <old> → <new> (<MAJOR | MINOR | PATCH>)

## Validation

- [ ] `just check` passes
- [ ] `/reload-plugins` confirms the change loads in a running session
```

Drop the **Versioning** section only when no `plugin.json` files changed.

## Push command

Feature-branch PRs use bare `git push -u origin <branch>`. The marketplace-specific `just push-marketplace` recipe is for post-merge pushes to `main`, not for opening a PR from a feature branch.

## Self-reference

The marketplace bans agent identity strings from branch names, commit messages, PR titles, and PR bodies (see the project-level `self_reference_policy`). The base `/opening-pr` skill already enforces this — no further additions here.
