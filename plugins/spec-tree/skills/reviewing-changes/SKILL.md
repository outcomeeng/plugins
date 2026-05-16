---
name: reviewing-changes
description: ALWAYS invoke this skill when the wrapper agent reviews the working changes on a branch against the PR's base ref. NEVER review changes by hand-formatting JSON or by reading thread-store records directly.
allowed-tools: Bash, Read
---

<objective>
Drive the reviewing-changes lens — read the branch's `pr.json`, compute the diff against the base ref, apply the judgment-style review prompt, validate the emitted JSON through the arbiter CLI, and persist `review-result.json` plus a rendered `review.md` under the branch slug. The arbiter is the source of validity; the wrapper agent never hand-validates the JSON it just emitted.
</objective>

<api_surface>

Four entry points under `${CLAUDE_SKILL_DIR}/scripts/` and one swappable prompt under `${CLAUDE_SKILL_DIR}/references/`:

| Entry point                                       | Effect                                                                                                        |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `scripts/compute_diff.py --slug <slug>`           | Read `pr.json` from the thread store, run `git diff <baseRefName>..HEAD`, write the diff to stdout            |
| `scripts/validate_review_result.py [--file PATH]` | Pipe a review-result JSON document through `review_result.parse_json`; exit 0 on conformance                  |
| `scripts/render_review.py --slug <slug>`          | Read `review-result.json`, parse through the arbiter, write `review.md` content to stdout                     |
| `scripts/review_result.py`                        | Policy module — `SCHEMA_VERSION`, frozen dataclasses, enums, `parse_json` / `to_json_dict` / `from_json_dict` |
| `references/review-prompt.md`                     | Swappable judgment-style review prompt — read via `Read` into the agent's context                             |

The lens uses the thread-store CLIs at `${CLAUDE_SKILL_DIR}/../thread-store/scripts/` for every persistence call.

</api_surface>

<chain>

The wrapper agent drives the chain top-to-bottom. Every filesystem effect routes through `thread_store`; every JSON document the agent emits passes through `validate_review_result.py` before any persistence call.

1. **Read `pr.json`** from the thread store under the current branch's slug:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/../thread-store/scripts/read_record.py" --slug "$SLUG" --name pr.json
   ```

2. **Compute the diff** against the base ref recorded in `pr.json`:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/compute_diff.py" --slug "$SLUG"
   ```

3. **Load the judgment-style prompt** into the agent's context:

   ```text
   Read ${CLAUDE_SKILL_DIR}/references/review-prompt.md
   ```

4. **Apply the prompt** to the diff plus any repository conventions you have already loaded; emit one `review-result.json` document conforming to the schema declared in `scripts/review_result.py`.

5. **Validate** the JSON through the arbiter. Pipe the emitted JSON in on stdin:

   ```bash
   echo "$REVIEW_RESULT_JSON" | python3 "${CLAUDE_SKILL_DIR}/scripts/validate_review_result.py"
   ```

   On non-zero exit, read the stderr message verbatim, repair the JSON (fix the missing key, the unknown enum value, or the consistency-invariant violation), and re-emit. **Do not** hand-check the JSON in agent prose — the arbiter is the single source of validity.

6. **Persist** the validated `review-result.json`:

   ```bash
   echo "$REVIEW_RESULT_JSON" | python3 "${CLAUDE_SKILL_DIR}/../thread-store/scripts/write_record.py" --slug "$SLUG" --name review-result.json
   ```

7. **Render** the human-readable surface and persist it:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_review.py" --slug "$SLUG" \
     | python3 "${CLAUDE_SKILL_DIR}/../thread-store/scripts/write_record.py" --slug "$SLUG" --name review.md
   ```

`render_review.py` re-parses `review-result.json` through `review_result.parse_json` before emitting; an invalid result fails the render with a non-zero exit before any markdown is produced.

</chain>

<validate_as_arbiter>

The validate-as-arbiter pattern is the cross-lens contract for the reviewing-changes lens. The agent emits JSON; the CLI is the only source of validity for that JSON; a non-zero exit is a re-emit signal, not a status to gloss over. The agent never:

- Hand-checks the required-key set, the enum membership, or the consistency invariant.
- Persists a `review-result.json` document that has not passed the arbiter.
- Treats agent prose as authoritative when the arbiter and the prose disagree.

The consistency invariant — `decision == "approve"` combined with any finding whose `severity == "must_fix"` — is enforced inside `review_result.parse_json` so direct Python callers that bypass the CLI still surface the violation. The CLI is the entry point the wrapper agent reads as exit code.

</validate_as_arbiter>

<constraints>

- Stdlib-only Python under `${CLAUDE_SKILL_DIR}/scripts/`. No third-party packages, no `outcomeeng_*` imports, no dependency on `uv` at runtime.
- Every filesystem effect routes through the `thread_store` facade — no direct `open()`, `pathlib.Path.write_*`, or `os.remove` against the thread-store backend's storage paths. `compute_diff.py` shells out to `git diff` via `subprocess.run`; that is the only `subprocess` call permitted in the script set.
- The judgment-style review prompt lives only at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`. It is never embedded inside this SKILL.md or any `.py` file under `scripts/`.
- Frozen dataclasses (`Finding`, `ReviewResult`) cross the parse → validate → render boundary. Any attempt to mutate one between steps raises `FrozenInstanceError`.

</constraints>

<success_criteria>

- [ ] The wrapper agent's invocation of `validate_review_result.py` exits 0 against every persisted `review-result.json`.
- [ ] `review-result.json` and `review.md` both exist under the current branch's slug in the thread store after the chain completes.
- [ ] No script under `scripts/` imports a third-party package or calls a direct filesystem primitive against the backend's storage paths.
- [ ] The swappable review prompt remains a standalone file at `references/review-prompt.md`; rotating the prompt does not require touching code.

</success_criteria>
