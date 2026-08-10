# Grant Locality Validation

PROVIDES a validator that flags a skill tool grant naming a path outside the granting skill's own directory, in either agent target's spelling of the skill-directory variable
SO THAT the marketplace quality gate and skill authors
CAN keep a shared script reachable through a consumer-owned entrypoint whose coupling breaks loudly, rather than through a permission string that degrades to a prompt when the provider moves

A grant that walks out of the skill directory puts the provider skill's name and internal script layout into a permission, where no import graph, type checker, or test follows it. Renaming the provider or moving its `scripts/` directory leaves every such grant matching nothing, and the call falls back to a permission prompt instead of failing. Ownership by a provider skill with a `__file__`-relative import from the consumer's own entrypoint keeps that coupling in Python, where a moved module raises at load.

Grant locality is decided by `spx/13-plugin-and-runtime-conventions.adr.md`; this node is its deterministic enforcement over shipped skill frontmatter.

## Assertions

### Scenarios

- Given a `SKILL.md` whose `allowed-tools` grants a path under `${CLAUDE_SKILL_DIR}/..`, when the validator scans it, then it reports the file, line, and grant and exits non-zero ([test](tests/test_grant_locality.scenario.l1.py))
- Given a `SKILL.md` whose grants all name paths inside its own directory, when the validator scans it, then it reports nothing and exits zero ([test](tests/test_grant_locality.scenario.l1.py))

### Compliance

- NEVER: the validator passes an `allowed-tools` grant whose skill-directory reference escapes that directory, in either agent target's spelling of the variable — the Claude spelling and the Codex spelling name one authored token, so a rule reading only one spelling misses every skill in the other generated tree ([test](tests/test_grant_locality.compliance.l1.py))
- ALWAYS: the validator reads grants only from an `allowed-tools` field declaration, so a skill body that quotes or documents an escaping grant is not itself a violation ([test](tests/test_grant_locality.compliance.l1.py))
- ALWAYS: the validator reads an `allowed-tools` value in either frontmatter form the marketplace uses — the inline scalar and the YAML list carrying each grant on its own indented line — because a rule reading only the declaration line passes every escaping grant written as a list item ([test](tests/test_grant_locality.compliance.l1.py))
- ALWAYS: the validator passes a skill-directory reference that stays inside the directory, including a descent that returns to it, because such a path resolves within the skill and names no sibling ([test](tests/test_grant_locality.compliance.l1.py))
