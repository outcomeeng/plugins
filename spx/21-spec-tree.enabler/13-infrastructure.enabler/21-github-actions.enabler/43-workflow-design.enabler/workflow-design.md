# Workflow Design

PROVIDES the architectural vocabulary for authoring GitHub Actions workflows: triggers, jobs, matrices, reusable workflows, composite actions, repository scripts, caches, artifacts, environments, validation commands, and the boundary between workflow code and repository code
SO THAT workflow authoring, workflow review, and workflow rearchitecture surfaces
CAN apply consistent architectural choices grounded in the same vocabulary

## Assertions

### Compliance

- ALWAYS: place reusable behavior according to ownership and reuse boundary — repository scripts (under `scripts/` or equivalent) hold locally runnable logic, composite actions hold step bundles, reusable workflows (`workflow_call`) hold cross-repository job orchestration, workflow YAML holds event wiring — duplication is the slow path to drift ([audit])
- ALWAYS: invoke validation commands (linters, type checkers, tests) through a dedicated repository script rather than inline shell — local and CI runs share the same surface ([audit])
- ALWAYS: keep secret access, deployment environments, publication steps, and privileged tokens isolated from untrusted build or test jobs — privilege bleed between jobs is a real attack vector ([audit])
- ALWAYS: name caches with stable, deterministic keys derived from lockfiles and toolchain versions — cache-poisoning risk requires explicit cache-key boundaries ([audit])
- ALWAYS: declare runner requirements (`runs-on`, container, services) explicitly per job — implicit defaults rot when GitHub changes runner images ([audit])
- NEVER: write inline multi-step shell when a repository script or composite action would expose the same behavior to local runs — workflows that only run in CI hide bugs from developers ([audit])
- NEVER: hard-code secrets, tokens, or environment-specific paths in workflow files — secrets live in `secrets:` and environment-specific values in `environment:` ([audit])
