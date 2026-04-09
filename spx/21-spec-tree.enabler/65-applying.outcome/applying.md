# Applying

WE BELIEVE THAT an 8-phase TDD flow (architect, test, code + audit gates) driven by spec assertions
WILL produce implementations that conform to their governing specs on the first pass
CONTRIBUTING TO reduced implementation rework and higher spec-test-code alignment

The `/applying` skill orchestrates: context loading, architecture (ADR if needed), test writing, implementation, and three audit gates (code, test evidence, architecture). The `applier` agent runs this flow autonomously as a subagent.

## Assertions

### Scenarios

- Given a target outcome node, when the applying flow starts, then `/contextualizing` is invoked before any implementation ([test](tests/test_applying.unit.py))
- Given an outcome with testable assertions, when the applying flow runs, then tests are written before implementation code ([test](tests/test_applying.unit.py))
- Given implementation completes, when audit gates run, then code, test evidence, and architecture audits produce structured verdicts ([test](tests/test_applying.unit.py))
- Given an audit gate returns REJECT, when the flow continues, then remediation is attempted before proceeding ([test](tests/test_applying.unit.py))

### Compliance

- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([review])
- ALWAYS: run all three audit gates after implementation — skipping gates produces unverified evidence ([review])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([review])
