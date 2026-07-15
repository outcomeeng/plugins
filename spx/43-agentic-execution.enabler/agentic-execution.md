# Agentic Execution

PROVIDES the bounded semantics for configured-agent task intent, execution policy, and runtime-independent invariants
SO THAT coding-agent surfaces and the product areas that define configured agents
CAN classify agentic work and select explicit runtime behavior without privileging one coding agent's vocabulary or configuration shape

## Assertions

### Compliance

- ALWAYS: configured-agent task intent and execution policy are expressible without reference to a coding-agent-specific grammar or configuration field — shared semantics remain portable across runtime surfaces ([audit])
- NEVER: a coding-agent surface defines shared task categories or cross-runtime model-selection semantics — runtime surfaces consume the agentic-execution domain and own only their native boundary ([audit])
