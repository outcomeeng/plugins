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

Scripts shipped in a skill's `scripts/` directory must be tested before inclusion. The skill's documentation records what was tested and with what inputs:

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

<runner_contract_rule>

A `SKILL.md` that states a contract for a bundled script — the operations the script accepts, the request fields each takes, the result fields each returns, and the reasons it blocks — states what that script does. A contract that names an operation the script lacks, omits one it has, names a request or result field the script does not read or write, states a field name, type, or requirement the script does not use, or lists a block reason the script never emits or omits one it emits misleads the caller, which fails at its first call.

Check the contract against the script, never against memory: read each operation, field, and block reason the contract states, and locate it in the script's argument parsing, request validation, result construction, and block paths. The rule applies to every skill whose `SKILL.md` states such a contract, whatever section holds it.

</runner_contract_rule>
