# Issues: Journal Projection

## Two shipped projection scripts await extraction into the SPX CLI

The `project-run-journal` skill ships two scripts past the fifty-line threshold:

- `src/plugins/spec-tree/skills/project-run-journal/scripts/journal_projection.py`
  (496 lines) — channel event construction from a run's results, the rollup
  computation over an event prefix, and the human-readable surface rendered from
  that prefix, all pure and backend-free.
- `src/plugins/spec-tree/skills/project-run-journal/scripts/render_review_run.py`
  (346 lines) — the compact inspection surface for a sealed review journal run.

Past fifty lines [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) makes a shipped script debt
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

## The command-form assertion omits the payload-path rule its skill states

The command-form assertion in
`spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/journal-projection.md`
states one command form per journal verb and an `append` that reads its event
through the input redirect from a file written with the file-write tool in the
session scratch directory. The `project-run-journal` skill's `<command_forms>`
also copies the scratch directory into each event path, stops before an
`append` whose file-write result reports a path outside that directory, passes
the reported path unchanged, and reruns an `append` once when its diagnostic
names the event file as absent. The assertion states none of those four rules.
The audit, audit-assertions, skills, subagents and prose nodes each carry them
in an assertion.

**Evidence**: CI review finding at
`spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/journal-projection.md:31`
on pull request 675, head `ea7372f9e907617492fa654a2c4ee994d8212796`. Returned
`filed` under properties 11 and 13 of
[`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md):
that changeset leaves the assertion unchanged, and the assertion still holds of
the skill, so the change does not invalidate it.

**Impact**: an assertion audit of this node cannot reject a skill that drops
the four rules.

**Settlement condition**: an assertion of this node states the four rules for
the run-journal command forms, and an assertion audit of the node raises no
finding on it.
