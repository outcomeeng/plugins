# Deficiencies: auditing-typescript-architecture

Insights from the `auditing-typescript-tests` rewrite applied to this skill. This skill is in better shape than the code audit — it has a clear scope (ADR review) and focused principles. Deficiencies are lighter.

## D1: No failure modes section

The test audit skills include concrete stories of auditor failures. This skill has none, despite architecture review being prone to specific failure patterns.

**Candidates for failure modes:**

- **Accepted temporal language because the sentence was technically true** — "Build orchestration currently shells out to Hugo" was accurate at review time, but the ADR became stale when the code changed. Accuracy ≠ atemporality.
- **Approved ADR without testing strategy because other sections were strong** — reviewer was impressed by the DI design and missed that no level assignments existed.
- **Rejected "After evaluating options" as temporal but the architect pushed back** — the line was in the Rationale section explaining why alternatives were rejected. Decision history narration is still temporal, even in Rationale.
- **Missed mocking language hidden in a code example** — ADR's example code showed `vi.mock()` in a test illustration, but reviewer only scanned prose.

## D2: No context loading for spec-tree (unlike Python version)

The Python architecture audit skill has a `<context_loading>` section that instructs the auditor to invoke `spec-tree:contextualizing` for spec-tree work items. The TypeScript version has no equivalent — it jumps straight to the review process.

**Action:** Add `<context_loading>` section matching the Python version. Without it, the auditor may review an ADR without loading ancestor ADRs/PDRs.

## D3: Example uses line numbers despite guidelines saying not to

The `<review_guidelines>` section is missing (present in Python as `<review_guidelines>`, absent in TypeScript). The example review references "Lines 45-47" — but the Python version's guidelines explicitly say "Don't reference specific line numbers (they change)."

**Action:** Add `<review_guidelines>` section. Remove line number references from the example.

## D4: Level definitions are TypeScript-specific but incomplete

The `<principles_to_enforce>` section lists Level 1 as "Node.js built-ins (fs, git, etc.) + temp fixtures" and Level 2 as "Hugo, Caddy, Claude Code, Docker, TypeScript compiler." This is a narrow set of examples.

**Action:** Generalize the level definitions to reference `/testing` Stage 2 Five Factors, then add TypeScript-specific examples. The current version looks like a hardcoded list rather than a principle.

## D5: Output format has unclosed code fence

The `<output_format>` section uses mixed ```` and ``` fencing that doesn't render correctly. The structure is sound but the formatting is broken.

**Action:** Fix code fence nesting in the output format template.

## D6: No structured verdict per principle checked

Like the code audit skill, the verdict is flat (APPROVED/REJECTED with a violations list). A structured per-principle table would make the output more consistent with the test audit format:

```text
| # | Principle            | Status | Detail                           |
|---|----------------------|--------|----------------------------------|
| 1 | Testing strategy     | PASS   | Levels assigned for all components |
| 2 | Mocking prohibition  | REJECT | "mock at boundary" in line 45    |
| 3 | Atemporal voice      | REJECT | Context narrates code state      |
```

## D7: Missing cross-reference to `/standardizing-typescript`

The Python version references `/standardizing-python-testing` for Protocol patterns. The TypeScript version doesn't reference `/standardizing-typescript` for interface/DI patterns.

**Action:** Add reference to `/standardizing-typescript` for TypeScript-specific DI patterns in ADR examples.

## Priority order

1. **D2** (add context loading) — critical for spec-tree correctness
2. **D1** (add failure modes) — highest impact on audit quality
3. **D3** (add guidelines, fix example) — consistency with Python version
4. **D5** (fix code fences) — rendering bug
5. **D6** (structured verdict) — machine-readable output
6. **D4** (generalize levels) — principle over examples
7. **D7** (add standardizing reference) — completeness
