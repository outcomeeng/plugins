# PLAN: Verification run-journal migration

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

- `pytest -q spx/21-spec-tree.enabler/tests/test_audit_journal_emit.mapping.l1.py spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/tests/test_journal_projection.scenario.l1.py spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/tests/test_journal_projection.mapping.l1.py spx/21-spec-tree.enabler/68-auditing.enabler/tests/test_auditing.scenario.l1.py` -> 118 passed.
- Live raw channel smoke: `open -> append -> seal -> read -> render` returned the sealed event prefix.
- Live audit adapter smoke: wrapper JSON -> `journal_emit.py build-events` -> `spx journal` -> `journal_emit.py render` returned `{"overall": "rejected", ...}` and synthesized the failing gate row correctly.

## Next

1. Run one real `audit` workflow against a small known scope, then inspect the sealed run with `spx journal read --type audit --run <token> --from 0`.
2. Confirm the terminal event includes `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `scope`, and `status`.
3. If the real audit works, finish the audit slice: remove remaining stale audit wording only where it is truly off-path, and gate normally.
4. Migrate review only after audit is proven in the real workflow.

## Remaining Migration

- `review-changes` still uses `thread_store`. Migrate it to `spx journal --type review`, consuming the shared projection rather than building a parallel model. The replacement must accept only a sealed terminal state matching the reviewed diff's `headSha`/`baseRef`/`baseSha`.
- `thread_store` and `manage-thread-store` are superseded by the journal and should be deleted when no review consumer uses them. Do not reframe them as current architecture.
- The stateful audit-orchestrator cross-run fold is blocked until `@outcomeeng/spx` exposes a backend-agnostic read/list of a branch/type scope's sealed run set in order. The upstream request is recorded as outcomeeng/spx session `2026-06-23_07-42-10`; the prototype evidence is in `prototypes/audit-orchestrator-spike/`.
- PR-thread human delivery remains consumer-owned: the journal's GitHub backend stores event-array JSON, not the human verdict comment. The PR consumer must render and deliver its human surface separately.
- Keep `verdict.py`, `aggregate_verdicts.py`, and `pass_results.py` only while child audit skills still emit verdict JSON. Delete the verdict-toolchain node and scripts only after every consumer is on journal events.

## Safety Rules

- Do not replace Thread Store yet; first prove audit, then migrate review.
- Do not invent a second keying model for review. Use the journal terminal run-state identity.
- Do not parse rendered comments or markdown as authoritative state.
- Do not duplicate the projection under audit or review; shared projection remains the single consumer-side primitive.
