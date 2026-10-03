---
id: 01a0ebba-5f69-7623-91a6-11e684c72c78
malleability: spec
---

# PR Opening Protocol

PROVIDES the pull-request opening protocol — `VERIFICATION_READINESS` evaluation, branch push with an explicit destination ref, draft pull-request creation at the first push, promotion to ready once `VERIFICATION_READINESS` holds, and the first management pass
SO THAT the GitHub-PR transport's `/manage-github-pr` orchestration
CAN publish a changeset as a ready-for-review pull request the moment `VERIFICATION_READINESS` holds, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given CI's deterministic checks pass on the pushed head of the draft pull request, required evidence-auditor predicates pass, and the local `changes-reviewer` review has converged when local review is declared, when `/open-pr` evaluates `VERIFICATION_READINESS`, then it marks the pull request ready for review ([audit])

### Compliance

- ALWAYS: `/open-pr` resolves the pull-request target repository, the push target repository, and the operator's access class on the target before the opening push, reports the three resolved values, and stops when the access class is not `ADMIN`, `MAINTAIN`, or `WRITE`, or when the two repositories differ because the checkout is a fork whose base resolved to the upstream ([audit])
- NEVER: `/open-pr` derives the pull-request target from the checkout's own repository identity — a fork reports itself there while the pull request opens against its parent, so the comparison guarding the fork case would compare one repository with itself and pass for every checkout ([audit])
- NEVER: `/open-pr` establishes the access class from a remote URL, an authenticated account name, or a successful push — one account holds different permissions across repositories, so only the target's own viewer permission decides ([audit])
- ALWAYS: `/open-pr` pushes the branch and opens the pull request as a draft, so CI's deterministic checks run on the pushed head, and establishes `VERIFICATION_READINESS` on that head — CI's deterministic checks pass, then the declared local agentic verification converges — before it marks the pull request ready, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: `/open-pr` presents `gh pr create --body-file -` payload input by supported harness environment — quoted heredoc for interactive Claude Code and Codex sessions, and one physical `printf '%s\n' ... | gh pr create ... --body-file -` line for programmatic runners that require single-line commands — per `spx/15-agent-tools.pdr.md` ([audit])
- NEVER: `/open-pr` marks the pull request ready before `VERIFICATION_READINESS` holds on its current head, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: each Verifier dispatch `/open-pr` makes before it marks the pull request ready — every applicable evidence Auditor and the local `changes-reviewer` — is preceded by the readiness record bound to the exact pushed head whose CI deterministic checks pass, per `spx/15-merging.pdr.md` ([audit])
