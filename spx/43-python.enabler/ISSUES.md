# Issues — Python plugin

## `python-code-standards` describes and branches on its callers

`instructions:skill-auditor` rejects `src/plugins/python/skills/python-code-standards/SKILL.md` for the blocking `caller_coupling` rule at three sentences that the skill-rename changeset leaves as `origin/main` carries them. Line 18 reads "Composing Python skills load these standards explicitly before writing, testing, or auditing." Line 24 reads "When another skill loads this reference inside a repository, it must also check for `spx/local/python.md`", which conditions the overlay check on being loaded by another skill. Line 342 reads "See `/audit-python-code` for false positive handling", which points to a named caller. A skill states its own behavior and does not name, describe or branch on its callers.

**Evidence**: `run-2026-10-16_23-30-29-164-c6d2cc27e43b.jsonl`, finding `caller_coupling`, severity blocking.

**Settlement condition.** The three sentences name no caller, the overlay instruction reads as the skill's own behavior, and the changeset passes `instructions:skill-auditor` over the skill.

## `python-code-standards` teaches general Python knowledge

`src/plugins/python/skills/python-code-standards/SKILL.md` restates what Claude already knows: modern union and generic syntax (`<modern_syntax>`, lines 286 to 297), avoiding a bare `except` (`<error_handling>`, lines 299 to 319), context managers for files (`<resource_management>`, lines 358 to 368) and why shadowing a builtin confuses (lines 228 to 233). The sections add ruff rule-code tables only. The file differs from `origin/main` at its `name` line alone. `instructions:skill-auditor` records the `known_content` rule at debt severity.

**Evidence**: `run-2026-10-16_23-30-29-164-c6d2cc27e43b.jsonl`, finding `known_content`, severity debt.

**Settlement condition.** The sections keep only product-specific conventions, non-obvious rules and verification commands, or a Verifier skips the finding on grounds recorded here.

## `rejection-criteria.md` restates the standards of `SKILL.md`

`src/plugins/python/skills/python-code-standards/references/rejection-criteria.md` is a recap table whose rows 7 to 30 repeat the ANN, N803, A002, E722, S1xx, SIM115, UP, ERA001, F401, import, `Any`, type-ignore and constant-object rules that `SKILL.md` states normatively. It also lists criteria that `SKILL.md` does not state: a fixture parameter in a test file and the PLR2004 magic values. Each standard has two homes, and the table carries two criteria with none. The only changed line is line 3, which names the renamed skill; the rows are as `origin/main` carries them. `instructions:skill-auditor` records the `duplicated_standards` rule at debt severity.

**Evidence**: `run-2026-10-16_23-30-29-164-c6d2cc27e43b.jsonl`, finding `duplicated_standards`, severity debt.

**Settlement condition.** One file holds each standard: the table is removed, or the two unstated criteria move into `SKILL.md` and the table restates nothing.

## `author-python-architecture` states skill dependencies as bare mentions

`src/plugins/python/skills/author-python-architecture/SKILL.md` line 50 ends "See `/author` for the complete ordering rules." and line 56 names the decision template as "owned by the `/understand` foundation's decision template". Both are unchanged against `origin/main`. Neither is the ``Use skill `{plugin}:{skill}`.`` instruction naming the exact installed skill. `instructions:skill-auditor` rejects the file with the blocking `composed_dependency_form` rule.

**Evidence**: `run-2026-10-16_23-46-46-029-7adab72f9537.jsonl`, finding `composed_dependency_form`, severity blocking.

**Settlement condition.** Each dependency reads ``Use skill `spec-tree:author`.`` and ``Use skill `spec-tree:understand`.``, and the changeset passes `instructions:skill-auditor` over the skill.

## `author-python-architecture` states one property twice

The objective at `src/plugins/python/skills/author-python-architecture/SKILL.md` line 16 (testability constraints live as ALWAYS/NEVER rules under the `## Verification` section's `### Audit` subsection) and the second success criterion at line 197 state the same property. Both lines are unchanged against `origin/main`. The objective names the output and its shape, and `<success_criteria>` states the properties that prove soundness without restating the objective. `instructions:skill-auditor` records the `objective_criteria_duplication` rule at debt severity.

**Evidence**: `run-2026-10-16_23-46-46-029-7adab72f9537.jsonl`, finding `objective_criteria_duplication`, severity debt.

**Evidence**: `run-2026-10-17_00-04-34-405-76b26fa5fae9.jsonl`, finding `objective_criteria_duplication`, severity debt, at `src/plugins/python/skills/author-python-architecture/SKILL.md` lines 16 and 197. The `<success_criteria>` bullet restates the objective's output property instead of adding a distinct soundness property.

**Settlement condition.** The objective and `<success_criteria>` share no restated property.

## `author-python-architecture` references route reads to a sibling and teach general knowledge

The five files under `src/plugins/python/skills/author-python-architecture/references/` are byte-identical to `origin/main` apart from the directory. `instructions:skill-auditor` records two debt-severity findings against them.

- `architecture-patterns.md` line 452 ends "See `test-infrastructure-patterns.md`.", so one reference routes a read to another (`nested_reference`). `SKILL.md` routes to each reference.
- Four files teach knowledge Claude already has (`known_content`): `architecture-patterns.md` lines 23 to 99, 247 to 299 and 367 to 420 (domain-driven entity, value-object and aggregate tutorials, single-responsibility examples, a definition of purity); `security-patterns.md` lines 274 to 314, 318 to 345 and 389 to 479 (`eval`/`exec`, SSL verification, path traversal and `pickle` tutorials); `testability-patterns.md` lines 29 to 102, 169 to 236 and 291 to 343 (debugging, regression and documentation test examples, a development progression of tests, pure-function and boundary-separation tutorials); `type-system-patterns.md` lines 144 to 192, 281 to 325 and 329 to 358 (`TypeVar`, generics, narrowing and dataclass tutorials).

**Evidence**: `run-2026-10-16_23-46-46-029-7adab72f9537.jsonl`, findings `nested_reference` and `known_content`, severity debt.

**Evidence**: `run-2026-10-17_00-04-34-405-76b26fa5fae9.jsonl`, finding `nested_reference`, severity debt, at `src/plugins/python/skills/author-python-architecture/references/architecture-patterns.md` line 452, which ends "See `test-infrastructure-patterns.md`." and routes a read from one reference to a sibling reference.

**Settlement condition.** No reference routes a read to another reference, and each reference keeps only product-specific conventions, non-training-data knowledge and verification thresholds, or a Verifier skips the findings on grounds recorded here.
