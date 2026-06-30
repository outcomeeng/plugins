# Reference Portability Validation

PROVIDES a validator that flags a reference in plugin content under `src/plugins/` pointing into this marketplace's own files — which a consumer checkout does not hold — while passing references to the consumer's own spec tree or to the plugin's own files
SO THAT the marketplace quality gate and skill, agent, and command authors
CAN keep shipped plugin content resolvable in a consumer repository that holds this marketplace's plugins but none of its internal directories

## Assertions

### Scenarios

- Given a file containing a non-portable reference, when the validator scans it, then it reports the file, line, and reference and exits non-zero ([test](tests/test_reference_portability.scenario.l1.py))
- Given a file whose references are all portable, when the validator scans it, then it reports nothing and exits zero ([test](tests/test_reference_portability.scenario.l1.py))

### Compliance

- NEVER: the validator passes a reference that points into this marketplace's own files — a spec-tree node or decision named by its sibling-local numeric prefix outside the illustrative `spx/55-example…` root sentinel (`spx/\d+-…`, such as `spx/15-validation.enabler/…` or `spx/13-plugin-and-runtime-conventions.adr.md`), the invalid `spx/NN-…` placeholder, or a path under one of this marketplace's own roots (`src/plugins/`, `dist/claude/`, `dist/codex/`, an `outcomeeng` toolchain package such as `outcomeeng/validation/…` or `outcomeeng_testing/…`, or a path under the marketplace's own GitHub repo slug such as `outcomeeng/plugins/AGENTS.md` or `outcomeeng/spx/src/types.ts`, caught even inside an absolute checkout path) — because none resolves in a consumer checkout ([test](tests/test_reference_portability.compliance.l1.py))
- ALWAYS: the validator passes a reference a consumer checkout resolves — a generic placeholder (`spx/{…}`) or the illustrative root sentinel (`spx/55-example…`) standing in for an example node, a methodology-universal tree path every consumer holds (a non-numbered `spx/…` such as `spx/EXCLUDE`, `spx/local/…`, `spx/sessions/`), a universal source-tree convention outside the marketplace roots (a bare `src/…` or `dist/…` such as `src/index.ts`), the marketplace's own bare GitHub org/repo slug used as a repo identifier with no trailing path segment (`outcomeeng/plugins`, `outcomeeng/spx`), and the plugin's own files via `${CLAUDE_SKILL_DIR}` or `${CLAUDE_PLUGIN_ROOT}` ([test](tests/test_reference_portability.compliance.l1.py))
