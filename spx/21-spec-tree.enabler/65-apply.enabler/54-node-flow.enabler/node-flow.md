# Node Flow

PROVIDES the per-node apply flow — composing the authoring, deterministic-verification, and artifact-audit lanes for every Output kind present, with numbered agentic gates selected by the changeset's least malleable node — driven by spec assertions and run for each node in a selected slice's work queue
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

### Compliance

- ALWAYS: invoke `/contextualize` for the work item before any implementation — the flow loads node context before code is written ([audit])
- ALWAYS: the Code lane writes tests derived from spec assertions before implementation; the Test-evidence lane authors tests as its final artifact; the Spec-or-decision, Skill, and Prose lanes author only their owned artifacts and carry no test-before-implementation sequence ([audit])
- ALWAYS: run every audit gate the changeset owes — the numbered evidence gates and review its least malleable node selects, and the artifact auditors its Output kinds select — through the responsible auditor agents before the flow is complete; the flow never self-approves a gate or runs an audit skill in its own context ([audit])
- ALWAYS: when a changeset spans nodes, widen every selected gate to its complete governed subject set without selecting an additional gate; Step 9 reviews the full changeset when the least malleable touched node selects review, and for a product or outcome-record change regardless of malleability ([audit])
- ALWAYS: when an audit gate returns REJECTED, UNKNOWN, or BLOCKED, attempt remediation before proceeding — the gate verdict governs progression ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([audit])
