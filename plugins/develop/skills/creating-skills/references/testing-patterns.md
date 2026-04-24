<overview>

Test skills with evaluation-driven development. Build evaluations BEFORE writing extensive documentation so the skill solves real problems, not imagined ones. Test with every model that will use the skill. Add feedback loops for quality-critical operations.

</overview>

<evaluation_driven_development>

Build evaluations first, not last. This ensures you solve actual problems, not anticipated ones.

**Process:**

1. **Identify gaps** — run Claude on representative tasks WITHOUT a skill. Document specific failures or missing context.
2. **Create evaluations** — build 3+ scenarios that test these gaps.
3. **Establish baseline** — measure Claude's performance without the skill.
4. **Write minimal skill** — create just enough content to address the gaps and pass evaluations.
5. **Iterate** — execute evaluations, compare against baseline, refine.

**Why:** solves actual problems; prevents over-engineering; provides objective success criteria; makes iteration measurable.

</evaluation_driven_development>

<evaluation_structure>

```json
{
  "skills": ["skill-name"],
  "query": "User request that triggers the skill",
  "files": ["test-files/input.pdf"],
  "expected_behavior": ["Specific behavior 1", "Specific behavior 2", "Specific behavior 3"]
}
```

| Field               | Content                         |
| ------------------- | ------------------------------- |
| `skills`            | Which skill(s) should be loaded |
| `query`             | User request to test            |
| `files`             | Any input files needed          |
| `expected_behavior` | Observable behaviors to verify  |

</evaluation_structure>

<evaluation_scenarios>

Minimum 3 scenarios per skill:

1. **Happy path** — standard use case, everything works.
2. **Edge case** — unusual input, boundary conditions.
3. **Error case** — invalid input, missing dependencies.

```json
[
  {
    "name": "basic_extraction",
    "query": "Extract text from this PDF",
    "files": ["simple.pdf"],
    "expected_behavior": ["Extracts all text", "Preserves structure"]
  },
  {
    "name": "scanned_pdf",
    "query": "Extract text from this scanned PDF",
    "files": ["scanned.pdf"],
    "expected_behavior": ["Detects scanned content", "Uses OCR", "Warns about accuracy"]
  },
  {
    "name": "corrupted_pdf",
    "query": "Extract text from this PDF",
    "files": ["corrupted.pdf"],
    "expected_behavior": ["Detects corruption", "Provides clear error", "Suggests alternatives"]
  }
]
```

</evaluation_scenarios>

<multi_model_testing>

Skills act as additions to models — effectiveness depends on the underlying model. Test with every model the skill will run against.

| Model  | Check                                   | Adjust if needed              |
| ------ | --------------------------------------- | ----------------------------- |
| Haiku  | Does the skill provide enough guidance? | Add more explicit steps       |
| Sonnet | Is the skill clear and efficient?       | Balance detail vs conciseness |
| Opus   | Does the skill avoid over-explaining?   | Remove obvious explanations   |

**Process:**

1. Run the same task with each target model.
2. Note where models struggle or diverge.
3. Adjust the skill to work across all targets.
4. Re-test after changes.

What works for Opus may need more detail for Haiku.

</multi_model_testing>

<iterative_development>

Develop skills with two Claude instances — "Claude A" authors, "Claude B" uses.

**Creating new skills:**

1. Complete a task without a skill using normal prompting with Claude A.
2. Identify a pattern in what you repeatedly provide as context.
3. Ask Claude A to create a skill that captures the pattern.
4. Review for conciseness — remove unnecessary explanations.
5. Test with a fresh Claude B instance with the skill loaded.
6. Bring observations back to Claude A and iterate.

**Improving existing skills:**

1. Use the skill in real workflows with Claude B.
2. Note struggles, successes, unexpected choices.
3. Return to Claude A: "When using this skill, Claude B forgot X…"
4. Apply refinements from Claude A.
5. Re-test with Claude B.

**What to observe in Claude B:**

- Unexpected exploration paths → structure isn't intuitive
- Missed references to important content → links need to be explicit
- Overreliance on certain sections → content should be in SKILL.md
- Content that's never accessed → might be unnecessary

</iterative_development>

<feedback_loops>

Quality-critical skills include explicit feedback loops.

**Validate-Fix-Repeat:**

```markdown
<process>

1. Make your edits to the file.
2. Validate immediately: run the validation script.
3. If validation fails:
   - Review the error message carefully.
   - Fix the issues.
   - Run validation again.
4. Only proceed when validation passes.
5. Finalize output.

</process>
```

**Plan-Validate-Execute** (complex, destructive, or batch operations):

```markdown
<process>

1. Analyze input; create `changes.json` plan.
2. Validate the plan: `python validate_changes.py changes.json`.
3. If validation fails, fix the plan and re-validate.
4. Only when valid: execute changes.
5. Verify output.

</process>
```

Why this works: catches errors before they're applied, machine-verifiable via scripts, reversible planning phase, clear debugging through specific error messages.

</feedback_loops>
