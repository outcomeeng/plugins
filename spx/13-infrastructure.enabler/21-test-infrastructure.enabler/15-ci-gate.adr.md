# CI Enforcement of the Quality Gate

CONSTRAINS the marketplace's quality gate
TO one GitHub Actions job that runs the `just check-full` recipe with the gate's full toolchain on `pull_request` and on push to `main`
SO THAT every change that reaches `main` passes the deterministic full gate

## Verification

### Test.Compliance: gate workflow

- gate-triggers: ALWAYS: the workflow triggers on `pull_request` and on push to `main` — every path to `main` passes through the gate
- full-gate-recipe: ALWAYS: the workflow runs the gate by invoking the `just check-full` recipe as a job step, never an inlined, re-enumerated, or filtered subset of the step list beyond the skip of the L3 tests [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md) declares — divergence from the full gate step list reintroduces the unseen-failure gap
- project-python: ALWAYS: the workflow provisions Python at the version `pyproject.toml`'s `requires-python` declares — CI uses the project's interpreter contract
- gate-toolchain: ALWAYS: the gate job provisions the gate's full toolchain: just, uv, the Python version `pyproject.toml`'s `requires-python` declares, actionlint, ShellCheck, dprint, git, the Claude Code CLI, the Codex CLI, and the `spx` CLI built from its pinned commit
- gate-least-privilege: ALWAYS: the workflow token holds only `contents: read`, and the gate step receives no credential, because no test outside the L3 tests uses one
- no-soft-passed-step: NEVER: a gate step is marked `continue-on-error`, gated out by a step-level `if:`, or soft-passed by its `run:` shell — a non-blocking gate is not a gate
- no-soft-passed-job: NEVER: the `check` job is gated out by a job-level `if:` or soft-passed by a truthy job-level `continue-on-error` — a job-level condition could skip the entire gate on `pull_request` or let a failed job report success, defeating the gate as surely as a soft-passed step
- job-timeout: ALWAYS: every job this repository defines with `runs-on` declares an explicit `timeout-minutes` at or below the declared maximum — an unbounded job never reports a conclusion, so it blocks no merge while holding a runner for the platform default
- no-timeout-on-uses: NEVER: a job that calls a reusable workflow through `uses` declares `timeout-minutes` — the platform rejects the key on such a job, so the bound for a called workflow's jobs is passed as an input rather than declared here

### Test.Compliance: spx pin

- spx-version-floor: ALWAYS: a gate step fails when the version the `spx` CLI the gate runs reports is below the declared minimum spx version, so a floor above what the pinned build reports fails the gate rather than shipping
- floor-source: ALWAYS: the declared minimum spx version is the one floor the version step reads, and the step reads the reported version from the `spx` CLI on the gate's `PATH`, the build the workflow provisions and the gate's other steps run
- one-spx-pin: ALWAYS: the `outcomeeng/spx` checkout the gate builds at the commit `SPX_COMMIT` pins in `.github/workflows/check.yml` is this Product's one pin on `outcomeeng/spx` and the one source of the shared orchestration fixture corpus `testing/fixtures/orchestration/`: the tests of the orchestration-configuration node read the corpus from that checkout at that commit through the test infrastructure under `outcomeeng_testing/`, whose harness resolves the corpus directory from the path the workflow's `outcomeeng/spx` checkout step declares, no second pin names an `outcomeeng/spx` revision, no fixture is copied into this repository, and a run that cannot find the corpus fails naming the missing path and never passes or skips
- pinned-build-only: NEVER: the workflow installs the `spx` CLI from the npm registry or from a moving ref; it builds the pinned commit
- spx-build: ALWAYS: the workflow checks out `outcomeeng/spx` at the commit `SPX_COMMIT` pins, installs its dependencies from its lockfile, runs its `build` script, and puts its `bin/spx.js` entry on `PATH` as `spx`, and it declares no `SPX_VERSION` variable
- spx-commit-form: ALWAYS: `SPX_COMMIT` is a full 40-character commit SHA of the `outcomeeng/spx` `main` branch whose build reports a version at or above the declared floor, and the pin carries no registry-update annotation

### Audit: pins and releases

- codex-pin: ALWAYS: in every changeset that changes the CI workflow file, the codex-cli version the workflow pins equals the codex-cli version the maintainers' development host runs, and the pin carries no registry-update annotation
- floor-rise: ALWAYS: the declared minimum spx version rises only in a changeset whose shipped skills or tests come to depend on an spx capability the previous floor lacks
- spx-capability-pin: ALWAYS: a changeset whose shipped skills or tests depend on an spx capability the pinned build lacks advances `SPX_COMMIT` to a commit that contains that capability
- no-release-wait: NEVER: a gate step, workflow, repository rule, or shipped skill waits for an `@outcomeeng/spx` release on the npm registry or names one as a precondition, and the floor names no release channel; a consumer repository meets the floor with any spx build that reports the floor version, from npm or from source

### Audit: branch protection

- required-check: ALWAYS: the branch protection of `main` names the gate `check` job as a required status check, so a red gate blocks the merge
