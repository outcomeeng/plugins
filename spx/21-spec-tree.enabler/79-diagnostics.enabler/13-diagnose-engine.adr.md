# Diagnose Engine

The diagnose deterministic pipeline — gathering each surface's readings, classifying them against fixed verdict tables, and folding the per-check verdicts into one overall verdict — lives in the `spx` CLI as the `spx diagnose` command, tested there and consumed by the plugins product as a trusted third party. The shipped `diagnose` skill is a thin invoker: it locates `spx diagnose`, relays its report verbatim, and adds remediation judgment on a non-healthy verdict. A plugin-shipped declarative diagnose manifest — carrying the spx-version floor, the methodology marketplace identity, and the check set — is the contract by which the plugin tells `spx diagnose` what to check. The marketplace-install check derives expected plugin state from the checkout's committed per-agent agent-harness configuration — the marketplace registration and plugin selection the agent harness keeps for each agent — rather than from a plugin catalog embedded in the shipped diagnostic output, per `spx/12-marketplace-state.adr.md`.

The manifest ships inside the plugin tree; the skill passes it by path. Its fields are the few facts a check needs that the `spx` CLI cannot know on its own (illustrative — the authoritative schema lives with the `spx` CLI):

```json
{
  "spx_floor": "<build-rendered from the product's single source-of-truth floor>",
  "marketplace": { "name": "outcomeeng", "source": "outcomeeng/plugins" },
  "checks": ["session-environment", "spx-reachability", "worktree-pool", "session-store", "marketplace-install"]
}
```

## Rationale

The diagnose pipeline is deterministic end to end: every reading comes from a command or an environment variable, every verdict from a fixed table, and the overall verdict from a fixed precedence fold. `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` binds deterministic classification to the testing verdict mode, scored by an automated test, not to the agentic evaluating mode an LLM drives. Running the classification as skill prose makes a language model re-derive a lookup table on every invocation — unverifiable as a deterministic contract and a per-consumer, per-invocation token cost. `spx/12-shipped-scripting.adr.md` sends a shipped script's logic into the `spx` CLI once it passes fifty lines and proves its value, extracted there, tested in its own right, consumed by the product as a trusted third party. The diagnose classification is that logic — a proven, multi-surface pipeline well past that threshold, and the node's own spec declares that a check outgrowing light orchestration extracts into the `spx` CLI — so it lives in `spx diagnose`, not the skill body.

The skill keeps the one judgment a model genuinely adds: reading a non-healthy deterministic report and proposing context-aware remediation given the session. Everything beneath that — the readings, the per-check verdicts, the aggregate — is `spx diagnose`'s deterministic output, relayed verbatim.

The manifest is declarative because the facts that vary by consumer — the floor the installed plugin requires, the marketplace it depends on, and the checks it runs — are the plugin's, not the `spx` CLI's. The plugin declares them; `spx diagnose` executes against them, keeping the CLI generic across the consumers a methodology marketplace installs into. Expected plugin state is not one of those manifest facts. The agent harness keeps each agent's marketplace state as committed repository configuration — Codex in `.agents/plugins/marketplace.json` and `.codex/config.toml`, Claude Code in `.claude-plugin/marketplace.json` and project-scope `.claude/settings.json` — so the marketplace-install check derives what plugins to expect by reading that per-agent configuration in the checkout, per `spx/12-marketplace-state.adr.md`. A plugin list embedded in shipped diagnostic output cannot reflect a consumer's selective, per-project install: language, craft, and domain plugins are enabled per product, so a shipped catalog would misclassify valid selective installations as drift. Deriving the expected set from the checkout's committed configuration keeps diagnosis true for whatever each consumer actually declares. The floor stays a single source of truth: the build renders the product's `REQUIRED_SPX_VERSION` into the manifest, exactly as `spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md` requires the floor rendered into the shipped tree, so the shipped floor cannot drift from the floor the product enforces in CI. The manifest is a product-owned data file the skill passes by path; the field that `spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md` rejects is a field in the *agent's* plugin manifest, whose schema the agent owns and validates — a different artifact from this contract.

The marketplace-install check reads each agent's plugin CLI (`claude plugin`, `codex plugin`), which are agent-specific where the rest of the pipeline is agent-agnostic. `spx diagnose` shells out to each present surface, skips an absent one, and reports not-applicable when neither is present, so one command covers every check while staying usable wherever a surface is missing.

The shipped `diagnose` skill depends on the published `spx diagnose` command
and carries no in-body check classification. It passes the plugin-shipped
manifest to `spx diagnose`, relays the deterministic report, and adds remediation
judgment from the report's non-healthy verdicts.

## Invariants

- The floor, marketplace identity, and check set `spx diagnose` judges against are the manifest's — a single product-owned, build-rendered contract — never values hard-coded in the `spx` CLI or duplicated in skill prose.
- The marketplace-install check's expected plugin state is derived from the checkout's committed per-agent agent-harness configuration — never from a plugin set embedded in the shipped manifest or read from the marketplace catalog.
- The overall verdict folds the per-check verdicts by the fixed precedence broken > unknown > degraded > healthy, with not-applicable excluded — identical for every consumer.

## Verification

### Audit

- ALWAYS: the diagnose deterministic pipeline — gather, verdict classification, and aggregation — lives in the `spx` CLI as `spx diagnose`, tested there and consumed by the plugins product as a trusted third party ([audit])
- ALWAYS: the shipped diagnose skill is a thin invoker — it locates and runs `spx diagnose`, relays the report verbatim, and adds only remediation judgment on a non-healthy verdict ([audit])
- NEVER: the shipped diagnose skill re-derives any check's reading-to-verdict classification or the overall-verdict fold in its own body — that logic is `spx diagnose`'s ([audit])
- ALWAYS: the consumer-varying inputs — the spx-version floor, the marketplace identity, and the check set — reach `spx diagnose` through a plugin-shipped declarative manifest the skill passes by path, the floor build-rendered from the product's single source of truth per `spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md` ([audit])
- ALWAYS: the marketplace-install check derives expected plugin state from the checkout's committed per-agent agent-harness configuration rather than from a plugin catalog embedded in shipped diagnostic output, per `spx/12-marketplace-state.adr.md` ([audit])
- NEVER: the shipped diagnose manifest embeds an expected or required plugin set — expected plugin state for the marketplace-install check is derived from the checkout's committed per-agent agent-harness configuration, not carried in shipped diagnostic output, per `spx/12-marketplace-state.adr.md` ([audit])
- NEVER: the `spx` CLI hard-codes a consumer's floor, marketplace identity, or check set — those are the manifest's, so `spx diagnose` stays generic across the consumers a methodology marketplace installs into ([audit])
- ALWAYS: the diagnose skill's `spx diagnose` dependency is provided by a published `@outcomeeng/spx` release included in the product's spx-version floor, per the publish-before-depend rule ([audit])
