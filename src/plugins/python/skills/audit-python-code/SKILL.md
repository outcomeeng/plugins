---
name: audit-python-code
description: >-
  Python implementation-code audit methodology — judges the Python code files in
  scope for design flaws and architecture-decision compliance.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(grep:*), Skill
---

{!% require_skill 'python:python-standards' %!}

<objective>

A verdict on Python implementation code — `APPROVED`, or `REJECTED` with each finding naming the design flaw, the violated rule, and the evidence.

</objective>

<constraints>

- NEVER modify files, generate fixes, write replacement code, commit changes, or change project state — this audit produces a verdict only.
- NEVER run deterministic validation, lint, type-check, test, or eval commands — this audit reads and judges; it never runs deterministic verification.
- NEVER evaluate test evidence quality — `/audit-python-tests` is the separate concern that judges it.
- ALWAYS keep findings to artifact, violated rule, evidence, and why the cited code violates the rule.
- NEVER include corrective code samples, implementation patches, prescribed refactors, or required-change summaries in the verdict.
- `APPROVED` means every concern row passes or is explicitly not applicable. `REJECTED` means at least one concern row fails. `APPROVED` output contains no notes, warnings, or suggestions sections.

</constraints>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/python.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<essential_principles>

**Comprehension is the whole job.**

This audit reads and judges Python implementation code; it runs no deterministic verification. Do NOT run or re-check the project's linters, type-checker, or tests. Spend the whole audit on comprehension.

**Comprehension is the core value.**

Automated tools catch syntax errors, type mismatches, and lint violations. Claude catches: functions that do more than their name says, dead parameters required by no Protocol, IO tangled with logic, and designs that will break under change. The predict/verify protocol (Phase 1) is how these surface.

**Test evidence is out of scope.**

`/audit-python-tests` evaluates whether tests provide behavior-coupled evidence using the 4-property model (coupling, falsifiability, alignment, coverage). This skill judges implementation design, not test evidence, and never runs the test suite. Do not duplicate that work.

**Binary verdict, no caveats.**

The verdict is the only output. Findings prove violations; they do not prescribe fixes.

</essential_principles>

<audit_workflow>

Execute phases IN ORDER. Do not skip. This audit runs no deterministic verification — no linter, type-checker, or test run.

**Phase 0: Scope and Product Config**

1. Determine target files/directories
2. Check `pyproject.toml` and `{{! file('root_guide') !}}`/`README.md` for tool and project configuration that informs comprehension (ruff, mypy, pytest settings; naming conventions) — read for context, never to run a gate. The linters already handled type annotations, magic numbers, bare excepts, unused imports, commented-out code, modern syntax, and security rules; comprehension covers what they cannot — deep relative imports, `sys.path` manipulation, unqualified `Any`, and `# type: ignore` without justification.

**Phase 1: Code Comprehension**

Read every file. Understand it. Question it. Do NOT skim, sample, or check boxes.

**1.1 Per-Function Protocol**

For each function/method:

1. **Read name and signature only** -- name, parameters, return type
2. **Predict** what it does in one sentence
3. **Read the body** -- validate the prediction
4. **Investigate surprises:**

| Surprise                               | What it suggests                                  |
| -------------------------------------- | ------------------------------------------------- |
| Parameter never used in body           | Dead parameter -- required by Protocol, or remove |
| Does more than name says               | SRP violation or misleading name                  |
| Does less than name says               | Name overpromises or logic is incomplete          |
| Variable assigned but never read       | Dead code or unfinished logic                     |
| Code path that can never execute       | Dead branch given calling context                 |
| Return value contradicts the type hint | Logic error or wrong return type                  |

Prediction matched? Move on. Surprise? Document it with `file:line`.

**1.2 Design Evaluation**

For the codebase as a whole:

- **IO vs logic separation** -- Can core logic be tested without IO? Tangled computation and side effects need factoring.
- **Dependency injection** -- External dependencies injected via parameters or Protocol, or imported as globals?
- **Single responsibility** -- Each module/class does one thing? Each function does one thing?
- **Error quality** -- Errors include what failed and with what input?
- **Domain exceptions** -- Custom exceptions for domain errors, or everything generic `ValueError`/`RuntimeError`?

**1.3 Import Evaluation**

Evaluate import structure using the same vocabulary as `/audit-python-tests`:

| Import pattern                                            | Classification                  |
| --------------------------------------------------------- | ------------------------------- |
| `import pytest`                                           | Framework -- not reviewed       |
| `from hypothesis import given`                            | Framework -- not reviewed       |
| `import json`                                             | Stdlib -- not reviewed          |
| `from typing import TYPE_CHECKING`                        | Type-only -- erased at runtime  |
| `from product.config import parse_config`                 | Codebase (production) -- review |
| `from ..config import parse_config`                       | Codebase (relative) -- review   |
| `from product_testing.harnesses import ConfigTestHarness` | Codebase (test infra) -- review |

