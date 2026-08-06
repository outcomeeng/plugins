# PR Opening Protocol

PROVIDES the pull-request opening protocol — `VERIFICATION_READINESS` evaluation, branch push with an explicit destination ref, ready pull-request creation, and the first management pass
SO THAT the GitHub-PR transport's `/manage-github-pr` orchestration
CAN publish a changeset as a ready-for-review pull request the moment `VERIFICATION_READINESS` holds, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given the selected transport's verification predicates hold — deterministic verification passes, required evidence-auditor predicates pass, and the local `changes-reviewer` review has converged when local review is declared — when `/open-pr` evaluates `VERIFICATION_READINESS`, then it creates the pull request `ready_for_review`, never as a draft gating step ([audit])

### Compliance

- ALWAYS: `/open-pr` resolves the pull-request target repository, the push target repository, and the operator's access class on the target before the opening push, reports the three resolved values, and stops when the access class is not `ADMIN`, `MAINTAIN`, or `WRITE`, or when the two repositories differ because the checkout is a fork whose base resolved to the upstream ([audit])
- NEVER: `/open-pr` establishes the access class from a remote URL, an authenticated account name, or a successful push — one account holds different permissions across repositories, so only the target's own viewer permission decides ([audit])
- ALWAYS: `/open-pr` re-establishes the selected transport's `VERIFICATION_READINESS` predicates — deterministic verification and any declared local agentic verification — on the diff the opening push publishes, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: `/open-pr` presents `gh pr create --body-file -` payload input by supported harness environment — quoted heredoc for interactive Claude Code and Codex sessions, and one physical `printf '%s\n' ... | gh pr create ... --body-file -` line for programmatic runners that require single-line commands — per `spx/15-agent-tools.pdr.md` ([audit])
- NEVER: open the pull request as a draft as a gating mechanism, or add a separate gated draft-to-ready promotion — the pull request opens ready once `VERIFICATION_READINESS` holds, per `spx/15-merging.pdr.md` ([audit])
