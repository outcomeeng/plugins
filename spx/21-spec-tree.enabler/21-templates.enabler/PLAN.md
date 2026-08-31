# Plan: Per-rule evidence type in the ADR and PDR templates

## Purpose

Each decision-record compliance rule declares the minimal evidence type it requires, so a decision binds the kind of proof its downstream spec assertions must carry. This closes the interpretation gap where an author satisfies a rule with weak evidence and an auditor argues it is insufficient — the decision states the floor.

## Change

Every MUST/NEVER bullet in the ADR and PDR decision templates carries a single evidence-type tag in bracket form, replacing the current `([audit])` / `([test])` tag:

`([scenario])`, `([mapping])`, `([conformance])`, `([property])`, or `([compliance])`

- The evidence type is the **minimum**. The spec node enforcing the rule carries at least that evidence type and may add more (more cases, deeper levels, a second type).
- The evidence type is chosen by invoking `/test` against the rule's claim shape — never hand-picked. The template instructs the author to route through `/test`.
- The evidence-type tag is a claim-shape classification, not a test reference: it carries no path, so it does not violate live `/understand` `<artifact_placement>`, where decision records contain no `[test](path)` links. The path lives on the downstream spec assertion.
- Evidence type and mechanism are distinct axes. The per-rule tag is one of the five **evidence types** above. The evidence **mechanism** (`[test]` / `[audit]` / `[eval]`) is the downstream spec assertion's concern and never a per-rule tag — `([eval])` is not a decision-rule evidence type. The five-type set is therefore complete; a rule whose downstream enforcement uses evaluate verification still carries an evidence-type tag (typically `([compliance])`), and the `[eval]` mechanism attaches to the spec assertion that enforces it.

## Files

- `src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.adr.md`
- `src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.pdr.md`
- `src/plugins/spec-tree/skills/understand/examples/adr-example.md` (show per-rule evidence types)
- `src/plugins/spec-tree/skills/understand/examples/pdr-example.md` (show per-rule evidence types)
- regenerate `dist/claude` + `dist/codex` via `just build-skills`

## Spec impact

`templates.md` assertion "ALWAYS: define required sections for each artifact type" extends so the audit verifies each decision template's Compliance rules carry a per-rule evidence-type tag naming one of the five evidence types. Author the amended/added assertion through `/author`.

## Implementation skills (in order)

1. `spec-tree:understand`
2. `spec-tree:contextualize` on `spx/21-spec-tree.enabler/21-templates.enabler`
3. `spec-tree:author` for the `templates.md` assertion change
4. `instructions:skill-standards` before editing template/example content
5. `spec-tree:commit-changes`

## Audit gates

- PDR/ADR-template structural check via `spx validation markdown`
- The decision-record audits (`pdr-auditor` / `adr-auditor`, see `spx/21-spec-tree.enabler/32-decisions.enabler/`) read this tag — keep the two changes consistent.
- `just check` — the template and example edits regenerate `dist/`, so the `dist-diff` gate must run.

## Related plans

- `spx/21-spec-tree.enabler/32-decisions.enabler/` — the audits that enforce the evidence-type floor
- `spx/21-spec-tree.enabler/35-evidence.enabler/` — the `/test` router that picks the evidence type
