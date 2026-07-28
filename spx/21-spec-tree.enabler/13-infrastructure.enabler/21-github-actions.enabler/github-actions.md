# GitHub Actions

PROVIDES GitHub Actions platform guidance, workflow safety policy, workflow design guidance, and Python-driven runtime observability
SO THAT spec-tree plugin users and marketplace maintainers
CAN choose, build, review, secure, maintain, and diagnose hosted automation through structured runtime guidance

## Assertions

### Compliance

- ALWAYS: route new automation requests through platform-boundary guidance before recommending GitHub Actions over local hooks, repository scripts, scheduled services, or another CI platform ([audit])
- ALWAYS: apply workflow safety policy before authoring, editing, rerunning, dispatching, canceling, or approving any workflow behavior ([audit])
- ALWAYS: source workflow state from Python orchestration of `gh` JSON output and GitHub API responses before summarizing runs, jobs, logs, checks, or workflow files ([audit])
- ALWAYS: separate workflow design, workflow review, runtime operation, and workflow evolution guidance so each surface consumes the lower-index infrastructure it needs ([audit])
- ALWAYS: keep authoring guidance explicit about triggers, permissions, secrets, cache boundaries, runner requirements, validation commands, reusable workflow boundaries, and repository script boundaries ([audit])
- ALWAYS: keep audit guidance explicit about least-privilege permissions, pinned third-party actions, untrusted pull request safety, secret exposure, cache poisoning risk, OIDC use, concurrency controls, and dependency freshness ([audit])
