---
name: auditing
description: Use when asked by the user to invoke the audit skill
allowed-tools: Read, Bash, Glob, Grep
---

<objective>

Run a deterministic audit over a code scope: prepare (Phase 0), automated gates (Phase 1), tests (Phase 2), implementation review (Phase 3), test evidence (Phase 4), ADR/PDR compliance (Phase 5), and emit (Phase 6). Partition the scope by language, dispatch to the corresponding `auditing-{lang}*` skills, aggregate each partition's verdict via `aggregate_verdicts.py`, and emit one wrapper verdict whose `children` array carries the per-language dispatched verdicts. The orchestrator itself embeds zero language-specific knowledge beyond the dispatch template — language audits live in their own skills, this one composes them.

This skill runs a single audit pass per invocation. By default it is stateless: it reads no prior verdict and persists nothing — the caller renders and delivers the emitted verdict (a CI workflow posts the `markdown+json` carrier to the PR comment thread; a local agent relays the rendered output). When a caller (e.g., the `audit-orchestrator` agent) needs cross-commit continuity, the skill exposes a stateful orchestration mode that drives the `audit_orchestrator.py` CLI to maintain `.spx/audits/<lang>/<branch-slug>.md` and a TTL-bounded lock at `<state-file>.lock`. See `<stateful_orchestration>` below.

Read-only over the audited code. The stateful mode writes only under the gitignored `.spx/audits/` partition; the audited project tree is never modified.

</objective>

<determinism_contract>

1. **Frozen scope.** The file list captured in Phase 0 is the scope for the rest of the run; later phases never expand it. The scope hash from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py::compute_scope_hash` identifies this exact scope and travels in the wrapper verdict's metadata.
2. **Canonical verdict shape.** Every verdict conforms to the schema in `${CLAUDE_SKILL_DIR}/scripts/verdict.py`. The orchestrator's wrapper has three rows (`automated-gates`, `test-execution`, `determinism-contract`); per-language children have their own rows owned by the dispatched skill. Row names are never invented inline.
3. **Frozen finding catalog.** Findings are only created from violations of the rules the dispatched `auditing-{lang}*` skills already enforce. Style preferences, taste-based critiques, and "could be cleaner" observations are NEVER findings.

If any mechanism cannot be applied, halt and report the obstacle — do not silently substitute a looser audit.

This skill is strictly read-only over the project. It uses `Read`, `Bash` (for git, project validation, and tests), `Glob`, and `Grep` — never `Write` or `Edit`. It does not write its verdict to a project path or any persisted location; the caller delivers it. The `/tmp` files Phase 6 uses to stage per-partition JSON for aggregation are ephemeral scratch space, not artifacts. The Subagent Restrictions section of `AGENTS.md` requires subagents never to create or modify files.

</determinism_contract>

<language_detection>

Partition the in-scope file list by file extension. The mapping from extension to language identifier is training-time knowledge for any LLM that can run this skill; no explicit table belongs in the orchestrator. For mixed-language scopes, run the protocol once per partition, collect each partition's verdict, and aggregate them via `aggregate_verdicts.py` into one wrapper verdict whose `children` array carries the per-language verdicts. Each partition's language identifier is the `<lang>` value substituted into the `auditing-{lang}*` dispatch template.

The orchestrator never embeds language-specific tokens beyond the dispatch template `auditing-{lang}*` and the language placeholder `<lang>` — the factoring rule that keeps this orchestrator language-neutral.

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

Phases 1 and 2 run the project's own commands as discovered in Phase 0 step 5; the orchestrator does not dispatch to a skill for those rows. Phases 3, 4, and 5 dispatch to the language-specific trio.

If any of the three dispatched skills is missing for the target language, halt before any phase runs with `missing required skill: auditing-{lang}-{kind}`. The marketplace validation pipeline enforces that every language plugin ships the trio; runtime absence indicates an installation or build issue, not a methodology decision.

</skill_map>

<process>

<phase number="0" name="prepare">

1. **Determine scope.** The caller provides one of:
   - An explicit file or directory list — use as-is.
   - A git ref or diff range (`HEAD`, `main..HEAD`, a branch name) — invoke `expand_diff_range(<range>, repo=Path('.'))` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py` to enumerate the files in the range.
   - No scope — invoke `uncommitted_scope(repo=Path('.'))` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py` to enumerate uncommitted, staged, **and untracked** changes (a fresh file added but not yet `git add`-ed is in scope). If the helper returns an empty list, halt with `no scope detected`. `expand_diff_range("HEAD", ...)` is **not** equivalent — it omits untracked files.

2. **Materialize the file list.** Filter to existing files. Sort lexicographically. This sorted list is the **frozen scope** for this run.

3. **Partition by language.** Group files by extension into per-language partitions. The remainder of the protocol runs once per partition; per-partition verdicts are aggregated in Phase 6 into one wrapper verdict whose `children` array carries them. If any partition's `auditing-{lang}*` trio is missing, halt now with `missing required skill: auditing-{lang}-{kind}` before any phase runs.

4. **Compute the scope hash.** Invoke `compute_scope_hash` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py`. Pass the frozen scope as `list[tuple[path, content]]`; the function returns a 12-character hex string. The hash identifies this exact scope and travels in the wrapper verdict's `metadata.scope_hash`.

