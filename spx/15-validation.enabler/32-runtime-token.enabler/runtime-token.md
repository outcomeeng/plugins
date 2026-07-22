# Runtime Token Validation

PROVIDES a validator that flags a raw runtime-divergent name in authored source the build renders or inlines — plugin content under `src/plugins/`, shared fragments under `src/_shared/`, and per-plugin templates under `src/templates/` — a name that renders differently per coding agent and so must be a registry-backed token such as `{{! tool('…') !}}` / `{{! file('…') !}}`, or a per-runtime conditional — while passing token-expressed references and an explicit ignore-list of tracked exemptions
SO THAT the marketplace quality gate and skill and agent authors
CAN keep each generated target's output naming only its own native tools and instruction files, with a raw literal caught at the validation gate rather than shipped as a foreign instruction into another agent's output

## Assertions

### Scenarios

- Given a file containing a raw runtime-divergent token, when the validator scans it, then it reports the file, line, and token and exits non-zero ([test](tests/test_runtime_token.scenario.l1.py))
- Given a file whose runtime-divergent references are all expressed as `{{! tool('…') !}}` tokens or per-runtime conditionals, when the validator scans it, then it reports nothing and exits zero ([test](tests/test_runtime_token.scenario.l1.py))
- Given a file on the ignore-list, when the validator scans it, then a raw runtime-divergent token in that file is not reported — the ignore-list is the explicit, tracked exception for a not-yet-converted file, an authored file of the instruction-block node whose subject is the two named instruction files, or a runtime-neutral citation surface that names both instruction filenames as citation targets for any repo under review ([test](tests/test_runtime_token.scenario.l1.py))

### Compliance

- NEVER: the validator passes a raw runtime-divergent token — a name registered in a guard-enforced kind (`tool`, `field`, `file`) of the build's runtime-token registry — in a non-ignored file under `src/plugins/` — because that literal ships into a target whose runtime does not provide it ([test](tests/test_runtime_token.compliance.l1.py))
- ALWAYS: the validator derives its forbidden-name set from the guard-enforced kinds (`tool`, `field`, `file`) of the build's runtime-token registry rather than a copied literal list — the registry is the single source of truth for which names diverge per runtime ([test](tests/test_runtime_token.compliance.l1.py))
- NEVER: the validator's forbidden-name set includes a name registered only in the review-only `term` kind — concept terms are common words a whole-token match would flag throughout prose, so the guard excludes them and review covers them instead ([test](tests/test_runtime_token.compliance.l1.py))
- ALWAYS: the validator enforces every authored-source file the build renders or inlines — plugin content under `src/plugins/`, shared fragments under `src/_shared/`, and per-plugin templates under `src/templates/` — by default, exempting only the files named on the ignore-list, so a newly added plugin, shared fragment, or template is enforced without being opted in ([test](tests/test_runtime_token.compliance.l1.py))
