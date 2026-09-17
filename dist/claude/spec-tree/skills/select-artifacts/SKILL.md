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
One selection record per supplied path — the registered artifacts whose detection matches it, most specific first, and the audit skill each names — with a canonical Python reader for the rendered artifact registry.
</objective>

<invocation>

When `$ARGUMENTS` is empty, load the API reference below without executing a command. Script consumers import the provider.

When one or more paths are supplied, select for them through this skill's own command:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/select_artifacts.py" "<path>" ["<path>" ...]
```

Pass each repository-relative path as one literal argument. The command reads the rendered `artifact-registry.json` beside the script and prints one JSON array with one record per path in the supplied order: `path`, and `artifacts` as the ordered selection of `{kind, role, audit}` records. A path matching no registered artifact yields an empty `artifacts` list. A missing, unrendered, or malformed registry exits 2 with `error: artifact selection failed` on stderr and no selection; report it as `blocked` and never fabricate a selection.

</invocation>

<api_surface>

The reader lives in `${CLAUDE_SKILL_DIR}/scripts/select_artifacts.py`, imported by sibling skills' scripts through the marketplace skill-co-located importlib convention (no path is hardcoded in agent prose). It is the only shipped reader of the rendered registry; a sibling script carries no copy of the document or its field names.

| Symbol                                 | Purpose                                                                                                               |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `RegistryField`                        | Field names of the rendered registry document                                                                         |
| `SelectionField`                       | Field names of a selection record: `path`, `artifacts`, `kind`, `role`, `audit`                                       |
| `load_artifact_registry()`             | The rendered registry beside the script; raises `ValueError` for a document that is not a registry                    |
| `select_artifacts(path, registry)`     | The artifacts one path selects: the most specific match per kind, then that kind's detection-less artifacts, in order |
| `kind_by_extension(registry)`          | Each declared extension mapped to its kind; raises `ValueError` for an extension declared under two kinds             |
| `selection_for_paths(paths, registry)` | One selection record per path, in the supplied order                                                                  |

</api_surface>

<selection_rule>

A path matches an artifact when its extension or filename is declared by that artifact's detection and every path pattern the detection carries matches the whole path. When two artifacts of one kind match, the one carrying a path pattern wins over an extension-only match. A kind with a match also selects each of its artifacts that carries no detection; the architecture artifact is selected that way. Selection reads the rendered registry alone: no installed skill inventory, path list, or caller-supplied hint plays a part in it.

</selection_rule>

<success_criteria>

- A selection printed by the command is byte-equal, per path, to `select_artifacts` applied to the rendered registry beside the script.
- The registry's field vocabulary, its reader, and the selection rule exist once, in this skill's script; every sibling consumer reaches them by import.
- The module imports only the Python standard library.

</success_criteria>