5. **Read project config.** `CLAUDE.md`, `AGENTS.md`, and any language-native configuration the dispatched `auditing-{lang}` skill expects. Identify the canonical validation command and the canonical test command for the project (the precedence convention in marketplace projects: `CLAUDE.md`/`AGENTS.md` → `justfile`/`Makefile` → language-native config; closer to repo root wins). If neither is discoverable from project files, halt — do not guess.

6. **Read repo-local overlays.** `spx/local/auditing.md` and `spx/local/auditing-{lang}*.md` for each language in scope — read each that exists. Local overlays supersede the pre-loaded standards from the dispatched skill.

Do not read source files for comprehension during Phase 0. Phase 0 only inventories.

</phase>

<phase number="1" name="automated-gates">

Run the project's canonical validation command (discovered in Phase 0 step 5). Any non-zero exit code is REJECT for row 1. Halt before subsequent phases — rows 2–6 are not evaluated.

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

For each language partition, the dispatched skills emit JSON verdicts per the canonical schema in `${CLAUDE_SKILL_DIR}/scripts/verdict.py`. Stage the children in a unique scratch directory created by `pass_results.py mkdir` (a `tempfile.mkdtemp`-backed unique path — two concurrent audit runs do not clobber each other) and write each partition's verdict JSON to its own file under that directory. The three orchestrator-owned rows (`automated-gates`, `test-execution`, `determinism-contract`) are then passed to `aggregate_verdicts.py` as repeatable `--row name=STATUS` arguments — `automated-gates` reflects Phase 1's validation-command exit (PASS on zero, FAIL otherwise), `test-execution` reflects Phase 2's test-command exit, and `determinism-contract` is PASS when Phase 0 produced a frozen scope plus scope hash without halts. The aggregator's stdout pipes directly into `emit_verdict.py`, which renders the wrapper to the requested surface form (`markdown`, `markdown+json`, or `json-only`; default `markdown+json` for PR-comment delivery). The wrapper verdict never touches disk — only the per-language children files do, because fanout (one orchestrator → N dispatched skills reading the same Phase 1/2 tool output) demands a directory.

