# Eval cache amortization — prototype

Quantifies how much the eval harness's per-run cost is prompt-cache amortization
rather than raw model work, and what breaks the amortization.

## Hypothesis

Each eval call is a `claude --print` subprocess that loads a plugin directory.
The plugin/system **prefix** is server-side prompt-cached (5-minute TTL). The
first call within a window pays a cache **write** (~1.25× input over the
prefix); every later call that sends the *same* prefix pays a cache **read**
(~0.1×). So a suite that holds one stable, warm prefix across its cases pays the
write once and reads it N−1 times; a workflow that sends a *different* prefix
per suite (e.g. per-suite `plugin_dir` divergence) pays a fresh write each time.

Measured eval transcripts already show this: cache-read tokens reach 50–99k
against ~10k fresh input, and per-call cost is bimodal — ~$0.09 warm read vs
~$0.42 cold write. This prototype reproduces the curve deliberately.

## What it measures

`measure.py` calls `claude` exactly as `outcomeeng_evals/runner.py` does
(`claude [--bare] --print --output-format json --no-session-persistence
--plugin-dir <dir>`), sends a fixed trivial prompt K times, and reads each
call's `cache_read_input_tokens` / `cache_creation_input_tokens` /
`total_cost_usd` from the JSON envelope — the same fields the harness now
records per trial.

- `--mode sequential` (one `plugin_dir`, K calls): the amortization curve.
  Call 1 writes; calls 2..K read warm. Reports cold/warm ratio and the
  projected N-case suite cost under "one warm prefix" vs "cold-per-case".
- `--mode alternating` (2+ `plugin_dir`, K calls): the counterfactual. Each
  switch forces a fresh write; a low hit ratio confirms per-suite prefix
  divergence is what costs.

## Cost

Every call is **metered to the active `claude` auth** (your OAuth subscription
when `ANTHROPIC_API_KEY` is unset). Use `--dry-run` first — it prints the plan,
the argv, and the prompt without calling. A 5-rep `spec-tree` sequential run is
roughly one cold write (~$0.30) plus four warm reads (~$0.06) ≈ $0.52, per the
measured `FINDINGS.md` Result 1.

## Run

```bash
# Inspect the plan and payload, no calls:
python3 measure.py --plugin-dir ../../dist/claude/spec-tree --reps 5 --dry-run

# Amortization curve (metered):
python3 measure.py --plugin-dir ../../dist/claude/spec-tree --reps 5

# Counterfactual: alternating prefixes defeat the cache (metered):
python3 measure.py --mode alternating \
  --plugin-dir ../../dist/claude/spec-tree \
  --plugin-dir ../../dist/claude/python --reps 6
```

## Status

Exploratory prototype per `spx/12-shipped-scripting.adr.md`: it proves the
amortization lever before any harness redesign. With the lever proven, the
logic moves into the eval harness / SPX CLI, not into this script.
