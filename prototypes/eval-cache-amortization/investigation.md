# Research: prompt-cache amortization in eval CI

Investigation into whether the eval harness can capture prompt-cache amortization
to cut the equivalent API cost of a CI eval run. Conclusion up front: **on the
subscription `claude --print` path the amortization *is* capturable — not by the
harness's current single-turn invocation, but by loading every plugin once into a
base session and forking that base per case so each case reads the shared prefix
warm. No metered API key is needed; realization is gated on the upstream CLI
regression [`anthropics/claude-code#34629`](https://github.com/anthropics/claude-code/issues/34629).**
The decision this informs is recorded in
`spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`,
which governs; this file is the supporting investigation.

## Question

A full CI eval run records a large equivalent API cost (`total_cost_usd`). The
prompt-caching ADR declares the lever as "hold one prompt prefix per run so the
provider's prompt cache serves it warm." Does holding one prefix actually
amortize the cost on the harness's current substrate (`claude --print` on a
Claude subscription, OAuth)?

## Measurement 1 — CI baseline (committed `history.jsonl`, git_sha d19bff08, 21 suites)

| metric                                    | value      |
| ----------------------------------------- | ---------- |
| full-run equivalent cost                  | **$10.38** |
| cached-prefix read tokens                 | 2,392,358  |
| cached-prefix write tokens                | 2,425,304  |
| cold-write share of cached-prefix traffic | **~50%**   |

A warm, fully-amortized run would spend almost everything on reads (one cold
write for the whole run). At 50% writes, the run pays cold writes pervasively.

Two causes ruled out:

- **Not prefix divergence.** 23 of 24 suites declare the same `plugin_dir`
  (`dist/claude/spec-tree`); only `shared-constant-bag` uses `typescript`. The
  prefix is already shared.
- **Not parallel cold-start.** CI runs suites sequentially (`for item in plan`
  loop) and `WORKERS` defaults to `1`, so cases run one at a time.

Yet the write share is ~50% even for a 17-case suite, where an amortized prefix
would give ~6%. So the prefix is not being reused across consecutive same-prefix
calls.

## Measurement 2 — per-case experiment (local, wrapper-protocol, `--workers 1`)

Ran one spec-tree suite sequentially and read per-case cache tokens:

| # | case                      | cache_read | cache_write |
| - | ------------------------- | ---------- | ----------- |
| 1 | clean-diff-protocol       | 15,536     | **27,263**  |
| 2 | broken-diff-protocol      | 15,536     | **27,317**  |
| 3 | must-fix-arbiter-recovery | 15,536     | **27,353**  |

Every case cold-writes the ~27k plugin prefix identically; only the ~15k base
system prompt stays warm. **Zero plugin-prefix reuse across cases** — structural,
not timing (cases ran seconds apart, same prefix, well within any TTL).

## Mechanism (documented)

Per [How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching):
skills, commands, agents "are appended after the existing conversation, so the
next request pays for the new content but still reads everything before it from
the cache," and "skills and commands inject their instructions as user messages
at the point of invocation." The cache breakpoint sits on the last **system**
block (core system + tools). So with `--print --no-session-persistence` and a
different prompt per case, only the byte-identical core system prefix (~15k) is
warm; the plugin/skill content rides in after the breakpoint as per-call content
and cold-writes every time. Anthropic prompt caching is byte-exact prefix match
([prompt caching guide](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).

## Levers investigated

- **Claude Agent SDK with explicit `cache_control`.** Rejected: the Agent SDK
  requires a metered `ANTHROPIC_API_KEY` and does not support subscription OAuth
  (Anthropic disallows claude.ai-subscription auth for SDK-built tools), and it
  exposes no explicit `cache_control` (caching is automatic). See
  [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview).
- **Direct Anthropic Messages API with explicit `cache_control`.** This is the
  only interface that lets you place a breakpoint after the system+plugin prefix
  and vary only the per-case message — but it requires a metered API key
  (per-token billing).
- **`claude --print` single-turn (current harness shape).** Subscription billing;
  with `--no-session-persistence` and a different prompt per case, the plugin
  content rides in after the cache breakpoint and cold-writes every case. This
  shape captures no plugin-prefix amortization — its failure is architectural.
- **`claude --print` with a fixed base session, forked per case (the capturing
  shape).** Load every plugin once into a base session, then `--fork-session` it
  per case: the fork inherits the base prefix and reads it warm from the cache,
  the case question appends after it, and cases stay independent because each forks
  the same clean base. Subscription billing, no metered key — this is the lever,
  gated only on the regression below.
- **`--print --resume`/`--fork-session` cache regression** ([anthropics/claude-code#34629](https://github.com/anthropics/claude-code/issues/34629)).
  Since v2.1.69 (installed CLI 2.1.185 is affected) resume/fork stopped reusing the
  cached conversation history — only the ~14.5k core system prompt caches and all
  history cold-writes. The fork-per-case shape needs this path working, so it is
  blocked until the regression is resolved upstream, a pre-regression CLI (v2.1.68)
  is pinned, or the published community cache fix is applied.
- **`ENABLE_PROMPT_CACHING_1H=1`.** Extends the TTL to 1 hour on subscription
  auth, but does not change the structural fact that the plugin prefix is after
  the breakpoint and re-written per differing case.

## Conclusion

The subscription `claude --print` path *can* capture the plugin-prefix
amortization — the earlier "uncapturable, metered-only" reading was drawn from the
single-turn shape alone and is wrong. Two shapes, two outcomes:

- **Single-turn independent calls** (the harness today) cold-write the plugin every
  case, because the per-case prompt sits in or after the plugin region so only the
  core system prefix stays byte-identical (Measurement 2).
- **A fixed base session forked per case** holds the expensive plugin content
  byte-identical and before the variable question, so each fork reads it warm —
  the fixed-prefix payoff Measurement 1 and `FINDINGS.md` quantify (5.45× per call,
  ~73–80% per suite) realized for real, differing cases, entirely on the
  subscription.

No metered key is required. The only blocker is regression
[`anthropics/claude-code#34629`](https://github.com/anthropics/claude-code/issues/34629),
which currently breaks resume/fork cache reuse.

## Implication for `15-prompt-caching.adr.md`

The ADR keeps prefix reuse as the cost lever and records the corrected mechanism:
capture it on the subscription path via a base session forked per case, keep the
`NEVER`-route-to-a-metered-API stance, and gate realization on regression #34629.
The harness keeps its current single-turn invocation until the regression clears
(upstream fix, pinned v2.1.68, or the community cache fix); the captured saving is
pending that. Empirical confirmation of fork-per-case on a real differing-case
workload is the validation step, to run once the resume/fork cache path is
restored — it cannot be measured on an affected CLI, which would only reproduce
the regression.
