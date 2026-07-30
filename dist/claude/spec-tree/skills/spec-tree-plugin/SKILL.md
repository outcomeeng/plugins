---
name: spec-tree-plugin
description: >-
  ALWAYS invoke this skill to operate the spec-tree plugin's own lifecycle in a checkout — report its version, manage whatever checkout footprint this plugin owns on the running agent, and check that footprint. Invoke it when this plugin's agents are missing from a session. NEVER hand-copy a plugin's agent definitions into a checkout or hand-edit them once placed.
argument-hint: "[help|version|init|upgrade|check]"
allowed-tools: Read, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/place_agents.py":*)
---

<objective>
The spec-tree plugin's consumer-side footprint reported, placed, or refreshed in the invocation checkout, bounded to the namespace this plugin owns.
</objective>

<verbs>

Read `$ARGUMENTS`, trim it, and match it against the table below. One verb runs per invocation; `help` is the default when `$ARGUMENTS` is empty. Text matching no row is an error naming the five verbs, never a guessed match.

| Verb      | Result                                                                               |
| --------- | ------------------------------------------------------------------------------------ |
| `help`    | This plugin's verbs, what each one changes, and where its changelogs are             |
| `version` | The plugin version the running session resolved                                      |
| `init`    | This plugin's checkout footprint established for this version †                      |
| `upgrade` | This plugin's checkout footprint brought to this version, retiring what it dropped † |
| `check`   | Whether the checkout's footprint matches this version, changing nothing †            |

† This agent's plugin manifest declares the plugin's agents, so they reach a session through the manifest and no checkout placement applies. `init`, `upgrade`, and `check` report that and change nothing here; they carry the footprint work only for an agent whose manifest cannot declare agents.

</verbs>

<changelogs>

`help` names where a reader answers "what changed for me, and what must I now do?", reading from disk without network access.

This plugin carries two changelogs, each on its own clock. Read one only when the reader asks what changed; never read both by default.

| Line        | Records                                                  | Path                                                 |
| ----------- | -------------------------------------------------------- | ---------------------------------------------------- |
| Marketplace | events no single plugin owns: harnesses, plugins renamed | `${CLAUDE_SKILL_DIR}/../../MARKETPLACE-CHANGELOG.md` |
| Plugin      | what changed in this plugin                              | `${CLAUDE_SKILL_DIR}/../../CHANGELOG.md`             |

The marketplace line records events no single plugin owns, so it ships here rather than in each plugin separately. It is current only as far as its newest entry — the topmost `##` heading, since entries run newest first. Report that date alongside it so the reader can tell whether a later event falls outside this copy.

</changelogs>

<version_reporting>

`version` reports the version of the plugin directory the session actually resolved. Read exactly one file:

```text
${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json
```

That path is relative to this skill's own directory, so it resolves inside whichever plugin copy the session loaded. A session may resolve a plugin from its marketplace source tree or from a versioned cache snapshot, and those diverge — so the version a reader needs is the one backing the running session, never the newest on disk elsewhere. Every plugin tree carries both manifest directories; read the one named above and never the other, because only that one is authoritative for the agent this copy was rendered for.

</version_reporting>

<placement>

Placement does not apply on this agent: its plugin manifest declares the plugin's agents, so the installer delivers them and no file is written into the checkout. The bundled script reports that and exits without changing anything; the call that reports it looks like this:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/place_agents.py" --checkout <repository-root>
```

`init`, `upgrade`, and `check` all report the same and write nothing, because this plugin's agents reach a session through the manifest rather than through the checkout.

</placement>

<persistence>

This agent receives the plugin's agents through its manifest, so the checkout carries no agent files from this plugin and this verb commits nothing.

</persistence>

<ownership_boundary>

This plugin claims no file in the checkout on this agent, because its manifest delivers the agents and no verb writes.

</ownership_boundary>

<failure_modes>

**Claude reported the version from a manifest elsewhere on disk.**

A marketplace source tree and a cache snapshot both carry a manifest, and they diverge, and each plugin tree carries a manifest directory per agent. The reported version described a plugin the session was not running. Read the one skill-directory-relative path `<version_reporting>` names, resolving it rather than searching for a manifest.

</failure_modes>

<success_criteria>

- Exactly one verb runs per invocation, defaulting to `help`.
- `version` reads only the skill-directory-relative manifest path named above, never another copy on disk.
- `help` names exactly the changelog lines `<changelogs>` lists, at the paths given there, and no other line.
  - A reported marketplace date equals the topmost `##` heading in this plugin's marketplace changelog.
- Every footprint verb reports that the manifest delivers this plugin's agents, and writes nothing.

</success_criteria>
