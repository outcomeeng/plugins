---
name: auditing
description: >-
  ALWAYS invoke this skill when running an audit pass over a code scope. Produces one structured APPROVED or REJECTED verdict per language partition, dispatching to language-specific auditing-{lang}* skills. NEVER use this skill to write code.
allowed-tools: Read, Bash, Glob, Grep
---

<objective>

Run a deterministic audit over a code scope: prepare (Phase 0), automated gates (Phase 1), tests (Phase 2), implementation review (Phase 3), test evidence (Phase 4), ADR/PDR compliance (Phase 5), and emit (Phase 6). Partition the scope by language, dispatch to the corresponding `auditing-{lang}*` skills, and emit one structured verdict per language partition. The orchestrator itself embeds zero language-specific knowledge beyond the dispatch template — language audits live in their own skills, this one composes them.

Read-only. Produces verdicts, not code changes.

</objective>

<determinism_contract>

1. **Frozen scope.** The file list captured in Phase 0 is the scope for the rest of the run; later phases never expand it. The scope hash from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py::compute_scope_hash` identifies this exact scope.
2. **Frozen concern table.** Every verdict has the same six rows in the same order (see `<verdict_format>`). Concerns are never added, removed, renamed, or reordered to fit a particular audit.
3. **Frozen finding catalog.** Findings are only created from violations of the rules the dispatched `auditing-{lang}*` skills already enforce. Style preferences, taste-based critiques, and "could be cleaner" observations are NEVER findings.

If any mechanism cannot be applied, halt and report the obstacle — do not silently substitute a looser audit.

This skill is strictly read-only. It uses `Read`, `Bash` (for git, project validation, and tests), `Glob`, and `Grep` — never `Write` or `Edit`. The skill does not persist its verdict and does not create the `.spx/audits/` directory. Re-run determinism depends on the **caller** writing the emitted verdict to a known path; the skill only reads from such a path when one already exists. The Subagent Restrictions section of `AGENTS.md` requires subagents never to create or modify files.

</determinism_contract>

<language_detection>

Partition the in-scope file list by file extension. The mapping from extension to language identifier is training-time knowledge for any LLM that can run this skill; no explicit table belongs in the orchestrator. For mixed-language scopes, run the protocol once per partition and emit one verdict per partition. Each partition's language identifier is the `<lang>` value substituted into the `auditing-{lang}*` dispatch template.

The orchestrator never embeds language-specific tokens beyond the dispatch template `auditing-{lang}*` and the language path-segment placeholder `<lang>` in state-file paths. See `spx/21-spec-tree.enabler/17-auditing.adr.md` for the factoring rule.

</language_detection>

<skill_map>

For each language partition, each phase invokes one of two sources — a project-local command discovered in Phase 0, or a dispatched skill from the `auditing-{lang}*` trio:

| Phase | Concern            | Source                                               |
| ----- | ------------------ | ---------------------------------------------------- |
| 1     | Automated gates    | Project's canonical validation command (no dispatch) |
| 2     | Test execution     | Project's canonical test command (no dispatch)       |
| 3     | Implementation     | Dispatch: `auditing-{lang}`                          |
| 4     | Test evidence      | Dispatch: `auditing-{lang}-tests`                    |
| 5     | ADR/PDR compliance | Dispatch: `auditing-{lang}-architecture`             |

Phases 1 and 2 run the project's own commands as discovered in Phase 0 step 6; the orchestrator does not dispatch to a skill for those rows. Phases 3, 4, and 5 dispatch to the language-specific trio.

If any of the three dispatched skills is missing for the target language, halt before any phase runs with `missing required skill: auditing-{lang}-{kind}`. The marketplace validation pipeline enforces that every language plugin ships the trio; runtime absence indicates an installation or build issue, not a methodology decision.

</skill_map>

<process>

<phase number="0" name="prepare">

1. **Determine scope.** The caller provides one of:
   - An explicit file or directory list — use as-is.
   - A git ref or diff range (`HEAD`, `main..HEAD`, a branch name) — invoke `expand_diff_range(<range>, repo=Path('.'))` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py` to enumerate the files in the range.
   - No scope — invoke `expand_diff_range("HEAD", repo=Path('.'))` to enumerate uncommitted + staged changes. If the helper returns an empty list, halt with `no scope detected`.

2. **Materialize the file list.** Filter to existing files. Sort lexicographically. This sorted list is the **frozen scope** for this run.

3. **Partition by language.** Group files by extension into per-language partitions. The remainder of the protocol runs once per partition and emits one verdict per partition.

