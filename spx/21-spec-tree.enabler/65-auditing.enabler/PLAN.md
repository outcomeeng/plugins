# PLAN — PR #10 / PR #11 bot-review continuation

Coordination notes for finishing the multi-round bot-review loop on the two open draft PRs. Both PRs are `MERGEABLE` with green CI; the loop continues until each round returns only minor nits.

## Two PRs, two branches

| PR                                                   | Branch                         | Scope                                                                                  | Last commit at handoff                                                                  |
| ---------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [#10](https://github.com/outcomeeng/plugins/pull/10) | `work/add-typescript-spec`     | `[eval]` evidence mechanism + `outcomeeng_evals` runner + slice migration              | `92f3e14` (round 6 pushed) — **awaiting r6 bot review**                                 |
| [#11](https://github.com/outcomeeng/plugins/pull/11) | `work/audit-verdict-toolchain` | verdict toolchain + audit-orchestration restoration + marketplace-wide skill alignment | `c686730` (round 4 pushed) — **r4 bot review read, round 5 in progress, NOT committed** |

Both branches are rebased onto `origin/main` (picked up the develop/prose version bumps that were causing the Codex-cache symlink validation failures). After any rebase, force-push with `--force-with-lease` and re-run `just push-marketplace` to confirm the Codex cache validates (exit 0, 1 informational warning is expected).

## Review-loop method

For each new bot review comment on a PR:

1. `gh pr view <N> --json comments --jq '.comments[-1].body'` to read the latest review.
2. Categorize findings: substantive (bugs, correctness, methodology violations) vs minor (style, doc notes).
3. Fix substantive items; address minor items where cheap. Skip cosmetic-only items and note them.
4. `just check` must pass. Commit with a focused `fix(...)` message listing each finding addressed. Push via `just push-marketplace`.
5. The `claude-review` CI job re-fires on each push (~3–8 min). Use `ScheduleWakeup` (~540s) to come back and check, then loop. Never poll with `gh run watch`.
6. Stop when a round returns only minor nits with no substantive items.

`ISSUES.md` and `PLAN.md` in node directories are committed escape hatches per `spx/CLAUDE.md` — legitimate, but the bot keeps flagging them against the root `AGENTS.md` "planning is ephemeral" line. There is a genuine doc inconsistency between `AGENTS.md` and `spx/CLAUDE.md` here; a methodology pass should reconcile them. For now: PLAN.md files that are pure finished-decision dumps get removed (the eval-harness PLAN.md was), PLAN.md files that are active coordination (like this one) stay, and ISSUES.md files that mix deferred-spec-work with methodology-layer issues should split the latter into a PDR or fix the specs.

## PR #11 — round 5 work (IN PROGRESS, not yet committed)

From the r4 bot review on PR #11. Pick up here on `work/audit-verdict-toolchain`.

### 1. `aggregate_verdicts.py` needs a `--row name=STATUS` repeatable flag (substantive)

`aggregate()` always produces `rows=()`, but `auditing/SKILL.md` `<verdict_format>` and `auditor.md` `<output_format>` both show the wrapper with three orchestrator-owned rows (`automated-gates`, `test-execution`, `determinism-contract`). A skill following the Phase 6 example produces `"rows": []`, contradicting its own schema example.

Fix: add `--row name=STATUS` (repeatable) to `_parse_args`; parse each into a `Row(name=name, status=Status(STATUS), findings=())` with `STATUS` validated against `SKILL_STATUSES`; thread the parsed rows into `aggregate(rows=...)`; in `aggregate()`, set `rows=rows` and change the rollup to `verdict.roll_up([r.status for r in rows] + [c.overall for c in children])` so wrapper-row FAILs propagate. Import `Row, Status` from `verdict`. Add scenario tests in `spx/21-spec-tree.enabler/32-evidence.enabler/65-verdict-toolchain.enabler/tests/test_aggregate_verdicts.scenario.l1.py` (rows present in wrapper; a FAIL wrapper row → REJECTED overall even when all children PASS). Then the `<verdict_format>` examples in `auditing/SKILL.md` and `auditor.md` are achievable as written — add a one-liner to the Phase 6 example showing `--row automated-gates=PASS --row test-execution=PASS --row determinism-contract=PASS`.

### 2. Language test-audit skills not aligned to JSON (check whether real)

The r4 bot claims `auditing-python-tests`, `auditing-typescript-tests`, `auditing-rust-tests` still emit markdown. They each have a `<verdict_format>` that says "Follow `<verdict_format>` in `/auditing-tests`" plus language-specific lines ("Gate 2 extraction target: `testing/harnesses/{name}.ts`", "Gate 0 check IDs for Python: F1, V1, C1", etc.). Since `/auditing-tests` was converted to the JSON shape in PR #11 round 2, the delegation carries through — but the language-specific lines still reference markdown-table concepts (gate columns, extraction targets as table cells). Verify each of the three files and, if the language-specific lines presume the old markdown table, rewrite them to express the same information in JSON-shape terms (check IDs as `rule` values; extraction targets as `message` content).

### 3. Track the `python3 -c` CLI-dispatcher follow-up in a durable artifact

`auditor.md`'s `<helper_invocation>` ships eight inline `python3 -c` heredocs (now using `${CLAUDE_PLUGIN_ROOT}` after round 4). The PR acknowledges these as interim. The r4 bot wants the planned CLI dispatcher captured before the 0.30.0 tag. This PLAN.md is that artifact — see "CLI dispatcher for `audit_orchestrator.py`" below. Update `auditor.md`'s `<helper_invocation>` closing note to reference `spx/21-spec-tree.enabler/65-auditing.enabler/PLAN.md` again (the round-3 edit removed the broken reference; now the file exists).

### 4. Minor PR #11 fixes

- `audit_orchestrator.py` `compute_scope_hash`: type hint is `list[tuple[str, str]]` but the docstring and `auditing/SKILL.md` say `list[tuple[path, content]]`. `Path` objects break on `.encode("utf-8")`. Make the docstring/SKILL.md explicit that paths must be `str`, or accept `os.PathLike` and `os.fspath()` it.
- `expand_diff_range`: `range_spec` is caller-controlled and passed straight to `git diff`. A malformed value could confuse git into treating path components as flags. Add a `re.match(r'^[A-Za-z0-9._/~^@{}-]+(\.\.\.?[A-Za-z0-9._/~^@{}-]+)?$', range_spec)` guard before the subprocess call; raise `ValueError` on no match.
- `audit_orchestrator.py` `STATE_OPEN_TABLE_SEPARATOR` / `STATE_RESOLVED_TABLE_SEPARATOR` are identical strings (both 6-column `| --- | ... |`). Add a one-line comment explaining the identity is structural (same column count) even though the headers differ, so a future reader doesn't think it's a copy-paste bug.
- `Status` dual-vocabulary note in `from_json_dict` (already added in round 3) — the r4 bot still flags the lack of a hard guard. Leave the docstring note; a real guard needs a skill registry. No code change.
- `RunLock` half-way context-manager use (`__enter__` via `python3 -c`, `__exit__` via shell `rm -f`) — folded into the CLI-dispatcher plan below (`acquire-lock` / `release-lock` subcommands make the pair symmetric).

### CLI dispatcher for `audit_orchestrator.py` (deferred — durable record for the r4 finding)

Replace the eight stateless `python3 -c` heredocs in `auditor.md` with one-liner subcommands on a CLI added to `audit_orchestrator.py` (stdlib `argparse`, no `uv`, per the Plugin Portability Constraints). Subcommands: `base-ref`, `current-branch`, `branch-slug <branch> <state-dir>`, `scope-hash <files-json-on-stdin>`, `branch-scope <base-ref> -- <patterns>`, `modified-since <prior-sha> -- <patterns>`, `sha-reachable <sha>`, `acquire-lock <path>`, `release-lock <path>`. The stateful state-file mutation path (`load_state` → `assign_finding_id`/`reopen_finding`/`resolve_finding` → `save_state`) stays as the one multi-line Python block in `auditor.md` — it needs to hold the `AuditState` object across several calls. Invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/skills/auditing/scripts/audit_orchestrator.py" <subcommand> ...`. Add scenario tests for the CLI surface (exit codes, stdout shape) alongside the existing helper tests.

## PR #10 — status at handoff

Round 6 (`92f3e14`) is pushed; the r6 `claude-review` job is running. When it lands, read it (`gh pr view 10 --json comments --jq '.comments[-1].body'`) and run the review-loop method above on `work/add-typescript-spec`.

Rounds 1–6 already addressed: PLAN.md flip post-strip; `[eval]` mechanism; eval-harness spec/tests; `describe()` HTML bug; `_pass_rate`/`trial_pass_rate` empty handling; parallel `_error_outcome` + `as_completed`; `--workers` IntRange(min=1, max=16); `--timeout-seconds`; `is_subset` multiset semantics + cardinality test; `HISTORY_ROW_FIELDS` enforced; `EVAL_TOML_FILENAME`/`RUNS_DIRNAME`/`HISTORY_FILENAME` extracted to `definition.py`/`history.py`; `[test]` link validation added to the link-integrity walker; `spx/` docstring refs removed from `outcomeeng_evals`; `sys.exit` → `ctx.exit`; `_render_prompt` single-pass injection-safe substitution + forward-scan; `_required_str` single-arg `KeyError`; `JSON_SCHEMA_VERSION` reverted to `"1"` to match baseline rows; eval-harness `PLAN.md` removed, open items → `ISSUES.md`; `view` command no-runs-yet error message; `cases.jsonl` comment-line + `is_subset` bool/int docstring notes; `RecordingRunner` `frozen=True` dropped.

Recurring bot complaints that are convention-correct (do not "fix" them): `ISSUES.md`/`PLAN.md` committed under `spx/` (escape-hatch convention); `is_subset(True, 1) == True` (JSON structural semantics); `auditing-tests` manual `sys.argv` parsing (script is trivial). The one that may need a methodology pass: the `AGENTS.md` "planning is ephemeral" line vs `spx/CLAUDE.md` "PLAN.md/ISSUES.md are committed escape hatches" — reconcile in a separate change, not in either PR.

## Done when

Both PRs: latest bot review round returns only minor nits, no substantive findings. Then they are ready for the user to mark ready-for-review and merge.
