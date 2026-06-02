# Verification

PROVIDES the architecture shared by the agentic verification types — reviewing and auditing — under which their skills and thin wrapper agents produce changeset-scoped results
SO THAT authors of agentic verification skills and the wrapper agents that drive them
CAN compose against one persistence model, one validation discipline, and one wrapper-agent shape

## Verification types

The five verification types and the two axes that classify them — verdict mode and purpose — are declared in the `/understanding` foundation reference `src/plugins/spec-tree/skills/understanding/references/verification-kinds.md` and grounded for this product in `spx/14-verification.pdr.md`. This enabler is the home of the agentic types' shared architecture, decided in `spx/21-spec-tree.enabler/16-verification.enabler/13-architecture.adr.md`; reviewing and auditing implement it.

## Assertions

### Compliance

- ALWAYS: every agentic verification skill and its wrapper agent conform to the architecture in `spx/21-spec-tree.enabler/16-verification.enabler/13-architecture.adr.md` — thread-store persistence, an arbiter-validated result paired with a markdown surface, and a thin wrapper agent declaring a model identifier, `tools: Bash, Read, Skill`, and `skills:` listing the skill ([audit])
- NEVER: an agentic verification skill embeds a backend-specific path, hand-validates its own emitted JSON, or pins a runtime model name the distribution pipeline cannot substitute ([audit])
