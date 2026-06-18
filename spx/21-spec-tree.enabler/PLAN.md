# Plan: Bring the SessionStart hook to the inline-guard form

`spx/15-hook-safety.pdr.md` binds the spec-tree plugin's single `SessionStart` hook. The implementation lags that contract: `src/plugins/spec-tree/hooks/hooks.json` runs `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py` with no explicit `timeout`, no inline floor, and no kill switch. The Python body fails open, but a missing script file at the substituted path errors before that body runs (the load-gate.py drift class). The spec-tree hook's own decision record, `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`, gains the inline-guard conformance assertions once the implementation satisfies them, so the spec tree never asserts compliance ahead of the shipped hook.

## Next implementation step

Rewrite the hook command in `src/plugins/spec-tree/hooks/hooks.json` to the inline-guard shape and rebuild `dist/`:

- an explicit short `timeout`;
- an inline command whose reachable floor is a successful exit emitting a well-formed empty result, so an absent script degrades to a no-op rather than a `python3` error;
- an environment kill switch that disables the hook without editing config or leaving the session;
- no dependency on a version-pinned cache path.

`session-start.py` already returns 0 on every error path; the gap is the command shape in `hooks.json`, not the script body. Verify against the hook-safety validator once it exists (see `spx/15-validation.enabler/PLAN.md`).

## Governing decision

`spx/15-hook-safety.pdr.md` — Product properties 1–2; Audit assertions on the inline floor, optional dependency, and kill switch.
