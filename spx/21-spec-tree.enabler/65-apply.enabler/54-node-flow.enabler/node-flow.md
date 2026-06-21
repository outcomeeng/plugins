# Node Flow

PROVIDES the per-node 8-phase TDD flow — architect, test, code, and the three audit gates — driven by spec assertions and run for each node in a selected slice's work queue
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

### Compliance

- ALWAYS: invoke `/contextualize` for the work item before any implementation — the flow loads node context before code is written ([audit])
- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([review])
- ALWAYS: run all three audit gates after implementation — skipping gates produces unverified evidence ([review])
- ALWAYS: when an audit gate returns REJECT, attempt remediation before proceeding — the gate verdict governs progression ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([review])
