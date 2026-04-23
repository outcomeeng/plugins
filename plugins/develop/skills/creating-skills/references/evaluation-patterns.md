<overview>
Evaluation-driven development ensures skills solve real problems. Create evaluations BEFORE writing extensive documentation.
</overview>

<evaluation_driven_development>
**Build evaluations first, not last.**

This approach ensures you're solving actual problems rather than anticipating requirements that may never materialize.

**Process**:

1. **Identify gaps**: Run Claude on representative tasks WITHOUT a skill. Document specific failures or missing context.

2. **Create evaluations**: Build 3+ scenarios that test these gaps.

3. **Establish baseline**: Measure Claude's performance without the skill.

4. **Write minimal instructions**: Create just enough content to address the gaps and pass evaluations.

5. **Iterate**: Execute evaluations, compare against baseline, refine.

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

**Components**:

- `skills`: Which skill(s) should be loaded
- `query`: The user request to test
- `files`: Any input files needed
- `expected_behavior`: Observable behaviors to verify

</evaluation_structure>

<iterative_testing>
**Develop skills iteratively with Claude**:

1. **Complete a task without a skill**: Work through a problem with Claude. Notice what information you repeatedly provide.

2. **Identify the reusable pattern**: What context would be useful for similar future tasks?

3. **Create the skill**: Capture the pattern in skill form.

4. **Review for conciseness**: Remove unnecessary explanations.

5. **Test on similar tasks**: Use the skill on related use cases.

6. **Iterate based on observation**: If Claude struggles, refine the skill.

**Observe how Claude navigates skills**:

- Unexpected exploration paths → structure isn't intuitive
- Missed connections → links need to be more explicit
- Overreliance on certain sections → content should be in SKILL.md
- Ignored content → might be unnecessary

</iterative_testing>

<evaluation_scenarios>
**Minimum 3 evaluation scenarios per skill**:

1. **Happy path**: Standard use case, everything works.

2. **Edge case**: Unusual input, boundary conditions.

3. **Error case**: Invalid input, missing dependencies.

**Example scenarios for a PDF skill**:

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

<feedback_loops>
**Implement feedback loops for quality-critical skills**:

Pattern: Run validator → fix errors → repeat

**Example**:

```text
<validation>After making changes:

1. Run validation: `python scripts/validate.py output/`
2. If errors found:
   - Review error message
   - Fix the issue
   - Run validation again
3. Only proceed when validation passes</validation>
```

Validation loops catch errors early and provide actionable feedback.
</feedback_loops>
