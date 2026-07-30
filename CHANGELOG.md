# Changelogs

This repository publishes two changelog lines, each on its own clock. Neither is kept at this path — a changelog only reaches its reader if it ships, and a consumer checkout receives installed plugin trees and nothing else from here.

| Line            | Records                                                        | Authored at                                      | Ships as                             |
| --------------- | -------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------ |
| **Plugin**      | what changed in one plugin                                     | `src/plugins/<name>/CHANGELOG.md`                | `<plugin>/CHANGELOG.md`              |
| **Marketplace** | events no single plugin owns: harnesses, plugins added/renamed | `src/plugins/spec-tree/MARKETPLACE-CHANGELOG.md` | `spec-tree/MARKETPLACE-CHANGELOG.md` |

**Editing.** Each line is authored once and ships from one plugin. The marketplace line ships with spec-tree because that plugin carries the methodology every other plugin operationalizes; the lifecycle skill's `help` verb cites it, which is how a consumer reaches it. Never edit a generated copy under `dist/`; edit the authored source and run `just build-skills`.

**Sections** are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. An entry earns its place when the change alters what a consumer can rely on, must do, or must know — artifact class is not the test.
