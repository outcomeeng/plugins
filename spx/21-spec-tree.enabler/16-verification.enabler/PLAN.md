# PLAN: Verification run-journal migration

## Why

`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` declares the append-only run-journal contract: an agentic verification run (auditing or reviewing) is one event journal that is its sole source of truth, every output surface is a projection rendered from the journal's event prefix, and the skill emits through one backend-neutral channel that binds the backend at the edge. The `spx` CLI's `spx journal` verbs own the journal and its backends. The node's children and the auditing decision still encode the superseded end-of-run verdict-toolchain and `.spx/audits` model; truth flows down, so align them to the contract.

`13-run-journal.adr.md` declares the end state correctly and needs no change.

## Definition of done

Every auditor and reviewer drives the `spx journal` channel (open/append/read/seal/render). The verdict-persistence toolchain is gone — `spx journal` is the source of truth, not `verdict.py` + `emit_verdict.py`/`read_verdict.py`/`aggregate_verdicts.py`/`pass_results.py`, and not `thread_store`. The node `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler` is deleted with its spec, tests, and scripts.

The only Python that survives is one minimal, pure, **shared** projection — event construction from a run's results, the rollup, and the human-readable surface render — generic over a run-result shape and type-agnostic, consumed by both auditing (`/audit`) and reviewing (`/review-changes`). It is a new shared enabler under `spx/21-spec-tree.enabler/16-verification.enabler` with its helper in a dedicated shared scripts home both consumers import (the `scope-changeset`/`changeset_scope.py` precedent), governed by the verification enabler — not co-located under either consumer, not governed by `17-auditing.adr`. "Projection" is a pure function of the event prefix; the consumer computes it (see Channel reality below).

## The channel — `spx journal` (spx 0.6.0, verified live)

Type-agnostic run journal; the verification kind (`auditing`/`reviewing`) is an opaque `--type <type>` scope segment. One run journal lives at `.spx/branch/<slug>/<type>/runs/run-<token>.jsonl`.

| Verb                                          | Contract role                                                 |
| --------------------------------------------- | ------------------------------------------------------------- |
| `open --type <t>`                             | open a run; returns `{runToken, runFile}`                     |
| `append --type <t> --run <tok>`               | append one event read from stdin and stream it back           |
| `read --type <t> --run <tok> --from <cursor>` | return events at or after the sequence cursor                 |
| `seal --type <t> --run <tok>`                 | make the sequence final; further appends are rejected         |
| `render --type <t> --run <tok>`               | return the event-prefix as a JSON array (identity projection) |

**Append input contract.** Stdin is one JSON object. The producer supplies `id`, `source`, `type`, `time` (all non-empty strings) and `attempt` (integer), plus an optional `data` object. The channel assigns `specversion` (`"1.0"`), `streamid`, `seq` (1-based, strictly increasing, contiguous), and `runid`. A correction is a later event; a sealed run rejects appends.

**Backend is edge-resolved** from the environment — `SPX_VERIFY_BACKEND` override, `SPX_VERIFY_BRANCH` scope — so a skill or wrapper agent names no backend: a local run-journal file on a developer machine, the GitHub pull-request backend under CI.

## Channel reality — `render` is identity by design (corrects the verb mapping)

`spx journal render` returns the event-prefix as a JSON array. Both render paths are identity: the `render` verb and the GitHub pull-request comment body (the backend posts the event-array JSON to the comment). This is intentional — spx's journal-channel decision forbids a verification-kind-specific rendered surface inside the type-agnostic channel, so a kind-specific markdown/findings/check surface is a **consumer-side projection by design**. No spx change is needed.

Corrected mapping (the prior "Python becomes `spx journal render`" framing was wrong):

