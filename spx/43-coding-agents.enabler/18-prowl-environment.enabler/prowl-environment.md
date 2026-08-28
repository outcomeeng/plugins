# Prowl Environment

PROVIDES a source-owned, versioned abstraction over the complete public Prowl command surface and correlated delegation handbacks
SO THAT agent communication, coordination, and recovery workflows
CAN operate between any positively identified Prowl agents without constructing raw Prowl commands or discovering command syntax at runtime

## Assertions

### Mappings

- Every supported operation — list, agents, read, send, key, focus, tab create, tab close, pane close, and open — maps each source-owned request shape through the source-owned operation registry to one Prowl argument vector and checked response result ([test](tests/test_prowl_environment.mapping.l1.py))
- Public Prowl agent evidence maps to complete source-preserved agent, pane, worktree, branch, repository, and applicable run identities or to a named unavailable or ambiguous result ([test](tests/test_prowl_environment.mapping.l1.py))
- An absolute worktree, repository, or working-directory path maps through one source-owned resolver to the complete caller, complete pane inventory, non-caller path matches, and candidate-specific immediate-return send request templates; zero, one, and multiple matches produce unavailable, succeeded, and ambiguous results without sending, while a selected template produces exactly one checked send result with trailing-Enter evidence and no retry ([test](tests/test_prowl_target_resolution.mapping.l1.py))
- A delegation request with semantic completion text maps to one source-generated structured handback block and exactly one correlated `delegation-completed`, `delegation-failed`, `delegation-rejected`, or `delegation-unavailable` terminal handback containing a complete inline result or an exact durable result reference with a bounded inline projection ([test](tests/test_prowl_environment.mapping.l1.py))
- Every supported operation maps a checked public Prowl response or named command failure to one versioned JSON result that preserves Prowl identity, status, conclusion, exit-code, open resolution, tab-creation, and send-submission values verbatim ([test](tests/test_prowl_result.mapping.l1.py))

### Properties

- Default subprocess input maps an absent payload to null-device stdin, and every explicit text payload reaches captured input unchanged ([test](tests/test_prowl_subprocess_input.property.l1.py))
- Matching repeated terminal handbacks for one coordination reference preserve one terminal outcome, while conflicting terminal states for that reference are rejected ([test](tests/test_prowl_environment.property.l1.py))

### Compliance

- ALWAYS: focus, key injection, tab or pane creation, tab or pane closure, and open require explicit mutation authorization in the operation request before any Prowl command runs ([test](tests/test_prowl_environment.compliance.l1.py))
- ALWAYS: `list` represents instantiated terminal panes, while authorized `open` against an exact known worktree maps an unentered sidebar row to its first returned pane without filesystem worktree enumeration ([test](tests/test_prowl_environment.compliance.l1.py))
- NEVER: another shipped coding-agents script constructs a raw Prowl argument vector or invokes Prowl command help ([test](tests/test_prowl_environment.compliance.l1.py))
- NEVER: a delegation request submitted over stdin carries a field the envelope does not forward or executable handback data the adapter must own — an unsupported key is rejected rather than dropped, so a caller never sends a delegation missing or corrupting data it believed it supplied ([test](tests/test_prowl_environment.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct raw Prowl commands, invoke Prowl command help, or depend on an external environment-control skill ([audit])
- ALWAYS: the adapter's source-owned operation registry is the sole declaration of public Prowl command tokens; test evidence imports those values and exercises request-to-command composition without restating them ([audit])
- ALWAYS: the delegation surface closes the loop by push through a source-generated structured handback block — the recipient writes a durable result before sending one line to the pane the block addresses, because the sender cannot poll for completion ([audit])
- ALWAYS: the structured handback block carries the exact adapter command and the environment conditions that break delivery — an unresolvable adapter path and a socket owned by a different instance — so a recipient distinguishes them from an absent sender ([audit])
- ALWAYS: operator-target resolution reports a target named by absolute worktree, repository, or working-directory path in the same path terms the operator supplied while using the selected pane identity internally, never asking for a pane UUID or selecting by focus, position, or title ([audit])
