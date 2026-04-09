# Update spx/

WE BELIEVE THAT detecting and applying updates to a project's `spx/CLAUDE.md` from the installed plugin template
WILL reduce methodology drift and ensure agents in user projects have current skill and agent guidance
CONTRIBUTING TO fewer skipped audits and correct subagent dispatch across the install base

## Assertions

### Scenarios

- Given a project with `spx/CLAUDE.md` at template_version 0.17.0 and the installed plugin at 0.18.2, when `/understanding` runs, then it detects the version mismatch and uses the template version as authoritative ([test](tests/test_update_spx.unit.py))
- Given `/understanding` detected a stale `spx/CLAUDE.md`, when `/handoff` runs, then the staleness is included in the persistence proposal ([test](tests/test_update_spx.unit.py))
- Given a user invokes `/update-spx`, when the project's `spx/CLAUDE.md` is older than the template, then the file is updated preserving user customizations in the product name placeholder ([test](tests/test_update_spx.unit.py))
- Given a project with no `spx/CLAUDE.md`, when `/update-spx` runs, then the template is scaffolded with a prompt for the product name ([test](tests/test_update_spx.unit.py))

### Properties

- The template_version in `spx/CLAUDE.md` always matches the installed spec-tree plugin version after `/update-spx` completes ([test](tests/test_update_spx.unit.py))

### Compliance

- ALWAYS: `/understanding` compares `spx/CLAUDE.md` frontmatter `template_version` against the installed template — staleness detection runs once per session ([review])
- ALWAYS: `/handoff` checks for the staleness marker emitted by `/understanding` and includes it in the persistence proposal ([review])
- NEVER: `/update-spx` overwrites user-specific content (product name, deleted language sections) — only structural sections from the template are merged ([review])

## Deliverables

| Artifact                 | Plugin    | Purpose                                                    |
| ------------------------ | --------- | ---------------------------------------------------------- |
| `/updating-spx` (skill)  | spec-tree | Methodology: diff template vs project file, merge strategy |
| `/update-spx` (command)  | spec-tree | User-facing command that invokes the skill                 |
| `spx-updater` (agent)    | spec-tree | Subagent that preloads the skill for autonomous execution  |
| `/understanding` changes | spec-tree | Staleness detection on session start                       |
| `/handoff` changes       | spec-tree | Staleness marker in persistence proposal                   |
