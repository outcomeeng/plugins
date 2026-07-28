# Aligning

PROVIDES systematic consistency checking across the spec tree — structural conformance, atemporal voice, and content placement
SO THAT all spec authors
CAN detect contradictions, gaps, and content misplacement before they reach implementation

## Assertions

### Compliance

- ALWAYS: report a spec's contradiction with an ancestor ADR compliance rule and cite the conflicting ADR ([audit])
- ALWAYS: flag implementation details in a spec as content misplaced from an ADR ([audit])
- ALWAYS: identify temporal language in a spec and provide atemporal rewrites for the temporal markers ([audit])
- ALWAYS: check specs against all ancestor ADRs/PDRs — decision records win by hierarchy ([audit])
- ALWAYS: when checking a changeset, report a product spec, ADR, PDR, or ancestor spec change that lacks both aligned first affected lower specs and first-affected-node `PLAN.md` grounding, deriving the changed-file set through `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` rather than ad hoc git diff logic ([audit])
- NEVER: weaken a spec to match code or tests — the declaration governs ([audit])
