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
