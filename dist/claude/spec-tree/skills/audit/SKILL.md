---
name: audit
description: >-
  Generic end-to-end code-scope audit orchestration preloaded by audit agents.
  Dispatch the audit agent that fits the requested run surface; the main conversation
  reaches a generic audit only through an audit agent.
argument-hint: "[scope]"
arguments: request
allowed-tools: Read, Bash, Glob, Grep, Skill
---

<dispatch_gate>

This orchestration runs in an audit agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch `auditor` for a one-off run over the requested scope. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on the requested code scope against the governing spec-tree and language methodology: APPROVED, or REJECTED with each finding naming the artifact, violated rule, and evidence.

</objective>

<constraints>

Read-only over the audited code: this skill produces a wrapper verdict and records it on the `spx journal`; it never edits, fixes, commits, or modifies the audited project tree. Its writes are limited to journal append/seal operations the channel owns and temporary scratch files used to aggregate child verdicts. Subagents it dispatches are read-only too.

</constraints>

<input_contract>

The invocation request `$request` carries the audit scope and optional PR identity. Run the standard audit path over the requested scope. When `$request` carries `REPO` and `PR NUMBER`, stamp the wrapper metadata with target kind `pull-request` and `pullRequestNumber` so the journal backend can project prior audit runs for the same PR. Never read state from rendered PR comments; the journal is the audit source of truth.

</input_contract>

<determinism_contract>

1. **Frozen scope.** The file list captured in Phase 0 is the scope for the rest of the run; later phases never expand it. The scope hash from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py::compute_scope_hash` identifies this exact scope and travels in the wrapper verdict's metadata.
2. **Canonical verdict shape.** Every verdict conforms to the schema in `${CLAUDE_SKILL_DIR}/scripts/verdict.py`. The orchestrator's wrapper has one row (`determinism-contract`); per-language children have their own rows owned by the dispatched skill. Row names are never invented inline.
3. **Frozen finding catalog.** Findings are only created from violations of the rules the dispatched `audit-{lang}*` skills already enforce. Style preferences, taste-based critiques, and "could be cleaner" observations are NEVER findings.

If any mechanism cannot be applied, halt and report the obstacle — do not silently substitute a looser audit.

This skill is strictly read-only over the project. It uses `Read`, `Bash` (for git and scope derivation, the `spx journal` channel, and the stdlib helper scripts), `Glob`, and `Grep` — never `Write` or `Edit`, and never the project's validation or test commands. It does not write its verdict to a project path or any persisted location; the caller delivers it. The scratch files the emit phase uses to stage per-partition JSON for aggregation are ephemeral scratch space, not artifacts. Subagents invoked by this skill never create or modify files.

</determinism_contract>

<language_detection>

Partition the in-scope file list by file extension. The mapping from extension to language identifier is training-time knowledge for any LLM that can run this skill; no explicit table belongs in the orchestrator. For mixed-language scopes, run the protocol once per partition, collect each partition's verdict, and aggregate them via `aggregate_verdicts.py` into one wrapper verdict whose `children` array carries the per-language verdicts. Each partition's language identifier is the `<lang>` value substituted into the `audit-{lang}*` dispatch template.

The orchestrator never embeds language-specific tokens beyond the dispatch template `audit-{lang}*` and the language placeholder `<lang>` — the factoring rule that keeps this orchestrator language-neutral.

</language_detection>

<skill_map>

Each phase dispatches one skill from the `audit-{lang}*` trio per language partition:

| Phase | Concern            | Source                                |
| ----- | ------------------ | ------------------------------------- |
| 1     | Implementation     | Dispatch: `audit-{lang}`              |
| 2     | Test evidence      | Dispatch: `audit-{lang}-tests`        |
| 3     | ADR/PDR compliance | Dispatch: `audit-{lang}-architecture` |

The audit runs no deterministic verification of its own — it dispatches only the agentic concern audits. Deterministic verification (validate, test, evaluate) is the caller's responsibility on the changeset before dispatching the audit, and CI's over the whole repository. Re-running the project's validation or test commands inside every dispatched audit only re-pays a cost the caller already paid.

If any of the three dispatched skills is missing for the target language, halt before any phase runs with `missing required skill: audit-{lang}-{kind}`. The marketplace validation pipeline enforces that every language plugin ships the trio; runtime absence indicates an installation or build issue, not a methodology decision.

</skill_map>

<audit_workflow>

<phase number="0" name="prepare">

1. **Determine scope.** The caller provides one of:
   - An explicit file list — use as-is. Directory scopes are not accepted here; callers expand directories before invoking audit.
   - A git ref or diff range (`HEAD`, `main..HEAD`, a branch name) — invoke `expand_diff_range(<range>, repo=Path('.'))` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py` to enumerate the files in the range.
   - No scope — invoke `uncommitted_scope(repo=Path('.'))` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py` to enumerate uncommitted, staged, **and untracked** changes (a fresh file added but not yet `git add`-ed is in scope). If the helper returns an empty list, halt with `no scope detected`. `expand_diff_range("HEAD", ...)` is **not** equivalent — it omits untracked files.

2. **Materialize the file list.** Filter to existing files. Sort lexicographically. This sorted list is the **frozen scope** for this run.

3. **Partition by language.** Group files by extension into per-language partitions. The remainder of the protocol runs once per partition; per-partition verdicts are aggregated in Phase 4 into one wrapper verdict whose `children` array carries them. If any partition's `audit-{lang}*` trio is missing, halt now with `missing required skill: audit-{lang}-{kind}` before any phase runs.

4. **Compute the scope hash.** Invoke `compute_scope_hash` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py`. Pass the frozen scope as `list[tuple[path, content]]`; the function returns a 12-character hex string. The hash identifies this exact scope and travels in the wrapper verdict's `metadata.scopeHash`.

