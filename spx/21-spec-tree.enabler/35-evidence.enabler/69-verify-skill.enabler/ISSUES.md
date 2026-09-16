# Issues

## Routing eval run history is stale

The newest passing row for `evals/routing` (9/9, git SHA
`4a8fdd878001296cf9a11cc2fa2be1a3ad9997fb`) predates later changes to the
producer, cases, assertions, and materialized prompt. It supplies no passing
execution claim for the current routing behavior.

The isolated eval-evidence audit reported `FAIL` on 2026-09-15, finding `f-001`
in the history file during Change #14. A later audit reported `f-005` on head
`a65659114b99767b90b4d920550fff5dc0824794` during Change #76 after its
frontmatter rewrite rematerialized the prompt. The operator instructed that
local eval execution remain skipped while normal CI is allowed; no current
passing run is claimed.

**Settlement condition**: one passing run of
`just eval spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/eval.toml`
on a head that carries the current producer, with its row committed to
`history.jsonl`, followed by an independent eval-evidence audit accepting that
evidence.
