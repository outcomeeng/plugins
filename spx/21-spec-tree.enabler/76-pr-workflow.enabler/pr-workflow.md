# PR Workflow

PROVIDES pull-request lifecycle skills (opening, managing, merging, reviewing) implementing the PR authority gate from `spx/15-agent-pr-authority.pdr.md`
SO THAT every product that installs the spec-tree plugin
CAN drive a pull request from creation to merge under one observable authority model with overlay-declared stricter gating per project

## Assertions

### Scenarios

- Given a PR whose closure gate has passed, all required checks are terminal-green, a current-head three-severity review on at least one inspected surface has no unresolved `BLOCKING` or `DEBT`, the latest push is at least five minutes prior to evaluation, branch hygiene including upstream-safety holds, and no project-declared production-class markers apply, when the PR-management skill evaluates the PR authority gate, then the gate authorizes both draft → ready promotion and merge from one verdict ([eval](evals/authority-gate-green/eval.toml))
- Given a PR with project-declared production-class markers applied, when the PR-management skill evaluates the PR authority gate, then the gate withholds autonomous authority and the skill emits an explicit-instruction action token for promotion and for merge regardless of the other predicates ([eval](evals/authority-gate-production/eval.toml))
- Given a project overlay declaring promotion authority as human-instruction, when the gate is otherwise green, then the PR-management skill defers promotion to explicit instruction and continues to evaluate merge under the overlay's merge-authority declaration ([eval](evals/overlay-human-promotion/eval.toml))
- Given a project overlay declaring merge authority as human-instruction, when the gate is otherwise green and the PR is ready, then the PR-management skill performs autonomous promotion and defers merge to explicit instruction ([eval](evals/overlay-human-merge/eval.toml))
- Given a PR whose branch hygiene fails (working tree dirty, upstream tracking the default branch, behind the resolved base, or topology unclassified), when the PR-management skill evaluates the gate, then the gate withholds autonomous authority for both actions regardless of the other predicates ([eval](evals/authority-gate-hygiene/eval.toml))
- Given a `review-result.json` produced by the changes-reviewer agent (or `/review-changes` slash command) on the working diff, when `/opening-pr`'s local review gate evaluates the `findings` array, then the gate stops the push if any entry has `severity == "blocking"` or `severity == "debt"` and authorizes the push otherwise — the `decision` field is informational because it is bound to `blocking` presence alone, so a `debt`-only review carries `decision == "approve"` ([eval](evals/local-review-gate/eval.toml))
- Given the gate-green-autonomous merge predicates are satisfied, when the PR-management skill selects the merge command, then it follows the overlay's declared merge command if any; when the overlay is silent on the merge command, it runs rebase merge (`gh pr merge --rebase`) as the universal default — the agent never selects a merge commit or squash command from the gate alone ([eval](evals/merge-command-overlay-precedence/eval.toml))

### Compliance

- ALWAYS: every PR authority gate evaluation completes in one inspection pass — separate inspections for promotion versus merge allow the predicates to drift between them, per `spx/15-agent-pr-authority.pdr.md` ([review])
- ALWAYS: each gate-evaluation outcome maps to exactly one named action token emitted by the PR-management skill workflow — vague handoff prose hides the verdict from the calling workflow ([review])
- NEVER: maintain divergent authority models for promotion versus merge that produce different verdicts from the same gate state — the gate's purpose is to unify them, per `spx/15-agent-pr-authority.pdr.md` ([review])
- NEVER: treat an agent-inferred "the work looks done" as the gate — the gate's predicates are observable PR state, not LLM judgment, per `spx/15-agent-pr-authority.pdr.md` ([review])
