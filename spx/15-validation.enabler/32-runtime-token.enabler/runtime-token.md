# Runtime Token Validation

PROVIDES a validator that flags a raw runtime-divergent tool or command name in authored plugin content under `src/plugins/` — a name that renders differently per coding agent and so must be a registry-backed `{{! tool('…') !}}` token or a per-runtime conditional — while passing token-expressed references and an explicit ignore-list of not-yet-converted files
SO THAT the marketplace quality gate and skill, agent, and command authors
CAN keep each generated target's output naming only its own runtime's tools, with a raw literal caught at the validation gate rather than shipped as a foreign instruction into another agent's output

## Assertions

### Scenarios

- Given a file containing a raw runtime-divergent token, when the validator scans it, then it reports the file, line, and token and exits non-zero ([test](tests/test_runtime_token.scenario.l1.py))
- Given a file whose runtime-divergent references are all expressed as `{{! tool('…') !}}` tokens or per-runtime conditionals, when the validator scans it, then it reports nothing and exits zero ([test](tests/test_runtime_token.scenario.l1.py))
- Given a file on the ignore-list, when the validator scans it, then a raw runtime-divergent token in that file is not reported — the ignore-list is the explicit, tracked exception for a not-yet-converted file ([test](tests/test_runtime_token.scenario.l1.py))

### Compliance

- NEVER: the validator passes a raw runtime-divergent token — a name registered in the build's runtime-token registry — in a non-ignored file under `src/plugins/` — because that literal ships into a target whose runtime does not provide it ([test](tests/test_runtime_token.compliance.l1.py))
- ALWAYS: the validator derives its forbidden-name set from the build's runtime-token registry rather than a copied literal list — the registry is the single source of truth for which names diverge per runtime ([test](tests/test_runtime_token.compliance.l1.py))
- ALWAYS: the validator enforces every file under `src/plugins/` by default, exempting only the files named on the ignore-list — a newly added plugin is enforced without being opted in ([test](tests/test_runtime_token.compliance.l1.py))
