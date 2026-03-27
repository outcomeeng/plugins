<overview>

When a spec and its tests are authored before the implementation exists, the node is in **specified** state. Tests import from modules that don't exist yet, so they break type checkers (unresolved imports) and test runners (ImportError). The `spx/EXCLUDE` file lists these nodes and a sync mechanism excludes them from the quality gate.

</overview>

<spx_exclude_file>

`spx/EXCLUDE` is a visible, version-controlled file listing node paths in specified state. Paths are relative to `spx/`.

```text
# Nodes excluded from the quality gate.
# Specs and tests exist. Implementation does not.
# Tests are excluded from pytest and type checking.
# Linting still runs — style is checked regardless.
#
# Run the project's sync command after editing.
# Remove entries when implementation begins.

57-subsystems.outcome/32-risc-v.outcome
```

**Why visible, not hidden:** The file shows where specified nodes exist. Agents and humans discover it by reading the `spx/` directory — no hunting required.

**Why in `spx/`, not project root:** The file describes spec tree state. It belongs with the tree, not as project-root cruft.

</spx_exclude_file>

<quality_gate_integration>

A sync mechanism reads `spx/EXCLUDE` and updates the project's tool configuration to exclude specified nodes. The specific tools and configuration format are language-specific — the spec-tree plugin defines the convention, language plugins define the implementation.

| Tool category    | Exclusion behavior                                                     |
| ---------------- | ---------------------------------------------------------------------- |
| **Linter**       | NOT excluded — style is checked regardless of implementation existence |
| **Type checker** | Excluded — imports from non-existent modules cause unresolvable errors |
| **Test runner**  | Excluded — imports fail at collection time                             |

**Linters always check.** A specified test file is still valid code with correct style. Excluding it from linting would mask real quality issues.

**The sync is a build step, not a hack.** It translates `spx/EXCLUDE` (the source of truth) into the native configuration format each tool expects.

</quality_gate_integration>

<lifecycle>

| Event                        | Action                                         |
| ---------------------------- | ---------------------------------------------- |
| Author spec + tests          | Add node path to `spx/EXCLUDE`, run sync       |
| Begin implementation         | Remove node from `spx/EXCLUDE`, run sync       |
| Tests start passing          | Node transitions from failing → passing        |
| Implementation removed later | Add node back to `spx/EXCLUDE` if tests remain |

Exclusion is not permanent. It declares "specs and tests exist, implementation does not." When the implementation arrives, the exclusion is removed and the tests join the quality gate.

</lifecycle>

<not_cheating>

Exclusion is fundamentally different from suppressing errors:

| Suppressing errors (wrong)       | Exclusion (correct)                              |
| -------------------------------- | ------------------------------------------------ |
| `# noqa` / `# type: ignore`      | `spx/EXCLUDE` lists nodes without implementation |
| Hides real bugs in existing code | Declares that implementation does not exist yet  |
| Stays forever unless removed     | Removed when implementation begins               |
| Per-line, scattered, invisible   | Per-node, centralized, visible                   |
| Cheating the quality gate        | Defining the quality gate's scope                |

</not_cheating>
