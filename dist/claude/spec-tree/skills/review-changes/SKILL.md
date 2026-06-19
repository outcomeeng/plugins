---
name: review-changes
description: ALWAYS invoke this skill when reviewing working changes on a branch against a base ref. NEVER review changes by hand-formatting JSON or by reading thread-store records directly.
allowed-tools:
  - Bash
  - Read
---

<objective>
Compute the diff against the resolved base ref, apply the judgment-style review prompt, validate the emitted JSON through the arbiter CLI, and persist `review-result.json` plus a rendered `review.md` to the current thread. The arbiter is the source of validity; never hand-validate the emitted JSON, and never name the thread address.
</objective>

<api_surface>

Four entry points under `${CLAUDE_SKILL_DIR}/scripts/` plus prompt and render-template references:

| Entry point                                       | Effect                                                                                                                                                                                                                               |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `scripts/compute_diff.py`                         | Resolve current thread, `base_ref` (env -> optional `changes.json` -> git origin/HEAD) and `head_ref` (env -> `changes.json` -> default `HEAD`), write committed merge-base, staged, unstaged, and untracked diff sections to stdout |
| `scripts/validate_review_result.py [--file PATH]` | Pipe a review-result JSON document through `review_result.parse_json`; exit 0 on conformance                                                                                                                                         |
| `scripts/render_review.py`                        | Read `review-result.json` from the current thread, parse through the arbiter, write `review.md` content to stdout                                                                                                                    |
| `scripts/review_result.py`                        | Policy module — `SCHEMA_VERSION`, frozen dataclasses, enums, `parse_json` / `to_json_dict` / `from_json_dict`                                                                                                                        |
| `references/review-prompt.md`                     | Swappable judgment-style review prompt — read via `Read` into context                                                                                                                                                                |
| `references/render/*.md`                          | Render templates loaded by `render_review.py` for the document, findings, acknowledgements, and empty severity buckets                                                                                                               |

This skill uses the thread-store CLIs at `${CLAUDE_SKILL_DIR}/../manage-thread-store/scripts/` for every persistence call. Every thread-store CLI accepts an optional `--slug`; Claude omits it so the CLI resolves the thread via `thread_store.current_slug()` (env `SPX_VERIFY_BRANCH` -> git current branch).

</api_surface>

<chain>

Claude drives the chain top-to-bottom. Every filesystem effect routes through `thread_store`; every JSON document Claude emits passes through `validate_review_result.py` before any persistence call. Claude invokes the chain with no required input — an optional `changes.json` override may pre-exist in the thread to override the auto-derived `base_ref`.

1. **Compute the diff** against the resolved base ref:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/compute_diff.py"
   ```

   On non-zero exit, read the stderr message — the script names every source it tried (env, optional `changes.json` field, git symbolic-ref) so the operator can populate one.

2. **Load the judgment-style prompt** into context:

   ```text
   Read ${CLAUDE_SKILL_DIR}/references/review-prompt.md
   ```

3. **Apply the prompt** to the diff plus any repository conventions already loaded; emit one `review-result.json` document conforming to the schema declared in `scripts/review_result.py`.

4. **Validate** the JSON through the arbiter. Pipe the emitted JSON in on stdin:

   ```bash
   echo "$REVIEW_RESULT_JSON" | python3 "${CLAUDE_SKILL_DIR}/scripts/validate_review_result.py"
   ```

   On non-zero exit, read the stderr message verbatim, repair the JSON (fix the missing key or the unknown enum value), and re-emit. **Do not** hand-check the JSON in agent prose — the arbiter is the single source of validity.

5. **Persist** the validated `review-result.json`:

   ```bash
   echo "$REVIEW_RESULT_JSON" | python3 "${CLAUDE_SKILL_DIR}/../manage-thread-store/scripts/write_record.py" --name review-result.json
   ```

6. **Render** the human-readable surface and persist it:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_review.py" \
     | python3 "${CLAUDE_SKILL_DIR}/../manage-thread-store/scripts/write_record.py" --name review.md
   ```

`render_review.py` re-parses `review-result.json` through `review_result.parse_json` before emitting; an invalid result fails the render with a non-zero exit before any markdown is produced.

</chain>

<validate_as_arbiter>

Validate-as-arbiter is the contract for this skill. Claude emits JSON; the CLI is the only source of validity for that JSON; a non-zero exit is a re-emit signal, not a status to gloss over. Claude never:

- Hand-checks the required-key set or the enum membership.
- Persists a `review-result.json` document that has not passed the arbiter.
- Treats agent prose as authoritative when the arbiter and the prose disagree.

Schema validation — required keys, enum membership, the path-style `rule` citation form — is enforced inside `review_result.parse_json` so direct Python callers that bypass the CLI still surface violations. The reviewer emits findings only — no decision or verdict — so the CLI's exit code is the single source of validity to read.

</validate_as_arbiter>

<constraints>

- Stdlib-only Python under `${CLAUDE_SKILL_DIR}/scripts/`. No third-party packages, no `outcomeeng_*` imports, no dependency on `uv` at runtime.
- Every filesystem effect routes through the `thread_store` facade — no direct `open()`, `pathlib.Path.write_*`, or `os.remove` against the thread-store backend's storage paths. Only `compute_diff.py` shells out, and only to run `git diff` / `git ls-files` for the committed, staged, unstaged, and untracked review input sections.
- The judgment-style review prompt lives only at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`. It is never embedded inside this SKILL.md or any `.py` file under `scripts/`.
- Frozen dataclasses (`Finding`, `ReviewResult`) cross the parse -> validate -> render boundary. Any attempt to mutate one between steps raises `FrozenInstanceError`.

</constraints>

<success_criteria>

- [ ] Every invocation of `validate_review_result.py` exits 0 against every persisted `review-result.json`.
- [ ] `review-result.json` and `review.md` both exist under the current branch's slug in the thread store after the chain completes.
- [ ] No script under `scripts/` imports a third-party package or calls a direct filesystem primitive against the backend's storage paths.
- [ ] The swappable review prompt remains a standalone file at `references/review-prompt.md`; rotating the prompt does not require touching code.

</success_criteria>
