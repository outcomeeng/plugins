# Issues: Spec Tree Enabler

Issues discovered during contradiction analysis of `spx/EXCLUDE`, sync-exclude, and the quality gate mechanism. Source: `methodology/skills/skill-structure.md` stale content + cross-file contradiction audit.

## 8. Multi-language test discovery missing from methodology (PARTIAL)

Multi-language discovery is documented in `excluded-nodes.md` and `sync-exclude.md` spec (mapping assertions for pytest/vitest). The `status.yaml` reference in `testing-foundation.md` was removed in commit `391e9e5`.

**Remaining:** upstream `outcomeeng/methodology` repo still needs the multi-language principle added to `spec-tree-reference.md`.

## 9. `committing-changes` references `just check`

`skill-structure.md` line 457: "Run product validation (e.g., `just check`)." Should reference `spx` validation as the spec-tree quality gate. `just check` is the product's own concern, separate from spec-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/spec-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/spec-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.

## 12. Repo-wide evidence links still contain legacy test naming

Several planned spec assertions, spec-tree templates, examples, and methodology references still use legacy evidence names such as `*.unit.py`, `*.integration.py`, and `*.unit.test.ts`. This session renamed only checked-in Python evidence files and their direct links.

Needs `/aligning` to enumerate the affected spec-tree docs, `/testing` plus language-specific testing skills to select evidence modes and levels, and `/auditing-tests` where changed links resolve to test evidence.

Revisit during the repo-wide evidence-naming cleanup or the next spec-tree methodology pass.

## 13. Audit-orchestration redesign

Architecture decisions live in [`spx/21-spec-tree.enabler/17-auditing.adr.md`](17-auditing.adr.md): a generic `/auditing` skill and `auditor` agent in the spec-tree plugin dispatch to language-specific `auditing-{lang}*` skills via template substitution; the LLM partitions mixed-language scopes by file extension; deterministic computations live in a co-located Python helper at `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py`; language plugins MUST ship the `auditing-{lang}*` trio.

### Landed

- `/auditing` skill at `plugins/spec-tree/skills/auditing/SKILL.md`.
- `auditor` agent at `plugins/spec-tree/agents/auditor.md`.
- Python helper module at `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` covering scope hashing, diff-range expansion, branch-scope (three-dot), modified-since (two-dot), SHA reachability, branch slug with collision suffix, run-lock with TTL, base-ref and current-branch detection, full `AuditState`/`Finding`/`ResolvedFinding` dataclasses with atomic `load_state`/`save_state`, monotonic `assign_finding_id`, cell escaping for `|` and newlines, regression-detection helpers `find_resolved_by_identity`/`reopen_finding`/`resolve_finding`, and a source-owned `Verdict(StrEnum)`. Helper-behavior coverage at `spx/21-spec-tree.enabler/65-auditing.enabler/tests/test_auditing.scenario.l1.py` (53 scenario tests) and `tests/test_auditing.property.l1.py` (2 property tests).
- AGENTS.md registration of the new skill and agent.

### Pending

- Content moves from the interim TypeScript work into `auditing-typescript*`.
- Marketplace validation enforcing the `auditing-{lang}*` trio at install/check time.
- CLI dispatcher follow-up for the helper module — see [`spx/21-spec-tree.enabler/65-auditing.enabler/PLAN.md`](65-auditing.enabler/PLAN.md). Replaces the agent's nine `uv run python -c "..."` heredocs with one-liner subcommands for the eight stateless helpers plus two lock subcommands; the stateful state-file path stays in the multi-line Python block.
- Migrate the six `[review]`-tagged assertions in `spx/21-spec-tree.enabler/65-auditing.enabler/auditing.md` to `[eval]` evidence under `outcomeeng_evals`'s per-eval directory model (`evals/{rule-slug}/eval.toml`). The assertions describe LLM-runtime behavior of `/auditing` and the `auditor` agent; the eval runner exists, but the per-eval directories for these specific rules have not been authored. One eval slice per assertion at the same cadence as the shared-test-owned-constant-bag slice under `spx/43-typescript.enabler/`.
- Verdict-format carrier alignment: `spx/15-audit-verdict-format.pdr.md` flipped to JSON in commit `dd03033`, but every audit skill (orchestrator, dispatched language audits, `/auditing-tests`, `/auditing-product-decisions`, develop-plugin audits) still emits a markdown verdict. The PDR also overreached during the flip — it prohibits markdown fences and mandates the response IS the verdict, which is wrong for the PR-comment carrier case. The resolution is a carrier+payload refinement: markdown carrier with a delimited JSON block (`<!-- AUDIT_VERDICT_JSON_BEGIN -->` / `<!-- AUDIT_VERDICT_JSON_END -->`). Detailed plan in [`65-auditing.enabler/PLAN.md`](65-auditing.enabler/PLAN.md) (section `## PLAN: verdict-format carrier alignment and orchestrator/dispatched coherence`).
- Orchestrator/dispatched-skill alignment: `/auditing`'s 6 frozen rows conflict with the dispatched language skills' tables (different row names; `auditing-typescript-architecture` has 7 rows). Phase 1/2 ownership ambiguity (both the orchestrator and `auditing-typescript` declare Phase 1 and Phase 2 doing the same gate/test work). "Phase 3" namespace collision between orchestrator dispatch and dispatched-skill internal phases. Resolution in the same `65-auditing.enabler/PLAN.md` section.
