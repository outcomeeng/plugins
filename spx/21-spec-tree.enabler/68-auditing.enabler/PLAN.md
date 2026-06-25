# PLAN — extend the no-deterministic-verification rule to the dispatched language audit family

## Governing declaration

`spx/14-verification.pdr.md` product property 9 and `spx/21-spec-tree.enabler/17-auditing.adr.md`
declare that a dispatched agentic verification runs no deterministic verification: the main agent
passes validate/test/evaluate on the changeset before dispatch, and CI re-runs them over the whole
repository. This node's `auditing.md` carries the matching `/audit`-level assertion.

## Gap

The declaration leads implementation. The first changeset realized it for the orchestrator
(`/audit`) and the implementation-code audits (`audit-python`, `audit-typescript`, `audit-rust`) plus
the four wrapper agents. The dispatched **test-evidence** audits still run deterministic gates and so
contradict the declaration:

- `src/plugins/python/skills/audit-python-tests/SKILL.md` — `<gate_0_deterministic>` runs
  `pytest --collect-only`, `ruff check`, `mypy` and halts with `REJECT` on failure.
- `src/plugins/typescript/skills/audit-typescript-tests/SKILL.md` — runs `spx validation literal`
  before the evidence gates.
- `src/plugins/rust/skills/audit-rust-tests/SKILL.md` — `<gate_0_deterministic>` runs
  `cargo fmt --check` and `cargo clippy`.

`/audit` dispatches `audit-{lang}-tests` as its test-evidence phase, so a normal `/audit` run still
executes the deterministic work the declaration moved to the main agent and CI.

## Observed behavior

Dispatching `test-evidence-auditor` (which composes `audit-python-tests`) against a single test file
ran, in one audit: `pytest --collect-only`, a full deterministic test run, `ruff check`, `mypy`, and
then the coverage measurement — `pytest --cov` executed **three times** (baseline excluding the file,
with-test, and an isolated `--cov-append` run). The coverage step, not `gate_0_deterministic`, is the
heavier cost: it runs the node's pytest suite three times per single test-evidence audit. Removing
`gate_0_deterministic` alone does not close the gap — the coverage-run machinery is the larger
re-execution of the project's tests.

## Remaining work

1. Remove or re-scope the deterministic work from the three `audit-{lang}-tests` skills so the
   test-evidence audits judge evidence quality only, matching the implementation-code audits already
   updated. This covers both `gate_0_deterministic` (collect/lint/type) and the coverage measurement
   (the repeated `pytest --cov` runs). Rebuild `dist/`, run `develop:skill-auditor` on each edited
   skill, and re-verify.
2. Sweep the full set of dispatched language audit skills — the three `audit-{lang}-architecture`
   skills, and any other dispatched concern — for residual deterministic verification. A token search
   over the `-architecture` skills surfaced no gate commands (`pytest`, `ruff`, `mypy`, `cargo`,
   `spx validation`); the authoritative confirmation that the whole family conforms is part of this
   sweep, not a precondition assumed here.

## Related: stale audit examples

The `audit-{lang}` skills' bundled examples are inconsistent with the skills' own verdict contract,
independent of the gate-removal change:

- `src/plugins/python/skills/audit-python/references/example-audit.md`,
  `src/plugins/rust/skills/audit-rust/references/example-audit.md`, and
  `src/plugins/typescript/skills/audit-typescript/references/example-audit.md` show a Markdown
  "CODE REVIEW" table, while each skill's `<verdict_format>` declares JSON output conforming to the
  canonical `verdict.py` schema. An auditor following the example emits Markdown the verdict
  toolchain cannot parse.
- The same examples still carry `Automated gates` and `Test execution` rows and "after Phase 1 and
  Phase 2 passed" framing — the phases removed from the skill bodies — plus a `rejected-gates-failed`
  example built entirely on the removed Phase-1 gate. The rust example also omits the
  `unsafe-soundness` row the skill's schema declares.

Rewrite the three examples to the JSON verdict shape with the current semantic-only row set when the
test-evidence sweep lands, so the example format and the gate-row removal are fixed together rather
than patching stale rows inside an already-obsolete format.

## Why separate from the originating PR

The originating change targeted the urgent machine-load source — the implementation-code audit skills
and their wrapper agents fanning out and re-running the project's linters and tests. Extending the
same removal across the test-evidence audits is a larger, lower-urgency sweep of the full audit
family, tracked here rather than blocking that fix.
