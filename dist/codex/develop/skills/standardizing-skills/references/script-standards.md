<overview>

Standards for skills that ship executable scripts in `scripts/`: validation-message quality and pre-inclusion testing. Read this before authoring a skill that bundles scripts.

</overview>

<validation_rule>

Validation scripts catch errors Claude might miss. They are force multipliers for quality-critical skills.

**A good validation script:**

- Emits verbose, specific error messages.
- Shows available valid options when something is invalid.
- Pinpoints the exact location of the problem.
- Suggests an actionable fix.
- Is deterministic — same input, same output.

```text
❌ "Validation failed."
✅ "Field 'signature_date' not found.
    Available fields: customer_name, order_total, signature_date_signed
    Did you mean 'signature_date_signed'?"
```

Verbose errors let Claude fix issues without user intervention.

</validation_rule>

<script_testing_rule>

Scripts shipped in a skill's `scripts/` directory must be tested before inclusion. The skill's documentation should record what was tested and with what inputs:

```bash
# scripts/extract_text.py
# Tested with:
# - Single page PDF ✓
# - Multi-page PDF ✓
# - Scanned PDF (OCR) ✓
# - Encrypted PDF → Returns clear error ✓
# - Non-PDF file → Returns clear error ✓
```

Cover: sample input, expected output match, error cases (invalid input, missing files), and cleanup (no temp files left behind).

</script_testing_rule>
