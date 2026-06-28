---
name: review-changes
description: ALWAYS invoke this skill when reviewing working changes on a branch against a base ref. NEVER review changes by hand-formatting JSON or by reading persisted review artifacts directly.
allowed-tools:
  - Bash(date:*)
  - Bash(mktemp:*)
  - Bash(printf:*)
  - Bash(python3:*)
  - Bash(rm -rf:*)
  - Bash(spx journal open:*)
  - Bash(spx journal append:*)
  - Bash(spx journal read:*)
  - Bash(spx journal seal:*)
  - Grep
  - Glob
  - Read
---

<objective>
A review run recorded as a sealed `spx journal --type review` event prefix, with the human-readable findings surface rendered from that prefix.
</objective>

<api_surface>

Two CLI scripts plus the policy module under `${CLAUDE_SKILL_DIR}/scripts/` and the prompt reference:

| Entry point                                       | Effect                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `${CLAUDE_SKILL_DIR}/scripts/compute_diff.py`     | Resolve `base_ref` (env -> git origin/HEAD) and `head_ref` (env -> default `HEAD`), write committed merge-base, staged, unstaged, and untracked diff sections to stdout or to a caller-owned scratch bundle outside the git worktree (`diff.md`, `manifest.json`)                                                  |
| `${CLAUDE_SKILL_DIR}/scripts/journal_emit.py`     | `metadata --manifest <manifest.json>` derives run identity from the computed review bundle; `scope-entered` / `scope-advanced` / `finding-reported` / `run-completed` each print one streaming journal event (the per-finding parse is the validity gate); `render` renders the human surface from a sealed prefix |
| `${CLAUDE_SKILL_DIR}/scripts/review_result.py`    | Policy module — `SCHEMA_VERSION`, frozen dataclasses, enums, `parse_json` / `parse_finding_json` / `to_json_dict` / `from_json_dict`                                                                                                                                                                               |
| `${CLAUDE_SKILL_DIR}/references/review-prompt.md` | Swappable judgment-style review prompt — read via `Read` into context                                                                                                                                                                                                                                              |
| `REVIEW.md` at repository root                    | Repository-local review override — read via `Read` when present and applied before the judgment prompt                                                                                                                                                                                                             |

Durable review state is the sealed `spx journal --type review` event prefix, and the human-readable surface is rendered only from that sealed prefix — the journal is the review's sole source of truth. The skill never writes review-result or rendered markdown files as authoritative artifacts, and no script renders a parallel surface. The run **streams** its events live — it never builds one batch of events from a finished review, so a reader resuming from a cursor watches the review advance in flight. `journal_emit.py finding-reported` parses each finding through `review_result.parse_finding_json` and fails before that finding's append, and the journal channel's append and seal are the durable validity signal — matching the audit kind. The diff bundle is caller-owned scratch review input for random access; it is not durable review state. `journal_emit.py metadata` reads that bundle's `manifest.json` so the terminal run state's `scope.changedFiles` and `scope.reviewInputSha256` match the exact diff bundle the reviewer examined.

</api_surface>

<workflow>

Claude drives the chain top-to-bottom and **streams the run live** — appending each event the moment the run reaches it, never gathering a finished review and dumping its events at the end. `journal_emit.py finding-reported` parses each finding Claude emits through `review_result.parse_finding_json` and fails before that finding's append, so the per-finding parse is the validity gate. Claude invokes the chain with no required input; callers that need a non-default scope export `SPX_VERIFY_BASE_REF` and `SPX_VERIFY_HEAD_REF` before invoking the skill.

1. **Compute the diff** against the resolved base ref into a caller-owned scratch bundle:

   ```bash
   REVIEW_INPUT_DIR=$(mktemp -d)
   REVIEW_INPUT_SUMMARY=$(python3 "${CLAUDE_SKILL_DIR}/scripts/compute_diff.py" \
     --bundle-dir "$REVIEW_INPUT_DIR")
   ```

   On non-zero exit, read the stderr message — the script names every source it tried (env and git symbolic-ref) so the operator can populate one.
   Read `manifest.json` from the reported `manifest_path`, then read `diff.md` from the reported `diff_path`. Use the manifest's section spans and file lists to revisit only the relevant diff section while reviewing. The scratch directory is owned by this invocation and is removed after the run is sealed and rendered.

