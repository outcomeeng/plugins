# Reference Portability Validation

PROVIDES a validator that flags a reference in plugin content under `src/plugins/` pointing into this marketplace's own files — which a consumer checkout does not hold — while passing references to the consumer's own spec tree or to the plugin's own files
SO THAT the marketplace quality gate and skill, agent, and command authors
CAN keep shipped plugin content resolvable in a consumer repository that holds this marketplace's plugins but none of its internal directories

## Assertions

### Compliance

- NEVER: the validator passes a reference that points into this marketplace's own files — a spec-tree node or decision named by its sibling-local numeric prefix (`spx/\d+-…`, such as `spx/15-validation.enabler/…` or `spx/13-plugin-and-runtime-conventions.adr.md`), or a repository path segment under `src/`, `dist/`, or `outcomeeng/` (caught even inside an absolute checkout path) — because none resolves in a consumer checkout; the validator passes a generic consumer-tree placeholder (`spx/{…}`), a methodology-universal tree path every consumer holds (a non-numbered `spx/…` such as `spx/EXCLUDE`, `spx/CLAUDE.md`, `spx/local/…`, `spx/sessions/`), and the plugin's own files via `${CLAUDE_SKILL_DIR}` or `${CLAUDE_PLUGIN_ROOT}` ([test](tests/test_reference_portability.compliance.l1.py))