```bash
CHILDREN_DIR=$(python3 "${CLAUDE_SKILL_DIR}/scripts/pass_results.py" mkdir)
# Caller owns cleanup unconditionally: the trap fires whether the
# aggregator pipeline succeeds, an earlier dispatched skill halted, or
# the shell is interrupted. A plain `rm -rf` at the end of the block
# would leak $CHILDREN_DIR on every non-happy exit path — exactly the
# scenario the marketplace's persistent-/tmp environments (CI runners
# reused across jobs, developer workstations) are vulnerable to. Caller-owned
# cleanup of a unique-per-invocation scratch dir is the portable
# scratch-storage rule every plugin follows.
trap 'rm -rf "$CHILDREN_DIR"' EXIT

# Dispatched skills emit their per-partition verdict JSON to
# $CHILDREN_DIR/<language>.json (one file per language partition).
# Replace each --row PASS below with FAIL when the corresponding phase
# exited non-zero (Phase 1 → automated-gates, Phase 2 → test-execution)
# or UNKNOWN when Phase 0 halted before producing a frozen scope
# (determinism-contract).
python3 "${CLAUDE_SKILL_DIR}/scripts/aggregate_verdicts.py" \
  --directory "$CHILDREN_DIR" \
  --row automated-gates=PASS \
  --row test-execution=PASS \
  --row determinism-contract=PASS \
  --skill auditing \
  --target <scope-target> \
  --metadata branch=<branch-name> \
  --metadata scope_hash=<scope-hash> \
| python3 "${CLAUDE_SKILL_DIR}/scripts/emit_verdict.py" \
  --format "${AUDIT_FORMAT:-markdown+json}"
```

The orchestrator does not write the verdict to disk — the caller delivers it. The orchestrator never hand-formats markdown; deterministic rendering lives in `emit_verdict.py`.

</phase>

</process>

<verdict_format>

The canonical schema is declared in `${CLAUDE_SKILL_DIR}/scripts/verdict.py` (`Status`, `Severity`, `Finding`, `Row`, `Verdict` dataclasses). The orchestrator's wrapper verdict has this shape:

```json
{
  "schema_version": 1,
  "skill": "auditing",
  "target": "<scope-target>",
  "overall": "APPROVED | REJECTED | UNKNOWN",
  "rows": [
    {"name": "automated-gates", "status": "PASS | FAIL | UNKNOWN", "findings": []},
    {"name": "test-execution", "status": "PASS | FAIL | UNKNOWN", "findings": []},
    {"name": "determinism-contract", "status": "PASS | FAIL | UNKNOWN", "findings": []}
  ],
  "children": [
    { "skill": "auditing-typescript", "overall": "PASS | FAIL | UNKNOWN", "rows": [...] }
  ],
  "metadata": {"branch": "<branch>", "scope_hash": "<12-char-hex>"}
}
```

The wrapper's three rows are the orchestrator-owned concerns (gates, tests, determinism). Per-language implementation, test-evidence, and ADR/PDR concerns live inside the children's `rows` arrays — dispatched skills own those.

Two `overall` vocabularies coexist: the **orchestrator wrapper** carries `APPROVED` / `REJECTED` / `UNKNOWN` (root-level decision); each **dispatched child** carries `PASS` / `FAIL` / `UNKNOWN` (skill-level contribution). The split is grounded in `verdict.py`'s `ROOT_STATUSES` vs `SKILL_STATUSES` sets. Row statuses use the skill-level vocabulary regardless of where the row sits, since a row is always one skill's contribution.

Overall rollup follows `verdict.roll_up`: APPROVED iff every wrapper row and every child is PASS or APPROVED; REJECTED if any row is FAIL or any child is REJECTED/FAIL; UNKNOWN if some row or child is UNKNOWN and none are FAIL/REJECTED.

</verdict_format>

<failure_modes>

**Improvised scope hashing.** Claude computes the scope hash in-prose (e.g., concatenating paths and contents in some ad hoc framing) instead of calling `compute_scope_hash` from `${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py`. Distinct file lists then collide on the same hash because the framing is ambiguous. The helper module is the boundary; never reproduce its logic inline.

**Scope drift mid-run.** Files added or removed between Phase 0 and Phase 5 yield inconsistent reads — one phase sees a file the next phase doesn't. The "frozen scope" invariant exists to prevent this: Phase 0 captures the file list once; later phases never re-enumerate. If a phase needs a file not in the frozen scope, halt and report; do not silently expand scope.

