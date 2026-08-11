# Changelog — prose plugin

Prose craft: writing and audit for interface text, documents, and standalone pieces.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.10.0

### Breaking

- **The kind is supplied, never detected.** `/author-prose` and `/audit-prose` take the kind as an input. A caller names it, a repository declares a path-to-kind map at `spx/local/prose.md`, or an interactive router asks once. A dispatched `/audit-prose` that receives no kind emits `UNKNOWN` and reads nothing, where it previously classified the text itself. A dispatch that relied on automatic classification now supplies `Kind: <kind>`.
- **Three kinds replace four.** `interface`, `document`, and `copy`. The `docs` and `internal-docs` kinds merge into `document`, because no rule distinguished a product-documentation page from a team page once the instruction caps and the page-architecture rules found their real triggers.
- **Renamed skills.** `docs-standards` and `internal-docs-standards` become `document-standards`; `author-docs` and `author-internal-docs` become `author-document`; `audit-docs` and `audit-internal-docs` become `audit-document`. A consumer naming a removed skill updates the name.
- **The verdict carries `kind`, not `kinds`.** One text carries one kind, so the field is singular, and `UNKNOWN` joins `APPROVED` and `REJECTED` in the `overall` vocabulary.

### Added

- **Rule packs.** `/prose-standards` `<rule_packs>` declares rules that bind on an observable feature inside every kind. The instruction pack — 20-word steps, one instruction per sentence, condition before command, no modal hedging, action-leading steps, articles present — fires on any numbered procedure, so a runbook's steps are governed wherever the runbook lives. The table pack fires on any table. Register variation inside one text is carried by packs, so per-part kind declaration is gone.

### Changed

- **Every kind layer transcludes the shared voice canon.** `copy-standards` and `document-standards` join `interface-standards` and the shipped `prose` output style in rendering from `prose/voice/fragment.md`. Three of four kinds previously stated no voice at all while claiming to carry the base voice.
- **Kind intake lives in the routers.** `/prose-standards` no longer carries a classification procedure, and no kind layer restates one. The catalog states rules.

### Removed

- **The kind-detection procedure.** Its audience and function tests asked for facts the artifact does not carry, and `/author-prose` runs before any text exists to read. An audit that infers the kind validates text against whatever kind it inferred, confirming text written for the wrong slot as correct.

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
