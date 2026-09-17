# Artifact Registry

PROVIDES the registry of artifact kinds the marketplace ships — each kind's artifacts, their detection features and precedence, and the architect, author, and audit skills and shared standard governing each — rendered by the build into every shipped consumer
SO THAT audit orchestration, instruction-block generation, and kind-dispatching skills
CAN read one declaration of what the marketplace governs instead of probing installed skills or keeping a copy

The registry is one source-owned declaration. Each registered kind names the artifacts it produces — implementation code, tests, architecture decisions, and the artifacts later kinds add — and for each artifact the detection features that select it (a file extension, a path pattern, a filename) and the architect, author, and audit skills and the shared standard that govern it; a kind names one architect per artifact that needs one. Selection resolves a changed path to the registered artifacts whose detection matches it. When two artifacts of one kind match, the most specific detection wins: a match carrying a path pattern beats an extension-only match. An artifact carrying no detection is selected through its kind when the same changeset selects another artifact of that kind; the architecture artifact is selected that way. A path matching no registered artifact selects nothing. The build renders the declaration into a data file beside every shipped script that reads it, so a shipped consumer knows every artifact the marketplace ships whether or not the consuming repository has installed the plugin, and no consumer keeps its own copy. The installed skill inventory never selects; it decides only whether a selected skill runs or is recorded as missing.

## Assertions

### Mappings

- ALWAYS: the build renders the registry into every shipped consumer's sibling data file, and each rendered file equals the declaration it renders ([test](tests/test_artifact_registry.mapping.l1.py))
- For every registered artifact, one path matching its detection selects that artifact and its audit skill; a path matching two artifacts of one kind selects the most specific; a kind with a match selects its detection-less architecture artifact; a path matching nothing selects nothing ([test](tests/test_artifact_registry.mapping.l1.py))

### Compliance

- NEVER: the `manifests` validation step accepts a registered artifact naming a skill its kind's plugin surface does not ship — the failure names the artifact and the missing skill ([test](tests/test_artifact_registry.compliance.l1.py))
- ALWAYS: the registry is one source-owned declaration in which every registered kind names each artifact it produces, its detection features or its selecting artifact, and the architect, author, and audit skills and shared standard that govern it, with one architect per artifact that needs one ([audit])
- NEVER: the implementation audit's orchestration, its wrapper agent, or the instruction-block generator carries its own list of kinds, artifacts, or extensions — each reads the rendered registry ([audit])
