# Changelog — prose plugin

Prose craft: structure, writing, and audit for interface text, documentation, and standalone pieces.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.10.2

### Fixed

- **`audit-prose` follows the verification journal provider's current name.** The audit invokes `verification-run-journal-standards` and uses that name for its streaming and verdict contracts, so the renamed provider resolves without a stale skill reference.

## 0.10.1

### Changed

- **`author-prose` no longer dispatches the audit.** It grants no agent-dispatch tool and no `Bash`, and its workflow ends at the written text. Dispatch policy belongs to the calling flow, which decides when the `prose-auditor` thin agent runs the audit in a separate verifier agent session. A caller that relied on `author-prose` to run and clear its own audit now dispatches `prose-auditor` itself.

### Fixed

- **The `prose-auditor` contract the router publishes matches what the agent returns.** The configured-verifier contract for a craft plugin's `{plugin}-auditor` states both output shapes — a structured verdict, or a sealed-run journal token rendered through `spx journal render` — so a caller no longer judges a correct raw-token result as malformed output.
- **`prose-auditor` declares its output contract.** The definition carries an `<output_format>` section naming the raw run token and the load-diagnostic fallback, and its success criteria cover the no-nested-dispatch and no-invented-policy rules its constraints already impose.
- **The documentation layer regained two structural-writing caps** the four-kind merge dropped: active voice, and the ban on `should`, `would`, `may`, and `might` across the whole page rather than only inside a numbered procedure.
- **The interface and documentation structural conventions no longer restate style rules.** Element wording, heading case, and the one-term-one-meaning rule live in the style layer and the voice canon; the architecture references keep only what an ADR decides — element types, parallel sets, terminology homes, and where depth lives.
- **`audit-prose`'s description names its subject and scope** without the run-journal delivery clause, matching the audit-skill description convention the language plugins follow.
- **The voice canon bans end punctuation on a heading.** The rule previously reached only the documentation kind through a structural reference; it belongs beside the sentence-case rule the canon already carries, so it now binds the shipped `prose` output style and every kind alike.

## 0.10.0

### Breaking

- **Five skills replace fifteen.** The surface is three workflow skills — `/architect-prose`, `/author-prose`, `/audit-prose` — over two composed-only standards skills, `/prose-standards` and `/prose-architecture-standards`. The twelve per-kind skills are removed: `author-copy`, `author-docs`, `author-internal-docs`, `author-interface`, `audit-copy`, `audit-docs`, `audit-internal-docs`, `audit-interface`, `copy-standards`, `docs-standards`, `internal-docs-standards`, and `interface-standards`. Each kind's style rules live in a `prose-standards` reference and its structural conventions in a `prose-architecture-standards` reference.
- **Three kinds replace four.** `interface`, `documentation`, and `copy`. The `docs` and `internal-docs` kinds merge into `documentation`, because no rule distinguished a product-documentation page from a team page once the instruction caps and the page-architecture rules found their real triggers.
- **The kind is supplied, never detected.** Every workflow skill takes the kind as an input. A caller names it, a repository declares a path-to-kind map at `spx/local/prose.md`, or an interactive skill asks once. A dispatched `/audit-prose` that receives no kind records a blocked run and reads nothing, where it previously classified the text itself. A dispatch that relied on automatic classification now supplies `Kind: <kind>`.
- **The audit verdict is a journal run, not a terminal JSON object.** `/audit-prose` streams scope progress and each finding — pattern, category, quote, rewrite — through `spx journal` as the run advances, and the `prose-auditor` agent's final message is the raw run token of the sealed run. A consumer that parsed the JSON verdict now renders the sealed run through the run-journal projection.

### Added

- **`/architect-prose`.** Structure and text have separate owners: `/architect-prose` writes prose ADRs — structural decisions for the artifacts a spec node governs, located in the spec tree — and `/author-prose` is the artifact's sole writer, complying with the governing ADR. Structural moves, including sequencing across sibling and descendant artifacts, are decision content, so no artifact carries structural annotation.
- **`/prose-architecture-standards`.** The prose ADR conventions and each kind's structural conventions, mirroring the language plugins' architecture-standards shape.
- **Rule packs.** `/prose-standards` `<rule_packs>` declares rules that bind on an observable feature inside every kind. The instruction pack — 20-word steps, one instruction per sentence, condition before command, no modal hedging, action-leading steps, articles present — fires on any numbered procedure, so a runbook's steps are governed wherever the runbook lives. The table pack fires on any table. Register variation inside one text is carried by packs, so per-part kind declaration is gone.

### Changed

- **One voice canon, every surface.** The shared voice canon renders into `/prose-standards` and the shipped `prose` output style from one authored fragment, and every kind's style layer derives from the shared catalog — kinds differ in register and composition, never in voice.

### Removed

- **The kind-detection procedure.** Its audience and function tests asked for facts the artifact does not carry, and `/author-prose` runs before any text exists to read. An audit that infers the kind validates text against whatever kind it inferred, confirming text written for the wrong slot as correct.

### Requires

- **The `verification-run-journal-standards` skill and the `spx` CLI for audit delivery.** `/audit-prose` streams its run through `spx journal` using the projection the spec-tree plugin's `verification-run-journal-standards` skill carries. A run without either reports the exact availability failure instead of auditing.

## 0.9.1

### Changed

- **Ambiguity resolution follows the caller's interactivity.** The interactive caller asks the user to select a kind; a dispatched audit honors a dispatch-declared kind only for text the detection procedure leaves ambiguous — ownership outranks a declared kind, and each declaration binds only the part it names — and undeclared ambiguity is reported in the verdict with the plausible kinds' shared rules audited.
- **internal-docs covers team documents wherever the team keeps them** — a workspace tool or a repository. The audience test reads the reader's context, not the storage platform.
- **The audit path runs at the craft model tier** — the `prose-auditor` agent, the `audit-prose` router, and the four composed audit skills declare the craft model (Opus on Claude Code, gpt-5.5 on Codex) instead of the mechanical-auditor tier.

### Fixed

- The generated Codex `prose-auditor` configuration declares `sandbox_mode = "read-only"`, matching every sibling auditor.
- The `prose-auditor` description names its excluded targets — chat responses, operational prose, and repository-governed artifacts — so automatic dispatch matches the kind-detection boundary.

## 0.8.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.7.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
