# Issues: Spec Tree Enabler

Issues discovered during contradiction analysis of `spx/EXCLUDE`, sync-exclude, and the quality gate mechanism. Source: `methodology/skills/skill-structure.md` stale content + cross-file contradiction audit.

## 8. Multi-language test discovery missing from methodology (PARTIAL)

Multi-language discovery is documented in `excluded-nodes.md` and `sync-exclude.md` spec (mapping assertions for pytest/vitest). The `status.yaml` reference in `testing-foundation.md` was removed in commit `391e9e5`.

**Remaining:** upstream `outcomeeng/methodology` repo still needs the multi-language principle added to `spec-tree-reference.md`.

## 9. `committing-changes` references `just check`

`skill-structure.md` line 457: "Run project validation (e.g., `just check`)." Should reference `spx` validation as the spec-tree quality gate. `just check` is the project's own concern, separate from spec-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/spec-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/spec-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.

## 12. Repo-wide evidence links still contain legacy test naming

Several planned spec assertions, spec-tree templates, examples, and methodology references still use legacy evidence names such as `*.unit.py`, `*.integration.py`, and `*.unit.test.ts`. This session renamed only checked-in Python evidence files and their direct links.

Needs `/aligning` to enumerate the affected spec-tree docs, `/testing` plus language-specific testing skills to select evidence modes and levels, and `/auditing-tests` where changed links resolve to test evidence.

Revisit during the repo-wide evidence-naming cleanup or the next spec-tree methodology pass.

## 13. Audit-orchestration is mis-factored — generalize across languages and reclaim language-specific surface into the per-language audit skills

The typescript audit infrastructure introduced in PR #9 ships an
`/orchestrating-typescript-audit` skill and a `typescript-audit-orchestrator`
agent. Both embed substantial language-specific knowledge that does not
belong in a coordinator and substantial deterministic computation that an
LLM cannot reliably execute in-process. Two related defects, one redesign.

**Defect 1 — language leakage.** The orchestration skill reaches into
TypeScript-specific concerns that already have homes in the
`auditing-typescript*` family: file-extension globs (`*.ts`, `*.tsx`),
project-config files (`tsconfig.json`, `package.json`), validation and
test command discovery (`pnpm validate`, `vitest`), failure-mode examples
(`vi.mock`, harness module bodies), and verdict examples (`src/orders.ts`).
A reader of the skill cannot tell which content describes the orchestration
contract and which describes how to audit TypeScript specifically. Every
new language audit (python, rust) would either copy this skill or fork
its protocol — both are wrong answers.

**Defect 2 — embedded shell.** The orchestration skill and agent embed
deterministic computations as inline Bash:

- Skill Phase 0 step 3: scope-hash over the frozen file list
  (length-prefixed `sha256sum` pipeline).
- Skill Phase 0 step 1: `git diff --name-only <range> -- '*.ts' '*.tsx'`
  for file-list expansion.
- Agent slug rule: branch slug + SHA-256 collision suffix on the original
  branch name.
- Agent Phase 0: base-ref detection (`git symbolic-ref refs/remotes/origin/HEAD`,
  with the prefix-strip subtlety the round-3 review caught), current-branch
  (`git rev-parse --abbrev-ref HEAD`), detached-HEAD halt.
- Agent Phase R: modified-files diff against `last_run_sha`.
- Agent failure modes: `last_run_sha` reachability check
  (`git rev-parse <sha>`).

LLMs cannot reliably execute these in-process. Inline shell relies on Bash
invocation discipline and is impossible to unit-test as a coherent unit.
PR #9's round-2 review caught a real silent-collision bug in the scope-hash
exactly because byte-stream framing was undertested; PR #9's round-3 review
caught the unnormalized base-ref and the inert lock acquisition for the
same reason.

### Target architecture

**Generic orchestrator in spec-tree, language-specific surface owned by
the per-language audit skills.**

A new `/orchestrating-audit` skill in `plugins/spec-tree/skills/orchestrating-audit/`:

- Owns the 6-phase ordering rule (declare → automated gates → tests →
  comprehension → test evidence → ADR compliance).
- Owns the determinism contract (frozen scope, scope hash, frozen
  concerns, frozen findings, re-run protocol).
- Owns the verdict-aggregation format and the "APPROVED iff every concern
  is PASS or N/A" decision rule.
