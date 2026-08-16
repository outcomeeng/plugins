# Issues: Journal Projection

## Two shipped projection scripts await extraction into the SPX CLI

The `verification-run-journal-standards` skill ships two scripts past the fifty-line threshold:

- `src/plugins/spec-tree/skills/verification-run-journal-standards/scripts/journal_projection.py`
  (496 lines) — channel event construction from a run's results, the rollup
  computation over an event prefix, and the human-readable surface rendered from
  that prefix, all pure and backend-free.
- `src/plugins/spec-tree/skills/verification-run-journal-standards/scripts/render_review_run.py`
  (346 lines) — the compact inspection surface for a sealed review journal run.

Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt
whose logic moves into the SPX CLI once the script proves its value; both have
proven their value in use across the audit and review surfaces, so extraction is
what they owe.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository. Projection is already
the SPX side of this boundary — the journal channel these scripts drive is the
CLI's — so the port consolidates a projection that is split across two products
today.

**Resolution shape**: port rollup computation and both rendering surfaces into
the SPX CLI beside the journal channel they read, publish it, advance the floor,
and reduce the shipped skill to its instruction with no scripts. The unsealed-
prefix and unique-coverage projection gaps recorded in
`spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md`
entries 5 and 6 are fixed in the ported surface rather than in the shipped
scripts. Revisit when the capability publishes.