| Old toolchain role                   | Where it goes                                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `verdict.py` schema                  | CloudEvents events — scope/finding/run facts travel in event `data`                                                                        |
| `read_verdict.py` (read)             | `spx journal read --from <cursor>`                                                                                                         |
| `pass_results.py` (staging)          | child-verdict staging; survives only while child skills still emit verdict JSON, removed once children emit events directly                |
| `aggregate_verdicts.py` rollup       | a pure consumer-side **rollup** over the event prefix — NOT `render` (which is identity); deterministic, never the model's inline judgment |
| `emit_verdict.py` (markdown surface) | NOT `render`. Local path drops it (the consumer reads event-prefix JSON). CI path: a consumer-side renderer + its own delivery (below)     |

**Local audit** consumes the event-prefix JSON directly — Claude is the only reader, so no markdown projection is needed locally.

**CI / pull-request path** owns both the human-readable verdict *and* its delivery: spx's GitHub backend posts event-array JSON to the PR comment, so the journal's own comment is not the human surface. The consumer must render the sealed run's event prefix into a human surface and choose its delivery (render client-side and post a distinct comment, or render into a separate human surface). This is the open design for the PR-thread-consumer change, where `emit_verdict.py`'s markdown role gets its real replacement.

## PR sequence

Each PR is spec-leading against `13-run-journal.adr.md`, gated with `/apply` audit gates and `/merge`; never self-merge without review. `/contextualize` each target node before editing it. The floor and CI pin advance to `0.6.0` in PR1 — `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) and the `SPX_VERSION` pin (`.github/workflows/check.yml`).

### PR1 — shared projection + auditing architecture + the first consumer (`/audit`)

PR1 establishes the shared projection both agentic types consume, reworks the auditing architecture onto the journal, and rewires the first consumer. The verification architecture **declares** the projection shared by auditing and reviewing (`verification.md`; `13-run-journal.adr.md` is type-agnostic over both), so reviewing is a known future consumer — PR1 builds the projection generic now to satisfy that declaration, and reviewing's later migration (a future PR) consumes it unchanged. There is no concurrent reviewing work to coordinate with; PR1 defines the generic run-result contract from the declared event vocabulary and both consumers' result shapes.

1. Advance the floor and CI pin `0.5.6` → `0.6.0`.
2. Author the **shared projection enabler** — a new child enabler under `spx/21-spec-tree.enabler/16-verification.enabler` governing a generic, type-agnostic projection: build `spx journal` event inputs from a run-result shape, and compute the rollup and render the human surface from an event prefix; pure (no journal backend, filesystem, or network). Its helper lives in a dedicated shared scripts home both `/audit` and `/review-changes` import (the `scope-changeset`/`changeset_scope.py` precedent), not co-located under either consumer. Implement test-first; tests live under the new node.
3. Rework `spx/21-spec-tree.enabler/17-auditing.adr.md` onto the journal: orchestrator state, CI state, and the PR comment become the journal and its projections through the `spx journal` channel (auditing's `<type>` segment); the wrapper agents `open`/`append`/`seal` and **consume the shared projection** (governed by the verification enabler, not by this ADR), rather than persisting verdicts via the toolchain and the PR-comment-as-database recovery. **Preserve the generic-auditor composition (the prior auditor collapse) and layer the journal rework on top — do not revert it.** Gate with `/align` then `/audit-adr`.
4. Rewire the `/audit` skill's stateless local emit (Phase 6) onto `spx journal` open/append/seal/read via the shared projection. Drop `emit_verdict.py`'s markdown from the local path. Keep `verdict.py` (schema the not-yet-migrated child skills still emit) and `pass_results.py` (child staging) until later consumer PRs; the rollup moves into the shared projection.

**Event model (the shared generic contract).** The generic core every agentic run appends as it advances: `scope.entered`, one `finding.reported` per finding, terminal `run.completed`. Auditing elaborates with `gate.evaluated` (per orchestrator row) and `partition.completed` (per language child); reviewing elaborates with its own event data. Each is a valid channel event input; the consumer reads the sealed event prefix back as JSON and computes the rollup over it.

Leave the stateful (`audit-orchestrator`) and PR-thread (`pr-reviewer`/`pr-review-orchestrator`) modes on the toolchain in PR1; they migrate with their consuming agents.

### PR2..N — remaining consumers, in batches

Rewire each consumer's emit onto the `spx journal` channel / event shape:

- The `audit-orchestrator` stateful mode. Cross-run resolved/reopened folds a changeset's sealed runs across its iterations — a finding resolved (in an earlier run, gone now) or reopened (resolved earlier, back now) across the changeset's revisions, keyed on `(file, line, rule, message)`; the fold is a consumer-side projection over the runs' events. It needs a backend-agnostic read of a changeset scope's sealed run set in order — the runs the journal already groups under one `(branch-slug, type)` scope — which the channel does not yet expose. The request is queued in the `outcomeeng/spx` repo as session `2026-06-23_07-42-10`; this migration is blocked until `@outcomeeng/spx` ships that read and the floor (`REQUIRED_SPX_VERSION`) advances. The benefit is established in `prototypes/audit-orchestrator-spike/`.
- The `pr-reviewer` / `pr-review-orchestrator` PR-thread mode, including the human-readable PR verdict and its delivery (Channel reality above).
- The language audit skills — `audit-python`/`audit-python-architecture`, `audit-typescript`/`audit-typescript-architecture`, `audit-rust`/`audit-rust-architecture` — and the artifact-type audit skills `audit-adr`/`audit-pdr`/`audit-specs`/`audit-tests`, and `develop`'s `audit-skills`/`audit-subagents`.
- `review-changes` (`review_result.py` / `thread_store`): migrate reviewing onto the same `spx journal` channel under reviewing's `<type>` segment, **consuming the shared projection enabler PR1 establishes** (adapting the review-result shape to its generic run-result input) rather than building a parallel projection. **The replacement MUST key review records by review-diff identity (head/base OID), not branch slug alone** — preserves the merge-safety property in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md` (a record keyed by branch slug alone lets a reused worktree or stale branch read the wrong diff's record). `thread_store` is superseded by the channel and removed (per Definition of done — deleted, not reframed); its branch-slug derivation already re-exports from `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler`, so nothing unique is lost, and the `manage-thread-store` skill that owns it is retired with it.

### Final PR — delete the toolchain node

Once no consumer references it, delete `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler` in full — spec, tests, and the scripts `verdict.py`/`emit_verdict.py`/`read_verdict.py`/`aggregate_verdicts.py`/`pass_results.py`, plus `outcomeeng_testing/harnesses/verdict_toolchain.py`. As part of this, re-home the verdict-vocabulary reference in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` (its in-slice-unresolved-work assertion cites the toolchain node for the `REJECTED`/`UNKNOWN`/`FAIL`/`REJECT` tokens) to cite the journal's terminal-seal event and the rendered-projection vocabulary.

## Reviewing result-delivery governance

`spx/15-audit-result-delivery.pdr.md` decides observable result delivery for **audit** runs; `13-run-journal.adr.md` applies the journal contract to **both** agentic types, but no decision declares reviewing's incremental-reveal behavior. Either broaden `spx/15-audit-result-delivery.pdr.md` to cover both types or author a separate reviewing-result-delivery decision; either way it must cover the consumer-owned human surface and its delivery (Channel reality above). Record the choice when reviewing migrates.

## Safety properties to preserve

- The verdict-persistence toolchain and `thread_store` are deleted, not reframed. The only surviving Python is one minimal, pure, **shared** projection (event construction, rollup, human-surface render), governed by the verification enabler and consumed by both auditing and reviewing — not duplicated per consumer.
- The reviewing/thread-store replacement keys review records by review-diff identity (head/base OID), not branch slug alone.
- The generic-auditor composition in `17-auditing.adr.md` is preserved; the journal rework layers on top.

## Survives unchanged

- `13-run-journal.adr.md` — declares the end state; no change.
- `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` — the journal contract still derives branch, slug, base ref, and the changed-file set from it.
