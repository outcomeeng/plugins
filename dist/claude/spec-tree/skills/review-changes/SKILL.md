---
name: review-changes
description: ALWAYS invoke this skill when reviewing working changes on a branch against a base ref. NEVER review changes by hand-formatting JSON or by reading persisted review artifacts directly.
allowed-tools:
  - Bash
  - Grep
  - Glob
  - Read
---

<objective>
A validated review-result JSON document for the working diff, recorded on `spx journal --type review`, with the human-readable surface rendered from the sealed event prefix.
</objective>

<api_surface>

Five entry points under `${CLAUDE_SKILL_DIR}/scripts/` plus prompt and render-template references:

| Entry point                                       | Effect                                                                                                                                                                  |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/compute_diff.py`                         | Resolve `base_ref` (env -> git origin/HEAD) and `head_ref` (env -> default `HEAD`), write committed merge-base, staged, unstaged, and untracked diff sections to stdout |
| `scripts/validate_review_result.py [--file PATH]` | Pipe a review-result JSON document through `review_result.parse_json`; exit 0 on conformance                                                                            |
| `scripts/render_review.py [--file PATH]`          | Parse validated review-result JSON through `review_result.parse_json`, write human-readable review content to stdout                                                    |
| `scripts/journal_emit.py`                         | Derive run metadata, map a review-result JSON document to review journal events, and render a sealed event prefix                                                       |
| `scripts/review_result.py`                        | Policy module — `SCHEMA_VERSION`, frozen dataclasses, enums, `parse_json` / `to_json_dict` / `from_json_dict`                                                           |
| `references/review-prompt.md`                     | Swappable judgment-style review prompt — read via `Read` into context                                                                                                   |
| `references/render/*.md`                          | Render templates loaded by `render_review.py` for the document, findings, acknowledgements, and empty severity buckets                                                  |

Durable review state is the sealed `spx journal --type review` event prefix. The skill never writes review-result or rendered markdown files as authoritative artifacts.

</api_surface>

<workflow>

Claude drives the chain top-to-bottom. Every JSON document Claude emits passes through `validate_review_result.py` before any journal append. Claude invokes the chain with no required input; callers that need a non-default scope export `SPX_VERIFY_BASE_REF` and `SPX_VERIFY_HEAD_REF` before invoking the skill.

1. **Compute the diff** against the resolved base ref:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/compute_diff.py"
   ```

   On non-zero exit, read the stderr message — the script names every source it tried (env and git symbolic-ref) so the operator can populate one.

2. **Load the judgment-style prompt** into context:

   ```text
   Read ${CLAUDE_SKILL_DIR}/references/review-prompt.md
   ```

3. **Apply the prompt** to the diff plus any repository conventions already loaded; emit one `review-result.json` document conforming to the schema declared in `scripts/review_result.py`.

4. **Validate** the JSON through the arbiter. Pipe the emitted JSON in on stdin:

   ```bash
   printf '%s' "$REVIEW_RESULT_JSON" | python3 "${CLAUDE_SKILL_DIR}/scripts/validate_review_result.py"
   ```

   On non-zero exit, read the stderr message verbatim, repair the JSON (fix the missing key or the unknown enum value), and re-emit. **Do not** hand-check the JSON in agent prose — the arbiter is the single source of validity.

5. **Render** the human-readable surface from the validated JSON:

   ```bash
   printf '%s' "$REVIEW_RESULT_JSON" | python3 "${CLAUDE_SKILL_DIR}/scripts/render_review.py"
   ```

6. **Record the review run on the journal and read it back from the sealed prefix.**

   ```bash
   RUN_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   RUN_COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   RUN_METADATA=$(python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" metadata \
     --started-at "$RUN_STARTED_AT" \
     --completed-at "$RUN_COMPLETED_AT")
   RUN_TOKEN=$(spx journal open --type review \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["runToken"])')
   printf '%s' "$REVIEW_RESULT_JSON" \
     | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" build-events \
       --now "$RUN_COMPLETED_AT" \
       --metadata "$RUN_METADATA" \
     | while IFS= read -r EVENT; do
         printf '%s' "$EVENT" | spx journal append --type review --run "$RUN_TOKEN" >/dev/null
       done
   spx journal seal --type review --run "$RUN_TOKEN" >/dev/null
   REVIEW_RENDERED=$(spx journal read --type review --run "$RUN_TOKEN" --from 0 \
     | python3 "${CLAUDE_SKILL_DIR}/scripts/journal_emit.py" render)
   printf '%s\n' "$RUN_TOKEN"
   printf '%s\n' "$REVIEW_RENDERED" \
     | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data["countLine"]); print(data["surface"] if int(data["blocking"]) or int(data["debt"]) else "", end="")'
   ```

The append loop iterates a finite event list; it is not a polling wait. `render_review.py` and `journal_emit.py build-events` both parse through `review_result.parse_json`; an invalid result fails before any journal append.

7. **Surface the result to the caller.** Print, in order: the `spx journal --type review` run token; a one-line count by render class (`BLOCKING: <n>, DEBT: <n>` — render class is identity-mapped from severity); and, when any finding is present, the rendered review surface. When the review carries no finding, the run token and the count line suffice. The caller then handles every finding by validity and phase, never by severity.

</workflow>

<validate_as_arbiter>

Validate-as-arbiter is the contract for this skill. Claude emits JSON; the CLI is the only source of validity for that JSON; a non-zero exit is a re-emit signal, not a status to gloss over. Claude never:

- Hand-checks the required-key set or the enum membership.
- Appends journal events for a review-result JSON document that has not passed the arbiter.
- Treats agent prose as authoritative when the arbiter and the prose disagree.

Schema validation — required keys, enum membership, the path-style `rule` citation form — is enforced inside `review_result.parse_json` so direct Python callers that bypass the CLI still surface violations. The reviewer emits findings only — no decision or verdict — so the CLI's exit code is the single source of validity to read.

</validate_as_arbiter>

<constraints>

- Stdlib-only Python under `${CLAUDE_SKILL_DIR}/scripts/`. No third-party packages, no `outcomeeng_*` imports, no dependency on `uv` at runtime.
- Durable review state is written only through `spx journal --type review`. Only `compute_diff.py` shells out for `git diff` / `git ls-files`; `journal_emit.py metadata` shells out only through the shared changeset-scope helper to resolve branch and commit identity.
- The judgment-style review prompt lives only at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`. It is never embedded inside this SKILL.md or any `.py` file under `scripts/`.
- Frozen dataclasses (`Finding`, `ReviewResult`) cross the parse -> validate -> render boundary. Any attempt to mutate one between steps raises `FrozenInstanceError`.
- Never hand-format the journal event types, run-state field names, or rendered journal surface in skill prose — `journal_emit.py` and the shared projection own those shapes.

</constraints>

<failure_modes>

**Unvalidated JSON append.** Claude emits review-result JSON, assumes it is valid, and starts `spx journal append` without first running `validate_review_result.py`. The arbiter is the only validity source for review-result JSON. Return to Step 4, validate the exact payload, repair any stderr-reported issue, and append only after the arbiter exits 0.

**Hand-built journal events.** Claude writes a `com.outcomeeng.spx.journal.run.completed` event by hand or omits `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `scope`, or `status`. The shared projection owns event construction and terminal run-state shape. Re-run `journal_emit.py metadata` and `journal_emit.py build-events`; never compose event JSON in prose or shell fragments.

**Rendered artifact treated as state.** Claude writes `review-result.json` or rendered markdown to a local path and treats that file as the durable review record. Durable review state is the sealed `spx journal --type review` prefix. Keep rendered markdown as conversation output only; use `spx journal read --type review --run "$RUN_TOKEN" --from 0` for persisted state.

</failure_modes>

<success_criteria>

- [ ] Every invocation of `validate_review_result.py` exits 0 before any journal append.
- [ ] `spx journal read --type review --run "$RUN_TOKEN" --from 0` returns a sealed prefix whose terminal event includes `headSha`, `baseRef`, `baseSha`, `branchSlug`, `configDigest`, `scope`, and `status`.
- [ ] No script under `scripts/` imports a third-party package or calls a direct storage-write primitive.
- [ ] The swappable review prompt remains a standalone file at `references/review-prompt.md`; rotating the prompt does not require touching code.
- [ ] After journal seal, the chain reads the sealed prefix, renders through `journal_emit.py render`, and surfaces the run token, the `BLOCKING`/`DEBT` count line, and (when any finding is present) the rendered surface to the caller.

</success_criteria>
