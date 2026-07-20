# Issues: Python Tests

## `audit-python-tests` derives gate status differently from its Rust and TypeScript siblings

`audit-rust-tests` and `audit-typescript-tests` each wrap their checks in named `gate_1_assertion` and `gate_2_architectural` tags and state the PASS/FAIL derivation explicitly. `audit-python-tests` instead organizes the same checks as flat top-level tags — `<coupling_audit>`, `<falsifiability_audit>`, `<source_ownership_audit>`, and siblings — with no gate wrapper and no stated derivation.

**Why it matters.** `/audit-tests` composes all three through its `compose_language` step and merges their findings by row name. Two of the three declare how a row reaches PASS or FAIL; the third leaves a composing reader to infer it.

**Evidence.** A skill audit of the test-audit family raised this at recommendation severity, confirming the asymmetry predates the changeset that introduced the shared `test-evidence-standards` skill and was neither introduced nor worsened by it.

**Why it is recorded rather than fixed.** Restructuring `audit-python-tests` into explicit gate blocks rewrites the skill's section layout rather than editing the regions a changeset touches. The changeset that surfaced it reconciled specific cross-file contracts — the `declarations` property, the coupling taxonomy, the oracle-independence split, the `NOT_APPLICABLE` composition shape — each a bounded correction to a named contradiction. A layout restructure is a different unit of work with a different review shape.

**Resolution shape.** Give `audit-python-tests` the same named gate tags and explicit status derivation the Rust and TypeScript auditors carry, keeping the check content unchanged. Run the skill auditor over all three afterward, since the composed contract is what the asymmetry affects.

**Revisit condition.** Resolve when `audit-python-tests` next needs a structural change, or when a change to `/audit-tests` `compose_language` depends on all three language auditors declaring status the same way.
