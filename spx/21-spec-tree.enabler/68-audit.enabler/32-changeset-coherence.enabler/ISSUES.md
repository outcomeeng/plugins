# Issues: Changeset Coherence

## Scope-resolver extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/audit-changeset-coherence/scripts/resolve_scope.py`
is the CLI entrypoint for the shared `resolve_committed_scope` provider in
`src/plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py`.
It emits base and head commit identity plus the changed-file set as one JSON
object so the audit resolves its own scope. The entrypoint and provider each
exceed fifty lines. Past fifty lines
`spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves
into the SPX CLI once the script proves its value; the resolver has proven its
value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: the resolver already routes its derivation through the
shared changeset primitives tracked in
`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/ISSUES.md`,
so it extracts with them — port both, publish, advance the floor, and reduce the
shipped skill to its instruction with no script. Preserve the caller-independent
scope resolution across the move: the audit names no caller and stays invocable
on its own. Revisit when the capability publishes.

## The coherence eval's committed run history predates its producer

`evals/coherence-verdict/history.jsonl` carries no run against the current
`src/plugins/spec-tree/skills/audit-changeset-coherence/SKILL.md`, whose
resolver relay and stale-base refusal changed the producer the eval scores. The
`[eval]` assertions the suite backs therefore rest on a history recorded for an
earlier producer.

**Evidence.** Pull request outcomeeng/plugins#580 merged as
`a24d145869614193a55ffae2c92f781a605802eb` with the eval run recorded as not
established in its test plan.

**Settlement condition**: one `just eval spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/eval.toml`
run against the released producer, its `history.jsonl` committed beside the
suite.
