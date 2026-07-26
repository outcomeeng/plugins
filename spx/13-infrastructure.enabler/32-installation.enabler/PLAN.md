# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

## What RELEASE means for this repository

A plugin change that reaches the default branch on origin has released only when **everyone on this
machine picks up the new version from GitHub** on their next refresh or new session. Publication is
not release; a merged commit nobody's agent resolves is not delivered.

The release action is therefore:

1. Update the Claude plugins from the GitHub marketplace.
2. Update the Codex plugins from the same GitHub marketplace.
3. Update the agent definitions.

Step 3 exists because a Codex plugin manifest ships skills but not agents. Both agents' definitions
come from one authored source, but the shipped artifacts are not identical — the build converts each
into that agent's native form, and the conversion is lossy. Comparing
`dist/claude/spec-tree/agents/spec-auditor.md` against its Codex counterpart: Markdown with YAML
frontmatter against TOML, `spec-auditor` against the flat-namespace `spec-tree_spec-auditor`, `model:
sonnet` against a mapped Codex model, a `tools` allowlist against derived `sandbox_mode` and
`web_search` values, a `skills` list against `[[skills.config]]` blocks, plus a
`shell_environment_policy` marker and an appended manual-review block that the source has no
counterpart for. `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md`
governs those mappings and requires that guidance precisely because some source semantics have no
Codex equivalent.

What is identical is the intent, not the bytes. Claude receives its artifact through the manifest;
Codex cannot, so its converted artifact arrives by a separate install. That is the only asymmetry,
and it is a Codex capability limit rather than a design choice.

The action is declared in `spx/local/merging.md` and runs under `RELEASE_READINESS` in the phase
order the spec-tree plugin ships. `spx/21-spec-tree.enabler/76-merging.enabler` builds the shipped
capability of driving a consumer's declared `PREVIEW`, `DEPLOY`, and `RELEASE` phases; this
repository is the consumer that exercises the release path, and with no declaration here that phase
never runs as anything but a no-op.

## What consumers need

A consumer declares the plugins it requires in `.claude/` and `.codex/`. That declaration is the
same for both agents: the same marketplace, the same plugin set.

**Claude is done.** `.claude/settings.json` names the GitHub marketplace and the enabled set, Claude
reads it, and the manifest carries both skills and agents. Nothing further is required.

**Codex needs two steps:**

1. Install, or ensure installed, the marketplace and the declared plugins. Codex installs skills
   through the plugin, so this step delivers every skill.
2. Materialize the agent definitions into the same destination those skills landed in.

The destination is `CODEX_HOME` by default, because that is where step 1 put the skills and agents
belong beside them. A `--scope project` override is available, matching what `claude plugin install`
already offers, so the two agents end up with the same semantics rather than Codex being
user-scope-only. What is insufficient is project scope as the *only* option — it would force the
placement to repeat for every repository on the machine while still costing the same explicit step
that one user-scope placement costs once.

Both steps exist because Codex requires an install regardless. Step 2 is not extra machinery bolted
on to work around a limitation; it is the second half of an install the developer is already
running.

## Sync is not what we are doing

There is no sync. Sync names a two-way convergence between a declaration and an installation, and no
such operation exists here. The flow is one-directional: a repository declares, and an explicit
install applies that declaration to the agent's installation. What an agent holds never feeds back
into what a repository declares.

Everything that assumed otherwise goes: reconciling a developer's marketplace registration,
repairing a plugin cache, resolving a marketplace-source worktree and fast-forwarding it so a local
`dist/` serves current content, compatibility-symlink repair, and cache-topology inspection. The
Directory-source registration that machinery serves is a preview pointer at one worktree under
review — never a delivery mechanism, and never a gate predicate.

## Work, in truth order

**Decision.** `spx/12-marketplace-state.adr.md` is wrong at the root and changes first. It declares
the toolchain checkout-bounded and forbids mutating user-scope marketplace state, and it places
converted agent definitions as committed repository content under the checkout's agent directory
(opening paragraph, and the assertions at lines 19, 23, 25). The corrected decision says: a
repository declares per agent; an explicit install applies that declaration to `CODEX_HOME`; release
advances every agent's installation to the published version; an installation changes only across an
install or a release.

**Specs.** First affected, in the same changeset as the decision:

