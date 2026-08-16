# Script Decomposition for Reviewing Changes

The public command surface for the review-changes skill is the single runner `review_run.py`. The skill invokes only `python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" ...`, reads files, and searches the repository read-only to discover the unchanged consumers of a changed governing declaration; all `git`, scratch-directory, helper-script, and `spx journal` calls stay behind the runner. `start` computes the review-input bundle, opens the review journal, appends the scope-entered event, and returns machine-readable execution state. `append-scope` and `append-finding` append the live events the run reaches. `finish` reads the event prefix, appends a terminal `com.outcomeeng.spx.journal.run.completed` event carrying review status and finding counts, seals the journal, cleans runner-owned scratch storage, and returns only the run token. The skill's caller-facing output is the raw run token; rendered review surfaces belong to later SPX projections over the sealed journal prefix.

`compute_diff.py`, `journal_emit.py`, and `review_result.py` remain shipped helper and legacy policy modules during the stop-gap. `compute_diff.py` still owns the full changeset diff bundle: committed merge-base, staged, unstaged, and untracked sections, with refs, hashes, spans, and changed files in `manifest.json`. `journal_emit.py` and `review_result.py` remain covered for compatibility and legacy projection tests, but the live skill path no longer exposes them to Claude and no longer depends on `journal_emit.py finding-reported` as the finding gate. For this local mitigation, finding shape and citation validation move out of the skill path; `spx journal append` is the authoritative event boundary until review-specific validation moves into SPX.

## Rationale

A single runner is the smallest stable capability boundary for the stop-gap. Tool restrictions authorize Claude to invoke the review runner, while the runner owns subcommand validation, argument validation, state validation, error messages, scratch cleanup, and journal mutation. Keeping direct `spx journal`, `git`, `mktemp`, `rm`, `date`, `printf`, and helper-script calls out of `allowed-tools` prevents the skill prose from becoming a shell transcript and keeps future runner-internal verbs from requiring frontmatter churn. Read-only search is granted beside `Read` because the review scope reaches unchanged consumers of changed truth, which the diff bundle cannot enumerate; the grant mutates nothing, and the runner keeps every write behind its verbs. The frontmatter grant is a value this decision declares and the skill source complies with, so their agreement is audit evidence per `spx/12-shipped-scripting.adr.md`.

The review journal is the durable source of truth. Returning only the run token avoids a second caller-facing projection that can drift from the sealed event prefix. The terminal run-completed event records the review status and finding counts so consumers can inspect the run through SPX. GitHub review rendering, inline citation placement, batching, and PR submission are SPX projection concerns, not Python skill concerns.

The prompt remains one bundled reference file because prompt iteration is orthogonal to runner behavior. Repository-root review prompt files are intentionally outside the live review context: local and hosted integrations use the same shipped prompt, and consumers do not get an example override that can drift from the runner protocol. The prompt instructs Claude to read the diff and provide findings only; deterministic verification has already passed before review starts.

## Verification

### Testing

- ALWAYS: `review_run.py start` computes the diff bundle, opens the review journal, appends the scope-entered event, and returns machine-readable run state ([test](tests/test_skill_orchestration.scenario.l2.py))
- ALWAYS: `review_run.py append-scope` and `review_run.py append-finding` append the live journal events for examined scope and findings ([test](tests/test_skill_orchestration.scenario.l2.py))
- ALWAYS: `review_run.py finish` appends a terminal run-completed event carrying review status and finding counts, seals the run, cleans scratch state, and returns only `runToken` ([test](tests/test_skill_orchestration.scenario.l2.py))
- ALWAYS: `compute_diff.py` resolves `base_ref` and `head_ref` through their precedence chains, scopes git-derived bases through the remote-tracking ref, and emits committed, staged, unstaged, and untracked diff sections into a caller-owned bundle outside the git worktree ([test](tests/test_skill_orchestration.scenario.l2.py))
- ALWAYS: review finding citations use the audit vocabulary in path-style spec citations (`AUDIT`) ([test](tests/test_review_result.scenario.l1.py))
- NEVER: scripts under `plugins/spec-tree/skills/review-changes/scripts/` import third-party packages, depend on `uv` at runtime, or import `outcomeeng_*` modules ([test](tests/test_reviewing_changes.audit.l1.py))

### Audit

- ALWAYS: the review-changes skill frontmatter grants only `Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py":*)`, `Read`, `Grep`, and `Glob` — the runner is the sole command boundary and the search grants are read-only consumer discovery ([audit])
- ALWAYS: the swappable review prompt at `references/review-prompt.md` is loaded by skill prose via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` ([audit])
- ALWAYS: the wrapper agent reaches the review implementation only by invoking the `review-changes` skill and reports only the observable skill output ([audit])
- NEVER: the skill, wrapper agent, or runner produces a caller-facing rendered review surface; the caller receives only the run token ([audit])
- NEVER: the reviewer runs validation, tests, evals, coverage, lint, typecheck, or another deterministic verification command during review ([audit])
- NEVER: the review prompt is embedded inside `SKILL.md` or any script; it remains one standalone Markdown reference ([audit])
