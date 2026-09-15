# Agent Delivery

Marketplace plugins deliver their skills and native subagent definitions as one versioned unit, in the same scope. Selected-home Codex definitions remain globally available independently of product skill activation. Placement preserves foreign and modified definitions and stops when a checkout definition shadows skills installed in another scope.

## Rationale

A subagent definition invokes its plugin's skills, so refreshing either alone permits incompatible versions to execute together. Ownership-bounded placement preserves developer control while letting products select skill context over a shared installation.

## Product properties

1. Every marketplace-shipped operation that delivers or refreshes skills or agent definitions carries both in the same run. Skills installed in an agent home carry definitions into that home's agent directory; a committed checkout copy is coherent only when the checkout also carries the invoked skill content. Installation and generated instructions never require committing definitions into a consumer checkout.
2. Codex discovers selected-home definitions independently of plugin activation. Product activation neither generates a checkout registry nor filters or prunes the home registry. A missing definition is repaired by refreshing the selected home's definitions and reloading the harness plugin index or starting a fresh session; a running session retains its loaded registry.
3. A plugin lifecycle operation changes only its plugin's owned namespace. Marketplace-wide reconciliation is a distinct operation with recorded ownership, never authority inferred from a filename prefix. Foreign or modified collisions remain untouched; a scope split reports every mismatched definition and stops without refreshing, pruning, or duplicating around it.

## Verification

### Testing

- ALWAYS: Codex subagent definitions for home-selected plugins remain in the global selected-home registry independently of trusted-product skill activation; plugin lifecycle placement retains its namespace and digest-bound ownership checks. ([compliance])
- NEVER: product skill activation generates a checkout subagent registry or filters the home registry. ([compliance])

- ALWAYS: a plugin's lifecycle skill places and prunes only within the namespace its own plugin owns, leaving agent definitions authored by the developer or provided by another plugin untouched ([compliance])
- ALWAYS: agent-home cleanup beyond one plugin's namespace runs as marketplace-scope reconciliation, distinct from plugin placement, and establishes recorded ownership before any prune or overwrite; a filename prefix alone supplies no authority, and a foreign collision is reported and left untouched ([compliance])
- ALWAYS: placement derives each plugin's destination scope from its invoked skill content, and reports a scope split without refreshing, pruning, or duplicating definitions across it ([compliance])

### Audit

- ALWAYS: a checkout receives a plugin's agent definitions only when it also carries their invoked skill content; installation and generated instructions never require checkout materialization ([audit])
- NEVER: a generated instruction surface directs a session to commit marketplace definitions into a checkout; missing definitions are repaired in the selected agent home, followed by a plugin-index reload or fresh session ([audit])
