---
id: 01a0ebba-5f65-7730-9254-ec8b09b3a9cd
malleability: spec
---

# Node Flow

PROVIDES the per-node 8-phase TDD flow — architect, test, code, and the three audit gates — driven by spec assertions and run for each node in a selected slice's work queue
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

- ALWAYS: before implementation, the flow runs each new or changed test and eval and confirms that it fails only because the implementation it verifies is absent; the evidence audit dispatches after implementation, on a committed head where that evidence passes, per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

### Compliance

- ALWAYS: invoke `/contextualize` for the work item before any implementation — the flow loads node context before code is written ([audit])
- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([audit])
- ALWAYS: run all three audit gates through the responsible auditor agents before the flow is complete — the flow never self-approves a gate or runs an audit skill in its own context ([audit])
- ALWAYS: when an audit gate's sealed run's terminal status is `rejected` or its launch is blocked, attempt remediation within the gate cap [`spx/21-spec-tree.enabler/65-apply.enabler/apply.md`](spx/21-spec-tree.enabler/65-apply.enabler/apply.md) states — the gate verdict governs progression ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([audit])
