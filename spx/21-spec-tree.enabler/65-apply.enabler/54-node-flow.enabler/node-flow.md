# Node Flow

PROVIDES the per-node 8-phase TDD flow — architect, test, code, and the three audit gates — driven by spec assertions and run for each node in a selected slice's work queue
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

### Compliance

- ALWAYS: `--agent [node-path]` dispatches the full flow to the `applier` agent and runs nothing else in the main context — the autonomous runner owns the per-node flow ([audit])
- ALWAYS: with a node-path argument the work queue is that single node, and with no argument it is derived from the conversation, falling back to the node paths listed in `spx/EXCLUDE` ([audit])
- ALWAYS: a multi-node work queue runs in ascending numeric-index order, removing each node from `spx/EXCLUDE` before its flow and committing per node, and a node whose flow cannot converge stops the queue with the remaining nodes left in `spx/EXCLUDE` ([audit])
- ALWAYS: invoke `/contextualize` for the work item before any implementation — the flow loads node context before code is written ([audit])
- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([review])
- ALWAYS: run all three audit gates after implementation — skipping gates produces unverified evidence ([review])
- ALWAYS: when an audit gate returns REJECT, attempt remediation before proceeding — the gate verdict governs progression ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([review])
