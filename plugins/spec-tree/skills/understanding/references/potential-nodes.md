<overview>

When a spec and its tests are authored before the implementation exists, the node is in **potential** state. Tests import from modules that don't exist yet, so they break type checkers (unresolved imports) and test runners (ImportError). The `spx/POTENTIAL` file declares these nodes and a sync mechanism excludes them from the quality gate.

</overview>

<spx_potential_file>

`spx/POTENTIAL` is a visible, version-controlled file listing node paths in potential state. Paths are relative to `spx/`.

```text
# Nodes with potential — specs and tests exist, implementation doesn't.
#
# Run the project's sync command after editing to update tool config.
# Remove entries when implementation begins and tests should run.

76-risc-v.outcome
```

**Why visible, not hidden:** The file indicates where potential exists in the product. Agents and humans discover it by reading the `spx/` directory — no hunting required.

**Why in `spx/`, not project root:** The file describes spec tree state. It belongs with the tree, not as project-root cruft.

</spx_potential_file>

<quality_gate_integration>

A sync mechanism reads `spx/POTENTIAL` and updates the project's tool configuration to exclude potential nodes. The specific tools and configuration format are language-specific — the spec-tree plugin defines the convention, language plugins define the implementation.

| Tool category    | Exclusion behavior                                                     |
| ---------------- | ---------------------------------------------------------------------- |
| **Linter**       | NOT excluded — style is checked regardless of implementation existence |
| **Type checker** | Excluded — imports from non-existent modules cause unresolvable errors |
| **Test runner**  | Excluded — imports fail at collection time                             |

**Linters always check.** A potential test file is still valid code with correct style. Excluding it from linting would mask real quality issues.

**The sync is a build step, not a hack.** It translates `spx/POTENTIAL` (the source of truth) into the native configuration format each tool expects. Similar to how `.lint-excludes` syncs to tool-specific exclude lists.

</quality_gate_integration>

<lifecycle>

| Event                        | Action                                           |
| ---------------------------- | ------------------------------------------------ |
| Author spec + tests          | Add node path to `spx/POTENTIAL`, run sync       |
| Begin implementation         | Remove node from `spx/POTENTIAL`, run sync       |
| Tests start passing          | Node transitions from failing → realized         |
| Implementation removed later | Add node back to `spx/POTENTIAL` if tests remain |

Potential is not a permanent state. It declares "this is where the product is going." When the implementation arrives, the exclusion is removed and the tests join the quality gate.

</lifecycle>

<not_cheating>

Potential exclusion is fundamentally different from suppressing errors:

| Suppressing errors (wrong)       | Potential exclusion (correct)                      |
| -------------------------------- | -------------------------------------------------- |
| `# noqa` / `# type: ignore`      | `spx/POTENTIAL` lists nodes without implementation |
| Hides real bugs in existing code | Declares intent for code that doesn't exist yet    |
| Stays forever unless removed     | Removed when implementation begins                 |
| Per-line, scattered, invisible   | Per-node, centralized, visible                     |
| Cheating the quality gate        | Declaring the quality gate's scope                 |

</not_cheating>
