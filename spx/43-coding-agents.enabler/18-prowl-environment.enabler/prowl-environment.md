# Prowl Environment

PROVIDES a source-owned, versioned abstraction over the complete public Prowl command surface and correlated delegation handbacks
SO THAT agent communication, coordination, and recovery workflows
CAN operate between any positively identified Prowl agents without constructing raw Prowl commands or discovering command syntax at runtime

## Assertions

### Mappings

- Every supported operation — list, agents, read, send, key, focus, tab create, tab close, pane close, and open — maps from one source-owned request shape to one exact Prowl argument vector and checked response result ([test](tests/test_prowl_environment.mapping.l1.py))
- Public Prowl agent evidence maps to complete source-preserved agent, pane, worktree, branch, repository, and applicable run identities or to a named unavailable or ambiguous result ([test](tests/test_prowl_environment.mapping.l1.py))
- A delegation request maps to exactly one correlated `delegation-completed`, `delegation-failed`, `delegation-rejected`, or `delegation-unavailable` terminal handback containing a complete inline result or an exact durable result reference with a bounded inline projection ([test](tests/test_prowl_environment.mapping.l1.py))

### Conformance

- Every operation emits a versioned JSON result conforming to its source-owned schema while preserving Prowl identity, status, conclusion, and exit-code values verbatim ([test](tests/test_prowl_environment.conformance.l1.py))
- A Prowl operation with no explicit input isolates the child command from the adapter request stream, while explicit input reaches the child unchanged ([test](tests/test_prowl_environment.conformance.l1.py))

### Properties

- Matching repeated terminal handbacks for one coordination reference preserve one terminal outcome, while conflicting terminal states for that reference are rejected ([test](tests/test_prowl_environment.property.l1.py))

### Compliance

- ALWAYS: focus, key injection, tab or pane creation, and tab or pane closure require explicit mutation authorization in the operation request before any Prowl command runs ([test](tests/test_prowl_environment.compliance.l1.py))
- NEVER: another shipped coding-agents script constructs a raw Prowl argument vector or invokes Prowl command help ([test](tests/test_prowl_environment.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct raw Prowl commands, invoke Prowl command help, or depend on an external environment-control skill ([audit])
