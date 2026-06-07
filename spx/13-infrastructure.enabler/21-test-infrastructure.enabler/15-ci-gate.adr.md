# CI Enforcement of the Quality Gate

The marketplace runs the full quality gate — `just check`, every step in the `outcomeeng.validation.STEPS` tuple — as a GitHub Actions job on `pull_request` and on push to `main`, wired as a required status check, so a deterministic-verification failure cannot reach `main` unseen. The job provisions the gate's full toolchain (uv, the Python version `pyproject.toml`'s `requires-python` declares, dprint, git, and the Claude Code CLI that the `manifests` step's `claude plugin validate` invocation needs) and runs the same `just check` recipe contributors run, never a reimplemented or filtered subset of steps.

## Rationale

Parity with the local `REVIEW_READINESS` gate is the point: any divergence between the CI gate and the local gate leaves open the path where a failing step lands on `main` unseen. Running `just check` (equivalently `uv run python -m outcomeeng.validation`) rather than enumerating steps in YAML keeps the CI gate in lockstep with the `STEPS` tuple, which stays the single source of truth in `outcomeeng/validation/_steps.py`. A subset that drops the `claude`-dependent `manifests` step leaves plugin-manifest schema and version-parity drift unguarded server-side — the class of failure the gate exists to stop — so the full gate runs, `claude` CLI cost included.

## Verification

### Testing

- ALWAYS: the workflow triggers on `pull_request` and on push to `main` — every path to `main` passes through the gate ([compliance])
- ALWAYS: the workflow runs the gate by invoking the `just check` recipe (or `uv run python -m outcomeeng.validation`) as a job step, never an inlined, re-enumerated, or filtered subset of the step list — divergence from the local step list reintroduces the unseen-failure gap ([compliance])
- ALWAYS: the workflow provisions Python at the version `pyproject.toml`'s `requires-python` declares — CI uses the project's interpreter contract ([compliance])
- NEVER: a gate step is marked `continue-on-error`, gated out by a step-level `if:`, or soft-passed by its `run:` shell — a non-blocking gate is not a gate ([compliance])
