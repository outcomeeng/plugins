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

## 13. Audit-orchestration shell snippets need to migrate to a spec-tree-shipped Python module

The typescript audit infrastructure introduced in PR #9 (commits `9cfd923`,
`593c661`, and the round-2 fixes through `6758b46`) embeds deterministic
computations as inline shell in the skill prose and the agent prompt:

- `plugins/typescript/skills/orchestrating-typescript-audit/SKILL.md` Phase 0
  step 3: scope-hash over the frozen file list (currently a length-prefixed
  `sha256sum` pipeline).
- `plugins/typescript/skills/orchestrating-typescript-audit/SKILL.md` Phase 0
  step 1: `git diff --name-only <range> -- '*.ts' '*.tsx'` for file-list
  expansion.
- `plugins/typescript/agents/typescript-audit-orchestrator.md` slug rule:
  branch slug + SHA-256 collision suffix on the original branch name.
- `plugins/typescript/agents/typescript-audit-orchestrator.md` Phase 0:
  base-ref detection (`git symbolic-ref refs/remotes/origin/HEAD`),
  current-branch (`git rev-parse --abbrev-ref HEAD`), detached-HEAD halt.
- `plugins/typescript/agents/typescript-audit-orchestrator.md` Phase R:
  modified-files diff against `last_run_sha`.
- `plugins/typescript/agents/typescript-audit-orchestrator.md` failure modes:
  `last_run_sha` reachability check (`git rev-parse <sha>`).

LLMs cannot reliably execute these in-process. Inline shell relies on Bash
invocation discipline and is hard to unit-test. The round-2 review caught
a real silent-collision bug in the scope-hash because the byte-stream
framing was undertested.

**Decision target:** these helpers live in a new
`plugins/spec-tree/scripts/audit_orchestrator.py` module, shipped with the
spec-tree plugin so any downstream installation that pairs a language
plugin with spec-tree gets the helper. `outcomeeng/scripts/` is repo-internal
marketplace tooling and is not shipped to plugin consumers — see PR #9
discussion for the deployment-shipping invariant.

**Resolution outline:**

1. Author an ADR under `spx/21-spec-tree.enabler/` recording the placement
   decision and the deployment-shipping invariant. Establish that audit
   orchestrators across language plugins (typescript, python, rust) share
   one helper module.
2. Decompose a new enabler under `spx/21-spec-tree.enabler/` for the
   audit-orchestration helpers. Define the module's public surface:
   `compute_scope_hash`, `compute_branch_slug`, `detect_base_ref`,
   `current_branch`, `branch_scope`, `modified_since`, `is_sha_reachable`,
   plus the regression-detection identity function (content-based, not
   line-based — closes the line-drift gap from item #4 in
   `plugins/typescript/agents/typescript-audit-orchestrator.md` failure
   modes).
3. TDD: scenario tests at `l1` for each helper, then the implementation.
4. Refactor `plugins/typescript/skills/orchestrating-typescript-audit/SKILL.md`
   and `plugins/typescript/agents/typescript-audit-orchestrator.md` to invoke
   the module via `uv run python -m spec_tree.audit_orchestrator <subcommand>`
   (or whichever entry-point the ADR settles on).
5. Validate that downstream installs of `typescript@outcomeeng + spec-tree@outcomeeng`
   resolve the helper without requiring `outcomeeng/scripts/`.

The shell forms in the skill and agent are explicitly marked interim —
both files cite this issue as the migration destination.

**Also fold these deferred review items into the Python migration** (raised
during PR #9 round 3, surface-scoped to the agent prompt — they will dissolve
when the prompt is rewritten to call into the Python module rather than
embed protocol details inline):

- **Validation command discovery has no precedence.** SKILL.md Phase 0
  step 5 reads `CLAUDE.md`, `AGENTS.md`, `tsconfig.json`, `package.json`
  for the canonical validation command with no tie-breaker. Two consecutive
  runs on the same repo could discover commands in different orders and
  resolve different commands. Establish a priority order in the Python
  module (e.g. CLAUDE.md/AGENTS.md > justfile/Makefile > package.json
  scripts; closer to repo root wins).
- **Phase F "write LAST" ambiguity.** The agent's failure_modes "State
  written, audit incomplete" gloss spells out the Phase R ordering but
  not the Phase F ordering. An implementor reading Phase F's bare
  "Write the state file. Emit the wrapper verdict." steps could emit at
  step 4 and write at step 5, opening the partial-write window. The
  Python module should make the ordering structural rather than rely on
  prose discipline.
- **APPROVED first-run parsing.** Phase F step 2 assumes a Findings table
  to parse for `next_finding_id` derivation. APPROVED first runs from the
  underlying skill have no Findings section. The Python module's state
  initializer should handle the no-findings case explicitly (start
  `next_finding_id` at 1).
- **Concern 6 "Determinism contract" is always PASS.** A verdict row
  that cannot REJECT is decorative. Either remove it from the verdict
  table and surface scope-hash and frozen-scope-size as metadata on the
  verdict header, or give it a real REJECT condition such as "REJECT if
  the file list read during Phase 3 differs from the one captured at
  Phase 0" (scope drift detection). The Python module should pick one
  and commit.
