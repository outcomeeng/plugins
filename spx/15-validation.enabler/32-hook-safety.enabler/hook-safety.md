# Hook Safety Validation

PROVIDES a validator that scans every marketplace plugin's hook configuration across the generated `dist/claude` and `dist/codex` trees and flags any hook that could trap an agent
SO THAT the marketplace quality gate and plugin authors
CAN guarantee no shipped hook violates the deterministic rules of `spx/15-hook-safety.pdr.md`

The same `hooks.json` ships byte-identical to `dist/claude` and `dist/codex`; both runtimes share the hook schema and resolve `${CLAUDE_PLUGIN_ROOT}` (Codex exposes it as a compatibility alias). A non-blocking event is therefore one observational on **every** shipped runtime — the cross-runtime intersection. An event blocking-capable on any one runtime (for example `PostToolUse`, which Codex can use to block continuation) is not a safe event.

## Assertions

### Scenarios

- Given a plugin hook config with a hook registered on a blocking-capable event, when the validator scans the dist trees, then it reports the plugin, file, and event and exits non-zero ([test](tests/test_hook_safety.scenario.l1.py))
- Given a plugin hook config where every hook is non-blocking, declares an explicit timeout, uses a guarded command, and names no version-pinned cache path, when the validator scans the dist trees, then it reports nothing and exits zero ([test](tests/test_hook_safety.scenario.l1.py))

### Compliance

- NEVER: the validator passes a hook registered on any event outside the permitted non-blocking (observe/inject) set — the enforcement is the allowlist, so every blocking-capable event (one where exit 2, a deny or block decision, or a timeout denies or halts the agent's action — such as `PreToolUse`, `Stop`, or `PreCompact`) and every unrecognized event alike is flagged, and a runtime that adds a new blocking event fails closed; the test parametrizes over the source-owned set of known blocking events ([test](tests/test_hook_safety.compliance.l1.py))
- NEVER: the validator passes a hook entry that declares no explicit timeout ([test](tests/test_hook_safety.compliance.l1.py))
- NEVER: the validator passes a hook command that is a bare invocation of a substituted-path script carrying no inline short-circuit fallback — a `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_SKILL_DIR}` path in the `dist/claude` tree or its build-rewritten `${PLUGIN_ROOT}`/`${SKILL_DIR}` form in the `dist/codex` tree, with or without a file extension; the floor's emitting a valid empty result on every branch is the audited inline-guard property of `spx/15-hook-safety.pdr.md`, not this deterministic check ([test](tests/test_hook_safety.compliance.l1.py))
- NEVER: the validator passes a hook command naming a version-pinned plugin cache path ([test](tests/test_hook_safety.compliance.l1.py))
- ALWAYS: the validator applies the rules identically across the generated `dist/claude` and `dist/codex` trees ([test](tests/test_hook_safety.compliance.l1.py))
