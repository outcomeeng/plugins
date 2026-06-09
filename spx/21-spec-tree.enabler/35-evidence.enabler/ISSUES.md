# Issues: Evidence Enabler

## Verification/assertion-type vocabulary: remaining conformance

The canonical names are settled in `evidence.md`:

- **verdict mode** — deterministic / agentic.
- **verification type** — testing / evaluating / auditing, named by the `[test]` / `[eval]` / `[audit]` tag an assertion carries; selected by fallback test → eval → audit.
- **assertion type** — under the testing verification type only, one of scenario, mapping, conformance, property, compliance, read from the assertion's quantifier.

`/testing` (with `/testing-{language}`) is the single authority that selects both, and the type is read from the assertion's quantifier, never inferred from a section heading. PR #144 conformed the spec-tree core (foundation references, decision templates, the governing specs `evidence.md` / `14-verification.pdr.md` / `32-decisions.enabler/decisions.md` / `21-templates.enabler/templates.md`, and `authoring`) and the python / typescript / rust skills. The retired names — "evidence lane", "evidence mechanism", "evidence type", "evidence mode" — and "claim" as a structural term are gone from those surfaces. This resolved the original two issues' core: the vocabulary is named, and assertion-type selection lives only in `/testing`.

Three pieces of conformance are deferred, each to its own change:

1. **Spec `## Assertions` structure.** ~75 node specs across the tree file `[audit]`/`[review]` assertions under `### Compliance`, and the node templates (`enabler-name.md`, `outcome-name.md`) head `## Assertions` by assertion type. Restructure to head by verification type so audit/eval assertions leave `### Compliance` — which is a test-only assertion type, not a home for semantic-judgment rules. Per-file judgment (which rules are genuine test-compliance vs audit); consumer-facing.

2. **Filename segment `<evidence>`.** The canonical model `<subject>.<evidence>.<level>[.<runner>]` (`spx/15-test-infrastructure.pdr.md`) keeps `<evidence>` as the segment that holds the assertion type. Renaming it to `<assertion-type>` touches that PDR, every `spx/**/tests/` filename, and the filename validators — a separate focused PR (operator-decided).

3. **Decision-audit skills.** `audit-pdr` / `audit-adr` and their `*-evidence-model.md` references still use "evidence type" and the `evidence-type-mismatch` rule code; that rename collides with the unbuilt adr/pdr-auditing eval suites tracked in `spx/21-spec-tree.enabler/32-decisions.enabler/ISSUES.md`. Conform them together with that migration.
