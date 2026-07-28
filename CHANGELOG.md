# Changelogs

This repository publishes three changelog lines, each on its own clock. None of them is kept at this path — a changelog only reaches its reader if it ships, and a consumer checkout receives installed plugin trees and nothing else from here.

| Line            | Records                                                        | Authored at                                                | Ships as                                                                            |
| --------------- | -------------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Methodology** | edition transitions, compatible extensions, deprecations       | `src/plugins/spec-tree/METHODOLOGY-CHANGELOG.md`           | `<spec-tree>/METHODOLOGY-CHANGELOG.md`                                              |
| **Plugin**      | what changed in one plugin                                     | `src/plugins/<name>/CHANGELOG.md`                          | `<plugin>/CHANGELOG.md`                                                             |
| **Marketplace** | events no single plugin owns: harnesses, plugins added/renamed | `src/templates/plugin/references/MARKETPLACE-CHANGELOG.md` | `<plugin>/skills/<plugin>-plugin/references/MARKETPLACE-CHANGELOG.md`, every plugin |

**Editing.** The methodology and plugin lines are authored once and ship from their own plugin. The marketplace line is authored once under `src/templates/plugin/references/` and fans out to every plugin, because a marketplace event has to stay readable whatever subset of plugins a repository installs — a plugin rename is unreadable from the renamed plugin once its old identity stops resolving. It lives in the lifecycle skill's `references/` directory and is cited by that skill's `help` verb, which is how a consumer reaches it. Never edit a generated copy under `dist/`; edit the authored source and run `just build-skills`.

**Sections** are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. An entry earns its place when the change alters what a consumer can rely on, must do, or must know — artifact class is not the test.
