---
name: select-artifacts
user-invocable: false
description: >-
  The registered artifacts and audit skills each changed path selects, resolved
  through the artifact registry the build renders beside this skill's reader.
argument-hint: "<path> [<path> ...]"
allowed-tools: Read, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/select_artifacts.py":*)
---

<objective>
One selection record per supplied path — for each registered kind the path matches, that kind's most specific matching artifact and its detection-less artifacts, in kind declaration order, each with the audit skill it names — with a canonical Python reader for the rendered artifact registry.
</objective>

<invocation>

When `$ARGUMENTS` is empty, load the API reference below without executing a command. A script in a sibling skill of the same plugin imports the reader by file location: from its own `__file__` it climbs to the plugin's `skills/` directory and loads `select-artifacts/scripts/select_artifacts.py`.

When one or more paths are supplied, select for them through this skill's own command:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/select_artifacts.py" "<path>" ["<path>" ...]
```

Pass each repository-relative path as one literal argument. The command reads the rendered `artifact-registry.json` beside the script and prints one JSON array with one record per path in the supplied order: `path`, and `artifacts` as the ordered selection of `{kind, role, plugin, audit, contract}` records. A path matching no registered artifact yields an empty `artifacts` list. A call with no path, and a registry file that is missing, not valid JSON, or lacks a `kinds` list, exit 2 with no selection. A registry failure prints `error: artifact selection failed`, the cause, and the repair on stderr — reinstall or update the spec-tree plugin so the rendered registry ships beside the script; report it as `blocked` with that line and never fabricate a selection.

</invocation>

<api_surface>

The reader lives in `${CLAUDE_SKILL_DIR}/scripts/select_artifacts.py`, and a sibling skill's script imports it as the invocation section states. It is the only shipped reader of the rendered registry, and it owns the document's field names.

| Symbol                                 | Purpose                                                                                                               |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `RegistryField`                        | Field names of the rendered registry document                                                                         |
| `SelectionField`                       | Field names of a selection record: `path`, `artifacts`, `kind`, `role`, `plugin`, `audit`, `contract`                 |
| `load_artifact_registry()`             | The rendered registry beside the script; raises `ValueError` for a document that is not a registry                    |
| `select_artifacts(path, registry)`     | The artifacts one path selects: the most specific match per kind, then that kind's detection-less artifacts, in order |
| `selection_for_paths(paths, registry)` | One selection record per path, in the supplied order                                                                  |

A record's `plugin` names the plugin that ships the artifact's audit skill, `audit` is `null` for an artifact no audit skill governs, and `contract` is the audit contract the registry declares for that skill, `concern` or `artifact-type`. The build renders a `role` and a `contract` for every artifact.

</api_surface>

<selection_rule>

A path matches an artifact when its extension or filename is declared by that artifact's detection and every path pattern the detection carries matches the whole path. When two artifacts of one kind match, the one carrying more path patterns wins, so a path-pattern match beats an extension-only match; two matches carrying the same number of path patterns resolve to the earlier-declared artifact. A kind with a match also selects each of its artifacts that carries no detection. Selection reads the rendered registry alone: no installed skill inventory, path list, or caller-supplied hint plays a part in it.

</selection_rule>

<success_criteria>

- A selection printed by the command is byte-equal, per path, to `select_artifacts` applied to the rendered registry beside the script.
- The registry's field vocabulary, its reader, and the selection rule exist once, in this skill's script.
- The module imports only the Python standard library.

</success_criteria>
