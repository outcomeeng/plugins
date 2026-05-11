# PLAN: CLI dispatcher for `audit_orchestrator` helpers

Coordination file for the deferred CLI-dispatcher follow-up to the
audit-orchestrator helper queue (which landed in this enabler across the
session commits `7c645ec`, `50e9291`, `e2c7cb1`, `1426dc5`, `018b880`,
`9091d57`, `4ff246a`, `c837dd3`).

## Why this exists

The `auditor` agent invokes the helper module via nine multi-line
`uv run python -c "..."` heredocs in
[plugins/spec-tree/agents/auditor.md](../../plugins/spec-tree/agents/auditor.md)
under the `<helper_invocation>` block. Each invocation:

- Spawns a fresh Python process via `uv run` (~50-300 ms startup per call,
  even with warm caches).
- Re-imports the helper module via `importlib.util.spec_from_file_location`.
- Runs a single helper call.
- Prints stdout, which the Bash tool captures.

The friction:

- Quoting and escaping: agent-authored Python source inside a shell `-c`
  argument requires careful handling of single quotes, newlines, embedded
  strings. An LLM authoring these inline is one typo away from a syntax error
  the runtime cannot recover from cleanly.
- Verdict-log noise: the Bash tool's output stream shows the raw Python
  source for every call, drowning the actual return value in boilerplate.
- The agent prose at lines 72-160 of `auditor.md` is dominated by the
  heredocs — a reader scanning the protocol for what each phase does has
  to mentally strip the `python -c` ceremony from every step.

## Scope

Hybrid design — not all helpers translate cleanly to per-call CLI:

| Helper class                   | Helpers                                                                                                                                                    | Dispatcher fit                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stateless single-call          | `compute_scope_hash`, `detect_base_ref`, `detect_current_branch`, `branch_slug`, `expand_diff_range`, `branch_scope`, `modified_since`, `is_sha_reachable` | **Clean.** Each call is `args in → text out`. One subcommand per helper; argparse routes to the corresponding function.                                                                                                                                                                                                                                                                                                                                                                                                      |
| Locking                        | `RunLock`                                                                                                                                                  | **Partial.** Acquire-and-hold across the whole phase does not survive process boundaries; the current `lock.__enter__()` + manual `rm -f` pattern already works around this. A dispatcher subcommand `acquire-lock` / `release-lock` would mirror the current shape.                                                                                                                                                                                                                                                         |
| State + ID counter + lifecycle | `AuditState`/`Finding`/`load_state`/`save_state`/`assign_finding_id`/`find_resolved_by_identity`/`resolve_finding`/`reopen_finding`                        | **Poor.** The in-memory `AuditState` cannot sit between subprocesses. Two options: (a) every mutation becomes load-mutate-save, doubling disk I/O for the ~10-50 ops a typical re-run produces; (b) collapse the whole phase into one subcommand (`run-phase-f`, `run-phase-r`) that the agent invokes with JSON-shaped args. Option (b) abstracts too much for an LLM to debug when something goes wrong. Recommended treatment: keep the existing multi-line Python sketch in `<helper_invocation>` for the stateful path. |

**Recommended deliverable:** dispatcher for the 8 stateless helpers plus
the 2 lock subcommands. Stateful operations stay in the multi-line Python
block that `auditor.md` already documents.

## Implementation sketch

`plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` gains an
`argparse`-based `main()`:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit_orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    # Stateless single-call subcommands
    p_base = sub.add_parser("detect-base-ref")
    p_base.add_argument("--repo", default=".")

    p_branch = sub.add_parser("detect-current-branch")
    p_branch.add_argument("--repo", default=".")

    p_slug = sub.add_parser("branch-slug")
    p_slug.add_argument("branch")
    p_slug.add_argument("state_dir")

    p_diff = sub.add_parser("expand-diff-range")
    p_diff.add_argument("range_spec")
    p_diff.add_argument("--patterns", nargs="*")
    p_diff.add_argument("--repo", default=".")

    p_scope = sub.add_parser("branch-scope")
    p_scope.add_argument("base_ref")
    p_scope.add_argument("--patterns", nargs="*")
    p_scope.add_argument("--repo", default=".")

    p_mod = sub.add_parser("modified-since")
    p_mod.add_argument("prior_sha")
    p_mod.add_argument("--patterns", nargs="*")
    p_mod.add_argument("--repo", default=".")

    p_reach = sub.add_parser("is-sha-reachable")
    p_reach.add_argument("sha")
    p_reach.add_argument("--repo", default=".")

    p_hash = sub.add_parser("compute-scope-hash")
    p_hash.add_argument("--scope-from-stdin", action="store_true")

    # Lock subcommands
    p_lock = sub.add_parser("acquire-lock")
    p_lock.add_argument("path")
    p_lock.add_argument("--max-age", type=int, default=DEFAULT_LOCK_TTL_SECONDS)

    p_unlock = sub.add_parser("release-lock")
    p_unlock.add_argument("path")

    args = parser.parse_args(argv)
    return _dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