5. **Read project config.** `CLAUDE.md`, `AGENTS.md`, and any language-native configuration the dispatched `audit-{lang}` skill expects.

6. **Read repo-local overlays.** `spx/local/audit.md` and `spx/local/audit-{lang}*.md` for each language in scope — read each that exists. Local overlays supersede the pre-loaded standards from the dispatched skill.

7. **Compute the config digest.** Invoke `config-digest` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py` over a stable newline-separated payload naming the repo-local overlays read and the language partitions. The digest identifies the run configuration and travels in the wrapper verdict's `metadata.configDigest`; never reuse the scope hash for this field.

Do not read source files for comprehension during Phase 0. Phase 0 only inventories.

</phase>

<phase number="1" name="implementation">

Dispatch to the partition's `audit-{lang}` skill for the implementation audit. That skill's protocol governs which files are read and how findings are emitted; this orchestrator does not re-do that work. Findings populate the child verdict's implementation row.

</phase>

<phase number="2" name="test-evidence">

Dispatch to `audit-{lang}-tests`. Findings populate the child verdict's test-evidence row.

</phase>

<phase number="3" name="adr-compliance">

Dispatch to `audit-{lang}-architecture`. Findings populate the child verdict's ADR/PDR-compliance row. If no ADRs or PDRs exist in the scope's ancestor tree, that row is N/A.

</phase>

<phase number="4" name="emit">

For each language partition, the dispatched skills emit JSON verdicts per the canonical schema in `${CLAUDE_SKILL_DIR}/scripts/verdict.py`. Stage each child verdict in a unique scratch directory created by `pass_results.py mkdir` (a `tempfile.mkdtemp`-backed unique path — two concurrent audit runs do not clobber each other) and write each partition's verdict JSON to its own file under that directory. The one orchestrator-owned row (`determinism-contract`) is passed to `aggregate_verdicts.py` as a `--row name=STATUS` argument — `determinism-contract` is PASS when Phase 0 produced a frozen scope plus scope hash without halts, UNKNOWN otherwise. The aggregator assembles one wrapper verdict whose `children` array carries the per-language verdicts. The wrapper verdict never touches disk — only the per-language children files do, because fanout (one orchestrator → N dispatched skills) demands a directory.

The agentic verification run is one append-only `spx journal` run that is its sole source of truth. Open the journal before dispatching any partition, append the scope-entered event immediately, then append scope-advanced and finding-reported events as each partition's child verdict returns. Append the terminal run-completed event from the streamed prefix, seal, then render from the sealed prefix. `${CLAUDE_SKILL_DIR}/scripts/journal_emit.py` builds one event at a time through the shared run-journal projection it consumes — the orchestrator never re-implements event construction, the rollup, or the render, and never hand-formats markdown. The journal's verification kind is the opaque `--type audit` segment; the backend is edge-resolved (a local run-journal file on a developer machine, the pull-request backend under CI), so the skill names no storage path.

```bash
CHILDREN_DIR=$(python3 "${CLAUDE_SKILL_DIR}/scripts/pass_results.py" mkdir)
RUN_TOKEN=''
AUDIT_JOURNAL_CLOSED=0
AUDIT_RUN_COMPLETED_APPENDED=0
finalize_audit_journal() {
  if [ -z "${RUN_TOKEN:-}" ] || [ "$AUDIT_JOURNAL_CLOSED" -eq 1 ]; then
    return
  fi
  RUN_COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if [ "$AUDIT_RUN_COMPLETED_APPENDED" -eq 0 ]; then
    spx journal read --type audit --run "$RUN_TOKEN" --from 0 \
      | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" run-completed \
        --metadata "$AUDIT_METADATA" \
        --completed-at "$RUN_COMPLETED_AT" \
        --now "$RUN_COMPLETED_AT" \
      | while IFS= read -r EVENT; do
          printf '%s' "$EVENT" | spx journal append --type audit --run "$RUN_TOKEN" >/dev/null
        done
    AUDIT_RUN_COMPLETED_APPENDED=1
  fi
  spx journal seal --type audit --run "$RUN_TOKEN" >/dev/null
  AUDIT_JOURNAL_CLOSED=1
}
# Caller owns cleanup unconditionally: the trap fires whether the run
# succeeds, an earlier dispatched skill halted, or the shell is interrupted.
# Once RUN_TOKEN is set, the same finalizer appends run-completed at most once
# and seals before removing scratch state.
# A plain `rm -rf` at the end of the block would leak $CHILDREN_DIR on every
# non-happy exit path; a completion-only seal would leave failed runs open.
# Caller-owned cleanup of a unique-per-invocation scratch dir plus terminal
# sealing is the portable run-state shape every agentic verification skill
# follows.
trap 'finalize_audit_journal; rm -rf "$CHILDREN_DIR"' EXIT

