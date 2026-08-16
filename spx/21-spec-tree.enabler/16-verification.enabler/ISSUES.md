# Issues: Verification Enabler

## Review still uses the legacy journal surface

Audit implementation moves to `spx verification run` in the active slice. Review still has source and tests that refer to `spx journal --type review`, including the review-run inspection helper and verification-run-journal-standards skill.

Required handling:

- Specify the review verification-run contract before replacing review journal helpers.
- Preserve the current `changes-reviewer` raw-token integration until the review verification-run replacement exists.

## Downstream enforcement for `[audit]` decision-rule modes

`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` carries `[audit]` rules under `## Verification` / `### Audit`. Establish how `[audit]` decision-rule modes are enforced downstream: either author node-spec `[audit]` assertions an audit skill checks against each rule, or refine `spx/21-spec-tree.enabler/32-decisions.enabler/decisions.md` so it recognizes audit/eval enforcement for `[audit]`/`[eval]` modes.

## Missing `[eval]` evidence on verification skill judgment surfaces

Verification skills that produce LLM-driven judgment need `[eval]` evidence where they emit structurally validatable verdicts. Apply the eval evidence pattern used by existing review-change evals to remaining verification skills as each surface is migrated.
