# Version Control

PROVIDES the git version-control primitives — changeset derivation (branch identity, addressing slug, base-ref resolution, merge-base diff scope) and automatic base synchronization (rebasing a branch behind its fetched base back onto that base)
SO THAT context loading, the agentic verification surfaces, and the merge lifecycle
CAN derive and act on a changeset's base from one shared source — reading product truth, scoping verification, and integrating work each against a current base — rather than re-deriving git base operations per consumer or surfacing base synchronization as an operator decision

## Assertions

### Compliance

- ALWAYS: every version-control operation resolves the base ref and its remote-tracking ref `origin/<base>` through the single changeset-scope module; no sibling re-implements base-ref, remote-tracking-ref, or branch derivation ([audit])
