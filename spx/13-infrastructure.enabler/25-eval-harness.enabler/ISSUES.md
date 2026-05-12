# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

## Just recipe naming

Confirm `just eval-run` vs. `just eval` aligns with the existing Justfile pattern when the eval recipes are added.

## Optional per-eval model pin

`claude --print` uses the user's default model. An optional `model` field in `eval.toml` would let an eval pin against a specific model for reproducibility. Defer until a real need arises.

## Cross-suite parallelism

The harness supports `--workers` for parallelism within a suite. `run --all` could also parallelize across suites. Defer; today's use case is one eval at a time.

## CI integration

A scheduled CI workflow that runs `outcomeeng-evals run --all` and posts results is not yet wired. The CLI's exit codes make this straightforward to add later. Until it lands, `history.jsonl` accumulates local appends on developer machines — contributors restore the file before committing unrelated changes.

## Independent uv project for `outcomeeng_evals`

`outcomeeng_evals` builds from the single repo `pyproject.toml`. Split into an independent uv project only when it is published to PyPI or its dependency surfaces diverge from the marketplace's.

## `outcomeeng_evals.testing` public-API contract

The runner ships fakes and factories under `outcomeeng_evals.testing`. Whether that subpackage is a stable, versioned surface or an internal helper with no compatibility guarantees is not yet declared. Decide when the first external consumer appears.