- Resolves the language under audit by detection (file extensions in
  scope) or explicit argument; rejects mixed-language scopes with
  "specify language explicitly".
- Dispatches each phase to the corresponding `auditing-{lang}*` skill via
  template substitution: Phase 1 and Phase 3 call `auditing-{lang}`,
  Phase 2 and Phase 4 call `auditing-{lang}-tests`, Phase 5 calls
  `auditing-{lang}-architecture`. The naming convention is the
  load-bearing invariant.

A new `audit-orchestrator` agent in `plugins/spec-tree/agents/`:

- Owns the branch-scoped wrapping protocol (state file, monotonic IDs,
  regression detection, lock acquisition, re-run flow).
- Takes language as parameter or detects from the branch diff.
- State path becomes `.spx/audits/<lang>/<slug>.md`.
- Calls the generic `/orchestrating-audit` skill, never any
  language-specific orchestrator.

A Python helper module shipped with the spec-tree plugin
(`plugins/spec-tree/scripts/audit_orchestrator.py`):

- Hosts every deterministic computation listed under Defect 2:
  `compute_scope_hash` (length-prefixed framing, content-based identity),
  `compute_branch_slug` (with SHA-256 collision suffix),
  `detect_base_ref` (with prefix normalization),
  `current_branch`, `branch_scope`, `modified_since`,
  `is_sha_reachable`,
  `acquire_lock` / `release_lock` (with stale-lock policy),
  `detect_language` (file-extension → language lookup, single-language
  enforcement, mixed-scope rejection),
  `validation_command` and `test_command` (per-language discovery with
  documented precedence: CLAUDE.md/AGENTS.md > justfile/Makefile >
  language-native config; closer to repo root wins),
  regression-detection identity (content-based hash of surrounding
  function body, replacing the line ± 5 heuristic that silently misses
  drifted regressions).

Per-language audit skills (`auditing-typescript`, `auditing-python`,
`auditing-rust`, and their `-tests` / `-architecture` siblings) grow a
**self-description block** at the top — a small machine-readable section
the orchestrator queries:

```yaml
audit_descriptor:
  language: typescript
  file_globs: ["*.ts", "*.tsx"]
  config_files: ["tsconfig.json", "package.json"]
  gate_command_discovery: ["pnpm validate", "npm run validate", "just check"]
  test_command_discovery: ["pnpm test", "npm test", "vitest run"]
  evidence_examples: references/typescript-evidence-examples.md
```

Examples and failure-mode prose move from the orchestration skill into
the corresponding language audit skill's references. The orchestrator
never embeds a `src/foo.ts` example or a `vi.mock` failure mode again.

The deployment-shipping invariant still applies: `outcomeeng/scripts/`
is repo-internal and not shipped to plugin consumers, so the helpers
must live inside a plugin downstream installations actually receive.
The spec-tree plugin is the right home — every language audit
orchestrator depends on it transitively.

### What moves where

| Today (in `plugins/typescript/skills/orchestrating-typescript-audit/SKILL.md` or `agents/typescript-audit-orchestrator.md`) | Where it belongs                                                  |
| --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Phase 0 file-extension globs (`*.ts`, `*.tsx`)                                                                              | `auditing-typescript` self-description                            |
| Phase 0 project-config files (`tsconfig.json`, `package.json`)                                                              | `auditing-typescript` self-description                            |
| Phase 0 validation-command discovery (`pnpm validate`, etc.)                                                                | `auditing-typescript` self-description; helper in Python module   |
| Phase 1 automated gate definition (tsc, eslint, prettier)                                                                   | `auditing-typescript`                                             |
| Phase 2 test runner (vitest/jest)                                                                                           | `auditing-typescript-tests` self-description                      |
| Phase 3 TypeScript predict/verify examples                                                                                  | `auditing-typescript`                                             |
| Phase 4 test-evidence patterns (`vi.mock`, harnesses)                                                                       | `auditing-typescript-tests`                                       |
| Phase 5 TypeScript ADR examples                                                                                             | `auditing-typescript-architecture`                                |
| Verdict-format examples (`src/orders.ts`)                                                                                   | `auditing-typescript` references                                  |
| Failure-mode examples (mock-hidden-in-harness, posthogHarness)                                                              | `auditing-typescript-tests` references                            |
| 6-phase ordering rule                                                                                                       | `/orchestrating-audit` (generic, in spec-tree)                    |
| Determinism contract (frozen scope, scope hash, frozen concerns and findings)                                               | `/orchestrating-audit`                                            |
| Re-run protocol                                                                                                             | `/orchestrating-audit`                                            |
| Verdict aggregation format and decision rule                                                                                | `/orchestrating-audit`                                            |
| Scope-hash, branch-slug, base-ref detection, file-list diff, sha reachability, lock acquisition                             | `plugins/spec-tree/scripts/audit_orchestrator.py`                 |
| Regression-detection identity (currently line ± 5)                                                                          | `plugins/spec-tree/scripts/audit_orchestrator.py` (content-based) |
| Language detection from file extensions                                                                                     | `plugins/spec-tree/scripts/audit_orchestrator.py`                 |
| Branch-state wrapping protocol                                                                                              | `plugins/spec-tree/agents/audit-orchestrator.md` (generic)        |

