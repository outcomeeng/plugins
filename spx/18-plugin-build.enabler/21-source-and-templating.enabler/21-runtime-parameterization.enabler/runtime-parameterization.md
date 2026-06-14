# Runtime Parameterization

PROVIDES runtime-neutral authoring of divergent references through a source-owned per-runtime registry, registry-backed template tokens, and a source-layer guard
SO THAT plugin authors and the per-target emission step
CAN write one source that renders each tool name, field name, and concept term into every target agent's native surface without privileging one runtime.

## Assertions

### Compliance

- ALWAYS: a registry-backed token renders the build target's name for its capability from the source-owned per-runtime registry — `tool('ask_user')` emits `AskUserQuestion` for the Claude target and `request_user_input` for the Codex target ([test](tests/test_runtime_parameterization.compliance.l1.py))
- ALWAYS: a runtime-explicit registry token renders the named runtime's name regardless of the build target — a cross-runtime comparison can name a specific agent's tool on every target ([test](tests/test_runtime_parameterization.compliance.l1.py))
- NEVER: a runtime-divergent unique token registered as a capability's per-runtime name (for example `AskUserQuestion` or `ScheduleWakeup`) appears in authored `src/plugins/` content outside a registry token or a per-runtime conditional — the source-layer guard fails the build ([test](tests/test_runtime_parameterization.compliance.l1.py))
- NEVER: a registry token names a capability the build target's registry has no name for without a surrounding per-runtime conditional — the build fails rather than emit an empty or foreign name ([test](tests/test_runtime_parameterization.compliance.l1.py))
