---
name: audit-python-code
model: sonnet
description: >-
  Python implementation-code audit methodology — design flaws and ADR compliance — composed by implementation-auditor for the Python code files in scope.
  Reached only through the dispatched implementation-auditor agent, never the main conversation.
allowed-tools: Read, Bash, Glob, Grep, Skill
---

<prerequisites>
Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.
</prerequisites>

<dispatch_gate>

This audit runs inside the dispatched `implementation-auditor` verifier context composing this skill for the Python code files in scope — isolated from the author context that produced the work under audit. When this skill loads in the author/main conversation rather than inside `implementation-auditor`, STOP — the audit must run in that verifier context. An already-dispatched implementation-auditor that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on Python implementation code — `APPROVED`, or `REJECTED` with each finding naming the design flaw, the violated rule, and the evidence.

</objective>

<constraints>

- NEVER modify files, generate fixes, write replacement code, commit changes, or change project state — this audit produces a verdict only.
- NEVER run deterministic validation, lint, type-check, test, or eval commands — the caller passes those before dispatch and CI re-runs them over the repository.
- NEVER evaluate test evidence quality — the composing implementation auditor invokes `/audit-python-tests` as a separate concern.
- ALWAYS keep findings to artifact, violated rule, evidence, and why the cited code violates the rule.
- NEVER include corrective code samples, implementation patches, prescribed refactors, or required-change summaries in the verdict.
- MUST set `APPROVED` only when every concern row passes or is explicitly not applicable; MUST set `REJECTED` when at least one concern row fails; NEVER add notes, warnings, or suggestions sections to `APPROVED` output.

</constraints>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/python.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<essential_principles>

**Comprehension is the whole job.**

This audit reads and judges Python implementation code; it runs no deterministic verification of its own. The caller brings the project's linters, type-checker, and tests to passing on the changeset before dispatching this audit, and CI re-runs them over the whole repository — so do NOT run or re-check what those gates already verified. Spend the whole audit on comprehension.

**Comprehension is the core value.**

Automated tools catch syntax errors, type mismatches, and lint violations. Claude catches: functions that do more than their name says, dead parameters required by no Protocol, IO tangled with logic, and designs that will break under change. The predict/verify protocol (Phase 1) is how these surface.

**Test evidence is out of scope.**

`/audit-python-tests` evaluates whether tests provide behavior-coupled evidence using the 4-property model (coupling, falsifiability, alignment, coverage). This skill judges implementation design, not test evidence — and it does not run the test suite; the caller already passed it before dispatch. Do not duplicate that work.

**Binary verdict, no caveats.**

The verdict is the only output. Findings prove violations; they do not prescribe fixes.

</essential_principles>

<audit_workflow>

Execute phases IN ORDER. Do not skip. This audit runs no deterministic verification — no linter, type-checker, or test run. The caller brought the project's validation and tests to passing on the changeset before dispatching this audit, and CI re-runs them over the whole repository; re-running them here only re-pays a cost already paid.

**Phase 0: Scope and Product Config**

1. Determine target files/directories
2. Check `pyproject.toml`, `AGENTS.md`, and `README.md` for tool and project configuration that informs comprehension (ruff, mypy, pytest settings; naming conventions) — read for context, never to run a gate. The linters already handled type annotations, magic numbers, bare excepts, unused imports, commented-out code, modern syntax, and security rules; comprehension covers what they cannot — deep relative imports, `sys.path` manipulation, unqualified `Any`, and `# type: ignore` without justification.

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

| Import pattern                                              | Classification                  |
| ----------------------------------------------------------- | ------------------------------- |
| `import pytest`                                             | Framework -- not reviewed       |
| `from hypothesis import given`                              | Framework -- not reviewed       |
| `import json`                                               | Stdlib -- not reviewed          |
| `from typing import TYPE_CHECKING`                          | Type-only -- erased at runtime  |
| `from product.config import parse_config`                   | Codebase (production) -- review |
| `from ..config import parse_config`                         | Codebase (relative) -- review   |
| `from <package>_testing.harnesses import ConfigTestHarness` | Codebase (test infra) -- review |

