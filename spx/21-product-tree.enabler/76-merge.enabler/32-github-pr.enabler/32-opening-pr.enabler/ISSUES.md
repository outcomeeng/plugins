# Issues: PR Opening Protocol

## The prescribed body-on-stdin form is unreachable for any body containing code spans

`/open-pr` Step 5 prescribes piping the pull-request body to `gh pr create --body-file -` through a quoted heredoc, and forbids temporary files: "Never use temporary files, helper files, command substitution, or post-hoc text substitution to assemble or repair the body." The dangerous-command guard blocks that command whenever the body contains Markdown code spans, because static analysis reads each backtick pair as POSIX command substitution assembling a shell launcher. A body naming a command inside a code span — a validation command in a test plan, a config key, a file path — triggers it; the guard reports the same reason after every substitution is removed from the command itself, because the backticks are in the heredoc content.

The two instructions therefore admit no compliant form for a body that uses code spans, which every non-trivial body does. The `printf` variant the same step offers fails identically: its single-quoted arguments still carry the backticks.

**Resolution shape**: reconcile the prohibition with the guard in the skill itself — either permit a body written to a path outside the repository and passed as `--body-file <path>` (no shell parsing of the content, which is what makes it safe), or prescribe an invocation whose body never reaches a statically analyzed command string. Until one lands, a body with code spans is written to a scratch path and passed by path; that departs from the written prohibition and needs recording each time rather than silently.

**Evidence**: `gh pr create` for pull request 498 was blocked twice by `dcg` rule `core.filesystem` / embedded-shell-launcher detection, first with a `$(git branch --show-current)` argument and again after replacing it with a literal branch name, leaving the heredoc body as the only remaining trigger.

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
