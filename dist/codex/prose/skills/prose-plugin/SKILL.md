---
name: prose-plugin
description: >-
  ALWAYS invoke this skill to operate the prose plugin's own lifecycle in a checkout — report its version, manage whatever checkout footprint this plugin owns on the running agent, and check that footprint. Invoke it when this plugin's agents are missing from a session. NEVER hand-copy a plugin's agent definitions into a checkout or hand-edit them once placed.
argument-hint: "[help|version|init|upgrade|check]"
allowed-tools: Read, Bash(python3 "${SKILL_DIR}/scripts/place_agents.py":*)
---

<objective>
The prose plugin's consumer-side footprint reported, placed, or refreshed in the invocation checkout, bounded to the namespace this plugin owns.
</objective>

<verbs>

Select one verb from the invocation. `help` is the default when none is given.

| Verb      | Result                                                                             |
| --------- | ---------------------------------------------------------------------------------- |
| `help`    | This plugin's verbs and what each one changes                                      |
| `version` | The plugin version the running session resolved                                    |
| `init`    | This plugin's checkout footprint established for this version                      |
| `upgrade` | This plugin's checkout footprint brought to this version, retiring what it dropped |
| `check`   | Whether the checkout's footprint matches this version, changing nothing            |

This agent's plugin manifest cannot declare agents, so `init`, `upgrade`, and `check` own this plugin's checkout footprint. When the plugin ships no agent definitions, they report that and change nothing.

</verbs>

<version_reporting>

`version` reports the version of the plugin directory the session actually resolved. Read exactly one file:

```text
${SKILL_DIR}/../../.codex-plugin/plugin.json
```

That path is relative to this skill's own directory, so it resolves inside whichever plugin copy the session loaded. A session may resolve a plugin from its marketplace source tree or from a versioned cache snapshot, and those diverge — so the version a reader needs is the one backing the running session, never the newest on disk elsewhere. Every plugin tree carries both manifest directories; read the one named above and never the other, because only that one is authoritative for the agent this copy was rendered for.

</version_reporting>

<placement>

Placement runs the bundled script, which writes every agent definition this plugin ships into the checkout's agent directory, the only path by which this agent's session receives them:

```bash
python3 "${SKILL_DIR}/scripts/place_agents.py" --checkout <repository-root>
```

The script owns the whole footprint operation: it writes this plugin's definitions, removes definitions that carry this plugin's prefix but no longer ship with it, and leaves every other file in that directory untouched. `check` passes `--check`, which reports drift and writes nothing.

Definitions are generated at build time and ship inside this skill, so placement is a file copy. Claude never edits a placed definition, and never converts, rewrites, or hand-authors one — a placed file that needs to change is changed at its source and re-placed.

</placement>

<persistence>

Placed definitions are durable checkout configuration, not local runtime output. Commit them. A session the placing verb never ran in — a hosted run, a continuous-integration job, a colleague's fresh clone — receives this plugin's agents only from the committed directory. Ignoring these files instead grants agents to whoever ran the verb and withholds them everywhere else.

`upgrade` changes the committed set rather than only adding to it. A version that renames an agent writes the new definition and removes the old one; a version that retires an agent removes it and writes nothing back. Git reports the first as a rename when the two definitions stay similar enough to pair and as a deletion plus an addition when they do not, and reports the second as a deletion. Those removals are the verb working. Commit them alongside the additions: restoring a removed definition keeps a retired agent dispatchable and leaves the checkout claiming a version it no longer carries.

An upgrade that renames one definition, retires another, and revises a third leaves this `git status --short` shape in the agent directory:

```text
R  prose_old-name -> prose_new-name
D  prose_retired-name
M  prose_revised-name
```

All three lines belong in one commit. Before committing, confirm every changed path falls inside the namespace `<ownership_boundary>` defines.

A committed set means each version bump shows in the diff. That cost buys every session the same agents, including the sessions that can run no verb at all.

</persistence>

<ownership_boundary>

This plugin places and prunes only within the namespace its own name prefixes. Agent definitions a developer authored, and definitions another plugin provides, are outside that namespace and stay untouched even when their content matches what this plugin would write.

A file inside the namespace is this plugin's to replace or remove. A file outside it is never this plugin's to claim, and matching content is not ownership.

</ownership_boundary>

<failure_modes>

**Claude hand-copied the agent definitions instead of running the script.**

The definitions were placed by hand from the skill directory, so pruning never ran and a definition retired in a later version stayed behind, shadowing nothing but reported as current. Run the script; it owns placement and pruning together.

**Claude treated the removals an upgrade made as damage.**

An upgrade retired one definition and renamed another, so the diff carried two deletions. Claude restored them, and the checkout kept dispatching an agent the plugin no longer ships while `check` reported drift that never cleared. Commit the removals with the additions; the verb prunes only inside this plugin's prefix, so a removal there is the upgrade, never a loss.

**Claude reported the version from a manifest elsewhere on disk.**

A marketplace source tree and a cache snapshot both carry a manifest, and they diverge, and each plugin tree carries a manifest directory per agent. The reported version described a plugin the session was not running. Read the one skill-directory-relative path `<version_reporting>` names, resolving it rather than searching for a manifest.

</failure_modes>

<success_criteria>

- Exactly one verb runs per invocation, defaulting to `help`.
- `version` reads only the skill-directory-relative manifest path named above, never another copy on disk.
- Placement and pruning happen through the bundled script, never by hand.
- Every file written or removed carries this plugin's namespace prefix; no other file in the agent directory changes.
- `check` writes nothing and reports drift.
- After `upgrade`, a `git status --short` over the agent directory reports no outstanding change: every addition, removal, and rename it produced is committed.

</success_criteria>
