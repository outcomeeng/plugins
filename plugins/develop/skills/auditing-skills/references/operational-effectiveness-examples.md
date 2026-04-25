<operational_effectiveness_examples>
Examples of operational effectiveness issues to flag:

<example name="unverifiable_success_criteria">
❌ Flag as critical for complex skills:
```xml
<success_criteria>
Task is complete when:
- All stories have SPX tests
- Coverage verified
- Legacy tests removed
</success_criteria>
```

**Why it fails**: "Coverage verified" is not testable. Verified how? What threshold? What command?

✅ Should be:

````xml
<success_criteria>
Task is complete when:
- All stories have SPX tests (verify: `ls spx/.../tests/*.test.ts` returns files for each story)
- Coverage parity confirmed (verify: both commands below show same % for target files)
  ```bash
  pnpm vitest run tests/legacy/... --coverage | grep "target.ts"
  pnpm vitest run spx/.../tests --coverage | grep "target.ts"
````

- Legacy tests removed via git rm (verify: `git status` shows deletions staged)

**Threshold**: Coverage delta must be ≤0.5%. If larger, STOP and identify missing tests.
</success_criteria>

````
**Why it works**: Every criterion has a verification command and a pass/fail threshold.
</example>

<example name="missing_verification_gates">
❌ Flag as critical for multi-step skills:
```xml
<workflow>
1. Read DONE.md files from worktree
2. Create SPX tests matching DONE.md entries
3. Verify coverage matches
4. Remove legacy tests with git rm
5. Create SPX-MIGRATION.md
</workflow>
````

**Why it fails**: No stop points. Agent could remove legacy tests before verifying coverage.

✅ Should be:

```xml
<workflow>1. Read DONE.md files from worktree
2. Create SPX tests matching DONE.md entries

**GATE 1**: Before proceeding, verify:
- [ ] SPX test count matches DONE.md entry count
- [ ] All SPX tests pass: `pnpm vitest run spx/.../tests`
If gate fails, fix tests before continuing.

3. Verify coverage matches (run both, compare percentages)
4. Remove legacy tests with git rm

**GATE 2**: Before committing, verify:
- [ ] `pnpm test` passes
- [ ] `git status` shows only expected changes
If gate fails, do not commit.

5. Create SPX-MIGRATION.md</workflow>
```

**Why it works**: Explicit gates prevent proceeding with broken state.
</example>

<example name="missing_failure_modes">
❌ Flag as recommendation for complex skills:
Skill has detailed workflow but no `<failure_modes>` section.

**Why it matters**: Agents will make the same mistakes that previous agents made. Failure modes capture hard-won operational knowledge.

✅ Should include:

```xml
<failure_modes>Failures from actual usage:

**Failure 1: Compared coverage at wrong granularity**
- What happened: Agent saw 39% coverage for one story and stopped, thinking migration failed
- Why it failed: Multiple stories share one legacy file; per-story coverage is meaningless
- How to avoid: ALWAYS compare at legacy file level, not story level

**Failure 2: Removed shared legacy file too early**
- What happened: Agent removed tests/integration/cli.test.ts after migrating story-32
- Why it failed: Stories 43 and 54 also contributed tests to that file
- How to avoid: Build legacy_file → [stories] map BEFORE migration. Only remove after ALL contributing stories migrated.</failure_modes>
```

**Why it works**: Future agents learn from past mistakes without repeating them.
</example>

<example name="abstract_vs_concrete_examples">
❌ Flag as recommendation:
```xml
<success_criteria>
Coverage should match between legacy and SPX tests.
</success_criteria>
```

**Why it fails**: What does "match" mean? What numbers? How do I compare my output?

✅ Should be:

```xml
<success_criteria>Coverage must match. Concrete example from actual migration:

Legacy tests:
  tests/unit/status/state.test.ts (5 tests)
  tests/integration/status/state.unit.test.ts (19 tests)
  Total: 24 tests, 86.3% coverage on src/status/state.ts

SPX tests:
  spx/.../21-initial.story/tests/state.mapping.l1.test.ts (5 tests)
  spx/.../32-transitions.story/tests/state.scenario.l2.test.ts (7 tests)
  spx/.../43-concurrent.story/tests/state.scenario.l2.test.ts (4 tests)
  spx/.../54-edge-cases.story/tests/state.scenario.l2.test.ts (8 tests)
  Total: 24 tests, 86.3% coverage on src/status/state.ts

Verdict: ✓ Test counts match (24=24), coverage matches (86.3%=86.3%)</success_criteria>
```

**Why it works**: Agent can compare their actual output to the example and know if they succeeded.
</example>

<example name="procedural_without_operational">
❌ Flag as critical for complex skills:
Skill has detailed `<workflow>` (450 lines of steps) but:
- `<success_criteria>` is 3 lines of vague statements
- No `<verification_gates>`
- No `<failure_modes>`

**Pattern**: Heavy procedural, light operational = agents know HOW but not WHETHER they succeeded.

**Why it matters**: This is the most common skill failure mode. The skill tells you what to do but not how to verify you did it right. Agents follow steps, produce wrong output, and don't realize it.

✅ Balanced skill has roughly equal investment in:

- Procedural content (workflow, steps, commands)
- Operational content (success criteria, verification gates, failure modes, concrete examples)

</example>
</operational_effectiveness_examples>
