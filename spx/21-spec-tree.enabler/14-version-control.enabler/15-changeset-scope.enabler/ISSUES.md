# Issues: Changeset Scope

## Changeset-primitive extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/changeset-scope-standards/scripts/changeset_scope.py` runs
to 344 lines — branch identity, the on-disk addressing slug, base-ref
resolution, the remote-tracking ref form, and merge-base diff scope. Past fifty
lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic
moves into the SPX CLI once the script proves its value; these primitives have
proven their value in use, so extraction is what they owe.

This module is the single home the audit, review-changes, sync-base, merge, and
coherence-audit skills all import rather than re-deriving, so its extraction
also removes the shipped-script debt those consumers inherit through it.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port the derivation primitives into the SPX CLI as a
consumable command surface, publish it, advance the floor, and repoint every
consuming skill at the published capability. Keep the one-derivation invariant
across the move — no consumer re-implements base-ref resolution or diff scope.
Revisit when the capability publishes.
