---
name: spec-tree-plugin
description: >-
  ALWAYS invoke this skill to operate the spec-tree plugin's own lifecycle — report its version and check or reconcile its agent-delivery footprint. Invoke it when this plugin's agents are missing from a session. NEVER commit marketplace-delivered agent definitions into a checkout.
argument-hint: "[help|version|init|upgrade|check]"
arguments: verb
allowed-tools: Read
---

<objective>
The spec-tree plugin's resolved version and agent-delivery state reported or reconciled in the scope that carries its skills.
</objective>

<verbs>

Read `$verb`, trim it, and match it against the table. One verb runs per invocation; `help` is the default when `$verb` is empty. Text matching no row is an error naming all five verbs.

| Verb      | Result                                                                                       |
| --------- | -------------------------------------------------------------------------------------------- |
| `help`    | This plugin's verbs, mutation boundaries, reload requirement, and changelog locations        |
| `version` | The version resolved by the running session                                                  |
| `init`    | Missing plugin-owned Codex definitions established in the selected agent home                |
| `upgrade` | Plugin-owned Codex definitions reconciled to this version, including safe stale-file pruning |
| `check`   | Selected-home drift, collision, and checkout scope-split state reported without mutation     |

`init`, `upgrade`, and `check` report that Claude Code receives this plugin's agents through the plugin manifest and change nothing.

</verbs>

<changelogs>

`help` names where a reader answers "what changed for me, and what must I now do?", reading from disk without network access.

This plugin carries two changelogs. Read one only when the reader asks what changed.

| Line        | Records                                                  | Path                                                 |
| ----------- | -------------------------------------------------------- | ---------------------------------------------------- |
| Marketplace | events no single plugin owns: harnesses, plugins renamed | `${CLAUDE_SKILL_DIR}/../../MARKETPLACE-CHANGELOG.md` |
| Plugin      | what changed in this plugin                              | `${CLAUDE_SKILL_DIR}/../../CHANGELOG.md`             |

The marketplace line is current through its topmost `##` heading. Report that date with the result.

</changelogs>

<version_reporting>

`version` reads exactly one skill-directory-relative manifest:

```text
${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json
```

Report the version from the plugin copy backing this running session. Never search for another manifest elsewhere on disk.

</version_reporting>

<agent_delivery>

The plugin manifest delivers this plugin's agents. Every footprint verb reports that fact and writes nothing. The bundled `scripts/place_agents.py` serves only the Codex rendering of this skill and is never invoked here.

</agent_delivery>

<ownership_boundary>

This plugin claims no standalone agent file because its manifest delivers the agents.

</ownership_boundary>

<examples>

`check`, `init`, and `upgrade` each print one line: manifest delivery is in effect and nothing was written.

</examples>

<reload>

Agent registries are loaded at session start. After a successful `init` or `upgrade`, reload the harness plugin index or start a new session before judging whether a role is available. Re-running the mutating verb in the same session does not refresh that session's already-loaded registry.

</reload>

<failure_modes>

**Claude repaired a missing role by copying its TOML into the checkout.**

The checkout copy shadows the selected-home definition while the home plugin can advance independently. Remove a byte-identical generated copy; inspect a changed or unrecognized copy. Reconcile the selected home, then reload the harness.

**Claude treated a plugin-looking filename as ownership proof.**

Filename prefixes collide with developer-authored files. Only the digest-bound ownership record authorizes replacement or pruning; preserve and report every other file.

**Claude reported a version from another plugin copy.**

A marketplace source and cache snapshot can diverge. Read only the skill-directory-relative manifest named in `<version_reporting>`.

</failure_modes>

<success_criteria>

- Exactly one verb runs, defaulting to `help`.
- `version` reads only the running skill copy's target manifest.
- `help` reports the exact changelog lines and paths declared above.
- Every footprint verb reports manifest delivery and writes nothing.
- Missing-role repair ends with a harness plugin-index reload or a new session.

</success_criteria>