**Mid-phase halt without trio verification.** Claude reaches Phase 3, finds `auditing-{lang}` missing, and halts there — but Phase 1 (automated gates) and Phase 2 (tests) already ran. The trio check belongs in Phase 0 step 3 (partition-by-language), before any phase runs. Halt with `missing required skill: auditing-{lang}-{kind}` before Phase 1 dispatches.

**Dropped partition in mixed-language scope.** Claude treats a mixed-language scope as one audit, dispatches to whichever language has a plurality of files, and silently skips the others. The contract is one dispatched verdict per partition aggregated into one wrapper; never drop a partition. If a partition's `auditing-{lang}*` skills do not exist, halt with the missing-skill error before any phase runs.

**Hand-formatted verdict.** Claude emits a markdown verdict directly into the conversation instead of producing JSON and piping through `emit_verdict.py`. The toolchain owns rendering; the orchestrator owns the JSON shape. Re-read `<verdict_format>` and the Phase 6 emit instructions if uncertain.

**Re-implemented rollup.** Claude computes the wrapper's overall by reading the children's rows and deciding APPROVED/REJECTED in-prose. The rollup lives in `verdict.roll_up`; `aggregate_verdicts.py` invokes it. Never re-implement the rollup logic inline.

</failure_modes>

<stateful_orchestration>

Callers that need cross-run continuity — carrying open finding IDs forward, resolving findings that have been fixed, reopening regressions under their original IDs — invoke this skill with the stateful-orchestration mode enabled. The mode is opt-in: a caller activates it by requesting state persistence (e.g., the `audit-orchestrator` agent in its prompt). When inactive, the skill runs the stateless protocol above unchanged.

State partitioning and naming are deterministic. State files live at `.spx/audits/<lang>/<branch-slug>.md` rooted in the repo working tree, with the run lock at `<state-file>.lock`. The `.spx/` root is gitignored — state is local development scratch, not product truth. Language partition is the same `<lang>` the orchestrator dispatches against in Phase 3–5; branch slug is derived from the current branch via the CLI.

The skill drives every CLI invocation from inside its own prose so the calling agent never constructs a path into `scripts/`. Each command below is invoked exactly once per language partition as part of the stateful flow. Every shell variable below is set within these blocks — there are no upward references to undefined names — so an agent that runs each block in order has every value in scope.

1. **Resolve the branch and the state path.** `LANG` is the partition language identifier from Phase 0 step 3 (`python`, `typescript`, `rust`, …). The block assumes `LANG` is set in the agent's environment — one invocation per partition with `LANG` set accordingly.

   ```bash
   BRANCH=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" current-branch)
   BASE=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" base-ref)
   STATE_DIR=".spx/audits/${LANG}"
   SLUG=$(python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" \
     branch-slug --branch "$BRANCH" --state-dir "$STATE_DIR")
   STATE_FILE="$STATE_DIR/${SLUG}.md"
   LOCK_FILE="${STATE_FILE}.lock"
   ```

