# Runtime Parameterization

PROVIDES runtime-neutral authoring of divergent references through a source-owned per-runtime registry and registry-backed template tokens
SO THAT plugin authors and the per-target emission step
CAN write one source that renders each tool name, field name, and concept term into every target agent's native surface without privileging one runtime.

## Assertions

### Compliance

- ALWAYS: a registry-backed token renders the build target's name for its capability from the source-owned per-runtime registry of its token kind — `tool('ask_user')` emits `AskUserQuestion` for the Claude target and `request_user_input` for the Codex target, and the `field(…)` and `term(…)` tokens render their own kind's registry the same way ([test](tests/test_runtime_parameterization.compliance.l1.py))
- ALWAYS: a runtime-explicit registry token renders the named runtime's name regardless of the build target — a cross-runtime comparison can name a specific agent's capability on every target ([test](tests/test_runtime_parameterization.compliance.l1.py))
- NEVER: a registry token names a kind the registry lacks, or a capability the build target's kind registry has no name for, without a surrounding per-runtime conditional — the build fails rather than emit an empty or foreign name ([test](tests/test_runtime_parameterization.compliance.l1.py))
- ALWAYS: a per-runtime conditional block wrapping a target-only registry token renders the token only for the named target and emits nothing for the others — a capability absent on a runtime is expressed as fact-level divergence ([test](tests/test_runtime_parameterization.compliance.l1.py))
- ALWAYS: the runtime-token registry is keyed by token kind (`tool`, `field`, `term`), and each kind declares whether the source-layer guard enforces its names — the `tool` and `field` kinds are guard-enforced unique tokens, the `term` kind of common-word concept terms is not, so a kind's names join or stay out of the validation gate's forbidden set explicitly ([test](tests/test_runtime_parameterization.compliance.l1.py))
- ALWAYS: that a raw runtime-divergent name never appears in authored source — the discipline this rendering mechanism exists to make possible — is enforced by the runtime-token validation gate at `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`, not by this node ([audit])
