# Issues

## Eval run history is stale for the coordination-decision suite

The newest passing row for `evals/coordination-decision` (16/16, git SHA
`d15d5b8a77c97b1cc1660dec6a4652e0c15af71b`, 2026-08-28) is an ancestor of the
current head, but the declared producers changed since: `message-agents/SKILL.md`
step 5 now requires a matching `/operate-prowl plan-handback` result before a
production request, `operate-prowl/scripts/prowl_environment.py` now requires the
handback `adapterPath` to equal the source-owned adapter path, and
`coordinate-agents/SKILL.md` frontmatter changed in Change #76, which
rematerialized `prompt.md`. No run is recorded after those changes.

**Settlement condition**: one passing run of
`just eval spx/43-coding-agents.enabler/32-inter-worktree-coordination.enabler/evals/coordination-decision/eval.toml`
on a head that carries the current producers, with its row committed to
`history.jsonl`.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-004` on head `a65659114b99767b90b4d920550fff5dc0824794`
during Change #76, whose prototype boundary runs no eval.