4. **Compute the scope hash.** Invoke `compute_scope_hash` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py`. Pass the frozen scope as `list[tuple[path, content]]`; the function returns a 12-character hex string. The hash identifies this exact scope and is used to look up any prior verdict in step 5.

5. **Read prior verdict if staged.** Look for the verdict file at the path the caller indicates (typically `.spx/audits/<lang>/<scope-hash>.md` for direct invocation, or `.spx/audits/<lang>/<branch-slug>.md` when invoked by the `auditor` agent). If found, read it — see `<re_run_protocol>`. If absent, this is a fresh run. The skill never creates this file; it only reads one the caller has placed there from a previous run.

6. **Read project config.** `CLAUDE.md`, `AGENTS.md`, and any language-native configuration the dispatched `auditing-{lang}` skill expects. Identify the canonical validation command and the canonical test command for the project (the precedence convention in marketplace projects: `CLAUDE.md`/`AGENTS.md` → `justfile`/`Makefile` → language-native config; closer to repo root wins). If neither is discoverable from project files, halt — do not guess.

7. **Read repo-local overlays.** `spx/local/auditing.md` and `spx/local/auditing-{lang}*.md` for each language in scope — read each that exists. Local overlays supersede the pre-loaded standards from the dispatched skill.

Do not read source files for comprehension during Phase 0. Phase 0 only inventories.

</phase>

<phase number="1" name="automated-gates">

Run the project's canonical validation command (discovered in Phase 0 step 6). Any non-zero exit code is REJECT for row 1. Halt before subsequent phases — rows 2–6 are not evaluated.

</phase>

<phase number="2" name="test-execution">

Run the project's canonical test command. Any failure is REJECT for row 2. Halt before subsequent phases.

</phase>

<phase number="3" name="implementation">

Dispatch to the partition's `auditing-{lang}` skill for the implementation audit. That skill's protocol governs which files are read and how findings are emitted; this orchestrator does not re-do that work. Findings populate row 3.

</phase>

<phase number="4" name="test-evidence">

Dispatch to `auditing-{lang}-tests`. Findings populate row 4.

</phase>

<phase number="5" name="adr-compliance">

Dispatch to `auditing-{lang}-architecture`. Findings populate row 5. If no ADRs or PDRs exist in the scope's ancestor tree, row 5 is N/A.

</phase>

<phase number="6" name="emit">

Construct the verdict (see `<verdict_format>`) in memory, then emit it to the conversation. The orchestrator does not write the verdict to disk — the caller persists it if re-run determinism is required.

</phase>

</process>

<verdict_format>

Emit the verdict in this exact structure, one per language partition:

```markdown
# Audit — <language> — <APPROVED | REJECTED>

**Scope hash:** <12-char hex>
**Scope:** <file count> files
**Run type:** <fresh | re-run from <prior-hash>>

| # | Concern              | Status                |
| - | -------------------- | --------------------- |
| 1 | Automated gates      | PASS \| REJECT        |
| 2 | Test execution       | PASS \| REJECT        |
| 3 | Implementation       | PASS \| REJECT \| N/A |
| 4 | Test evidence        | PASS \| REJECT \| N/A |
| 5 | ADR/PDR compliance   | PASS \| REJECT \| N/A |
| 6 | Determinism contract | PASS                  |

## Findings (<count>)

| # | File:line     | Concern        | Root cause | Required fix |
| - | ------------- | -------------- | ---------- | ------------ |
| 1 | <path>:<line> | implementation | <one-line> | <one-line>   |

## Detail (per finding)

**Finding 1.** <2-4 sentences elaborating root cause and required fix>
```

The verdict is APPROVED iff every concern row is PASS or N/A. A single REJECT row makes the whole verdict REJECTED.

</verdict_format>

<re_run_protocol>

When the caller stages a prior verdict at a path keyed by the scope hash, Phase 0 reads it. If the prior verdict was APPROVED and the scope hash matches the new run, return the same APPROVED verdict without re-running phases 1–5 — the audit is stable by definition.

If the prior verdict was REJECTED, run the full audit. For every prior finding:

- If the issue is now absent from the code, mark the finding **RESOLVED** in the new verdict's "Resolved from prior run" section.
- If the issue persists, carry the finding forward with the same ID.

New findings introduced this run receive fresh IDs. Finding IDs are monotonic: a resolved finding's ID is never reused for a new finding.

The `auditor` agent wraps this skill with branch-keyed persistence (state file at `.spx/audits/<lang>/<branch-slug>.md`) so finding identity is preserved across the scope changes that come with each push. Direct callers of this skill use the content-keyed `<scope-hash>.md` path instead.

</re_run_protocol>

<failure_modes>

**Improvised scope hashing.** Claude computes the scope hash in-prose (e.g., concatenating paths and contents in some ad hoc framing) instead of calling `compute_scope_hash` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py`. Distinct file lists then collide on the same hash because the framing is ambiguous, breaking re-run determinism silently. The helper module is the boundary; never reproduce its logic inline.

**Scope drift mid-run.** Files added or removed between Phase 0 and Phase 5 yield inconsistent reads — one phase sees a file the next phase doesn't. The "frozen scope" invariant exists to prevent this: Phase 0 captures the file list once; later phases never re-enumerate. If a phase needs a file not in the frozen scope, halt and report; do not silently expand scope.

**Mid-phase halt without trio verification.** Claude reaches Phase 3, finds `auditing-{lang}` missing, and halts there — but Phase 1 (automated gates) and Phase 2 (tests) already ran and produced output that suggested the audit was in progress. The trio check belongs in Phase 0 step 3 (partition-by-language), before any phase runs. Halt with `missing required skill: auditing-{lang}-{kind}` before Phase 1 dispatches.

**Merged verdict for mixed-language scopes.** Claude treats a mixed-language scope as one audit, dispatches to whichever language has a plurality of files, and emits one verdict — silently dropping coverage of the other partitions' findings. The contract is one verdict per language partition; partition first, then loop the protocol per partition.

**Verdict-format drift.** Claude emits a verdict missing one of the six concern rows, or rearranges them, or relabels them ("Implementation" → "Code review"). The frozen concern table is part of the determinism contract — every verdict has the same six rows in the same order. Re-read `<verdict_format>` before emitting if uncertain.

</failure_modes>

<success_criteria>

- One verdict emitted per language partition in the frozen scope.
- Each verdict's six concern rows are evaluated and labeled.
- The verdict is APPROVED iff every row is PASS or N/A.
- The orchestrator's prose contains zero language-specific tokens beyond the dispatch template `auditing-{lang}*` and the language path-segment placeholder `<lang>`.
- The scope hash is reproducible: re-running the skill on the same frozen scope produces the same hash.

</success_criteria>
