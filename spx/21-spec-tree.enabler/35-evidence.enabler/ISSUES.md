# Issues: Evidence Enabler

## Verification/assertion-type vocabulary: remaining conformance

The canonical names are settled in `evidence.md`:

- **verdict mode** — deterministic / agentic.
- **verification type** — test / evaluate / audit, named by the `[test]` / `[eval]` / `[audit]` tag an assertion carries; selected from the real subject's verdict.
- **assertion type** — under the testing verification type only, one of scenario, mapping, conformance, property, compliance, read from the assertion's quantifier.

`/verify` is the authority that selects the verification type. After it selects test, `/test` selects the test assertion type from the assertion's quantifier, never from a section heading, and `/test-{language}` supplies only language-specific expression. The retired names — "evidence lane", "evidence mechanism", "evidence type", "evidence mode" — and "claim" as a structural term remain excluded from these surfaces.

Two pieces of conformance are deferred, each to its own change:

1. **Filename segment `<evidence>`.** The canonical model `<subject>.<evidence>.<level>[.<runner>]` (`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`) keeps `<evidence>` as the segment that holds the assertion type. Renaming it to `<assertion-type>` touches that PDR, every `spx/**/tests/` filename, and the filename validators — a separate focused PR (operator-decided).

2. **Decision-audit skills.** `audit-pdr` / `audit-adr` and their `*-evidence-model.md` references still use "evidence type" and the `evidence-type-mismatch` rule code; that rename collides with the unbuilt adr/pdr-auditing eval suites tracked in `spx/21-spec-tree.enabler/32-decisions.enabler/ISSUES.md`. Conform them together with that migration.
