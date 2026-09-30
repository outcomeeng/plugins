# Issues — Rust plugin

## `architect-rust` reference files structure themselves as markdown

`/audit-skill` `<reference_file_guidance>` prefers semantic XML for a reference file's own structure, reserving markdown for content that is itself a markdown artifact. `architect-rust/references/adr-patterns.md` and `architect-rust/references/rust-principles.md` use `#`/`##` headings for their own scaffolding, while the sibling `code-rust/references/{test-patterns,outcome-engineering-patterns}.md` already use pure XML. In `adr-patterns.md` the markdown *inside* each pattern is correct — an ADR is a markdown artifact — and only the file's own sections are at issue.

**Resolution shape**: convert each file's own sections to semantic XML tags, leaving the markdown-artifact examples alone.

**Revisit condition**: the auditor rates this recommendation-level rather than critical, and the same shape appears in other plugins — `spx/43-typescript.enabler/ISSUES.md` records the TypeScript half under "Legacy XML Structure Cleanup". Resolve per plugin when `architect-rust` next needs a reference-file change.

**Evidence**: raised by `instructions:skill-auditor` against `architect-rust` during the predicate-seam correction.

## Success criteria assert upstream sequencing nothing can check

`rust-test-standards` opens `<success_criteria>` with bullets asserting that `/test` selected the assertion type before implementation and that `/rust-standards` loaded before this reference. `architect-rust` carries the same shape at its own `<success_criteria>`. Neither is a property of the produced artifact, so no inspection of a test file or an ADR can falsify either. The remaining criteria in both skills are checkable, and `rust-test-standards`' `<predicate_and_oracle_litmus>` already operationalizes its own into inversion and mutation checks.

**Resolution shape**: fold the sequencing bullets into `<objective>`, `<reference_note>`, or the protocol phase that already prescribes the read order, and scope `<success_criteria>` to properties inspectable in the artifact.

**Revisit condition**: `python-test-standards` and `typescript-test-standards` carry the test-standards half verbatim, so correcting rust alone diverges it from two untouched siblings — the divergence `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`'s defect-class-sweep rule exists to prevent. Resolve as one pass across the three language plugins, each with its own `skill-auditor` gate and version bump.

**Evidence**: raised by `instructions:skill-auditor` against `rust-test-standards` and `architect-rust` during the predicate-seam correction.
