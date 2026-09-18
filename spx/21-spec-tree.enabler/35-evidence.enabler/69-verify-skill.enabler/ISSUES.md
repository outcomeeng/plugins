# Issues

## Eval run history is stale for the routing suite

The newest passing row for `evals/routing` (9/9, git SHA
`4a8fdd878001296cf9a11cc2fa2be1a3ad9997fb`) predates the `allowed-tools`
frontmatter rewrite of `src/plugins/spec-tree/skills/verify/SKILL.md` and its
Codex rendering in Change #76, which rematerialized `prompt.md`. The delta is
frontmatter only and touches no routing rule; no committed run covers the current
materialized prompt.

**Settlement condition**: one passing run of
`just eval spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/eval.toml`
on a head that carries the current producer, with its row committed to
`history.jsonl`.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-005` on head `a65659114b99767b90b4d920550fff5dc0824794`
during Change #76, whose prototype boundary runs no eval.
