# Issues: Merging Enabler

## `production-readiness` eval is threshold-fragile (FOLLOW-UP)

`spx/21-spec-tree.enabler/76-merging.enabler/evals/production-readiness/` has **4 cases at an 85% pass threshold**, so a single LLM-non-deterministic case flip drops the suite to 75% and fails the `evals` CI check. This blocked PR #143 once and recovered on the next re-roll; `history.jsonl` shows the same 0.75 dip on 2026-06-06 recovering minutes later. The fragility is intrinsic to a 4-case / 85% suite (one flip = a 25% swing).

**Resolution shape**: raise the case count so one flip is below the threshold's granularity, or lower the threshold to match the case count, or raise pass@k for the non-deterministic cases. Audit the other small merging evals (now under the transport children) for the same 4-case fragility while here.

Surfaced during the autonomous merge of PR #143 (2026-06-08).
