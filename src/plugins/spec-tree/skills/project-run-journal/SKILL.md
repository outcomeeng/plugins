---
name: project-run-journal
user-invocable: false
description: >-
  Verification run-journal projection methodology loaded by audit and review
  skills when building spx journal events, computing rollups, or rendering verdict
  surfaces.
allowed-tools: Bash, Read
---

<objective>
A verification run recorded as an append-only `spx journal` and its verdict derived from the sealed event prefix, produced through one shared projection that every agentic verification surface — audit and review — drives identically: a run's results in, ordered channel events out; a sealed event prefix in, rollup and human-readable surface out.
</objective>

<channel>

The `spx` CLI owns the run journal. The verification kind is the opaque `--type <type>` segment (`audit` or `review`); the backend is edge-resolved (`SPX_VERIFY_BACKEND` override, `SPX_VERIFY_BRANCH` scope), so name no backend — a local run-journal file on a developer machine, the GitHub pull-request backend under CI.

| Verb                                                      | Role                                                          |
| --------------------------------------------------------- | ------------------------------------------------------------- |
| `spx journal open --type <t>`                             | open a run; reports `{runToken, runFile}`                     |
| `spx journal append --type <t> --run <tok>`               | append one event read from stdin and stream it back           |
| `spx journal read --type <t> --run <tok> --from <cursor>` | return events at or after the sequence cursor                 |
| `spx journal seal --type <t> --run <tok>`                 | make the sequence final; further appends are rejected         |
| `spx journal render --type <t> --run <tok>`               | return the event-prefix as a JSON array (identity projection) |

An append event is a JSON object with non-empty `id`, `source`, `type`, and `time` strings and an integer `attempt`, plus an optional `data` object; the channel assigns `specversion`, `streamid`, `seq` (1-based, contiguous), and `runid`. `read` and `render` return the event-prefix JSON unchanged — the channel renders no verification-kind-specific surface, so the rollup and the human-readable verdict are this skill's consumer-side projection over that prefix.

</channel>

<api_surface>

The projection lives in `${CLAUDE_SKILL_DIR}/scripts/journal_projection.py`, imported by sibling skills' scripts through the marketplace skill-co-located importlib convention (no path is hardcoded in agent prose). It is pure — it touches no journal backend, filesystem, or network — so it is verified at `l1` without a real journal and without mocking.

| Symbol                                      | Purpose                                                                                                                                                                                                                       |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `build_events(run_result, *, now, attempt)` | Ordered channel event inputs from a run's results: a scope-entered event, one finding-reported event per finding, a terminal `com.outcomeeng.spx.journal.run.completed` event whose data is the core journal run-state record |
| `compute_overall(events)`                   | The rollup over an event prefix: any `REJECT` finding maps to a rejected overall, else any `UNKNOWN` finding to unknown, else approved                                                                                        |
| `render_surface(events)`                    | The human-readable verdict surface rendered from an event prefix                                                                                                                                                              |

</api_surface>

<workflow>

To record a verification run, the consuming skill drives the channel (Bash) and passes event data to and from the pure projection:

1. `spx journal open --type <type>` for the run's verification kind; capture the run token.
2. `build_events(run_result, now=<utc>, attempt=<n>)` to derive the ordered event inputs. The run result carries scope hash, branch name, branch slug, target kind, head SHA, base ref, optional base SHA, config digest, participants, path-filter scope, timestamps, and output paths so the terminal event can fold through the core journal run-state projection.
3. `spx journal append --type <type> --run <token>` once per event, reading each event from stdin.
4. `spx journal seal --type <type> --run <token>` to finalize the sequence.
5. `spx journal read --type <type> --run <token> --from 0` to read the sealed event prefix, then `compute_overall` for the verdict and `render_surface` for the human-readable surface.

The consuming skill elaborates the generic core (scope-entered, finding-reported, run-completed) with its own event kinds — audit adds gate and per-partition events; review adds its own — but never re-implements event construction, the rollup, or the render.

</workflow>

<success_criteria>

- A run is recorded as journal events and its verdict derived from the sealed event prefix, never from a separate store.
- `build_events` output conforms to the channel append-input contract; `compute_overall` follows the rollup rule; both are pure and `l1`-verifiable without a real journal.
- Every agentic verification surface drives the run journal through this one projection — no consumer re-implements event construction or the rollup.
- `journal_projection.py` imports only the Python standard library.

</success_criteria>

<failure_modes>

**Incomplete terminal identity.** Claude emitted a reduced completion event with only an overall verdict. The `spx journal` fold requires the core `com.outcomeeng.spx.journal.run.completed` event, including branch slug, head/base identity, config digest, timestamps, scope, outputs, and terminal status. Avoid this by building the terminal event through `journal_projection.py` and asserting every run-state field in `l1` tests.

**Scope/config collapse.** Claude reused the scope hash as the config digest. The two fields answer different questions: `scopeHash` identifies the audited file set, while `configDigest` identifies the run configuration. Avoid this by requiring both fields in the run result and testing that audit metadata supplies them separately.

</failure_modes>