2. **Acquire the lock before any state read or write.** A fresh held lock means another run is in progress on this branch — halt the audit and report the lock holder so the caller can decide whether to wait or abort.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" acquire-lock \
     --path "$LOCK_FILE" || exit 1
   ```

   Crash recovery is the TTL's responsibility, not a shell `trap`. The agent invokes the stateful flow as a sequence of separate `Bash` tool calls, each spawning a fresh shell; a `trap EXIT` registered in the acquisition call does not survive into later calls. If the agent or session aborts between this step and step 5's explicit release, the lock file persists until its mtime exceeds `DEFAULT_LOCK_TTL_SECONDS` (600 s), after which the next acquire-lock invocation overwrites it. The clean-exit release lives in step 5 below.

3. **Run the audit (stateless Phases 0–6).** Phase 6 writes per-language verdict JSON files into the scratch directory `$CHILDREN_DIR` defined inside the Phase 6 `<phase number="6">` block above. Read this partition's verdict back into a shell variable with `read_verdict.py`:

   ```bash
   FINDINGS_JSON=$(python3 "${CLAUDE_SKILL_DIR}/scripts/read_verdict.py" \
     --file "$CHILDREN_DIR/${LANG}.json" --field findings)
   ```

4. **Apply the state transition.** Pipe `FINDINGS_JSON` into `state-transition`. The CLI writes the new state file atomically and emits the `{open, resolved, reopened}` classification on stdout. `VERDICT` is the wrapper verdict's `overall` from Phase 6 (`APPROVED`, `REJECTED`, or `UNKNOWN`).

   ```bash
   CURRENT_SHA=$(git rev-parse HEAD)
   NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   printf '%s' "$FINDINGS_JSON" | \
     python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" state-transition \
       --state-file "$STATE_FILE" \
       --branch "$BRANCH" \
       --current-sha "$CURRENT_SHA" \
       --now "$NOW" \
       --verdict "$VERDICT"
   ```

   The stdin payload conforms to the `state-transition` contract: a JSON object with a top-level `findings` array, each entry carrying `file_line`, `concern`, `root_cause`, and `required_fix` strings. Construct `FINDINGS_JSON` as that shape (the Phase 6 dispatched-skill verdicts already populate the four fields per finding).

5. **Release the lock and render the emitted output.** Run `release-lock` as the final step of the clean-exit path; the call is idempotent so re-running is safe.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" release-lock \
     --path "$LOCK_FILE"
   ```

   Then render with the state classification merged into the wrapper verdict's metadata (`state.open_count`, `state.resolved_this_run`, `state.reopened_this_run`). The verdict surface form follows the caller's format flag; the orchestration mode does not change which format is rendered.

The lock TTL defaults to `DEFAULT_LOCK_TTL_SECONDS` (600 seconds). A lock with mtime older than the TTL is treated as stale (left by a crashed run) and overwritten; this is the crash-recovery path. The explicit `release-lock` above is the clean-exit path.

The state-transition CLI distinguishes three failure modes by exit code: `1` for lock-held / acquisition failure, `2` for `StateFileCorruptError` (the on-disk state file failed to parse), `3` for malformed stdin JSON (missing required finding keys). Exit `2` is the agent's signal to surface the state-file path and ask the caller whether to discard it for a clean re-run or keep it for inspection.

The stateful mode never writes outside `.spx/audits/`. The wrapper verdict, dispatched children, and `$CHILDREN_DIR` scratch space remain ephemeral per the stateless contract.

</stateful_orchestration>

<verdict_thread_orchestration>

CI callers that need cross-CI-run continuity over a pull request — surfacing what got fixed and what regressed across iterations — invoke this skill with one of the two PR-thread modes. Both are opt-in via an explicit `MODE:` line in the invocation prompt. The skill keys on the line: `MODE: prior-verdict-read` for the prior-verdict ingest, `MODE: with-prior-verdict` for the audit that diffs against a prior verdict. State for these modes lives in the PR comment thread itself — the durable cross-CI-run surface for an audit verdict — the skill writes nothing to `.spx/` in either mode.

The `MODE:` line is the explicit signal — a free-text description of the intent may accompany it for human readability but the skill matches on the `MODE:` line, not on the prose. Exactly one `MODE:` line must appear per invocation: if the invocation contains no recognised `MODE: prior-verdict-read` or `MODE: with-prior-verdict` line and the standard six-phase audit is not in scope either, OR contains both `MODE:` lines (a template copy-paste accident), STOP and return an error naming which condition was hit — never default silently and never pick one of the conflicting modes. Silent defaulting produces spurious extra PR comments or wrong resolved/reopened classifications when a calling agent's wording drifts; loud failure surfaces the drift on the next CI run.

**MODE: prior-verdict-read.** Pull the prior audit verdict, if any, from the target PR's comment thread. The caller supplies `REPO` (owner/repo) and `PR NUMBER`. The skill drives the pipeline below from inside its own prose so the calling agent never constructs a path into `scripts/`.