# Dispatched skills emit their per-partition verdict JSON to
# $CHILDREN_DIR/<language>.json (one file per language partition).
# Set --row determinism-contract to UNKNOWN when Phase 0 halted before
# producing a frozen scope; PASS otherwise. The audit runs no
# deterministic verification of its own, so it contributes no
# validation- or test-gate row.
#
# Stamp the journal run-state identity through the shared git derivation
# helpers. The base SHA is resolved through remote_tracking_ref, not by
# composing origin/<base> in prose.
RUN_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
BRANCH_NAME=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" current-branch)
BRANCH_SLUG=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" branch-slug \
  --branch "$BRANCH_NAME")
BASE_REF=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" base-ref)
BASE_REMOTE_REF=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" remote-tracking-ref \
  --base "$BASE_REF")
HEAD_SHA=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" commit-oid \
  --ref HEAD)
BASE_SHA=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" commit-oid \
  --ref "$BASE_REMOTE_REF")
SCOPE_HASH=$(printf '%s\n' <frozen-scope-paths> \
  | python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" scope-hash)
SCOPE_JSON=$(printf '%s\n' <frozen-scope-paths> \
  | python3 -c 'import json,sys; print(json.dumps({"include":[line for line in sys.stdin.read().splitlines() if line]}))')
CONFIG_DIGEST=$(printf '%s\n' <audit-config-digest-input-lines> \
  | python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" config-digest)
PARTICIPANTS_JSON='["audit"]'
OUTPUT_PATHS_JSON='[]'
TARGET_KIND='branch'
PULL_REQUEST_JOURNAL_ARGS=()
PULL_REQUEST_VERDICT_METADATA_ARGS=()
if [ -n "${PR_NUMBER:-}" ]; then
  TARGET_KIND='pull-request'
  PULL_REQUEST_JOURNAL_ARGS=(--pull-request-number "$PR_NUMBER")
  PULL_REQUEST_VERDICT_METADATA_ARGS=(--metadata pullRequestNumber="$PR_NUMBER")
fi

AUDIT_METADATA=$(python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" metadata \
  --target <scope-target> \
  --scope-hash "$SCOPE_HASH" \
  --branch-name "$BRANCH_NAME" \
  --branch-slug "$BRANCH_SLUG" \
  --head-sha "$HEAD_SHA" \
  --base-ref "$BASE_REF" \
  --base-sha "$BASE_SHA" \
  --config-digest "$CONFIG_DIGEST" \
  --participants-json "$PARTICIPANTS_JSON" \
  --scope-json "$SCOPE_JSON" \
  --started-at "$RUN_STARTED_AT" \
  --completed-at "$RUN_STARTED_AT" \
  --output-paths-json "$OUTPUT_PATHS_JSON" \
  --target-kind "$TARGET_KIND" \
  "${PULL_REQUEST_JOURNAL_ARGS[@]}")

RUN_TOKEN=$(spx journal open --type audit \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["runToken"])')

python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" scope-entered \
  --metadata "$AUDIT_METADATA" \
  --now "$RUN_STARTED_AT" \
  | while IFS= read -r EVENT; do
      printf '%s' "$EVENT" | spx journal append --type audit --run "$RUN_TOKEN" >/dev/null
    done

# Immediately after each partition's three audit-{lang}* phases return and
# $CHILD_JSON exists, append that partition's progress and finding events.
CHILD_JSON="$CHILDREN_DIR/<language>.json"
PARTITION_COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" scope-advanced \
  --unit "<language>" \
  --now "$PARTITION_COMPLETED_AT" \
  | while IFS= read -r EVENT; do
      printf '%s' "$EVENT" | spx journal append --type audit --run "$RUN_TOKEN" >/dev/null
    done
python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" findings-reported \
  --now "$PARTITION_COMPLETED_AT" \
  < "$CHILD_JSON" \
  | while IFS= read -r EVENT; do
      printf '%s' "$EVENT" | spx journal append --type audit --run "$RUN_TOKEN" >/dev/null
    done

# Assemble the wrapper verdict. This is the run's verdict artifact.
WRAPPER_JSON=$(python3 "${CLAUDE_SKILL_DIR}/scripts/aggregate_verdicts.py" \
  --directory "$CHILDREN_DIR" \
  --row determinism-contract=PASS \
  --skill audit \
  --target <scope-target> \
  --metadata scopeHash="$SCOPE_HASH" \
  --metadata branchName="$BRANCH_NAME" \
  --metadata branchSlug="$BRANCH_SLUG" \
  --metadata headSha="$HEAD_SHA" \
  --metadata baseRef="$BASE_REF" \
  --metadata baseSha="$BASE_SHA" \
  --metadata configDigest="$CONFIG_DIGEST" \
  --metadata participants="$PARTICIPANTS_JSON" \
  --metadata scope="$SCOPE_JSON" \
  --metadata startedAt="$RUN_STARTED_AT" \
  --metadata outputPaths="$OUTPUT_PATHS_JSON" \
  --metadata targetKind="$TARGET_KIND" \
  "${PULL_REQUEST_VERDICT_METADATA_ARGS[@]}")
printf '%s\n' "$WRAPPER_JSON"

finalize_audit_journal
spx journal read --type audit --run "$RUN_TOKEN" --from 0 \
  | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" render
```

The append loops consume finite event streams emitted by the adapter — no `sleep`, no condition retry. The wrapper JSON is emitted exactly once, then the sealed journal projection is emitted after it. The `EXIT` trap seals any opened audit journal through the same run-completed projection path before deleting scratch state, so an early halt still records a terminal event and seal. The journal is the run's source of truth; the rendered `{overall, surface}` is a projection of the sealed prefix, never authoritative state.

</phase>

</audit_workflow>

<verdict_format>

The canonical schema is declared in `${CLAUDE_SKILL_DIR}/scripts/verdict.py` (`Status`, `Severity`, `Finding`, `Row`, `Verdict` dataclasses). Treat `verdict.py` as authoritative for every field; the abbreviated shape below shows the orchestrator-specific wrapper values only.

```json
{
  "schema_version": 1,
  "skill": "audit",
  "target": "<scope-target>",
  "overall": "APPROVED | REJECTED | UNKNOWN",
  "rows": [
    {"name": "determinism-contract", "status": "PASS | FAIL | UNKNOWN", "findings": []}
  ],
  "children": [
    { "skill": "audit-{lang}*", "overall": "PASS | FAIL | UNKNOWN", "rows": [...] }
  ],
  "metadata": {
    "scopeHash": "<12-char-hex>",
    "branchName": "<branch>",
    "branchSlug": "<branch-slug>",
    "headSha": "<head-oid>",
    "baseRef": "<base-ref>",
    "baseSha": "<base-oid>",
    "configDigest": "<config-digest>",
    "participants": "[\"audit\"]",
    "scope": "{\"include\":[\"<path>\"]}",
    "startedAt": "<utc-timestamp>",
    "outputPaths": "[]"
  },
  "resolved": [],
  "reopened": []
}
```

The full wire format always carries `schema_version`, `skill`, `target`, `overall`, `rows`, `children`, `metadata`, `resolved`, and `reopened`. Each `Row` carries `name`, `status`, and `findings`; each `Finding` carries `id`, `file`, `line`, `rule`, `severity`, and `message`. The wrapper's single row is the orchestrator-owned determinism concern. Per-language implementation, test-evidence, and ADR/PDR concerns live inside the children's `rows` arrays — dispatched skills own those. The audit contributes no deterministic validation- or test-gate row: deterministic verification is the caller's on the changeset before dispatch and CI's over the whole repository.

Two `overall` vocabularies coexist: the **orchestrator wrapper** carries `APPROVED` / `REJECTED` / `UNKNOWN` (root-level decision); each **dispatched child** carries `PASS` / `FAIL` / `UNKNOWN` (skill-level contribution). The split is grounded in `verdict.py`'s `ROOT_STATUSES` vs `SKILL_STATUSES` sets. Row statuses use the skill-level vocabulary regardless of where the row sits, since a row is always one skill's contribution.

Overall rollup follows `verdict.roll_up`: APPROVED iff every wrapper row and every child is PASS or APPROVED; REJECTED if any row is FAIL or any child is REJECTED/FAIL; UNKNOWN if some row or child is UNKNOWN and none are FAIL/REJECTED.

</verdict_format>

<failure_modes>

**Improvised scope hashing.** Claude computes the scope hash in-prose (e.g., concatenating paths and contents in some ad hoc framing) instead of calling `compute_scope_hash` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py`. Distinct file lists then collide on the same hash because the framing is ambiguous. The helper module is the boundary; never reproduce its logic inline.

**Scope drift mid-run.** Files added or removed between Phase 0 and Phase 4 yield inconsistent reads — one phase sees a file the next phase doesn't. The "frozen scope" invariant exists to prevent this: Phase 0 captures the file list once; later phases never re-enumerate. If a phase needs a file not in the frozen scope, halt and report; do not silently expand scope.

**Mid-phase halt without trio verification.** Claude reaches Phase 2, finds `audit-{lang}-tests` missing, and halts there — but Phase 1 (`audit-{lang}`) already dispatched, producing a partial verdict. The trio check belongs in Phase 0 step 3 (partition-by-language), before any phase runs. Halt with `missing required skill: audit-{lang}-{kind}` before Phase 1 dispatches.

**Re-running deterministic verification.** Claude runs the project's validation or test command inside the audit to "confirm" the changeset. The audit dispatches only the agentic concern audits; the caller passed deterministic verification on the changeset before dispatching, and CI re-runs it over the whole repository. Re-running it inside every dispatched audit multiplies cost for no new signal.

**Dropped partition in mixed-language scope.** Claude treats a mixed-language scope as one audit, dispatches to whichever language has a plurality of files, and silently skips the others. The contract is one dispatched verdict per partition aggregated into one wrapper; never drop a partition. If a partition's `audit-{lang}*` skills do not exist, halt with the missing-skill error before any phase runs.

**Hand-formatted verdict.** Claude emits a markdown verdict directly into the conversation instead of recording the run on the `spx journal` and reading the verdict back through `journal_emit.py render`. The shared projection owns the rollup and the render; the orchestrator owns only the wrapper JSON shape. Re-read `<verdict_format>` and the Phase 4 emit instructions if uncertain.

**Re-implemented rollup.** Claude computes the wrapper's overall by reading the children's rows and deciding APPROVED/REJECTED in-prose. The rollup lives in `verdict.roll_up`; `aggregate_verdicts.py` invokes it. Never re-implement the rollup logic inline.

</failure_modes>

<success_criteria>

- One wrapper verdict emitted, with one child verdict per language partition in the frozen scope.
- The wrapper has one orchestrator-owned row (`determinism-contract`) and one child per partition; the audit runs no deterministic verification and contributes no validation- or test-gate row.
- The wrapper's `overall` is APPROVED, REJECTED, or UNKNOWN per `verdict.roll_up` applied to wrapper rows plus children overalls.
- The journal-rendered verdict and wrapper JSON agree on overall status, row statuses, child verdicts, finding content, resolved entries, and reopened entries.
- Pull-request audit runs stamp `pullRequestNumber` and target kind into wrapper metadata and read prior state through the journal backend, never from rendered PR comments.
- Resolved/reopened projection uses content identity `(file, line, rule, message)` and treats a first PR run as empty prior state.
- The orchestrator's prose contains zero language-specific tokens beyond the dispatch template `audit-{lang}*` and the language placeholder `<lang>`.
- The scope hash is reproducible: re-running the skill on the same frozen scope produces the same hash.
- If the run halts, the halt reason is reported on `determinism-contract` (UNKNOWN): an empty scope or a missing `audit-{lang}*` trio is a Phase 0 halt before a frozen scope exists, and no dispatch phase runs.

</success_criteria>
