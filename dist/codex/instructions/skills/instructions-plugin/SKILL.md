---
name: instructions-plugin
description: >-
  ALWAYS invoke this skill to operate the instructions plugin's own lifecycle — report its version and check or reconcile its agent-delivery footprint. Invoke it when this plugin's agents are missing from a session. NEVER commit marketplace-delivered agent definitions into a checkout.
argument-hint: "[help|version|init|upgrade|check]"
arguments: verb
allowed-tools: Read, Bash(python3 "${SKILL_DIR}/scripts/place_agents.py":*)
---

<objective>
The instructions plugin's resolved version and agent-delivery state reported or reconciled in the scope that carries its skills.
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

`init`, `upgrade`, and `check` use the bundled reconciliation script. The script never writes into a checkout.

</verbs>

<changelogs>

`help` names where a reader answers "what changed for me, and what must I now do?", reading from disk without network access.

This plugin carries one changelog:

| Line   | Records                     | Path                              |
| ------ | --------------------------- | --------------------------------- |
| Plugin | what changed in this plugin | `${SKILL_DIR}/../../CHANGELOG.md` |

Marketplace-wide events ship in the methodology plugin's marketplace changelog; this plugin carries no copy.

</changelogs>

<version_reporting>

`version` reads exactly one skill-directory-relative manifest:

```text
${SKILL_DIR}/../../.codex-plugin/plugin.json
```

Report the version from the plugin copy backing this running session. Never search for another manifest elsewhere on disk.

</version_reporting>

<agent_delivery>

The plugin ships generated TOML definitions inside this skill. They belong in the selected `CODEX_HOME/agents/` directory beside the installed skill content they invoke.

Before every verb, resolve the selected home from `CODEX_HOME`. When it is absent, require an explicit absolute `--home` value; never guess another account or fall back to a checkout. Resolve the invocation checkout root and pass it with `--checkout` so the read-only scope-split preflight can report shadowing plugin copies.

Run the check form first:

```bash
python3 "${SKILL_DIR}/scripts/place_agents.py" --home <selected-codex-home> --checkout <repository-root> --check
```

`check` ends there. For `init` or `upgrade`, stop on any collision or scope split. Otherwise name every destination the check reported, state that the ownership record changes with them, and run the mutating form only after the harness grants that external write:

```bash
python3 "${SKILL_DIR}/scripts/place_agents.py" --home <selected-codex-home> --checkout <repository-root>
```

Run the check form again afterward. Success requires zero remaining drift, collision, or scope-split report. An interrupted `init` or `upgrade` is safe to re-run: every write is atomic per file and the ownership record is recomputed from the shipped definitions on each run. A `collision: <path> (changed after preflight)` line means the home changed while the run was planning; re-run the check form for a fresh plan instead of retrying the mutating form.

</agent_delivery>

<ownership_boundary>

The shared agent home is reconciled through `.outcomeeng-marketplace-ownership.json`. This plugin may create, replace, or prune only entries that record `instructions` as owner and whose on-disk digest still matches the record. An unrecorded destination, a modified owned file, malformed ownership data, or a destination owned by another plugin is a collision: report it and change nothing.

A checkout definition byte-identical to a shipped definition is a scope split with directed removal. A changed checkout definition, or one that claims this plugin by filename prefix or by enabling one of its skills, is a scope-split collision requiring inspection. Either state stops home mutation; never refresh the home skills underneath a shadowing checkout definition.

</ownership_boundary>

<examples>

A `--check` run against a home carrying one stale owned definition, one recorded definition the plugin no longer ships, and one developer file the ownership record does not know prints its plan and exits `2` on any collision or scope split, `1` when writes or prunes are pending, and `0` when the home already matches:

```text
write: /Users/dev/.codex/agents/instructions_reviewer.toml
prune: /Users/dev/.codex/agents/instructions_verifier.toml
collision: /Users/dev/.codex/agents/instructions_notes.toml (unrecorded)
```

`write` names a destination whose bytes differ from the shipped definition, `prune` a recorded `instructions` destination the plugin no longer ships, and `collision` a present file the ownership record does not authorize, with its cause: `symlink`, `unrecorded`, `owned by <plugin>`, `not a regular file`, or `digest mismatch`. A `scope-split directed-removal:` or `scope-split collision:` line names a checkout copy under `.codex/agents/` — matched by shipped bytes, by the `instructions` filename prefix, or by a `skills.config` entry naming a `instructions:` skill — and stops mutation. After the mutating form succeeds, the ownership record carries one entry per written destination:

```json
{ "destination": "agents/instructions_reviewer.toml", "plugin": "instructions", "digest": "<sha256 of the installed bytes>" }
```

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
- `check` writes nothing and reports every drift, collision, and scope split.
- `init` and `upgrade` mutate only the selected home after a clean preflight and external-write approval.
- Every replacement or prune is authorized by matching plugin ownership and digest; foreign or modified files remain untouched.
- A final check reports no drift, collision, or scope split.
- Missing-role repair ends with a harness plugin-index reload or a new session.

</success_criteria>
