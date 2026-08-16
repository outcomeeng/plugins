---
name: code-python
description: >-
  ALWAYS invoke this skill when writing or fixing implementation code for Python.
  NEVER write or fix Python implementation without this skill.
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Bash(python3 -m pytest:*), Bash(python3 -m mypy:*), Bash(python3 -m ruff:*)
---

Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

<repo_local_overlay>
**Standards are pre-loaded above.** After loading, check for `spx/local/python.md` and `spx/local/python-tests.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<objective>
Python implementation code that satisfies its node's established evidence and passes every selected deterministic check.
</objective>

<mode_detection>
**Determine the current mode:**

1. **WRITE mode** - Implementation doesn't exist or selected deterministic evidence is failing
   - Check: Selected tests fail, selected evals miss their declared threshold, or the governed implementation is absent
   - Action: Write implementation to satisfy the selected evidence

2. **FIX mode** - Implementation exists but was rejected by reviewer
   - Check: Recent `/audit-python-code` output shows REJECT with specific issues
   - Action: Read the rejection, fix the specific issues, re-run verification

**Always check which mode before proceeding.**
</mode_detection>

<prerequisites>

Before invoking this skill:

1. **Evidence must exist** - Established through `/verify`; when test is selected, expressed through `/test` and `/test-python`
2. **Evidence must be reviewed** - Approved by the auditor matching each selected evidence type
3. **Spec must be loaded** - Context from `/spec-tree:contextualize`
4. **Standards are pre-loaded above**

If required evidence does not exist or lacks approval, return to the evidence workflow.
</prerequisites>

<audit_requirement_handoff>

For every `/verify` routing row whose verification type is audit, the authoritative requirement is the exact assertion or decision-rule text in the routed spec or decision artifact carrying `([audit])`.

Before reporting completion:

1. Read the routed source artifact again and confirm the exact subject text still carries `([audit])`.
2. Emit one row per audit routing row under `Audit requirements`:

```text
| Source artifact | Exact subject | Status |
| <full spx/... path> | <exact assertion or rule text> | preserved |
```

The table's row count must equal the count of audit rows in `/verify`'s routing result. When that count is zero, report `Audit requirements: none selected` instead of an empty table.

</audit_requirement_handoff>

<write_mode_workflow>

Run the product's own canonical commands when it documents them — a `AGENTS.md` instruction, a Justfile or Makefile recipe, or a package script. The `python3 -m …` invocations below are the portable fallback for a product that ships no wrapper; report any tool the product lacks rather than skipping it.

`allowed-tools` preapproves only the listed raw-tool fallbacks. A repository-canonical wrapper outside those patterns uses the runtime's normal per-call approval path; NEVER select a fallback merely to avoid that approval.

Resolve `<python-source-paths>` to the implementation paths declared by the product's package metadata and named by the governed test imports or eval producer contract. Never assume a package directory name.
Set `{node_path}` to the canonical full node path established by the loaded spec-tree context.

**Step 1 — Understand the selected evidence.** Read `/verify`'s routing result for the node and handle every selected type:

- **Test:** Use Glob to list `{node_path}/tests/*.py`, Read each linked test file, and run the focused product test command to observe its failure before implementation. The raw fallback is:

```bash
python3 -m pytest {node_path}/tests/ -v
```

- **Evaluate:** Read each linked eval definition, cases, materialized prompt, and real producer contract. Run the product's selected eval command to observe the current score and declared completion threshold before implementation.
- **Audit:** Apply `<audit_requirement_handoff>` to the pathless isolated-verifier requirement and read the semantic constraint it will judge. Do not invent a test or eval artifact for it.

Identify the behavior each selected evidence artifact establishes, the expected interfaces, and the source path that implements the real subject.

**Step 2 — Write implementation.** Write minimal code that satisfies the governed behavior and every selected evidence requirement.

**Code standards (per `/python-standards`):**

```python
# ✅ Type annotations on ALL functions
def process_order(order: Order, config: Config) -> OrderResult: ...


# ✅ Source-owned semantic values in production modules
MIN_ORDER_VALUE = 10
MAX_ITEMS = 100


# ✅ Dependency injection for external dependencies
@dataclass
class Deps:
    run_command: CommandRunner
```

**Step 3 — Run selected deterministic evidence.**

Run the focused product test command for selected tests and the product eval command for selected evals. The Python test fallback is:

```bash
python3 -m pytest {node_path}/tests/ -v
```

Every selected test must pass and every selected eval must meet its declared threshold. Record each pathless audit requirement through `<audit_requirement_handoff>` for the later isolated verifier.

**Step 4 — Refactor.** Clean up while keeping every selected deterministic check passing:

1. Move semantic values to the owning source module
2. Simplify
3. DRY

**Step 5 — Self-verify.**

```bash
# Type checking
python3 -m mypy <python-source-paths>

# Linting
python3 -m ruff check <python-source-paths>

# Selected tests, when present
python3 -m pytest {node_path}/tests/ -v
```

Run selected eval commands here as well. Type checking, linting, every selected test, and every selected eval threshold must pass before declaring complete.

</write_mode_workflow>

<fix_mode_workflow>

**Step 1 — Read rejection feedback.** Find the most recent `/audit-python-code` output. Look for:

- Specific file:line locations
- Issue categories (magic values, missing DI, etc.)
- Required fixes

**Step 2 — Apply fixes.** For each rejection reason:

| Rejection Category       | Fix Action                                       |
| ------------------------ | ------------------------------------------------ |
| Magic values             | Move semantic values to the owning source module |
| Missing type annotations | Add types to all functions                       |
| Direct external imports  | Refactor to dependency injection                 |
| Deep relative imports    | Change to absolute imports                       |
| Missing `-> None`        | Add return type                                  |
| Security issues          | Fix the vulnerability (don't suppress)           |

**Step 3 — Verify fixes.**

```bash
# Run selected tests, when present
python3 -m pytest {node_path}/tests/ -v

# Type checking
python3 -m mypy <python-source-paths>

# Linting
python3 -m ruff check <python-source-paths>
```

Run every selected eval command after the fix and require its declared threshold. Rebuild and verify the `<audit_requirement_handoff>` rows for re-review.

**Step 4 — Report what was fixed.**

```markdown
## Implementation Fixed

### Issues Addressed

| Issue       | Location        | Fix Applied                       |
| ----------- | --------------- | --------------------------------- |
| Magic value | handler.py:45   | Extracted to MAX_RETRIES constant |
| Missing DI  | processor.py:12 | Added ProcessorDeps dataclass     |

### Verification

All selected deterministic evidence passes. Types and lint clean. Every `Audit requirements` row reports `preserved` for re-review.
```

</fix_mode_workflow>

<code_patterns>

**Named constants**

```python
# ❌ REJECTED
def validate_score(score: int) -> bool:
    return 0 <= score <= 100


# ✅ REQUIRED
MIN_SCORE = 0
MAX_SCORE = 100


def validate_score(score: int) -> bool:
    return MIN_SCORE <= score <= MAX_SCORE
```

**Dependency injection**

```python
# ❌ REJECTED
import subprocess


def sync_files(src: str, dest: str) -> bool:
    result = subprocess.run(["rsync", src, dest])
    return result.returncode == 0


# ✅ REQUIRED
@dataclass
class SyncDeps:
    run_command: CommandRunner


def sync_files(src: str, dest: str, deps: SyncDeps) -> bool:
    returncode, _, _ = deps.run_command.run(["rsync", src, dest])
    return returncode == 0
```

**Type annotations**

```python
# ✅ All functions have full type annotations
def get_user(user_id: int) -> User | None:
    users: list[User] = fetch_users()
    return next((u for u in users if u.id == user_id), None)
```

</code_patterns>

<output_format>

**WRITE mode output:**

```markdown
## Implementation Complete

### Node: {node_path}

### Files Created/Modified

| File                 | Action  | Description   |
| -------------------- | ------- | ------------- |
| `product/handler.py` | Created | Order handler |

### Verification

- Selected evidence: ✓ Pass
- Types: ✓ Pass
- Lint: ✓ Pass
- Python standards audit: required
- Standards: `/python-standards`; overlays: `<loaded spx/local/python*.md paths or none>`

Ready for review.
```

**FIX mode output:**

```markdown
## Implementation Fixed

### Issues Addressed

| Issue   | Location    | Fix Applied |
| ------- | ----------- | ----------- |
| {issue} | {file:line} | {fix}       |

### Verification

All checks pass. Ready for re-review.

- Python standards audit: required
- Standards: `/python-standards`; overlays: `<loaded spx/local/python*.md paths or none>`
```

</output_format>

<failure_modes>

**Claude forced a test workflow onto an eval-backed node.**

What happened: Claude listed `{node_path}/tests/*.py` and required pytest RED/GREEN even though `/verify` selected evaluate for the governed behavior.

Why it failed: the implementation workflow treated test as universal evidence and had no valid path for an LLM-driven producer whose structured output is scored by an eval.

How to avoid: branch only on `/verify`'s routing rows. Run pytest RED/GREEN for selected tests, run the selected eval command and threshold for selected evals, and create neither artifact for an audit-only subject.

**Claude dropped a pathless audit requirement after deterministic checks passed.**

What happened: tests, mypy, and Ruff passed, then the readiness report omitted the audit-backed assertion the isolated verifier still had to judge.

Why it failed: “preserve the audit requirement” named no source artifact or observable handoff.

How to avoid: apply `<audit_requirement_handoff>`, re-read each routed `([audit])` subject, and require one `preserved` report row per audit routing row before readiness.

**Claude self-attested Python standards compliance.**

What happened: the readiness checklist claimed the implementation followed `/python-standards` without a deterministic result or isolated audit verdict.

Why it failed: a subjective checkbox let the authoring context grade its own conformance.

How to avoid: emit `Python standards audit: required` with the loaded standards and overlays; publication waits for the implementation-audit projection's exact `terminalStatus: approved`.

</failure_modes>

<success_criteria>

Implementation is ready for review when:

- [ ] Every selected Python test command passes and every selected eval command meets its declared threshold; a type absent from `/verify`'s routing result is not fabricated
- [ ] The product's resolved Python type-check command passes
- [ ] The product's resolved Python lint/format check command passes
- [ ] The `Audit requirements` report has one `preserved` row per audit routing row from `/verify`, or reports `none selected` when the routing result has none
- [ ] The readiness report carries `Python standards audit: required` and names `/python-standards` plus every loaded Python overlay path; after the implementation audit, publication requires the returned projection's exact `terminalStatus` to be `approved`
- [ ] FIX mode addresses every supplied reviewer finding with a code change or a stated evidence-based rejection

</success_criteria>
