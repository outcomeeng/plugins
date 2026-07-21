# Issues: Evidence Enabler

## Verification/assertion-type vocabulary: remaining conformance

The canonical names are settled in `evidence.md`:

- **verdict mode** — deterministic / agentic.
- **verification type** — test / evaluate / audit, named by the `[test]` / `[eval]` / `[audit]` tag an assertion carries; selected from the real subject's verdict.
- **assertion type** — under the testing verification type only, one of scenario, mapping, conformance, property, compliance, read from the assertion's quantifier.

`/verify` is the authority that selects the verification type. After it selects test, `/test` selects the test assertion type from the assertion's quantifier, never from a section heading, and `/test-{language}` supplies only language-specific expression. The retired names — "evidence lane", "evidence mechanism", "evidence type", "evidence mode" — and "claim" as a structural term remain excluded from these surfaces.

One piece of conformance is deferred:

1. **Filename segment `<evidence>`.** The canonical model `<subject>.<evidence>.<level>[.<runner>]` (`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`) keeps `<evidence>` as the segment that holds the assertion type. Renaming it to `<assertion-type>` touches that PDR, every `spx/**/tests/` filename, and the filename validators — a separate focused PR (operator-decided).

## Language test-standards litmus intro omits `<assertion_type_litmus>`

The `<predicate_and_oracle_litmus>` section in each language authoring standard (`src/plugins/python/skills/python-test-standards/SKILL.md`, `src/plugins/typescript/skills/typescript-test-standards/SKILL.md`, `src/plugins/rust/skills/rust-test-standards/SKILL.md`) opens by naming only `/test-evidence-standards` `<common_litmus_questions>` and `<mutation_litmus>` as "the complete list" the bullets render. Two of those bullets — case-to-source tracing and expected-result-to-oracle tracing — render the per-assertion-type source/oracle columns from `/test-evidence-standards` `<assertion_type_litmus>`, which the intro sentence does not name. A reader auditing traceability against the stated "complete list" would not know to also check `<assertion_type_litmus>` for drift.

**Status against the standard.** Consistency gap, not a contradiction — the bullets render the correct content; only the intro's enumeration of governing sections is incomplete. The wording is identical across all three language renderings (Python is the origin the others were mirrored from), so it is a shared-pattern gap, not a Rust-specific defect. The Rust rendering is a faithful mirror of the Python and TypeScript siblings; closing it in Rust alone would make Rust diverge from them.

**Resolution shape.** Name `<assertion_type_litmus>` alongside `<common_litmus_questions>` and `<mutation_litmus>` in the intro sentence of all three renderings in one coordinated change (Python and Rust in this repo, TypeScript in its own worktree), so the three stay identical. Surfaced by `instructions:skill-auditor` on `rust-test-standards` during the Rust seam alignment (finding f-004).
