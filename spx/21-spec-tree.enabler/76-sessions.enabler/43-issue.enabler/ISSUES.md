# Issues: Issue Filing

## Marketplace-resolver extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/issue/scripts/resolve_marketplace.py` runs to 133
lines — resolution of a marketplace entry's registered local source from JSON on
stdin, covering the Claude Directory-source and Codex local-marketplace-source
shapes, with distinct errors for malformed JSON and an unresolvable target. Past
fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose
logic moves into the SPX CLI once the script proves its value; the resolver has
proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port marketplace-source resolution into the SPX CLI,
publish it, advance the floor, and reduce the shipped skill to its instruction
with no script. Keep the per-agent source shapes — Claude Directory source and
Codex local marketplace source — both resolvable after the move, since
`spx/12-marketplace-state.adr.md` makes each agent's registration committed
repository configuration. Revisit when the capability publishes.
