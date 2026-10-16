# Issues — Rust plugin

## `author-rust-architecture` reference files structure themselves as markdown

`/audit-skill` `<reference_file_guidance>` prefers semantic XML for a reference file's own structure, reserving markdown for content that is itself a markdown artifact. `author-rust-architecture/references/adr-patterns.md` and `author-rust-architecture/references/rust-principles.md` use `#`/`##` headings for their own scaffolding, while the sibling `author-rust-code/references/{test-patterns,outcome-engineering-patterns}.md` already use pure XML. In `adr-patterns.md` the markdown *inside* each pattern is correct — an ADR is a markdown artifact — and only the file's own sections are at issue.

**Resolution shape**: convert each file's own sections to semantic XML tags, leaving the markdown-artifact examples alone.

**Revisit condition**: the auditor rates this recommendation-level rather than critical, and the same shape appears in other plugins — `spx/43-typescript.enabler/ISSUES.md` records the TypeScript half under "Legacy XML Structure Cleanup". Resolve per plugin when `author-rust-architecture` next needs a reference-file change.

**Evidence**: raised by `instructions:skill-auditor` against `author-rust-architecture` during the predicate-seam correction.

## Success criteria assert upstream sequencing nothing can check

`rust-test-standards` opens `<success_criteria>` with bullets asserting that `/test` selected the assertion type before implementation and that `/rust-code-standards` loaded before this reference. `author-rust-architecture` carries the same shape at its own `<success_criteria>`. Neither is a property of the produced artifact, so no inspection of a test file or an ADR can falsify either. The remaining criteria in both skills are checkable, and `rust-test-standards`' `<predicate_and_oracle_litmus>` already operationalizes its own into inversion and mutation checks.

**Resolution shape**: fold the sequencing bullets into `<objective>`, `<reference_note>`, or the protocol phase that already prescribes the read order, and scope `<success_criteria>` to properties inspectable in the artifact.

**Revisit condition**: `python-test-standards` and `typescript-test-standards` carry the test-standards half verbatim, so correcting rust alone diverges it from two untouched siblings — the divergence [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)'s defect-class-sweep rule exists to prevent. Resolve as one pass across the three language plugins, each with its own `skill-auditor` gate and version bump.

**Evidence**: raised by `instructions:skill-auditor` against `rust-test-standards` and `author-rust-architecture` during the predicate-seam correction.

## Credentialed level 3 behavior has no governing decision

`docs/cross-language-test-standards-drift-audit.md` records Rust test-standard follow-ups, and one remains open: whether credentialed `l3` behavior belongs in a shared cross-language decision or in a Rust execution-level child node. After that decision exists, the `#[ignore]` credential examples in the Rust test standards become fail-loud credential helpers. `audit-rust-test` accepts a reasoned `#[ignore = "..."]` in a `.l3.rs` file only when a loaded product spec or decision declares the credentialed Level 3 lane. The remaining work decides credential resolution and skip policy, and it is independent of the predicate-seam correction already made to the worked examples.

**Settlement condition.** A decision names the home of credentialed `l3` behavior, the examples change to fail-loud credential helpers, and the changeset passes `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check` and `rust:audit-rust-test`.

## The Rust delta of the source-laundering rule is unauthored

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` carries the language-neutral source-laundering rule: a case, example or expectation table placed inside a module under test so a test can cite a production path as its provenance, with ownership following consumption rather than address. `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/` declares the Python discriminator, and Rust has no delta.

The Rust delta is the discriminator in Rust terms: a `pub` item in the product crate whose only callers are `spx/**/tests/` modules and the `<product>-testing` crate, reached because `#[path]`-wired spec tests compile inside the product crate and can call items no released consumer can. `#[cfg(test)]` gating is the adjacent case and a different defect: it keeps the symbol out of the shipped artifact while still putting test data in the product crate.

**Settlement condition.** The delta is authored in this node and its evidence exists. Nothing blocks it.

## The Rust node still carries nine compliance assertions

