# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualizing` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Govern Go test conventions before a Go language plugin ships

The methodology documents Go's test-infrastructure home (`internal/testinfra/`) in `spx/15-test-infrastructure.pdr.md` and Go test-file naming (`<subject>.<evidence>.<level>[.<runner>]_test.go`) in the testing and understanding skill references. No decision governs Go test-runner selection (`go test`), subtest conventions, `t.Helper()` policy, or the per-language `[test]` runner the way `spx/15-test-language.adr.md` does for this product's own pytest suite — and that ADR does not mention Go.

**Resolution shape**: before a Go language plugin ships, author the governing decision(s) for Go test conventions and reconcile them with the test-infrastructure home already documented here. The package-name constraint (`internal/testinfra/` is package `testinfra`, never `testing`) is already stated in `spx/15-test-infrastructure.pdr.md`, but its audit assertions cover the normative path generically — add a Go-specific audit assertion verifying the package name as part of this work.

## Lean PDR template vs. normative-heavy decisions (FOLLOW-UP)

`spx/15-test-infrastructure.pdr.md` is migrated to the lean decision template and conforms to its `## Product properties` cap of three items, but still departs from the template's minimal shape in two ways its normative substance forces: (1) three decision-body sections (`## Category Semantics`, `## Evidence Chain`, `## Spec Traceability`) between the opening statement and `## Rationale`, beyond the four-section shape (opening, `## Rationale`, `## Product properties`, `## Verification`); and (2) a multi-paragraph `## Rationale` that absorbs the former `## Context` and `## Trade-offs accepted` content (including the trade-offs table) rather than the one-to-two-sentence Rationale the template prescribes. Both deviations are content-driven: the per-language path table, the harness/generator/fixture category tables, the evidence-chain rules, traceability, and the folded context/trade-offs reasoning are the decision itself and have no home in the minimal four-section template; `/audit-pdr` approved the migrated structure, and the operator completed the mandated human content-preservation review against the pre-migration revision — confirming no normative content was lost — and approved the migration. The lean PDR template (`src/plugins/spec-tree/skills/understanding/templates/decisions/decision-name.pdr.md`) prescribes the four-section shape and a one-to-two-sentence Rationale and does not describe an extension for normative-heavy decisions that legitimately need decision-body sections.

**Resolution shape**: decide whether to (a) amend the lean PDR template to describe an extension for normative-heavy decisions (decision-body sections and a longer Rationale), naming `spx/15-test-infrastructure.pdr.md` as the reference, or (b) restructure this PDR into the minimal four-section shape without losing normative content. Until then, `spx/15-test-infrastructure.pdr.md` stands as a documented deviation.

Identified during the lean-template migration of the product-level decision records.

## Migrate command wrappers to skills

`spx/13-plugin-and-runtime-conventions.adr.md` declares the skill as the marketplace's sole user-facing invocation artifact; the command artifact type is not authored. Seven command wrappers predate this convention, each a thin `/<name>` that fronts a skill, all in the spec-tree plugin:

- `src/plugins/spec-tree/commands/` — `apply`, `author`, `bootstrap`, `clarify`, `commit`, `review-changes`, `rtfm`.
- No other plugin ships a `commands/` directory (verified by `ls src/plugins/*/commands/*.md`). Re-enumerate before migrating in case new commands have landed.

Each command already maps to a governing skill (e.g. `/commit` → `committing-changes`, `/apply` → `applying`, `/author` → `authoring`, `/bootstrap` → `bootstrapping`, `/clarify` → `clarify`/`interviewing`, `/review-changes` → `reviewing-changes`, `/rtfm` → `refocusing`). The `develop` plugin also ships `create-commands` and `audit-commands` skills whose status this convention affects — fold their disposition into the migration. `/open-pr` is removed by `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/`, which makes `/pr` the shipping route and treats opening/management as internal protocols.

**Resolution shape**: per-command (or per-batch) PRs that drop each `commands/*.md`, name the skill like the former command where a rename is wanted, update both marketplace catalogs (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`) and the README plugin catalog, and rebuild `dist/`. Once no `commands/` directories remain, the ADR's `[audit]` authoring-stance rules can be reinforced by a conformance `[test]` that walks `src/plugins/**` and asserts no `commands/` directory ships. Audit gate: `/aligning` against `spx/13-plugin-and-runtime-conventions.adr.md` + `just check`.
