# Issues: PR Opening Protocol

## Review-readiness eval retired pending producer-backed evidence

The retired `evals/review-readiness/` suite modeled the `/open-pr`
`VERIFICATION_READINESS` decision by prompting a model to classify provided JSON
state. That shape does not run the producing `/open-pr` skill, does not exercise
the branch push or ready pull-request creation path, and does not prove the
assertion's real producer behavior. The governing assertion now uses `[audit]`
evidence until a replacement eval can drive the actual producer surface and score
its structured output.

Revisit condition:

- Add a producer-backed eval that invokes the real `/open-pr` decision path, or a
  harnessed producer artifact with the same parseable decision contract.
- Include cases for deterministic verification failure, required
  evidence-auditor predicate failure, local review not converged, and all
  predicates holding.
- Run the canonical eval command and commit `history.jsonl`.