The subtractive reduction removed the restated language-neutral seam assertions from `rust.md`, which cites `test-verification.md` and [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) for them, and left 9 Compliance assertions where it had 15. That is above the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`. Duplication no longer forces a decomposition, and assertion count does not close it. Rust has no test-standards subtree to absorb the residual deltas, unlike its Python and TypeScript siblings.

**Settlement condition.** A Rust test-standards subtree is warranted and `/decompose` creates it, or a Verifier skips the signal on the grounds this entry records.

## The architecture standards restate the decision template

A standard begins by loading the matching `/understand` template when one exists, and no skill encodes the template's shape, because a restated shape drifts the moment the template advances. The prose plugin conforms. In this node's skills, `src/plugins/rust/skills/rust-architecture-standards/SKILL.md` and `src/plugins/rust/skills/author-rust-architecture/SKILL.md` restate the ADR section list inline.

**Settlement condition.** Each restated section list becomes a pointer that loads the decision template through the live `/understand` foundation, keeping only language-specific content rules, with the changeset gating its skills with `instructions:skill-auditor`. The Python and TypeScript pairs carry the same gap in `spx/43-python.enabler/25-python-standards.enabler/21-python-architecture.enabler/ISSUES.md` and `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler/ISSUES.md`.

## `rust-code-standards` describes and branches on its callers

`instructions:skill-auditor` rejects `src/plugins/rust/skills/rust-code-standards/SKILL.md` for the `caller_coupling` rule at two sentences that the skill-rename changeset leaves as `origin/main` carries them. Line 18, in `<reference_note>`, reads "Composing Rust skills load these standards explicitly before writing, testing, or auditing." Line 22, in `<repo_local_overlay>`, opens "When another skill loads this reference inside a repository, it must also check for `spx/local/rust.md`", which conditions the overlay check on being loaded by another skill. A skill states its own behavior and does not name, describe or branch on its callers. The verdict is blocking, so the skill does not pass `/audit-skill` while the two sentences stand.

**Evidence**: `run-2026-10-16_23-47-02-323-2e1559d6997f.jsonl`, finding `caller_coupling`, severity blocking.

**Settlement condition.** The `<reference_note>` sentence names no caller, and the overlay instruction reads as the skill's own behavior ("inside a repository, check for `spx/local/rust.md` at the repository root, then read it after this reference if it exists"), with the changeset passing `instructions:skill-auditor` over the skill.

## Rust skills state composed skill dependencies as bare slash mentions

`instructions:skill-auditor` rejects three Rust skills for the `composed_dependency_form` rule. Each states a dependency as a slash mention or as `invoke`/`Invoke`/`Read` instead of ``Use skill `{plugin}:{skill}`.`` naming the exact installed skill. Every listed line is unchanged against `origin/main`:

- `src/plugins/rust/skills/author-rust-architecture/SKILL.md` lines 36 ("Invoke `spec-tree:contextualize`"), 101 ("See `/author` skill"), 119 ("Read `/rust-test-standards`"), 124 ("Read `/author` skill for ADR template"), 153 ("(from `/understand`)") and 213 ("`/rust-test-standards` was loaded"). Line 72 of the same file already uses the exact form for `rust:rust-test-standards`, so the file is inconsistent with itself. Run `run-2026-10-16_23-46-45-343-9c6b28e60df3.jsonl`.
- `src/plugins/rust/skills/simplify-rust-code/SKILL.md` lines 28 (`/understand`), 29 (`/scope-changeset`), 30 (`/contextualize`) and 76 (`/scope-changeset`). Run `run-2026-10-16_23-46-53-896-e4b6c2d39577.jsonl`; run `run-2026-10-16_23-30-17-467-300fe8a25927.jsonl` raised lines 28 to 30 against the same unchanged text.
- `src/plugins/rust/skills/author-rust-code/SKILL.md` line 96 ("invoke `spec-tree:contextualize` with the full path"). Run `run-2026-10-16_23-46-48-006-fc4c697d67ea.jsonl`.

All are blocking verdicts. The dependency form is the one the sibling lines in the same files already use, so the divergence is inside each skill.

**Settlement condition.** Each listed dependency reads ``Use skill `spec-tree:contextualize`.``, ``Use skill `spec-tree:author`.``, ``Use skill `spec-tree:understand`.``, ``Use skill `spec-tree:scope-changeset`.`` or ``Use skill `rust:rust-test-standards`.`` as the dependency requires, and the changeset passes `instructions:skill-auditor` over the three skills.

## `author-rust-code` workflows name bundled references by bare relative path

`src/plugins/rust/skills/author-rust-code/workflows/implementation.md` and `src/plugins/rust/skills/author-rust-code/workflows/remediation.md` list `references/outcome-engineering-patterns.md`, `references/test-patterns.md` and `references/verification-checklist.md` at lines 4 to 6 of `<required_reading>` without the `${CLAUDE_SKILL_DIR}` token that `SKILL.md` and `references/verification-checklist.md` use for the same files. Both workflow files are byte-identical to `origin/main` apart from the directory. `instructions:skill-auditor` rejects each with the blocking `bundled_file_reference` rule.

**Evidence**: `run-2026-10-16_23-46-48-006-fc4c697d67ea.jsonl` and `run-2026-10-16_23-30-06-545-5578d2816a69.jsonl`, finding `bundled_file_reference`, severity blocking.

**Settlement condition.** Each path at lines 4 to 6 of both workflow files begins with `${CLAUDE_SKILL_DIR}/`, and the changeset passes `instructions:skill-auditor` over the skill.

## `author-rust-code` remediation workflow teaches general Rust knowledge

`src/plugins/rust/skills/author-rust-code/workflows/remediation.md` carries snippets that restate what Claude already knows: borrowing instead of cloning (`<type_and_ownership_issues>`, lines 33 to 43), a `CommandRunner` trait declaration (`<boundary_and_process_issues>`, lines 48 to 54) and a trivial `matches!` error test (`<add_regression_evidence>`, lines 66 to 77). None carries a product-specific convention. The file is byte-identical to `origin/main` apart from the directory. `instructions:skill-auditor` records the `known_content` rule at debt severity.

**Evidence**: `run-2026-10-16_23-30-06-545-5578d2816a69.jsonl`, finding `known_content`, severity debt.

**Settlement condition.** The three snippets are removed or replaced by the repository's own convention, or a Verifier skips the finding on grounds recorded here.

## `author-rust-code` verification checklist routes a read to a sibling reference

`src/plugins/rust/skills/author-rust-code/references/verification-checklist.md` line 56 sends the reader to `${CLAUDE_SKILL_DIR}/references/test-patterns.md` `<anti_patterns>`, so one reference routes a read to another. References sit one level below `SKILL.md` and route to nothing. The file is byte-identical to `origin/main` apart from the directory. `instructions:skill-auditor` records the `nested_reference` rule at debt severity.

**Evidence**: `run-2026-10-16_23-30-06-545-5578d2816a69.jsonl`, finding `nested_reference`, severity debt.

**Settlement condition.** The checklist states the criterion in place, and `SKILL.md` or a workflow routes to `references/test-patterns.md`.
