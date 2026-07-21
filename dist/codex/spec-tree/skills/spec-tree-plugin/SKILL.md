---
name: spec-tree-plugin
description: >-
  ALWAYS invoke this skill to operate the spec-tree plugin's own lifecycle in a checkout — report its version, install or refresh the agent definitions it provides when they are missing, and check its footprint. NEVER hand-copy a plugin's agent definitions into a checkout or hand-edit them once placed.
argument-hint: "[help|version|init|upgrade|check]"
allowed-tools: Read, Bash(python3 "${SKILL_DIR}/scripts/place_agents.py":*)
---

<objective>
The spec-tree plugin's consumer-side footprint reported, placed, or refreshed in the invocation checkout, bounded to the namespace this plugin owns.
</objective>

<verbs>

Select one verb from the invocation. `help` is the default when none is given.

| Verb      | Result                                                                               |
| --------- | ------------------------------------------------------------------------------------ |
| `help`    | This plugin's verbs and what each one changes                                        |
| `version` | The plugin version the running session resolved                                      |
| `init`    | The plugin's agent definitions placed into the checkout's agent directory            |
| `upgrade` | The placed definitions brought to this version, retiring any a later version dropped |
| `check`   | Whether the checkout's placed definitions match this version, changing nothing       |

`init`, `upgrade`, and `check` operate only where this plugin ships agent definitions. When it ships none, they report that and change nothing — the plugin has no consumer-side footprint to manage.

</verbs>

<version_reporting>

`version` reports the version of the plugin directory the session actually resolved. Read exactly one file:

```text
${SKILL_DIR}/../../.codex-plugin/plugin.json
```

That path is relative to this skill's own directory, so it resolves inside whichever plugin copy the session loaded. A session may resolve a plugin from its marketplace source tree or from a versioned cache snapshot, and those diverge — so the version a reader needs is the one backing the running session, never the newest on disk elsewhere. Every plugin tree carries both manifest directories; read the one named above and never the other, because only that one is authoritative for the agent this copy was rendered for.

</version_reporting>

<placement>

Placement runs the bundled script, which writes every agent definition this plugin ships into the checkout's agent directory for an agent whose plugin manifest cannot declare agents:

```bash
python3 "${SKILL_DIR}/scripts/place_agents.py" --checkout <repository-root>
```

The script owns the whole footprint operation: it writes this plugin's definitions, removes definitions that carry this plugin's prefix but no longer ship with it, and leaves every other file in that directory untouched. `check` passes `--check`, which reports drift and writes nothing.

Definitions are generated at build time and ship inside this skill, so placement is a file copy. Claude never edits a placed definition, and never converts, rewrites, or hand-authors one — a placed file that needs to change is changed at its source and re-placed.

</placement>

<ownership_boundary>

This plugin places and prunes only within the namespace its own name prefixes. Agent definitions a developer authored, and definitions another plugin provides, are outside that namespace and stay untouched even when their content matches what this plugin would write.

A file inside the namespace is this plugin's to replace or remove. A file outside it is never this plugin's to claim, and matching content is not ownership.

</ownership_boundary>

<failure_modes>

**Claude hand-copied the agent definitions instead of running the script.**

The definitions were placed by hand from the skill directory, so pruning never ran and a definition retired in a later version stayed behind, shadowing nothing but reported as current. Run the script; it owns placement and pruning together.

**Claude reported the version from a manifest elsewhere on disk.**

A marketplace source tree and a cache snapshot both carry a manifest, and they diverge, and each plugin tree carries a manifest directory per agent. The reported version described a plugin the session was not running. Read the one skill-directory-relative path `<version_reporting>` names, resolving it rather than searching for a manifest.

</failure_modes>

<success_criteria>

- Exactly one verb runs per invocation, defaulting to `help`.
- `version` reads only the skill-directory-relative manifest path named above, never another copy on disk.
- Placement and pruning happen through the bundled script, never by hand.
- Every file written or removed carries this plugin's namespace prefix; no other file in the agent directory changes.
- `check` writes nothing and reports drift.

</success_criteria>
