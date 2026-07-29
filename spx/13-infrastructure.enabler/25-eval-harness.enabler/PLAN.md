# Eval Harness: Plan — relocation and prompt-caching background

## Relocation

The eval-harness redesign re-homes this concern: eval-verification governance
moves to `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/`
(harness vocabulary under its `21-eval-harness.enabler` child), and the runtime
adapter contract the redesigned harness delegates to lives under
`spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/`.
New eval-harness decisions and specs land there; this node's specs, decisions,
and evidence stay authoritative for the shipped harness until the
implementation cutover named in the new subtree's `PLAN.md` files, after which
this node retires.

Eval coupling for the methodology is decided by
`spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md`,
which reaches the installed plugin through the adapter contract instead of
materializing producer text into a prompt.
`spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`
is scoped to the `outcomeeng_evals` harness alone, so the two decisions govern
disjoint subjects while the shipped harness stands. At cutover this node's
producer-coupling assertions — the `prompt_source` kind conformance rules, the
`materialize-prompts` CLI rule, and the producer-derived materialization
property — retire with the `outcomeeng_evals/producer_prompt.py` machinery and
the generated `prompt.md` files they govern, replaced by the adapter-invoked
case shape the new decision declares. The prompt-caching plan below predates the redesign: its
gate condition is stale (`anthropics/claude-code#34629` closed without
resolution and the regression persists), and the caching decision re-derives at
the new location rather than being implemented here.

`.github/workflows/spec-tree-evals.yml` is authored and lint-clean. It
collects changed paths, then delegates planning and execution to
`outcomeeng-evals ci`: PRs use changed paths plus `owned_paths` and
`smoke_cases` from each `eval.toml`, while `push` to main, the weekly
schedule, and manual dispatch run the full non-manual suite set under the
configured root. Each selected suite runs through Python-owned
`outcomeeng-evals run` command construction, using the suite's declared
`plugin_dir` or the workflow fallback, and the job gates on the aggregate
exit code. On main the appended `history.jsonl` rows are committed back via
the `OUTCOMEENG_EVAL_STORE` PAT.

The root merge-gate policy probes moved out of LLM evals and into
deterministic mapping tests at
`spx/21-spec-tree.enabler/76-merge.enabler/tests/test_merge_gate_policy.mapping.l1.py`.
The CI eval workflow now covers the authored PR management,
PR opening, review-changes, and TypeScript test-ownership evals directly.

The `OUTCOMEENG_EVAL_STORE` org secret is visible to `outcomeeng/plugins`, and
the token account can bypass `main` branch protection for commit-back pushes.

Deferred follow-ups tracked in `ISSUES.md` include cross-suite parallelism.

## Prompt-caching background (re-derived at the relocated subtree)

The prompt-caching decision is reconciled.
`spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`
keeps prefix reuse as the cost lever and records the corrected mechanism:
**capture the amortization on the subscription `claude --print` path via a base
session loaded with every plugin once and forked per case**, so each case reads
the shared prefix warm and writes only its case-specific suffix, keeping the
`NEVER`-route-to-a-metered-API stance. The supporting investigation is recorded
in `prototypes/eval-cache-amortization/investigation.md` (outside `spx/`;
conclusion corrected from the earlier single-turn-only reading); the empirical
fixed-prefix payoff is `prototypes/eval-cache-amortization/FINDINGS.md` (5.45× per
call, ~73–80% per suite).

The fork-session cache regression persists: since v2.1.69
(`anthropics/claude-code#34629`, closed without resolution; current CLI
releases remain affected), `claude --print --resume`/`--fork-session` stops
reusing the cached conversation history, so a forked case cold-writes the
prefix exactly as the current single-turn shape does. The harness keeps its
current single-turn invocation while the regression persists. The telemetry
that makes a run's caching observable already ships (the per-run cache read
and creation token aggregates in `cost_summary` and `history.jsonl`).

No fork-per-case implementation happens in this node. Per the Relocation
section above, the caching decision re-derives under
`spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/`,
where its `PLAN.md` records the realization paths (community interceptor,
partial amortization, single-turn) as an operator decision. The
`prototypes/eval-cache-amortization/` prototype stays in place as the durable
measurement record (`FINDINGS.md`, `investigation.md`) until the relocated
subtree absorbs or retires it per the prove-then-migrate-or-remove lifecycle
in `spx/12-shipped-scripting.adr.md`.

## References

- **Workflow**: `.github/workflows/spec-tree-evals.yml`
- **Runner contract**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md:18`
- **Gate-policy tests**: `spx/21-spec-tree.enabler/76-merge.enabler/tests/test_merge_gate_policy.mapping.l1.py`
- **PR-authority PDR**: `spx/15-merging.pdr.md`
- **Launch-in-CI + configurable-surface reference**: `outcomeeng/gh-actions` `spec-tree-review.yml`
- **Prompt-caching decision**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`
- **Cache investigation + measurement**: `prototypes/eval-cache-amortization/investigation.md`, `prototypes/eval-cache-amortization/FINDINGS.md`
- **CLI cache regression**: `anthropics/claude-code#34629`
