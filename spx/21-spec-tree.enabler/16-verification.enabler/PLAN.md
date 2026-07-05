# PLAN: Verification run-journal migration

## DONE: streaming implementation (phase 2)

`13-run-journal.adr.md`, `verification.md`, and `18-journal-projection.enabler/journal-projection.md` declare that a run **streams** its events live — opens the journal, appends each domain event at the moment the run reaches it (`scope.entered` → `scope.advanced` per unit of scope examined → `finding.reported` the instant raised → `run.completed`), and seals — per `spx/15-audit-result-delivery.pdr.md`. Phase 2 landed the implementation against those specs:

1. **Shared projection.** `build_events(run)` is replaced by four per-event builders (`scope_entered_event`, `scope_advanced_event`, `finding_reported_event`, `run_completed_event`) plus the new `verification.scope.advanced` event type. `render_surface` renders any prefix (partial in-flight or sealed); `compute_overall` unchanged. Tests rewritten.
2. **Review.** `journal_emit.py` exposes per-event subcommands (`scope-entered`, `scope-advanced`, `finding-reported`, `run-completed`); `review_result.parse_finding_json` is the per-finding validity gate; the SKILL, `changes-reviewer` agent, `review-prompt.md`, node spec, `21-script-decomposition.adr.md`, tests, and wrapper-protocol eval stream per-finding.
3. **Audit.** The orchestrator still aggregates the per-language children into the wrapper verdict (the verdict artifact + cross-run-fold key) but streams the journal through `scope-entered`, partition `scope-advanced`, partition `finding-reported`, and terminal `run-completed` events. `17-audit.adr.md` and the node spec carry the streaming ALWAYS and the NEVER-batch.

### Remaining streaming follow-ups

- **Stream eval coverage.** The wrapper-protocol eval now lists the streaming subcommands; an audit equivalent asserting `scope.advanced` per partition between the floor and ceiling is not yet authored.

## Target

`spx journal` is the source of truth for every agentic verification run. Audit and review open one run, append CloudEvents, seal it, read the sealed event prefix, and compute all verdict/check/comment surfaces as consumer-side projections. The journal backend is selected at the edge; skills do not name storage paths or parse rendered comments as state.

`spx journal render` is intentionally identity: it returns the event-prefix JSON array. Kind-specific markdown/findings/check surfaces are rendered by the consumer from the prefix, not by the type-agnostic channel.

## Current State

Done in the current audit slice:

- Shared projection exists at `src/plugins/spec-tree/skills/project-run-journal/scripts/journal_projection.py`, with generated copies under `dist/claude` and `dist/codex`.
- `/audit` Phase 6 records the default local run through `spx journal open/append/seal/read` and renders through `journal_emit.py`.
- The terminal event is `com.outcomeeng.spx.journal.run.completed` and carries the core run-state identity: `branchName`, `branchSlug`, `targetKind`, `headSha`, `baseRef`, `baseSha`, `configDigest`, `participants`, `scope`, timestamps, `outputPaths`, and `status`.
- Audit now requires `baseSha` in wrapper metadata before emitting journal events. The generic spx fold allows optional `baseSha`; audit deliberately does not, because its producer resolves `origin/<base>` to an OID.
- Removed the obsolete `/audit` prose for `.spx/audits` state files and PR-comment-as-database modes from the current audit path.

Verification already run:

- `pytest -q spx/21-spec-tree.enabler/tests/test_audit_journal_emit.mapping.l1.py spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/tests/test_journal_projection.scenario.l1.py spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/tests/test_journal_projection.mapping.l1.py spx/21-spec-tree.enabler/68-audit.enabler/tests/test_auditing.scenario.l1.py` -> 118 passed.
- Live raw channel smoke: `open -> append -> seal -> read -> render` returned the sealed event prefix.
- Focused audit adapter tests now stream wrapper metadata and per-partition child verdicts through `scope-entered`, `scope-advanced`, `findings-reported`, `run-completed`, and `render`, preserving the expected rollup and synthesizing failing or unknown child verdicts without representative findings.

## Next

1. Run one real `audit` workflow against a small known scope, then inspect the sealed run with `spx journal read --type audit --run <token> --from 0`.
2. Confirm the terminal event includes `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `scope`, and `status`.
3. If the real audit works, finish the audit slice: remove remaining stale audit wording only where it is truly off-path, and gate normally.
4. Exercise the journal-backed review path in the same real-workflow pass as audit.

## Remaining Migration

- `review-changes` now records validated review results through `spx journal --type review`, consumes the shared projection, renders counts from the sealed prefix, and stamps terminal state with `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `changedFiles`, and `status`.
- `thread_store` and `manage-thread-store` are superseded by the journal and should be deleted when no remaining consumer uses them. Do not reframe them as current architecture.
- The stateful audit-orchestrator cross-run fold is blocked until `@outcomeeng/spx` exposes a backend-agnostic read/list of a branch/type scope's sealed run set in order. The upstream request is recorded as outcomeeng/spx session `2026-06-23_07-42-10`; the prototype evidence is in `prototypes/audit-orchestrator-spike/`.
- PR-thread human delivery remains consumer-owned: the journal's GitHub backend stores event-array JSON, not the human verdict comment. The PR consumer must render and deliver its human surface separately.
- Keep `verdict.py`, `aggregate_verdicts.py`, and `pass_results.py` only while child audit skills still emit verdict JSON. Delete the verdict-toolchain node and scripts only after every consumer is on journal events.

## Overlap: deterministic-phase removal from the audit skills (coordinate)

A separate change (`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` — a dispatched agentic verifier runs no deterministic verification; the main agent passes validate/test/evaluate on the changeset before dispatch and CI re-runs them over the whole repository) removed the deterministic Phase 1 (`automated-gates`) and Phase 2 (`test-execution`) from the `/audit` orchestrator skill and from `audit-python`, `audit-typescript`, and `audit-rust`. That dropped the `automated-gates` and `test-execution` rows from those skills' `verdict_format`. When this migration rewires the language audit skills' verdict emission from the `verdict.py` object onto journal events, the row set is already reduced — `journal_emit.py` synthesizes a finding only for a failing row, so fewer rows simply means fewer synthesizable rows; the determinism-contract row remains the orchestrator's only wrapper row. Reconcile the language-auditor `verdict_format` rewrite against the post-removal row set, not the original three-row shape.

Marketplace scenario evidence now guards the resolved/reopened finding-identity rule by varying both `id` and `severity` while holding `(file, line, rule, message)` fixed. The later relocation still moves `compute_verdict_diff` and the full run-set property evidence into `spx journal` / the SPX CLI with the verdict-toolchain deletion, because `compute_verdict_diff` remains complex, test-bearing shipped-script logic governed by `spx/12-shipped-scripting.adr.md`.

## Safety Rules

- Do not delete Thread Store yet; first prove audit and review journal paths in real workflows.
- Do not invent a second keying model for review. Use the journal terminal run-state identity.
- Do not parse rendered comments or markdown as authoritative state.
- Do not duplicate the projection under audit or review; shared projection remains the single consumer-side primitive.
