# Workflow Safety

PROVIDES the security and mutation policy for any workflow running on GitHub Actions: permissions, event trust, OIDC, secrets, third-party action pinning, cache boundaries, runner trust, concurrency controls, and run-control gates
SO THAT workflow design, workflow review, runtime operations, and workflow evolution surfaces
CAN apply a single consistent safety baseline rather than per-workflow ad hoc choices

## Assertions

### Compliance

- ALWAYS: treat fork pull requests, `pull_request_target` events, user-controlled workflow inputs, checked-out code, caches, artifacts, and matrix values as untrusted until the workflow proves the trust boundary — trust is established explicitly, never assumed ([audit])
- ALWAYS: apply least-privilege `permissions` blocks at workflow and job level — `permissions: write-all` and unscoped defaults are forbidden ([audit])
- ALWAYS: pin third-party actions by commit SHA in `uses:` references — version tags are mutable and supply-chain attacks publish under existing tags; `outcomeeng/gh-actions` beta-test callers may track `@main` only when the caller is under the same trust boundary, carries an explicit `# BETA TESTER:` marker naming the risk, and any static-analysis exclusion or Renovate update exemption for the beta caller workflow is scoped to that marked caller workflow ([test](tests/test_workflow_safety.compliance.l1.py))
- ALWAYS: use OIDC for cloud authentication where the target cloud supports it — long-lived cloud credentials in repository secrets are forbidden where OIDC is available ([audit])
- ALWAYS: set `concurrency` groups for long-running or expensive workflows to bound parallelism — uncontrolled concurrent runs cost minutes and produce racing artifacts ([audit])
- NEVER: run untrusted pull-request payload from forks with privileged context — `pull_request_target` requires explicit gating before checkout of fork code ([audit])
- NEVER: cache build outputs across mutually distrusting branches without a branch-scoped cache key — cache poisoning across branches is a real attack ([audit])
- NEVER: keep generic Claude caller workflows (`claude.yml`, `claude-code-review.yml`) active in this repository's `.github/workflows/` directory alongside the spec-tree callers — duplicate agent workflows spend tokens for the same issue and pull-request events ([test](tests/test_workflow_safety.compliance.l1.py))
