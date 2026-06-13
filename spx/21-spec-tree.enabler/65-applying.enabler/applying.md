# Applying

PROVIDES an 8-phase TDD flow (architect, test, code + audit gates) driven by spec assertions
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

### Scenarios

- Given a target outcome node, when the applying flow starts, then `/contextualizing` is invoked before any implementation ([test](tests/test_applying.scenario.l1.py))
- Given an outcome with testable assertions, when the applying flow runs, then tests are written before implementation code ([test](tests/test_applying.scenario.l1.py))
- Given implementation completes, when audit gates run, then code, test evidence, and architecture audits produce structured verdicts ([test](tests/test_applying.scenario.l1.py))
- Given an audit gate returns REJECT, when the flow continues, then remediation is attempted before proceeding ([test](tests/test_applying.scenario.l1.py))

### Compliance

- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([review])
- ALWAYS: run all three audit gates after implementation — skipping gates produces unverified evidence ([review])
- ALWAYS: when the change touches files or specs beyond the target node, run a whole-changeset review (the `changes-reviewer` agent or `/reviewing-changes`) over the full diff and point the language audit gates at the whole changeset before declaring the flow complete — per-node gates miss cross-node effects ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([review])
