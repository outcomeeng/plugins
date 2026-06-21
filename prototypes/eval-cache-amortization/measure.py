#!/usr/bin/env python3
"""Measure prompt-cache amortization across consecutive ``claude --print`` calls.

The eval harness spawns one ``claude --print`` subprocess per (case x trial),
each loading a plugin directory into context. The plugin/system prefix is
server-side prompt-cached (5-minute TTL): the first call within a window pays
a cache *write* (~1.25x input price over the prefix), and every later call that
sends the same prefix pays a cache *read* (~0.1x). This prototype quantifies
that curve directly from the ``claude --output-format json`` envelope's
``cache_read_input_tokens`` / ``cache_creation_input_tokens`` fields — the same
fields the eval harness now records per trial.

Two modes:

  sequential  K calls against ONE plugin_dir. Expected: call 1 writes the
              cache, calls 2..K read it warm. This is the amortization the
              "one shared, warm, all-plugins context" design would capture.

  alternating K calls cycling through 2+ plugin_dirs. Expected: each switch
              sends a different prefix, so every call pays a fresh write and
              nothing amortizes. This is the counterfactual — what per-suite
              plugin_dir divergence costs today.

The invocation mirrors ``outcomeeng_evals/runner.py``: ``claude [--bare]
--print --output-format json --no-session-persistence --plugin-dir <dir>``,
deriving ``--bare`` from ``ANTHROPIC_API_KEY`` like the runner's default path.
This prototype replicates only that default derivation, not the runner's
``bare=True`` / ``bare=False`` constructor overrides.

Stdlib only; run with ``python3`` on a managed interpreter.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


# A trivial, fixed case suffix. Output is one short JSON object, so per-call
# cost is dominated by the cached prefix behavior we are measuring, not by
# generation. The same body is sent every call so the prefix stays identical.
PROMPT = (
    "Respond with exactly this JSON object and nothing else: "
    '{"ok": true}. No prose, no code fence.'
)


@dataclass(frozen=True)
class CallResult:
    index: int
    plugin_dir: str
    input_tokens: int | None
    output_tokens: int | None
    cache_read: int | None
    cache_creation: int | None
    cost_usd: float | None
    duration_ms: float


def _bare_flag() -> bool:
    return "ANTHROPIC_API_KEY" in os.environ


def _argv(binary: str, plugin_dir: Path) -> list[str]:
    argv = [binary]
    if _bare_flag():
        argv.append("--bare")
    argv.extend(
        [
            "--print",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--plugin-dir",
            str(plugin_dir),
        ]
    )
    return argv


def _coerce_int(value: object) -> int | None:
    return (
        int(value) if isinstance(value, int) and not isinstance(value, bool) else None
    )


def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    return float(value) if isinstance(value, (int, float)) else None


def _subprocess_env() -> dict[str, str]:
    # Mirror the runner (outcomeeng_evals/runner.py): strip CLAUDECODE so a
    # nested call from inside a Claude Code session runs as a clean print-mode
    # subprocess, not under the interactive-session guard. Without this the
    # measured context would differ from the runner's.
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    return env


def _one_call(index: int, binary: str, plugin_dir: Path, timeout: float) -> CallResult:
    argv = _argv(binary, plugin_dir)
    start = time.perf_counter()
    completed = subprocess.run(
        argv,
        input=PROMPT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=_subprocess_env(),
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if completed.returncode != 0:
        raise RuntimeError(
            f"claude exited {completed.returncode}: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        envelope = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        # A zero exit with non-JSON stdout (a startup warning, a prepended
        # line) must surface through main()'s structured "call N failed"
        # handler, not as a bare JSONDecodeError traceback.
        raise RuntimeError(
            f"claude returned non-JSON output: {completed.stdout[:200]!r}"
        ) from exc
    usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
    return CallResult(
        index=index,
        plugin_dir=plugin_dir.name,
        input_tokens=_coerce_int(usage.get("input_tokens")),
        output_tokens=_coerce_int(usage.get("output_tokens")),
        cache_read=_coerce_int(usage.get("cache_read_input_tokens")),
        cache_creation=_coerce_int(usage.get("cache_creation_input_tokens")),
        cost_usd=_coerce_float(envelope.get("total_cost_usd")),
        duration_ms=elapsed_ms,
    )


def _plan(mode: str, plugin_dirs: list[Path], reps: int) -> list[Path]:
    if mode == "sequential":
        return [plugin_dirs[0]] * reps
    # alternating: cycle through the provided dirs
    return [plugin_dirs[i % len(plugin_dirs)] for i in range(reps)]


def _fmt(value: object, width: int = 9) -> str:
    if value is None:
        return "—".rjust(width)
    if isinstance(value, float):
        return f"{value:.4f}".rjust(width)
    return str(value).rjust(width)


def _print_table(results: list[CallResult]) -> None:
    print()
    print(
        f"{'call':>4}  {'plugin':<14} {'in':>7} {'out':>6} "
        f"{'cache_rd':>9} {'cache_wr':>9} {'cost_usd':>9} {'ms':>7}"
    )
    print("-" * 78)
    for r in results:
        print(
            f"{r.index:>4}  {r.plugin_dir:<14} "
            f"{_fmt(r.input_tokens, 7)} {_fmt(r.output_tokens, 6)} "
            f"{_fmt(r.cache_read)} {_fmt(r.cache_creation)} "
            f"{_fmt(r.cost_usd)} {_fmt(round(r.duration_ms), 7)}"
        )


def _summarize(mode: str, results: list[CallResult]) -> None:
    costs = [r.cost_usd for r in results if r.cost_usd is not None]
    if not costs:
        print("\nNo cost metadata returned — cannot summarize.")
        return
    total = sum(costs)
    first = costs[0]
    rest = costs[1:]
    print()
    print(f"total cost over {len(costs)} calls: ${total:.4f}")
    print(f"call 1 (cold): ${first:.4f}")
    if rest:
        warm_mean = statistics.fmean(rest)
        print(f"calls 2..{len(costs)} mean: ${warm_mean:.4f}")
        if warm_mean > 0:
            print(f"cold/warm cost ratio: {first / warm_mean:.2f}x")
        # Projected suite cost for N cases, both regimes.
        for n in (10, 50):
            amortized = first + warm_mean * (n - 1)
            cold_each = first * n
            saved = 1 - amortized / cold_each if cold_each else 0
            print(
                f"projected {n}-case suite: "
                f"one warm prefix ${amortized:.2f}  vs  "
                f"cold-per-case ${cold_each:.2f}  "
                f"({saved * 100:.0f}% cheaper)"
            )
    reads = [r.cache_read or 0 for r in results]
    writes = [r.cache_creation or 0 for r in results]
    print(
        f"\ncache tokens — read total {sum(reads)}, write total {sum(writes)}; "
        f"hit ratio {sum(reads) / (sum(reads) + sum(writes)):.1%}"
        if (sum(reads) + sum(writes))
        else "\nno cached-prefix tokens billed"
    )
    if mode == "alternating":
        print(
            "alternating mode: if cache writes dominate, prefix divergence is "
            "forcing cold writes; if cache reads dominate, both prefixes were "
            "within the TTL at once — the server cache holds several prefixes "
            "simultaneously, so alternation alone does not force cold writes "
            "(see FINDINGS.md revised cost model)."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-dir",
        dest="plugin_dirs",
        action="append",
        required=True,
        type=Path,
        help="Plugin directory to load. Repeat for alternating mode (2+ dirs).",
    )
    parser.add_argument("--reps", type=int, default=5, help="Number of calls.")
    parser.add_argument(
        "--mode",
        choices=("sequential", "alternating"),
        default="sequential",
    )
    parser.add_argument("--binary", default="claude")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan, the argv, and the prompt without calling claude.",
    )
    args = parser.parse_args()

    for d in args.plugin_dirs:
        if not d.is_dir():
            parser.error(f"plugin dir not found: {d}")
    if args.mode == "alternating" and len(args.plugin_dirs) < 2:
        parser.error("alternating mode needs at least two --plugin-dir values")

    plan = _plan(args.mode, args.plugin_dirs, args.reps)

    print(f"mode: {args.mode}  reps: {args.reps}  bare: {_bare_flag()}")
    print(f"plan: {[d.name for d in plan]}")
    print(f"argv (call 1): {' '.join(_argv(args.binary, plan[0]))}")
    print(f"prompt: {PROMPT!r}")

    if args.dry_run:
        print(
            "\n[dry-run] no calls made. Each call is metered to the active "
            "claude auth (OAuth subscription or ANTHROPIC_API_KEY). Re-run "
            "without --dry-run to measure."
        )
        return 0

    results: list[CallResult] = []
    for i, plugin_dir in enumerate(plan, start=1):
        try:
            r = _one_call(i, args.binary, plugin_dir, args.timeout)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            print(f"call {i} failed: {exc}", file=sys.stderr)
            return 1
        results.append(r)
        print(
            f"  call {i}/{len(plan)} [{plugin_dir.name}] "
            f"read={r.cache_read} write={r.cache_creation} "
            f"cost=${r.cost_usd if r.cost_usd is not None else 0:.4f}",
            flush=True,
        )

    _print_table(results)
    _summarize(args.mode, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
