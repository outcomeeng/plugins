# Issues

## Eval run history is stale for the routing suite

The newest passing row for `evals/routing` (9/9, git SHA
`4a8fdd878001296cf9a11cc2fa2be1a3ad9997fb`) predates two deltas. The
`allowed-tools` frontmatter rewrite of `src/plugins/product-tree/skills/verify/SKILL.md`
and its Codex rendering in Change #76 rematerialized `prompt.md` and touched no
routing rule. The probe-route change of Change #868 then added the probe-bullet
reroute to the same skill, rematerialized `prompt.md` again, and added the
`reroutes-probe-misrouted-report` case to `cases.jsonl`. No committed run covers
the current materialized prompt or that case, and
`35-evidence.enabler/ISSUES.md` records the same unrun suite against `/probe`.

**Settlement condition**: one passing run of
`just eval spx/21-product-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/eval.toml`
on a head that carries the current producer, with its row committed to
`history.jsonl`.

**Evidence**: `product-tree:eval-evidence-auditor` finding `f-005` on head `a65659114b99767b90b4d920550fff5dc0824794`
during Change #76, whose prototype boundary runs no eval.
