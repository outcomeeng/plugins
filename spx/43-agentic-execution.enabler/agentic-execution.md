# Agentic Execution

PROVIDES portable semantics for configured-agent task intent and execution policy
SO THAT coding-agent surfaces and configured-agent producers
CAN classify agentic work and select explicit execution behavior without privileging one agent harness's grammar or configuration shape

## Assertions

### Compliance

- ALWAYS: configured-agent task intent and execution policy are expressible without reference to an agent-harness-specific grammar or configuration field — shared semantics remain portable across coding-agent surfaces ([audit])
- NEVER: a coding-agent surface defines shared task categories or cross-harness model-selection semantics — coding-agent surfaces consume the agentic-execution domain and own only their native boundary ([audit])
