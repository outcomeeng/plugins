# Spec Tree

PROVIDES the Spec Tree methodology — context loading, spec authoring, testing, implementation, and commit workflows
SO THAT all language-specific and craft plugins
CAN operate within a structured, spec-first framework with deterministic context

## Assertions

### Scenarios

- Given a spec-tree enabler directory, when its contents are listed, then a spec file named `{slug}.md` exists ([test](tests/test_spec_tree.scenario.l1.py))
- Given a node directory with a numeric prefix, when validated, then the prefix is an integer between 10 and 99 ([test](tests/test_spec_tree.scenario.l1.py))

### Properties

- Every node directory in the tree contains exactly one spec file matching `{slug}.md` — no orphan directories exist ([test](tests/test_spec_tree.property.l1.py))

### Compliance

- ALWAYS: load complete spec-tree context before any implementation work ([review])
- ALWAYS: use atemporal voice in all specs — specs are permanent truth ([review])
- ALWAYS: the `/understanding` skill's references declare the canonical test-infrastructure subtree `infrastructure → testing → {generators, fixtures, harnesses}` with normative slugs, per `spx/15-test-infrastructure.pdr.md` ([review])
- ALWAYS: the methodology — skill prose, references, templates, audit findings, examples — uses "infrastructure" as the category term for test harnesses, generators, and inert fixtures, per `spx/15-test-infrastructure.pdr.md` ([review])
- NEVER: proceed with partial context — abort if any required document is missing ([review])
- NEVER: the methodology uses "support", "helpers", "utilities", or "tools" as a governing category in the testing context — these are anti-terms per `spx/15-test-infrastructure.pdr.md` ([review])
