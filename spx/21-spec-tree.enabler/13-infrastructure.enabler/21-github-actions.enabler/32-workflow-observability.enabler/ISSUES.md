# Issues: Workflow Observability

## Three shipped inspection scripts await extraction into the SPX CLI

The `inspect-github-actions` skill ships three scripts past the fifty-line
threshold:

- `src/plugins/spec-tree/skills/inspect-github-actions/scripts/workflow_inspect.py`
  (296 lines) — run listing, single-run and job inspection, failed-log
  retrieval with byte bounds, PR check rollup, and artifact inspection.
- `src/plugins/spec-tree/skills/inspect-github-actions/scripts/gh_access.py`
  (214 lines) — repository identity, host, and `gh` authentication detection,
  including GitHub Enterprise host parsing. Also consumed by
  `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/54-runtime-operations.enabler`.
- `src/plugins/spec-tree/skills/inspect-github-actions/scripts/mutation_gate.py`
  (191 lines) — the state-changing-command gate that holds GitHub mutations
  behind explicit user instruction in the same turn.

Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt
whose logic moves into the SPX CLI once the script proves its value; all three
have proven their value in use, so extraction is what they owe.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port workflow inspection, access detection, and the
mutation gate into the SPX CLI, publish it, advance the floor, and reduce the
shipped skill to its instruction with no scripts. The mutation gate carries the
product-level compliance rule that state-changing operations occur only with an
explicit user instruction in the same turn, so its port preserves that boundary
rather than relaxing it. Revisit when the capability publishes.

## `inspect-github-actions` reads the newest runs at a bound the page-bound property reads as a completeness bound

`src/plugins/spec-tree/skills/inspect-github-actions/SKILL.md` lines 66 and 70 list workflow runs with `gh run list --commit "$HEAD_SHA" --limit 5` and `gh run list --branch "$BRANCH" --limit 5`. Each is a most-recent-N read, for which a full result of five is the expected answer. Product property 3 of `spx/15-agent-tools.pdr.md` requires a `gh` list call whose result fills its bound to return a blocked result, and draws no line between a read that needs the whole collection and a read that takes the newest N, so a commit or branch with five or more runs reads as blocked.

`spec-tree:changes-reviewer` run `2026-10-06_18-56-26-316-837e0b2a122f` on head `27de076ed368f5eee6477012d9526a89a8af2b77` raised this as a `consistency` finding against the decision at line 15.

**Settlement condition.** The decision states that a read ordered by recency which takes the newest N is outside the blocked-result clause, or the skill returns a blocked result at its bound; the decision and the skill then agree under one PDR audit and one typed skill audit of `inspect-github-actions`.
