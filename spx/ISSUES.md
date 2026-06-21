# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualize` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Govern Go test conventions before a Go language plugin ships

The methodology documents Go's test-infrastructure home (`internal/testinfra/`) in `spx/15-test-infrastructure.pdr.md` and Go test-file naming (`<subject>.<evidence>.<level>[.<runner>]_test.go`) in the testing and understanding skill references. No decision governs Go test-runner selection (`go test`), subtest conventions, `t.Helper()` policy, or the per-language `[test]` runner the way `spx/15-test-language.adr.md` does for this product's own pytest suite — and that ADR does not mention Go.

**Resolution shape**: before a Go language plugin ships, author the governing decision(s) for Go test conventions and reconcile them with the test-infrastructure home already documented here. The package-name constraint (`internal/testinfra/` is package `testinfra`, never `test`) is already stated in `spx/15-test-infrastructure.pdr.md`, but its audit assertions cover the normative path generically — add a Go-specific audit assertion verifying the package name as part of this work.

## Lean PDR template vs. normative-heavy decisions (FOLLOW-UP)

`spx/15-test-infrastructure.pdr.md` is migrated to the lean decision template and conforms to its `## Product properties` cap of three items, but still departs from the template's minimal shape in two ways its normative substance forces: (1) three decision-body sections (`## Category Semantics`, `## Evidence Chain`, `## Spec Traceability`) between the opening statement and `## Rationale`, beyond the four-section shape (opening, `## Rationale`, `## Product properties`, `## Verification`); and (2) a multi-paragraph `## Rationale` that absorbs the former `## Context` and `## Trade-offs accepted` content (including the trade-offs table) rather than the one-to-two-sentence Rationale the template prescribes. Both deviations are content-driven: the per-language path table, the harness/generator/fixture category tables, the evidence-chain rules, traceability, and the folded context/trade-offs reasoning are the decision itself and have no home in the minimal four-section template; `/audit-pdr` approved the migrated structure, and the operator completed the mandated human content-preservation review against the pre-migration revision — confirming no normative content was lost — and approved the migration. The lean PDR template (`src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.pdr.md`) prescribes the four-section shape and a one-to-two-sentence Rationale and does not describe an extension for normative-heavy decisions that legitimately need decision-body sections.

**Resolution shape**: decide whether to (a) amend the lean PDR template to describe an extension for normative-heavy decisions (decision-body sections and a longer Rationale), naming `spx/15-test-infrastructure.pdr.md` as the reference, or (b) restructure this PDR into the minimal four-section shape without losing normative content. Until then, `spx/15-test-infrastructure.pdr.md` stands as a documented deviation.

Identified during the lean-template migration of the product-level decision records.

## Conformance test reinforcing the no-command authoring stance

`spx/13-plugin-and-runtime-conventions.adr.md` declares the skill the marketplace's sole user-facing invocation artifact and forbids authoring a command (`commands/*.md`); the rule carries `[audit]` evidence. No `src/plugins/*/commands/` directory ships. A deterministic conformance `[test]` that walks `src/plugins/**` and asserts no `commands/` directory exists would reinforce that `[audit]` stance with executable evidence.

The `develop` plugin retains its `create-commands` and `audit-commands` skills and `command-auditor` agent: those serve the consumer audience (authoring commands in other repositories), which the product-internal ADR does not govern.

**Resolution shape**: the ADR is a product-root decision file with no co-located `tests/` directory, so the conformance assertion needs a naturally-placed home — the distribution enabler (`spx/32-distribution.enabler/`) or another node governing the shipped plugin layout. Decide placement, then add the `[test]` assertion plus its Python test per `spx/15-test-language.adr.md`.