### Resolution outline

1. **Author an ADR** under `spx/21-spec-tree.enabler/` recording: the
   factoring rule (orchestrator never knows the language), the
   audit-skill self-description contract, the deployment-shipping
   invariant, the naming convention as load-bearing invariant, and the
   placement of the Python helper module.
2. **Decompose** a new enabler under `spx/21-spec-tree.enabler/` for
   the audit-orchestration concern. Define the Python module's public
   surface and the audit-skill self-description schema.
3. **TDD on the Python module:** scenario tests at `l1` for every helper
   listed above, then implementation.
4. **Audit-skill self-description rollout:** add the descriptor block to
   `auditing-typescript`, `auditing-typescript-tests`,
   `auditing-typescript-architecture` first (PR #9 already has the
   typescript work in motion). Move the language-specific examples and
   failure modes from the orchestration skill into the corresponding
   audit-skill references during this step.
5. **Generic skill in spec-tree:** create `/orchestrating-audit` with the
   6-phase ordering, determinism contract, verdict aggregation, and
   dispatch protocol that template-resolves `auditing-{lang}*` from the
   detected or specified language.
6. **Generic agent in spec-tree:** create `audit-orchestrator` that
   wraps `/orchestrating-audit` with branch-scoped persistence,
   delegating all deterministic computation to the Python module.
7. **Retire the typescript-specific surface:** delete
   `plugins/typescript/skills/orchestrating-typescript-audit/` and
   `plugins/typescript/agents/typescript-audit-orchestrator.md` once
   the generic skill and agent cover the case. AGENTS.md and the
   typescript plugin manifest reflect the removal.
8. **Validate** that downstream installs of
   `typescript@outcomeeng + spec-tree@outcomeeng` (and
   `python@outcomeeng + spec-tree@outcomeeng` when ready) resolve every
   helper without requiring `outcomeeng/scripts/`.
9. **Repeat per language** as `python` and `rust` grow their own audit
   orchestrators: only the audit-skill self-description blocks change;
   the generic skill and agent stay constant.

### Deferred review items absorbed by this redesign

PR #9's round-3 review surfaced four small issues scoped to the
typescript-specific orchestrator. All four dissolve in the rewrite —
they are fixed once by the generic implementation and never reappear:

- **Validation command discovery has no precedence.** Resolved by the
  Python module's `validation_command` helper, which encodes the
  precedence rule (CLAUDE.md/AGENTS.md > justfile/Makefile > language-
  native config; closer to repo root wins).
- **Phase F write-LAST ambiguity.** Resolved by the generic agent
  enforcing the order structurally — the helper module exposes
  `write_state_then_emit(state, verdict)` rather than relying on prose
  to discipline two separate steps.
- **APPROVED first-run parsing.** Resolved by the helper's state
  initializer handling the no-findings case explicitly
  (`next_finding_id` starts at 1; absent Findings section is not a
  parse error).
- **Concern 6 "Determinism contract" is always PASS.** Resolved by
  giving it a concrete REJECT condition in the generic skill: REJECT
  if the file list read during Phase 3 differs from the one captured
  at Phase 0 (scope drift detection mid-audit). The frozen-scope-size
  and scope-hash also surface as metadata on the verdict header.

The shell forms and language-specific surface in the typescript skill
and agent are explicitly marked interim — both files cite this issue
as the migration destination.
