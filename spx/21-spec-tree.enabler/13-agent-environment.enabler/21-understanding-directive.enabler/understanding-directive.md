# Understanding Directive

PROVIDES a session-start directive that prompts loading the Spec Tree methodology foundation in a spec-tree repository
SO THAT an agent beginning spec-tree work
CAN load the foundation before acting rather than proceeding from memory

## Assertions

### Scenarios

- Given a `SessionStart` payload whose project directory contains a product spec (`spx/*.product.md`), when the hook runs, then stdout carries a `<SPEC-TREE_SESSION_START foundation="load"/>` directive instructing the agent to invoke `/spec-tree:understanding` before spec-tree work and `/spec-tree:contextualizing` on the target node ([test](tests/test_understanding_directive.scenario.l1.py))

### Mappings

- A project directory maps to the understanding-directive output: a directory containing `spx/*.product.md` maps to a directive naming `/spec-tree:understanding`; a directory without one maps to no directive ([test](tests/test_understanding_directive.mapping.l1.py))

### Compliance

- ALWAYS: detect a spec-tree repository by the presence of `spx/*.product.md` under the project directory — never from `.spx/` state or other heuristics ([test](tests/test_understanding_directive.compliance.l1.py))
