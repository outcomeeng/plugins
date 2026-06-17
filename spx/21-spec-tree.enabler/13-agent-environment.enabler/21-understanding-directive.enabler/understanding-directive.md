# Understanding Directive

PROVIDES a session-start directive that prompts loading the Spec Tree methodology foundation in a spec-tree repository
SO THAT an agent beginning spec-tree work
CAN load the foundation before acting rather than proceeding from memory

`spx hooks session-start` assembles this directive and emits it in the session-start JSON document per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`: the `specTree.directives` array carries an entry of kind `understanding`, and the rendered `additionalContext` names `/spec-tree:understand` and `/spec-tree:contextualize` and points at the mechanical `PreToolUse` load gate (`spx/21-spec-tree.enabler/13-agent-environment.enabler/54-load-gating.enabler`) as the enforcement.

## Assertions

### Scenarios

- Given a `SessionStart` payload whose project directory contains a product spec (`spx/*.product.md`), when `spx hooks session-start` runs, then it exits zero and its JSON document carries a `specTree.directives` entry of kind `understanding` ([test](tests/test_understanding_directive.scenario.l1.py))

### Mappings

- A project directory maps to the understanding directive: a directory containing `spx/*.product.md` maps to a `specTree.directives` entry of kind `understanding`; a directory without one maps to no `understanding` entry ([test](tests/test_understanding_directive.mapping.l1.py))

### Compliance

- ALWAYS: detect a spec-tree repository by the presence of `spx/*.product.md` under the project directory — never from `.spx/` state or other heuristics ([test](tests/test_understanding_directive.compliance.l1.py))
