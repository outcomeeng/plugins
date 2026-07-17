# Audit Verification

PROVIDES Outcome Engineering governance for agentic audit verification across artifact types
SO THAT methodology specs, plugin implementations, runtime tools, and language standards
CAN judge evidence and declarations through portable, artifact-specific audit methods

## Assertions

### Compliance

- ALWAYS: audit verification uses the agentic verdict mode and correctness or conformance purpose declared by `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`, with each verdict produced in a verifier context isolated from the author context ([audit])
- ALWAYS: artifact-type audit methodology owns the portable judgment model for its subject, while delivery plugins and runtime integrations implement that model without redefining it ([audit])
- ALWAYS: an artifact audit inspects the complete evidence or declaration chain relevant to its subject and identifies the exact artifact and property affected by each finding ([audit])
- NEVER: portable artifact-audit methodology depends on one delivery plugin, wrapper-agent roster, journal backend, persistence path, or rendered result surface ([audit])
