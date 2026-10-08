# Issues — Rust plugin

## `architect-rust` reference files structure themselves as markdown

`/audit-skill` `<reference_file_guidance>` prefers semantic XML for a reference file's own structure, reserving markdown for content that is itself a markdown artifact. `architect-rust/references/adr-patterns.md` and `architect-rust/references/rust-principles.md` use `#`/`##` headings for their own scaffolding, while the sibling `code-rust/references/{test-patterns,outcome-engineering-patterns}.md` already use pure XML. In `adr-patterns.md` the markdown *inside* each pattern is correct — an ADR is a markdown artifact — and only the file's own sections are at issue.

**Resolution shape**: convert each file's own sections to semantic XML tags, leaving the markdown-artifact examples alone.

**Revisit condition**: the auditor rates this recommendation-level rather than critical, and the same shape appears in other plugins — `spx/43-typescript.enabler/ISSUES.md` records the TypeScript half under "Legacy XML Structure Cleanup". Resolve per plugin when `architect-rust` next needs a reference-file change.

**Evidence**: raised by `instructions:skill-auditor` against `architect-rust` during the predicate-seam correction.

## Success criteria assert upstream sequencing nothing can check

`rust-test-standards` opens `<success_criteria>` with bullets asserting that `/test` selected the assertion type before implementation and that `/rust-standards` loaded before this reference. `architect-rust` carries the same shape at its own `<success_criteria>`. Neither is a property of the produced artifact, so no inspection of a test file or an ADR can falsify either. The remaining criteria in both skills are checkable, and `rust-test-standards`' `<predicate_and_oracle_litmus>` already operationalizes its own into inversion and mutation checks.

**Resolution shape**: fold the sequencing bullets into `<objective>`, `<reference_note>`, or the protocol phase that already prescribes the read order, and scope `<success_criteria>` to properties inspectable in the artifact.

**Revisit condition**: `python-test-standards` and `typescript-test-standards` carry the test-standards half verbatim, so correcting rust alone diverges it from two untouched siblings — the divergence [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)'s defect-class-sweep rule exists to prevent. Resolve as one pass across the three language plugins, each with its own `skill-auditor` gate and version bump.

**Evidence**: raised by `instructions:skill-auditor` against `rust-test-standards` and `architect-rust` during the predicate-seam correction.

## Credentialed level 3 behavior has no governing decision

`docs/cross-language-test-standards-drift-audit.md` records Rust test-standard follow-ups, and one remains open: whether credentialed `l3` behavior belongs in a shared cross-language decision or in a Rust execution-level child node. After that decision exists, the `#[ignore]` credential examples in the Rust test standards become fail-loud credential helpers. `audit-rust-tests` accepts a reasoned `#[ignore = "..."]` in a `.l3.rs` file only when a loaded product spec or decision declares the credentialed Level 3 lane. The remaining work decides credential resolution and skip policy, and it is independent of the predicate-seam correction already made to the worked examples.

**Settlement condition.** A decision names the home of credentialed `l3` behavior, the examples change to fail-loud credential helpers, and the changeset passes `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check` and `rust:audit-rust-tests`.

## The Rust delta of the source-laundering rule is unauthored

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` carries the language-neutral source-laundering rule: a case, example or expectation table placed inside a module under test so a test can cite a production path as its provenance, with ownership following consumption rather than address. `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/` declares the Python discriminator, and Rust has no delta.

The Rust delta is the discriminator in Rust terms: a `pub` item in the product crate whose only callers are `spx/**/tests/` modules and the `<product>-testing` crate, reached because `#[path]`-wired spec tests compile inside the product crate and can call items no released consumer can. `#[cfg(test)]` gating is the adjacent case and a different defect: it keeps the symbol out of the shipped artifact while still putting test data in the product crate.

**Settlement condition.** The delta is authored in this node and its evidence exists. Nothing blocks it.

## The Rust node still carries nine compliance assertions

The subtractive reduction removed the restated language-neutral seam assertions from `rust.md`, which cites `test-verification.md` and [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) for them, and left 9 Compliance assertions where it had 15. That is above the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`. Duplication no longer forces a decomposition, and assertion count does not close it. Rust has no test-standards subtree to absorb the residual deltas, unlike its Python and TypeScript siblings.

**Settlement condition.** A Rust test-standards subtree is warranted and `/decompose` creates it, or a Verifier skips the signal on the grounds this entry records.

## The architecture standards restate the decision template

A standard begins by loading the matching `/understand` template when one exists, and no skill encodes the template's shape, because a restated shape drifts the moment the template advances. The prose plugin conforms. In this node's skills, `src/plugins/rust/skills/rust-architecture-standards/SKILL.md` and `src/plugins/rust/skills/architect-rust/SKILL.md` restate the ADR section list inline.

**Settlement condition.** Each restated section list becomes a pointer that loads the decision template through the live `/understand` foundation, keeping only language-specific content rules, with the changeset gating its skills with `instructions:skill-auditor`. The Python and TypeScript pairs carry the same gap in `spx/43-python.enabler/25-python-standards.enabler/21-python-architecture.enabler/ISSUES.md` and `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler/ISSUES.md`.
