---
id: 01a1051e-4491-75d5-a324-76e29cffac18
malleability: spec
---

# Artifact Registry

PROVIDES the registry of every artifact kind the marketplace ships — each kind's artifacts, their detection features and precedence, and the author, audit and standards skills governing each — rendered by the build into a data file beside its provider skill's reader
SO THAT audit orchestration and kind-dispatching skills
CAN read one declaration of what the marketplace governs instead of probing installed skills or keeping a copy

The registry is one source-owned declaration. Each registered kind names the artifacts it produces and, for each artifact, the detection features that select it (a file extension, a path pattern, a filename) or the artifact that selects it, and the author, audit and standards skills that govern it. A code kind names its implementation, test and architecture artifacts; every other kind names the one artifact it produces.

Selection resolves a changed path to the registered artifacts whose detection matches it. When two artifacts of one kind match, the most specific detection wins: a match carrying a path pattern beats an extension-only match. An artifact carrying no detection is selected through its kind when the same changeset selects another artifact of that kind; the architecture artifact is selected that way. A path matching no registered artifact selects nothing. An artifact whose audit skill follows a contract other than the concern contract keeps its row and names that skill, so a path it selects is accounted for under that skill's name and never dispatched as a concern.

The build renders the declaration into one data file beside the shipped reader that owns it — a provider skill whose script every consuming script imports — so a shipped consumer knows every artifact the marketplace ships whether or not the consuming repository has installed the plugin, and no consumer keeps its own copy of the document, its field names or the selection rule. The installed skill inventory never selects; it decides only whether a selected skill runs or is recorded as missing.

## Assertions

### Mappings

- ALWAYS: the build renders the registry into the data file beside the provider skill's reader, and the rendered file equals the declaration it renders ([test](tests/test_artifact_registry.mapping.l1.py))
- For every registered artifact, one path matching its detection selects that artifact and its audit skill; a path matching two artifacts of one kind selects the most specific; a kind with a match selects its detection-less architecture artifact; a path matching nothing selects nothing ([test](tests/test_artifact_registry.mapping.l1.py))

### Compliance

- ALWAYS: the registry is one source-owned declaration in which every registered kind names each artifact it produces, its detection features or its selecting artifact, and the author, audit and standards skills that govern it; the kinds are the four code kinds with their implementation, test and architecture artifacts, decision records, specs, skills, subagent definitions, prose and the Change record ([audit])
- NEVER: the `manifests` validation step accepts a registered artifact naming a skill its kind's plugin does not ship; the failure names the artifact and the missing skill ([test](tests/test_artifact_registry.compliance.l1.py))
- NEVER: the implementation audit's orchestration or its wrapper agent carries its own list of kinds, artifacts or extensions, or its own reader of the rendered registry; each reaches the provider skill's reader by import ([audit])
