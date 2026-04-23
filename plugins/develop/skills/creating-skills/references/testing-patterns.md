# Testing Patterns

Test skills with multiple models and use evaluation-driven development.

---

## Test With Multiple Models

Skills act as additions to models, so effectiveness depends on the underlying model. Test with all models you plan to use.

### Model-Specific Considerations

| Model  | Check                               | Adjust If Needed              |
| ------ | ----------------------------------- | ----------------------------- |
| Haiku  | Does skill provide enough guidance? | Add more explicit steps       |
| Sonnet | Is skill clear and efficient?       | Balance detail vs conciseness |
| Opus   | Does skill avoid over-explaining?   | Remove obvious explanations   |

What works perfectly for Opus might need more detail for Haiku.

### Testing Process

1. Run same task with each target model
2. Note where models struggle or diverge
3. Adjust skill to work well across all targets
4. Re-test after changes

---

## Evaluation-Driven Development

**Build evaluations BEFORE writing extensive documentation.** This ensures your skill solves real problems rather than documenting imagined ones.

### Process

1. **Identify gaps**: Run Claude on representative tasks WITHOUT a skill. Document specific failures
2. **Create evaluations**: Build 3 scenarios that test these gaps
3. **Establish baseline**: Measure Claude's performance without the skill
4. **Write minimal skill**: Create just enough content to address gaps and pass evaluations
5. **Iterate**: Execute evaluations, compare against baseline, refine

### Evaluation Structure

```json
{
  "skills": ["skill-name"],
  "query": "Task description that user would ask",
  "files": ["test-files/sample.pdf"],
  "expected_behavior": [
    "Successfully performs action X",
    "Handles edge case Y correctly",
    "Produces output in format Z"
  ]
}
```

### Why This Matters

- Ensures you solve actual problems, not anticipated ones
- Prevents over-engineering
- Provides objective success criteria
- Makes iteration measurable

---

## Iterative Development with Claude

Work with one Claude instance ("Claude A") to create skills that another instance ("Claude B") will use.

### Creating New Skills

1. **Complete task without skill**: Work through problem with Claude A using normal prompting
2. **Identify pattern**: Notice what context you repeatedly provide
3. **Ask Claude A to create skill**: "Create a skill that captures this pattern"
4. **Review for conciseness**: Remove unnecessary explanations
5. **Test with Claude B**: Fresh instance with skill loaded
6. **Iterate**: Bring observations back to Claude A

### Improving Existing Skills

1. Use skill in real workflows with Claude B
2. Note struggles, successes, unexpected choices
3. Return to Claude A: "When using this skill, Claude B forgot X..."
4. Apply refinements from Claude A
5. Re-test with Claude B

### What to Observe

- Unexpected file access patterns
- Missed references to important content
- Overreliance on certain sections
- Content that's never accessed

---

## Feedback Loops

### Validate-Fix-Repeat Pattern

For quality-critical operations, include explicit feedback loops:

```markdown
## Document Editing Process

1. Make your edits to the file
2. **Validate immediately**: Run validation script
3. If validation fails:
   - Review the error message carefully
   - Fix the issues
   - Run validation again
4. **Only proceed when validation passes**
5. Finalize output
```

### Plan-Validate-Execute Pattern

For complex, destructive, or batch operations:

```markdown
## Batch Update Process

1. Analyze input, create `changes.json` plan
2. Validate plan: `python validate_changes.py changes.json`
3. If validation fails, fix plan and re-validate
4. Only when valid: execute changes
5. Verify output
```

**Why this works:**

- Catches errors before they're applied
- Machine-verifiable (scripts provide objective checks)
- Reversible planning phase
- Clear debugging (specific error messages)

---

## Script Testing

### Test Process for scripts/

All scripts must be tested before inclusion:

1. Run with sample input
2. Verify output matches expected
3. Test error cases (invalid input, missing files)
4. Check cleanup (no temp files left)

### Documentation Format

```bash
# scripts/extract_text.py
# Tested with:
# - Single page PDF ✓
# - Multi-page PDF ✓
# - Scanned PDF (OCR) ✓
# - Encrypted PDF → Returns clear error ✓
# - Non-PDF file → Returns clear error ✓
```

### Verbose Error Messages

Make validation scripts verbose with specific error messages:

```
❌ Field 'signature_date' not found.
   Available fields: customer_name, order_total, signature_date_signed

   Did you mean 'signature_date_signed'?
```

This helps Claude fix issues without user intervention.