```

Exit codes:

- `0` for normal success (including `is_sha_reachable=False`, which
  prints `False` and exits 0 — boolean is a result, not an error).
- `2` for `DetachedHeadError` from `detect_current_branch`.
- `3` for `RunLockError` from `acquire-lock`.
- `1` for unexpected exceptions.

The agent's `<helper_invocation>` block collapses from nine heredocs to
nine one-liners:

```bash
uv run python -m audit_orchestrator detect-base-ref --repo .
uv run python -m audit_orchestrator detect-current-branch --repo .
uv run python -m audit_orchestrator branch-slug <branch> .spx/audits/<lang>
uv run python -m audit_orchestrator acquire-lock .spx/audits/<lang>/<slug>.md.lock
uv run python -m audit_orchestrator release-lock .spx/audits/<lang>/<slug>.md.lock
uv run python -m audit_orchestrator branch-scope <base> --patterns '*.py' --repo .
uv run python -m audit_orchestrator modified-since <prior_sha> --patterns '*.py' --repo .
uv run python -m audit_orchestrator is-sha-reachable <prior_sha> --repo .
uv run python -m audit_orchestrator compute-scope-hash --scope-from-stdin
```

The multi-line `python -c` sketch for state operations stays as-is.

## Tests

A new file
`spx/21-spec-tree.enabler/65-auditing.enabler/tests/test_audit_orchestrator_cli.scenario.l1.py`:

- `main(["detect-base-ref", "--repo", str(repo)])` writes `main\n` to stdout.
- `main(["detect-current-branch", "--repo", str(repo_detached)])` exits 2.
- `main(["branch-slug", "feature/x", str(state_dir)])` writes `feature__x\n`.
- `main(["acquire-lock", str(path)])` exits 0 on first call, 3 on second.
- `main(["is-sha-reachable", "0"*40, "--repo", str(repo)])` writes `False\n`,
  exits 0.

Use `pytest.CaptureFixture` to assert on stdout and the `SystemExit` code
to assert on exit codes. Each test invokes `main()` in-process so the
test does not pay the `uv run` startup cost per call.

## Estimated effort

- ~80 lines of argparse + dispatch in `audit_orchestrator.py` (or sibling
  `__main__.py` if the existing file gets too long).
- ~10 scenario tests for the CLI surface.
- ~30 lines of prose updates in `auditor.md`'s `<helper_invocation>` block.
- One pass through `just check` and the code/test auditors.

Approximate landing budget: one focused session, similar in shape to the
PRIORITY 1 / PRIORITY 2 passes that landed the state-file helpers.

## What this plan is not

- Not a redesign of the state-handling protocol. Stateful operations
  remain as the multi-line Python sketch.
- Not a Python package conversion of the helper module. The
  `audit_orchestrator.py` file stays a single skill-co-located script
  per `spx/21-spec-tree.enabler/17-auditing.adr.md`.
- Not a replacement for `importlib`-based test loading. Tests continue
  to load the module via absolute path; the CLI is a parallel surface,
  not a substitute.

## When to remove this PLAN.md

After the dispatcher lands and `auditor.md` is updated to use the
one-liners, this file should be deleted. Per spec-tree convention,
PLAN.md is non-durable coordination — it exists only while the work
is deferred.

---

## PLAN: verdict-format carrier alignment and orchestrator/dispatched coherence

Captured for the next session. Discovered during PR #10 review of the
audit skill stack against the JSON-flipped `spx/15-audit-verdict-format.pdr.md`
(commit `dd03033`).

### Why this exists

The PDR mandates JSON verdicts. Every audit skill on the branch still emits
markdown verdict blocks. Per the truth hierarchy, the PDR governs; the
skills must change. **However**, the JSON flip overreached in one specific
way: the audit-skill case delivers its verdict into a PR comment (the only
durable cross-CI-run surface), and pure JSON in a PR comment is less
scannable for humans than a markdown summary. The right resolution is not
to revert the JSON contract — it is to refine the PDR so the JSON structural
contract holds inside a markdown carrier delimited by HTML comments, then
update every audit skill to emit that carrier+payload shape.

### What the PDR overreached on

Two clauses I added during the flip are wrong for the audit-skill case
(they were drafted as if every verdict has no carrier — true for the
eval-harness slice, false for audit skills posting to PR comments):

- **MUST: "Emit the verdict as the entire assistant response — no prose
  wrapping, no fenced code blocks"** — wrong for audit-skill-to-PR mode.
- **NEVER: "Wrap the verdict in markdown fences or in any other container"**
  — wrong for the same reason.

These need to be walked back to allow markdown carriers with delimited
JSON blocks while still preserving the JSON structural contract.

### The carrier+payload model

Audit-skill verdicts are delivered as markdown that contains a JSON block
wrapped by HTML comment delimiters:

````markdown
## Verdict: REJECT

<short prose summary for humans>

<!-- AUDIT_VERDICT_JSON_BEGIN -->

```json
{
  "status": "rejected",
  "findings": [
    { "id": 7, "rule": "...", "present": true, "location": "..." }
  ]
}
```

<!-- AUDIT_VERDICT_JSON_END -->

<optional markdown-rendered findings table for human review>
````

The HTML comments survive markdown rendering (GitHub does not strip them),
giving the validator an unambiguous extraction target. The validator
parses the JSON between the delimiters; reviewers read the surrounding
markdown; the next CI run's agent extracts the JSON by the delimiters and
reads prior findings as structured data.

The eval-harness slice keeps pure-JSON output because it has no carrier —
the harness reads the assistant's message directly with no PR comment in
the loop.

### Scope (next-session work)

#### 1. PDR refinement — `spx/15-audit-verdict-format.pdr.md`

Three small edits:

- Drop the MUST clause "Emit the verdict as the entire assistant response —
  no prose wrapping, no fenced code blocks".
- Drop the NEVER clause "Wrap the verdict in markdown fences or in any
  other container".
- Add a new Compliance section (`### Embedded delivery`) describing the
  carrier+payload model: when the verdict is delivered into a markdown
  surface (PR comment, state file, etc.), it is wrapped by
  `<!-- AUDIT_VERDICT_JSON_BEGIN -->` and `<!-- AUDIT_VERDICT_JSON_END -->`
  delimiters around a `` ```json `` fenced block; the validator extracts the
  JSON between the delimiters.

#### 2. Audit-skill verdict-emit alignment

Every audit skill's verdict-emit section in its `SKILL.md` adds the
delimited JSON block to the existing markdown verdict. The markdown
summary stays for human readability; the JSON block is added alongside it
inside the delimiters. Affected skills:

- `plugins/spec-tree/skills/auditing/SKILL.md` (lines 117-150)
- `plugins/spec-tree/agents/auditor.md` (lines 222-264)
- `plugins/spec-tree/skills/auditing-tests/SKILL.md`
- `plugins/spec-tree/skills/auditing-product-decisions/SKILL.md`
- `plugins/typescript/skills/auditing-typescript/SKILL.md` (lines 187-237)
- `plugins/typescript/skills/auditing-typescript-architecture/SKILL.md` (lines 101-159)
- `plugins/typescript/skills/auditing-typescript-tests/SKILL.md` (defers to `/auditing-tests`; aligns when that skill aligns)
- `plugins/python/skills/auditing-python/SKILL.md`
- `plugins/python/skills/auditing-python-architecture/SKILL.md`
- `plugins/python/skills/auditing-python-tests/SKILL.md`
- `plugins/develop/skills/auditing-skills/SKILL.md`
- `plugins/develop/skills/auditing-commands/SKILL.md`
- `plugins/develop/skills/auditing-subagents/SKILL.md`
- `plugins/hdl/skills/reviewing-vhdl/SKILL.md`, `reviewing-systemverilog/SKILL.md` (if they emit a verdict)
- `plugins/prose/skills/auditing-prose/SKILL.md` (if it emits a verdict)

The shape is additive — the markdown verdict stays; the JSON block is
inserted inside the existing verdict section between the new HTML-comment
delimiters.

#### 3. Orchestrator/dispatched-skill alignment

Structural mismatches between `/auditing` and the dispatched language audit
skills, found during the same review:

- **Concern-row mismatch.** `/auditing` declares 6 frozen rows
  (Automated gates, Test execution, Implementation, Test evidence,
  ADR/PDR compliance, Determinism contract). `auditing-typescript`
  emits its own 6 rows with different names (Function comprehension,
  Design coherence, Import structure). `auditing-typescript-architecture`
  emits 7 rows. The orchestrator's frozen contract must align with the
  dispatched skills' tables, or the orchestrator's aggregation breaks.
  Decision needed: do orchestrator rows compose with dispatched-skill
  rows (one orchestrator row per dispatched-skill concern), or do
  dispatched-skill rows compose into orchestrator's frozen taxonomy
  (each dispatched row maps to one orchestrator row)? Either model is
  defensible; the SKILL.md files must agree on which.

- **Phase 1/2 ownership ambiguity.** The orchestrator's Phase 1
  (Automated gates) and Phase 2 (Test execution) run the project's
  validation/test commands. `auditing-typescript`'s Phase 1 and Phase 2
  do the same. If both run, commands execute twice; if only one runs,
  the prose in both files reads as the canonical owner. Decision:
  orchestrator runs gates and tests once; dispatched skills consume
  the result. Update the dispatched-skill prose to say "the
  orchestrator has already produced the gate report — read it from
  the state file rather than re-running commands."

- **"Phase 3" namespace collision.** Orchestrator Phase 3 = "dispatch
  to auditing-{lang}". Dispatched-skill Phase 3 = internal "Code
  Comprehension" with 3.1/3.2/3.3 subsections. Cross-references like
  "see Phase 3" become ambiguous. Decision: rename the dispatched
  skill's internal phases to "Step 3.1 / 3.2 / 3.3" or similar so
  "Phase N" without further qualification always means the orchestrator's
  phase.

#### 4. Spot defects in `plugins/typescript/skills/auditing-typescript/SKILL.md`

Captured in `spx/43-typescript.enabler/ISSUES.md`:

- Typo "Typecsript" → "TypeScript" at line 25.
- Broken `${CLAUDE_SKILL_DIR}/rules/` reference at line 77 — the
  directory does not exist; the skill ships `references/` only.
- `quick_start` invokes `/testing` and `/testing-typescript` (test
  evidence skills) at line 33; the skill itself explicitly delegates
  test concerns to `auditing-typescript-tests` elsewhere. Remove the
  test-skill invocations from `quick_start`.

These can land independently of the carrier+payload work.

### What this plan is not

- Not a revert of the JSON flip. The PDR's structural contract stays JSON.
- Not a rewrite of every audit skill's verdict shape. The markdown summary
  stays; the JSON block is added alongside it.
- Not a redesign of the orchestrator's protocol — only the surface points
  where it overlaps with dispatched skills get aligned.

### When to remove this section

After the PDR refinement lands and every audit skill emits the carrier+payload
shape (or at least every audit skill that runs in CI to a PR comment),
this section should be deleted. The orchestrator/dispatched-skill
alignment can land separately; remove its bullets when each lands.