2. **Load repository-local review instructions and the judgment-style prompt** into context. If `REVIEW.md` exists at the repository root, read it first and apply it as the repository-local review override for taxonomy guidance and repository-specific review rules. It does not override the `Finding` JSON schema, required keys, severity and concern enums, or the journal-rendered output shape. Read only the active root override; do not search for review template or example files. Then read the swappable prompt:

   ```text
   Read REVIEW.md  (only when present at repository root)
   Read ${CLAUDE_SKILL_DIR}/references/review-prompt.md
   ```

3. **Open the run and derive its identity at the start**, then append the scope-entered event:

   ```bash
   RUN_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   REVIEW_MANIFEST=$(printf '%s' "$REVIEW_INPUT_SUMMARY" \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["manifest_path"])')
   RUN_METADATA=$(python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" metadata \
     --started-at "$RUN_STARTED_AT" --manifest "$REVIEW_MANIFEST")
   RUN_TOKEN=$(spx journal open --type review \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["runToken"])')
   python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" scope-entered \
     --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --metadata "$RUN_METADATA" \
     | spx journal append --type review --run "$RUN_TOKEN" >/dev/null
   ```

4. **Apply the prompt and stream the run while reviewing.** Work through the changed files listed in the bundle manifest. As each changed file is examined, append a scope-advanced event naming it; the instant a finding is raised, emit that one finding as a JSON object conforming to the `Finding` schema in `${CLAUDE_SKILL_DIR}/scripts/review_result.py` and append its finding-reported event. Do not gather findings into one document and append them at the end.

   ```bash
   # As you examine each changed file:
   python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" scope-advanced \
     --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --unit "<changed-file>" \
     | spx journal append --type review --run "$RUN_TOKEN" >/dev/null

   # The instant you raise a finding ($FINDING_JSON is one Finding object).
   # finding-reported is the validity gate: it prints the event only on a
   # successful parse and exits non-zero otherwise. Append ONLY when the gate
   # succeeds, so a failed parse never lets `spx journal append` run on empty
   # output.
   if FINDING_EVENT=$(printf '%s' "$FINDING_JSON" \
       | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" finding-reported \
         --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)"); then
     printf '%s' "$FINDING_EVENT" \
       | spx journal append --type review --run "$RUN_TOKEN" >/dev/null
   fi
   ```

   `finding-reported` parses the one finding; on a non-zero exit read the stderr message verbatim, repair the finding JSON (the missing key or unknown enum value), and re-emit before appending. Appending only the events the builders print, never hand-composed JSON.

5. **Close the run and read it back from the sealed prefix.** `run-completed` reads the streamed prefix and derives the terminal status from it; the render is the review's only human-readable surface — a projection of the sealed events.

   ```bash
   RUN_COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   spx journal read --type review --run "$RUN_TOKEN" --from 0 \
     | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" run-completed \
       --now "$RUN_COMPLETED_AT" --completed-at "$RUN_COMPLETED_AT" --metadata "$RUN_METADATA" \
     | spx journal append --type review --run "$RUN_TOKEN" >/dev/null
   spx journal seal --type review --run "$RUN_TOKEN" >/dev/null
   REVIEW_RENDERED=$(spx journal read --type review --run "$RUN_TOKEN" --from 0 \
     | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" render)
   printf '%s\n' "$RUN_TOKEN"
   printf '%s\n' "$REVIEW_RENDERED" \
     | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data["countLine"]); print(data["surface"] if int(data["blocking"]) or int(data["debt"]) else "", end="")'
   rm -rf "$REVIEW_INPUT_DIR"
   ```

   Each append is one event the run has reached; this is streaming, not a polling wait.

6. **Surface the result to the caller.** Print, in order: the `spx journal --type review` run token; a one-line count by render class (`BLOCKING: <n>, DEBT: <n>` — render class is identity-mapped from severity); and, when any finding is present, the rendered review surface. When the review carries no finding, the run token and the count line suffice. The caller then handles every finding by validity and phase, never by severity.

</workflow>

<validity_at_parse>

