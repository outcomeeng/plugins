# Runtime Token Validation

PROVIDES a validator that flags a raw runtime-divergent name in authored source the build renders or inlines — plugin content under `src/plugins/`, shared fragments under `src/_shared/`, and per-plugin templates under `src/templates/` — a name that renders differently per coding agent and so must be a registry-backed token such as `{{! tool('…') !}}` / `{{! file('…') !}}`, or a per-runtime conditional — while passing token-expressed references and an explicit ignore-list of tracked exemptions
SO THAT the marketplace quality gate and skill and agent authors
CAN keep each generated target's output naming only its own native tools and instruction files, with a raw literal caught at the validation gate rather than shipped as a foreign instruction into another agent's output

## Assertions

### Mappings

- ALWAYS: a raw runtime-divergent token maps to its file, line, and token in a
  non-zero validation result ([test](tests/test_runtime_token.mapping.l1.py)).
- ALWAYS: runtime-divergent references expressed as `{{! tool('…') !}}` tokens
  or matching per-runtime conditionals map to no validation result
  ([test](tests/test_runtime_token.mapping.l1.py)).
- ALWAYS: a raw runtime-divergent token in an ignore-listed file maps to no
  validation result — the ignore-list is the explicit, tracked exemption for a
  file that needs a conversion exemption, an authored file of the
  instruction-block node whose subject is the two named instruction files, or a
  runtime-neutral citation surface that names both instruction filenames as
  citation targets for any repo under review
  ([test](tests/test_runtime_token.mapping.l1.py)).

### Compliance

- ALWAYS: the configuration guard scans every file under `src/`, including
  conditional blocks and files exempted from other token checks, and reports
  the path and line of each literal model identifier or authored native model
  or reasoning assignment; profile selection and generated configuration
  requests pass ([test](tests/test_profile_configuration.compliance.l1.py)).
- ALWAYS: the configuration guard derives model identifiers and native fields
  from their owning configuration definitions, detecting both independent
  configuration overrides and model identifiers absent from the selected
  profiles without maintaining a second model inventory
  ([test](tests/test_profile_configuration.mapping.l1.py)).
- NEVER: skill frontmatter declares a model or reasoning override, whether
  literal or template-generated; the guard reports it before distribution
  ([test](tests/test_profile_configuration.compliance.l1.py)).
- NEVER: the configuration guard treats an ordinary prose word as a model or
  reasoning assignment merely because it is a native configuration value
  ([test](tests/test_profile_configuration.compliance.l1.py)).
- NEVER: the validator passes a raw runtime-divergent token — a name registered in a guard-enforced kind (`tool`, `field`, `file`) of the build's runtime-token registry — in a non-ignored file under `src/plugins/` — because that literal ships into a target whose runtime does not provide it ([test](tests/test_runtime_token.compliance.l1.py))
- ALWAYS: the validator derives its forbidden-name set from the guard-enforced kinds (`tool`, `field`, `file`) of the build's runtime-token registry rather than a copied literal list — the registry is the single source of truth for which names diverge per runtime ([test](tests/test_runtime_token.mapping.l1.py))
- NEVER: the validator's forbidden-name set includes a name registered only in the review-only `term` kind — concept terms are common words a whole-token match would flag throughout prose, so the guard excludes them and review covers them instead ([test](tests/test_runtime_token.compliance.l1.py))
- ALWAYS: the validator enforces every authored-source file the build renders or inlines — plugin content under `src/plugins/`, shared fragments under `src/_shared/`, and per-plugin templates under `src/templates/` — by default, exempting only the files named on the ignore-list, so a newly added plugin, shared fragment, or template is enforced without being opted in ([test](tests/test_runtime_token.compliance.l1.py))
