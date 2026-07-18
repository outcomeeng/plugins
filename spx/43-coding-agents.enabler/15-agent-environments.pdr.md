# Agent Environments

Agent-facing workflows consume coding environments through source-owned capabilities that publish their supported operations, preserve environment-owned identities verbatim, and return explicit unavailable results for unsupported operations or environments. Within a supported environment, any positively identified coding agent can delegate bounded work to any other positively identified coding agent and receive one correlated terminal handback without discovering environment command syntax.

## Rationale

Environment capabilities keep workflow semantics stable while local panes, native supervisors, and remote-managed tasks retain their own identities and lifecycle mechanisms. Requiring workflows to construct raw environment commands duplicates command knowledge and turns missing lifecycle support into polling or inference.

## Product properties

1. Each supported environment exposes a versioned operation surface and preserves every native participant, task, status, conclusion, and result identity unchanged.
2. A delegation request reaches exactly one completed, failed, rejected, or unavailable terminal handback carrying the complete initiating coordination reference.
3. Agent-facing workflows use the environment capability directly rather than invoking raw environment commands, command help, or an external environment-control skill.

## Verification

### Testing

- ALWAYS: supported and unsupported environment operations map to source-owned success or unavailable results without fallback inference ([mapping])
- ALWAYS: delegation requests and terminal handbacks preserve complete participant and coordination identities across every supported result form ([property])

### Audit

- NEVER: an environment-neutral product decision specifies a concrete environment command, command-line flag, implementation language, local pane mechanism, native supervisor API, or remote task API ([audit])