- `spx/13-infrastructure.enabler/32-installation.enabler/installation.md` — declares checkout-bounded
  reading and a per-plugin refresh form that forbids `codex plugin marketplace upgrade`. Becomes the
  one-directional install into `CODEX_HOME`.
- `spx/32-distribution.enabler/21-sync.enabler/sync.md` — the node is named for the concept that does
  not exist. Its disposition is structural, so it routes through `/decompose` on
  `spx/32-distribution.enabler` rather than being reworded: sync goes, `21-push.enabler` loses the
  half that invokes it, and neither the install nor the release action has a node today.
- `spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md` — restates the
  superseded per-agent configuration enumeration; the derive-from-committed-config rule itself
  survives.
- `spx/outcomeeng.product.md` scope bullet — "Repository-scoped marketplace synchronization".

**Code.** Follows the specs.

How agent definitions are shipped is the thing to preserve. A Codex plugin manifest declares skills
and not agents, so the agents ride inside a skill's own directory — `spec-tree-plugin/agents/` — and
the script that materializes them ships in that same skill at
`dist/codex/spec-tree/skills/spec-tree-plugin/scripts/place_agents.py`, authored at
`src/templates/plugin/scripts/place_agents.py`. That is what makes delivery contractual rather than
incidental, and it is why the decision requires the definitions to sit inside a surface the manifest
declares.

- **Keep `place_agents.py`.** It already does the whole placement job: reads its declaration, copies
  drifted definitions, prunes stale ones within its own plugin's prefix, and offers `--check` for
  drift detection. Nothing about it is superseded.
- **Add its equivalent as the install step.** Install is required for Codex regardless, so the new
  script is the operation that registers the marketplace and installs the declared plugin set — the
  half `place_agents.py` does not cover.
- **Make the destination scope-aware.** `outcomeeng/distribution/build.py:1470` sets
  `checkout_directory=".codex/agents"`, which the build writes into each plugin's `placement.json`
  and `place_agents.py` resolves against `--checkout`, defaulting to the working directory. Default
  the resolution to `CODEX_HOME` instead — beside the skills — and accept `--scope project` for the
  Claude-equivalent override. The registry field's name follows the semantics rather than the
  reverse.
- This repository's 14 committed `.codex/agents/*.toml` exist because placement defaulted to project
  scope. Once the default is the agent home, whether this repository still keeps a project-scope copy
  is a choice to make deliberately, not a state to inherit.

**Overlay.** `spx/local/merging.md` carries the release declaration. Its current "Release marketplace
sync" section is the superseded model end to end, including the `worktree-pool` preflight predicate
that requires the diagnosed main checkout to equal the marketplace-source path.

## Evidence

Route the release and install assertions through `/verify`, then `/test` for whatever it routes to
test. Do not presuppose the verification type, the assertion type, or the execution level: the
assertion's quantifier selects the assertion type and operational reality selects the level. This
node already reads a real agent CLI at `L1` (`test_installed_set.conformance.l1.py`), so invoking a
CLI is not what makes evidence heavier — full install cost across the catalog is. Whatever setup the
routing needs, including a disposable agent home, belongs to a spec-governed harness; the executed
test owns the assertion flow alone.

State what we want, not what we do not. An assertion like "NEVER declare a step whose contract is
`codex_cache_preserve`" can only be tested by grepping for a literal string, passes the moment the
step is renamed, and is defined entirely by reference to a design being removed. The provable form
names the observable outcome: what an agent's installation holds after the operation.

`work/sync-marketplace-cutover` holds an isolated real-runtime harness
(`outcomeeng_testing/harnesses/marketplace_runtime.py`) that provisions real `claude` and `codex`
against a disposable home, installs every real catalog plugin, and reads the install state back from
the CLIs. It is worth porting for the install-completeness evidence. Port it to a fresh branch rather
than rebasing: that branch is 421 behind `origin/main` and overlaps main in 14 files including
`agents.py`, `contracts.py`, `orchestration.py`, `sync.py`, and `install.py`.

## Open — operator's call

Release step 3 reads two ways. "Update the agent definitions in each consuming repo" and "install
agents in `CODEX_HOME`, not per project" agree if release updates `CODEX_HOME` once and every
repository on the machine resolves that one copy. Confirm before the decision is written.

## Out of scope

`spx/21-spec-tree.enabler/76-merging.enabler/PLAN.md` describes product truth for the spec-tree
plugin and stays free of this repository's specifics. The declaration above is what makes that
plugin's release path exercised, never part of its content.
