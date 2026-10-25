# ISSUES — hook safety enabler

Coordination note; not spec truth.

## Scenario hook configs hand-write the contract vocabulary `spx/15-validation.enabler/32-hook-safety.enabler/tests/test_hook_safety.scenario.l1.py` `SAFE_COMMAND, blocking_config, safe_config, guarded_substituted_config` `source-ownership`

They hand-write the event name "SessionStart" (`SESSION_START_EVENT` in `outcomeeng/validation/hook_contract.py`), the hooks.json schema keys, the timeout value 5, and the commands. No source module owns the schema keys (hooks, matcher, type, command, timeout).

**Settlement condition**: A source contract owns the schema keys, and the scenario configs draw the event name, keys, timeout, and commands from source.

## Compliance hook configs and commands are hand-picked inline `spx/15-validation.enabler/32-hook-safety.enabler/tests/test_hook_safety.compliance.l1.py` `the config() helper, the hand-picked command strings (bare, guarded, leading, quoted, skill-dir, codex-token, extensionless), and the event names "SessionStart", "PostToolUse", "SomeFutureEvent"` `test-owned-data`

Violating cases are inline author-chosen strings and configs rather than whole-payload violating fixtures passed by path.

**Settlement condition**: Violating cases are whole-payload fixtures passed by path.