**Import depth rules:**

| Depth           | Example                   | Verdict                          |
| --------------- | ------------------------- | -------------------------------- |
| Package import  | `from product.config ...` | OK -- preferred                  |
| 1 level         | `from ..config ...`       | Review -- truly module-internal? |
| 2+ levels       | `from ....helpers ...`    | REJECT -- use package import     |
| sys.path manip. | `sys.path.insert(0, ...)` | REJECT -- always                 |

For stable locations (`product_testing.harnesses.*`, `product_testing.generators.*`, and inert fixture path providers), package imports are mandatory.

See `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` for application context when evaluating security and linter suppression comments.

**Phase 2: ADR/PDR Compliance**

Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`). Verify each constraint is followed. Undocumented deviations make this concern `FAIL`. If the product has no spec hierarchy, this concern is `NOT_APPLICABLE`.

| Decision Record Constraint           | Violation Example                   | Verdict |
| ------------------------------------ | ----------------------------------- | ------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | FAIL    |
| "`l1` tests for logic" (ADR)         | `l1` tests hitting network          | FAIL    |
| "No ORM" (ADR)                       | SQLAlchemy models introduced        | FAIL    |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | FAIL    |

</audit_workflow>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved code that passed ruff+mypy but had a design flaw.** Claude trusted the green linters and skimmed comprehension. The code had a function named `validate_config` that also wrote the config file -- SRP violation hidden behind a reasonable name. The predict/verify protocol would have caught it: "Given the name, I predict this validates. But the body also calls `Path.write_text()`. Surprise."

**Rejected code for a false positive.** Claude flagged a parameter as "dead code" because it wasn't used in the function body. The parameter was required by a `CommandHandler` Protocol contract -- other implementations used it. Before flagging dead parameters, check if the function implements a Protocol.

**Tried to evaluate test evidence instead of delegating.** Claude found `lambda cmd: (0, "", "")` in tests and spent time analyzing whether it severed coupling. That's `/audit-python-tests`' job, and this audit never runs the test suite. Claude should have moved straight to comprehending the implementation code.

**Distracted by style while missing a logic bug.** Claude spent review time on naming conventions, import ordering, and docstring completeness. Meanwhile, a branch condition was inverted -- `if is_valid` should have been `if not is_valid`. Comprehension (understanding what the code does) must come before style. Style is the linter's job.

**Accepted code with tangled IO.** A `process_orders` function both computed order totals AND sent confirmation emails. Tests passed and types were correct. But the function was untestable without an email server -- IO and logic were tangled. The design evaluation (1.2) would have caught it: "Can core logic be tested without IO? No."

</failure_modes>

<verdict_format>

Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff every concern row is `PASS` or `NOT_APPLICABLE`; it is `REJECTED` if any concern is `FAIL`. An unavailable required inspection is `FAIL`, never `NOT_APPLICABLE`. Findings use severity `blocking` or `debt`.

```json
{
  "schema_version": 1,
  "skill": "audit-python-code",
  "target": "<scope-target>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "function-comprehension", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "design-coherence", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "import-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding carries `file`, `line`, `rule` (the concern name from the verdict table or a specific violation name), `severity: "blocking | debt"`, `message`, `observed`, and `expected`. The message names the violated rule and consequence only; it contains no corrective code sample, implementation patch, prescribed refactor, or required-change summary.

</verdict_format>

<what_to_avoid>

- Do NOT run or re-check the project's linters, type-checker, or tests — this audit runs no deterministic verification
- Do NOT evaluate test evidence quality; `/audit-python-tests` is the separate concern that judges it
- Do NOT commit or modify code (this skill is read-only)
- Do NOT generate fixes, replacement code, refactors, or required-change summaries
- Do NOT approve with caveats (binary verdict only)
- Do NOT reject for code style when comprehension found no design flaws

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for complete PASS and FAIL examples.

</example_review>

<success_criteria>

A sound verdict has these properties:

- [ ] The verdict states exactly one overall determination: `APPROVED` or `REJECTED`
- [ ] Every applicable Python concern in the verdict table was judged, with no skipped concern hidden by an approval
- [ ] Each `FAIL` finding names the file, line, violated concern or rule, and concrete evidence
- [ ] Each `NOT_APPLICABLE` row explains why the concern does not apply; a missing or blocked required inspection produces `FAIL`
- [ ] The same repository state and audit scope can reproduce the verdict from the listed evidence

</success_criteria>
