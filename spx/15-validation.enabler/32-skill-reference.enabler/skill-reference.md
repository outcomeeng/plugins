# Skill Reference Validation

PROVIDES a validator that flags a skill reference in authored plugin content and in the toolchain naming a skill no marketplace plugin ships, whether the reference is written literally, through a brace alternation, or through a placeholder template
SO THAT the marketplace quality gate and skill and agent authors
CAN rename, add, and remove skills without leaving a reference to an absent skill behind

## Assertions

### Scenarios

- Given authored content whose every skill reference names a shipped skill, when the validator scans it, then it reports nothing and exits zero ([test](tests/test_skill_reference.scenario.l1.py))
- Given a file that names a skill no marketplace plugin ships, when the validator scans it, then it reports the file, line, and reference and exits non-zero ([test](tests/test_skill_reference.scenario.l1.py))
- Given a file whose placeholder reference no shipped skill name matches, or whose brace alternation names a member no plugin ships, when the validator scans it, then it reports the file, line, reference, and unmatched expansion and exits non-zero ([test](tests/test_skill_reference.scenario.l1.py))

### Compliance

- NEVER: the validator passes a reference to an unshipped skill that its tracked exemption list does not name, in any form it recognizes: a plugin-qualified `<plugin>:<skill>` name, a slash invocation `/<skill>` standing as its own token rather than a path segment, or a placeholder template ([test](tests/test_skill_reference.compliance.l1.py))
- ALWAYS: the validator expands a brace alternation such as `{code|tests|architecture}` over each member, and passes any other brace placeholder, such as `{type}` or `{role}`, only when at least one shipped skill name matches the template with the placeholder standing for one or more name characters ([test](tests/test_skill_reference.compliance.l1.py))
- ALWAYS: the validator derives the shipped skill set from the skill directories under `src/plugins/` and the plugin names from the committed marketplace catalog, never from a copied list ([test](tests/test_skill_reference.compliance.l1.py))
- ALWAYS: the validator passes a plugin-qualified `<plugin>:<name>` reference whose name is a subagent definition that plugin ships under its `agents/` directory, and flags the same name qualified under a plugin that ships no such definition or written as a slash invocation `/<name>` ([test](tests/test_skill_reference.compliance.l1.py))
- ALWAYS: the validator scans every file under `src/plugins/`, `src/_shared/`, `src/templates/`, `outcomeeng/`, and `outcomeeng_testing/`, except plugin changelogs, inert test fixtures, tool-generated directories such as caches and virtual environments, a slash invocation of a harness command on its harness-command list, and a slash token naming a top-level filesystem directory ([test](tests/test_skill_reference.compliance.l1.py))

### Mappings

- ALWAYS: every file of this repository the validator scans passes it, the validator passing a reference to an unshipped skill only when its tracked exemption list names that reference together with the Change that removes it ([test](tests/test_skill_reference.mapping.l1.py))
