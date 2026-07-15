# Script Decomposition for Reviewing Changes

The public command surface for the review-changes skill is the single runner `review_run.py`. The skill invokes only `python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" ...` and reads files; all `git`, scratch-directory, helper-script, and `spx journal` calls stay behind the runner. `start` computes the review-input bundle, opens the review journal, appends the scope-entered event, and returns machine-readable execution state. `append-scope` and `append-finding` append the live events the run reaches. `finish` reads the event prefix, appends a terminal `com.outcomeeng.spx.journal.run.completed` event carrying review status and finding counts, seals the journal, cleans runner-owned scratch storage, and returns only the run token. The skill's caller-facing output is the raw run token; rendered review surfaces are SPX projections over the sealed journal prefix.

`compute_diff.py`, `journal_emit.py`, and `review_result.py` are shipped helper and compatibility policy modules. `compute_diff.py` owns the full changeset diff bundle: committed merge-base, staged, unstaged, and untracked sections, with refs, hashes, spans, and changed files in `manifest.json`. Compatibility and projection tests cover `journal_emit.py` and `review_result.py`; the live skill path exposes neither module to the reviewer and uses `spx journal append` as the authoritative event boundary.

## Rationale

A single runner is the smallest stable capability boundary. Tool restrictions authorize the reviewer to invoke the review runner, while the runner owns subcommand validation, argument validation, state validation, error messages, scratch cleanup, and journal mutation. Keeping direct `spx journal`, `git`, `mktemp`, `rm`, `date`, `printf`, and helper-script calls out of `allowed-tools` prevents the skill prose from becoming a shell transcript and keeps runner-internal verbs from requiring frontmatter churn.

The review journal is the durable source of truth. Returning only the run token avoids a second caller-facing projection that can drift from the sealed event prefix. The terminal run-completed event records the review status and finding counts so consumers can inspect the run through SPX. GitHub review rendering, inline citation placement, batching, and PR submission are SPX projection concerns, not Python skill concerns.

The prompt remains one bundled reference file because prompt iteration is orthogonal to runner behavior. Repository-root review prompt files are intentionally outside the live review context: local and hosted integrations use the same shipped prompt, and consumers do not get an example override that can drift from the runner protocol. The prompt instructs Claude to read the diff and provide findings only; the review consumes a changeset whose deterministic verification is passing.

## Verification

### Testing

- ALWAYS: the review-changes skill frontmatter grants only `Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py":*)` and `Read` ([compliance])
- ALWAYS: `review_run.py start` computes the diff bundle, opens the review journal, appends the scope-entered event, and returns machine-readable run state ([compliance])
- ALWAYS: `review_run.py append-scope` and `review_run.py append-finding` append the live journal events for examined scope and findings ([compliance])
- ALWAYS: `review_run.py finish` appends a terminal run-completed event carrying review status and finding counts, seals the run, cleans scratch state, and returns only `runToken` ([compliance])
- ALWAYS: `compute_diff.py` resolves `base_ref` and `head_ref` through their precedence chains, scopes git-derived bases through the remote-tracking ref, and emits committed, staged, unstaged, and untracked diff sections into a caller-owned bundle outside the git worktree ([compliance])
- ALWAYS: review finding citations accept the current claim-shape vocabulary in path-style spec citations, including `COMPLIANCE`, while preserving `AUDIT` for legacy spec citations ([mapping])
- NEVER: scripts under `plugins/spec-tree/skills/review-changes/scripts/` import third-party packages, depend on `uv` at runtime, or import `outcomeeng_*` modules ([compliance])

### Audit

- ALWAYS: the swappable review prompt at `references/review-prompt.md` is loaded by skill prose via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` ([audit])
- ALWAYS: the wrapper agent reaches the review implementation only by invoking the `review-changes` skill and reports only the observable skill output ([audit])
- NEVER: the skill, wrapper agent, or runner produces a caller-facing rendered review surface; the caller receives only the run token ([audit])
- NEVER: the reviewer runs validation, tests, evals, coverage, lint, typecheck, or another deterministic verification command during review ([audit])
- NEVER: the review prompt is embedded inside `SKILL.md` or any script; it remains one standalone Markdown reference ([audit])
