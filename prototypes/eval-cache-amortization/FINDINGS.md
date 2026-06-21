# Findings — eval cache amortization (live measurement)

Measured 2026-06-21 against the OAuth `claude` CLI (v2.1.185), `claude --print
--output-format json --no-session-persistence --plugin-dir <dir>`, the exact
invocation `outcomeeng_evals/runner.py` uses. Output token count held at 9 per
call, so per-call cost is prefix-cache-dominated by construction.

## Result 1 — sequential same-prefix run is the headline

`spec-tree` plugin, 5 reps, back-to-back:

| call     | cache_read | cache_write | cost_usd |
| -------- | ---------- | ----------- | -------- |
| 1 (cold) | 15,536     | 25,842      | 0.3007   |
| 2        | 41,378     | 0           | 0.0552   |
| 3        | 41,378     | 0           | 0.0552   |
| 4        | 41,378     | 0           | 0.0552   |
| 5        | 41,378     | 0           | 0.0552   |

- **cold/warm cost ratio: 5.45×.** Call 1 writes the spec-tree prefix (25,842
  tokens); calls 2–5 read the full prefix warm (read rises to 41,378 = shared
  base + spec-tree; write falls to 0).
- Projected suite cost, one warm prefix vs cold-per-case:
  - 10 cases: **$0.80 vs $3.01 — 73% cheaper**
  - 50 cases: **$3.00 vs $15.03 — 80% cheaper**
- Hit ratio over the run: 87.5%.

This confirms the lever directly: holding one stable prefix warm across a
suite's cases pays the cold write once and reads it N−1 times.

## Result 2 — the cache holds multiple prefixes within TTL

`alternating spec-tree / python`, planned 6 reps, rate-limited (429) after 2:

| call | plugin    | cache_read | cache_write | cost_usd |
| ---- | --------- | ---------- | ----------- | -------- |
| 1    | spec-tree | 41,378     | 0           | 0.0552   |
| 2    | python    | 41,378     | 0           | 0.0578   |

Both prefixes read warm because both were loaded earlier in the session and
were still inside the 5-minute TTL. The server-side cache is not a single slot —
it holds several distinct prefixes at once. So **alternation alone does not
force cold writes**; the original counterfactual hypothesis was too strong.

## Cold-write data points (what a distinct prefix's first load costs)

- python plugin, first load (smoke): write 25,840, **$0.314**
- spec-tree plugin, first load (seq call 1): write 25,842, **$0.3007**

(Note the shared base system prompt — ~15,536 tokens — was already warm in both,
so only the plugin-specific portion was the fresh write.)

## Revised cost model

Per-suite cost is driven by two things, not by alternation:

1. **Number of distinct prefixes that must each be written once** (~$0.30 each).
   A workflow that points each suite at a different `plugin_dir` pays one cold
   write per distinct prefix. One shared all-plugins context = exactly one
   write, then warm reads everywhere.
2. **TTL expiry (5 min).** A gap longer than the window evicts the prefix and
   the next call re-pays the write. Temporal packing — running suites
   back-to-back rather than spread out — keeps the prefix warm.

## Implication for the harness

The amortization lever is real and large (5.45× per-call, ~73–80% per suite).
Two design levers capture it, both already supported by the measured behavior:

- **One frozen shared context** across every eval (one prefix → one write),
  instead of per-suite `plugin_dir` divergence — each distinct prefix is one
  avoidable ~$0.30 cold write.
- **Temporal packing** — run the suite (and ideally the whole tree) within one
  warm window so the single write is never re-paid.

Model tiering is not needed to capture this: the win is in the prefix cache, not
the base token rate.

## Cost of this measurement

~$0.94 metered (smoke $0.31 + sequential $0.52 + alternating-partial $0.11).
The alternating arm was rate-limited (429, server-side throttle); not retried.