Validity comes from the per-finding `journal_emit.py finding-reported` parse. When `finding-reported` parses a finding through `review_result.parse_finding_json` — required keys, enum membership, the path-style `rule` citation form — a non-zero exit is a re-emit signal, not a status to gloss over. Claude never:

- Hand-checks the required-key set or the enum membership in agent prose.
- Appends a finding-reported event for a finding that did not parse.
- Treats agent prose as authoritative when the parse error and the prose disagree.

Emit findings only — no summary, acknowledgement, decision, or verdict — and the journal channel's append and seal are the durable validity signal for the recorded run, matching the audit kind.

</validity_at_parse>

<constraints>

- Stdlib-only Python under `${CLAUDE_SKILL_DIR}/scripts/`. No third-party packages, no `outcomeeng_*` imports, no dependency on `uv` at runtime.
- Durable review state is written only through `spx journal --type review`. `compute_diff.py --bundle-dir` may write only caller-owned scratch review-input files. Only `compute_diff.py` shells out for `git diff` / `git ls-files`; `journal_emit.py metadata` shells out only through the shared changeset-scope helper to resolve branch and commit identity.
- The judgment-style review prompt lives only at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`. It is never embedded inside this SKILL.md or any `.py` file under `scripts/`.
- Frozen dataclasses (`Finding`, `ReviewResult`) cross the parse boundary as values. Any attempt to mutate one between steps raises `FrozenInstanceError`.
- Never hand-format the journal event types, run-state field names, or rendered journal surface in skill prose — `journal_emit.py` and the shared projection own those shapes.

</constraints>

<failure_modes>

**Batch dump at the end.** Claude gathers every finding into one document and appends all the events at the end of the review, instead of appending each event the moment the run reaches it. That is the opaque-run shape the run-journal contract forbids: stream the events live — scope-entered at the start, a scope-advanced per examined file, a finding-reported the instant each finding is raised, run-completed at the end.

**Unparsed finding append.** Claude composes a finding-reported event by hand and appends it without running the finding through `journal_emit.py finding-reported`, skipping the parse that rejects a malformed finding. `finding-reported` is the validity gate: it parses the one finding and exits non-zero before printing any event. Always pipe each finding through `finding-reported`; append only the event it produces, and repair any stderr-reported issue before re-running.

**Hand-built journal events.** Claude writes a `com.outcomeeng.spx.journal.run.completed` event by hand or omits `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `scope`, or `status`. The shared projection owns event construction and terminal run-state shape. Re-run `journal_emit.py metadata` and `journal_emit.py run-completed`; never compose event JSON in prose or shell fragments.

**Rendered artifact treated as state.** Claude writes `review-result.json` or rendered markdown to a local path and treats that file as the durable review record. Durable review state is the sealed `spx journal --type review` prefix. Keep rendered markdown as conversation output only; use `spx journal read --type review --run "$RUN_TOKEN" --from 0` for persisted state.

**Scratch bundle retained as state.** Claude leaves the diff bundle behind or treats `manifest.json` as a review record. The bundle is caller-owned scratch input for one invocation. Remove it after the journal is sealed and rendered; read durable facts from the journal.

</failure_modes>

<success_criteria>

- [ ] The run streams its events live — scope-entered, a scope-advanced per examined file, a finding-reported the instant each finding is raised, run-completed — never one batch built from a finished review.
- [ ] `journal_emit.py finding-reported` parses each finding and exits 0 before that finding's append; a parse failure is repaired and re-emitted, never appended.
- [ ] `spx journal read --type review --run "$RUN_TOKEN" --from 0` returns a sealed prefix whose terminal event includes `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `scope`, and `status`.
- [ ] No script under `scripts/` imports a third-party package or writes durable review state outside the journal; `compute_diff.py --bundle-dir` writes only caller-owned scratch `diff.md` and `manifest.json` outside the git worktree.
- [ ] The swappable review prompt remains a standalone file at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`; rotating the prompt does not require touching code.
- [ ] After journal seal, the chain reads the sealed prefix, renders through `journal_emit.py render`, and surfaces the run token, the `BLOCKING`/`DEBT` count line, and (when any finding is present) the rendered surface to the caller.

</success_criteria>