**Import depth rules:**

| Depth           | Example                   | Verdict                          |
| --------------- | ------------------------- | -------------------------------- |
| Package import  | `from product.config ...` | OK -- preferred                  |
| 1 level         | `from ..config ...`       | Review -- truly module-internal? |
| 2+ levels       | `from ....helpers ...`    | REJECT -- use package import     |
| sys.path manip. | `sys.path.insert(0, ...)` | REJECT -- always                 |

For stable locations (`<package>_testing.harnesses.*`, `<package>_testing.generators.*`, and inert fixture path providers), package imports are mandatory.

See `${SKILL_DIR}/references/false-positive-handling.md` for application context when evaluating security and linter suppression comments.

**Phase 2: ADR/PDR Compliance**

Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`). Verify each constraint is followed. Undocumented deviations make this concern `FAIL`. If the product has no spec hierarchy, this concern is `NOT_APPLICABLE`.

| Decision Record Constraint           | Violation Example                   | Verdict |
| ------------------------------------ | ----------------------------------- | ------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | FAIL    |
| "`l1` tests for logic" (ADR)         | `l1` tests hitting network          | FAIL    |
| "No ORM" (ADR)                       | SQLAlchemy models introduced        | FAIL    |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | FAIL    |

</audit_workflow>

<verdict_format>

Emit a structured verdict consumed by the composing verification workflow. The skill's entire output is the verdict payload. The composing workflow records findings, terminal state, and rendered projection through `spx verification run`.

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

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved code that passed ruff+mypy but had a design flaw.** What happened: Claude trusted green linters and approved `validate_config`, although it also wrote the config file. Why it failed: lint and type success were treated as design evidence. How to avoid: apply the predict/verify protocol and compare the function name with every side effect in its body.

**Rejected code for a false positive.** What happened: Claude flagged an unused parameter that a `CommandHandler` Protocol required. Why it failed: local body usage was judged without the implemented interface contract. How to avoid: inspect Protocol and base-class signatures before reporting dead parameters.

**Tried to evaluate test evidence instead of delegating.** What happened: Claude analyzed whether a test lambda severed coupling. Why it failed: implementation-code scope was mixed with the dedicated test-evidence concern. How to avoid: leave test evidence to `/audit-python-tests` and comprehend implementation behavior only.

**Distracted by style while missing a logic bug.** What happened: Claude reviewed naming, imports, and docstrings while missing an inverted branch. Why it failed: linter concerns displaced behavioral comprehension. How to avoid: comprehend control flow before judging design and leave mechanical style to validation.

**Accepted code with tangled IO.** What happened: Claude approved `process_orders`, which computed totals and sent email. Why it failed: passing tests and types hid a boundary that tangled pure logic with IO. How to avoid: apply design evaluation 1.2 and require core logic to remain testable without external IO.

</failure_modes>

<what_to_avoid>

- Do NOT run or re-check the project's linters, type-checker, or tests — the caller passed them on the changeset before dispatch, and CI re-runs them over the whole repository
- Do NOT evaluate test evidence quality; the composing implementation auditor invokes `/audit-python-tests` separately
- Do NOT commit or modify code (this skill is read-only)
- Do NOT generate fixes, replacement code, refactors, or required-change summaries
- Do NOT approve with caveats (binary verdict only)
- Do NOT reject for code style when comprehension found no design flaws

</what_to_avoid>

<example_review>
Read `${SKILL_DIR}/references/example-audit.md` for complete PASS and FAIL examples.

</example_review>

<success_criteria>

A sound verdict has these properties:

- [ ] The verdict states exactly one overall determination: `APPROVED` or `REJECTED`
- [ ] Every applicable Python concern in the verdict table was judged, with no skipped concern hidden by an approval
- [ ] Each `FAIL` finding names the file, line, violated concern or rule, and concrete evidence
- [ ] Each `NOT_APPLICABLE` row explains why the concern does not apply; a missing or blocked required inspection produces `FAIL`
- [ ] The same repository state and audit scope can reproduce the verdict from the listed evidence

</success_criteria>