```bash
PRIOR_RAW=$(gh -R "$REPO" pr view "$PR_NUMBER" --json comments --jq \
  '[.comments[] | select(.body | contains("<!-- AUDIT_VERDICT_JSON_BEGIN -->"))] | last | .body')
if [ -z "$PRIOR_RAW" ] || [ "$PRIOR_RAW" = "null" ]; then
  printf '{"prior": null}\n'
else
  PRIOR_JSON=$(printf '%s' "$PRIOR_RAW" | python3 "${CLAUDE_SKILL_DIR}/scripts/read_verdict.py")
  printf '{"prior": %s}\n' "$PRIOR_JSON"
fi
```

The skill returns `{"prior": null}` when no comment carries the `<!-- AUDIT_VERDICT_JSON_BEGIN -->` delimiter (first run on a new PR), or `{"prior": <parsed verdict>}` when the most recent audit comment is found. The caller (the `pr-review-orchestrator` agent) tolerates both shapes — the no-prior case yields empty `resolved` and `reopened` in the next mode.

**MODE: with-prior-verdict.** Run the standard stateless six-phase audit, then diff the emitted verdict against the prior verdict to compute `resolved` and `reopened`, populating those arrays in the wrapper verdict that gets rendered. The caller supplies the prior verdict as a JSON file path (typically the `prior` payload returned by `prior-verdict-read`, written to a temp file).

```bash
PRIOR_FILE=$(mktemp)
printf '%s' "$PRIOR_VERDICT_JSON" > "$PRIOR_FILE"
# Run Phases 0–6 as documented above; capture the wrapper verdict JSON in $WRAPPER_JSON.
ENRICHED_JSON=$(printf '%s' "$WRAPPER_JSON" | \
  python3 "${CLAUDE_SKILL_DIR}/scripts/audit_orchestrator.py" verdict-diff \
    --prior "$PRIOR_FILE")
rm -f "$PRIOR_FILE"
printf '%s' "$ENRICHED_JSON" | python3 "${CLAUDE_SKILL_DIR}/scripts/emit_verdict.py" \
  --format "${AUDIT_FORMAT:-markdown+json}"
```

`compute_verdict_diff` (see `audit_orchestrator.py`) computes resolved + reopened by content identity `(file, line, rule, message)` — `id` and `severity` are deliberately excluded so a regenerated finding with a fresh ID or an upgraded severity matches its prior counterpart. The diff carries forward state across runs: `resolved` accumulates findings that have been resolved at any point in the PR's history (minus anything currently reopened), and `reopened` is the set of currently-open findings that match a previously-resolved entry. First-run (`PRIOR_FILE` absent or `--prior` omitted) yields empty `resolved` and `reopened` in the enriched verdict.

When the caller composes a single combined PR comment from the rendered enriched verdict plus a review prose section (the `pr-review-orchestrator` flow), the JSON payload's `<!-- AUDIT_VERDICT_JSON_BEGIN --> ... <!-- AUDIT_VERDICT_JSON_END -->` delimiters are preserved verbatim so the next iteration's `prior-verdict-read` can recover this verdict as the prior. The caller MUST NOT wrap the JSON in a markdown fence and MUST NOT post the verdict as a separate comment — both would break the next ingest.

</verdict_thread_orchestration>

<success_criteria>

- One wrapper verdict emitted, with one child verdict per language partition in the frozen scope.
- The wrapper has three orchestrator-owned rows (`automated-gates`, `test-execution`, `determinism-contract`) and one child per partition.
- The wrapper's `overall` is APPROVED, REJECTED, or UNKNOWN per `verdict.roll_up` applied to wrapper rows plus children overalls.
- The verdict is emitted via `emit_verdict.py` with the format axis forwarded from the caller.
- The orchestrator's prose contains zero language-specific tokens beyond the dispatch template `auditing-{lang}*` and the language placeholder `<lang>`.
- The scope hash is reproducible: re-running the skill on the same frozen scope produces the same hash.
- If the run halts (missing `auditing-{lang}*` trio, empty scope, or a non-zero exit from the canonical validation or test command), the halt reason is reported on the relevant row and no subsequent phase runs.

</success_criteria>
