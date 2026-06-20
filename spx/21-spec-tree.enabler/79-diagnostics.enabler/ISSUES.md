# Issues: Diagnostics Enabler

## Eval evidence deferred to a follow-up slice

The node's three behavior assertions in `diagnostics.md` carry `[eval]` links to evidence files that do not exist yet:

- `evals/session-environment-check/eval.toml`
- `evals/spx-reachability-check/eval.toml`
- `evals/diagnostic-report/eval.toml`

The node is listed in `spx/EXCLUDE` so validation and `spx spec status` skip it while the evidence is absent, leaving it in the `declared` state. Authoring the evidence is the next slice (PLAN.md step 3): each `[eval]` needs an `eval.toml`, `cases.jsonl`, and `prompt.md` run through the eval harness, plus a `test-evidence-auditor` pass — a distinct effort beyond this changeset's scope, which is to author, register, and ship the `diagnose` skill. Remove the node from `spx/EXCLUDE` once the evidence exists and the assertions are evidenced.
