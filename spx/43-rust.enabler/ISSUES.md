# Issues: Rust Enabler

## 1. Compliance assertions embed the full workspace-member crate spec inline

`spx/43-rust.enabler/rust.md` Compliance rules restate the full per-language test-infrastructure layout (Cargo package name, import-path module names, `[dev-dependencies]` registration) on every assertion. The Python and TypeScript siblings cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` and quote only the rule-specific surface.

Replacing the inline restatements with PDR citations would keep the assertions terse, eliminate drift between the rust spec and the PDR, and keep the rule-specific surface visible to the rust auditor without losing the per-language context. The current verbose form is not wrong — spec assertions are machine-read and length is not in itself a defect — but it diverges from the sibling-language style.

Surfaced by `claude-review` on PR 14 round 3 (2026-05-13).

## 2. rust-test-standards renders no language-specific shared-litmus section

`src/plugins/python/skills/python-test-standards/SKILL.md` and `src/plugins/typescript/skills/typescript-test-standards/SKILL.md` each carry a section that applies every question in `/test-evidence-standards` `<common_litmus_questions>` and every mutation in its `<mutation_litmus>`, then renders the language-specific form of those items while deferring to the shared set as complete. `src/plugins/rust/skills/rust-test-standards/SKILL.md` carries no equivalent section and no reference to `/test-evidence-standards`.

**Status against the standard.** This is parity, not a contradiction. rust-test-standards holds no inline litmus, predicate-seam, semantic-binding, oracle-independence, case-provenance, or mutation content, so the shared standard duplicates nothing there and invalidates none of its guidance. The Rust audit path still receives the shared litmus through the base `/audit-tests`, which invokes `/test-evidence-standards` for every language. The gap is only that Rust authors reading rust-test-standards do not get the Rust-specific rendering their Python and TypeScript counterparts get.

**Evidence.** Surfaced while wiring the shared `test-evidence-standards` skill into the Python and TypeScript authoring standards. The seam changeset touches the Rust auditor (`audit-rust-tests`) and Rust test skill (`test-rust`) but not `rust-test-standards`, so the file lies outside the changeset.

**Resolution shape**: add a shared-litmus section to `rust-test-standards` mirroring the Python and TypeScript siblings — apply the complete `/test-evidence-standards` litmus and mutation set, then render the Rust-specific form (borrow/lifetime bindings, `#[cfg(test)]` module ownership, trait-object doubles) without replacing or bounding the shared set. Run `instructions:skill-auditor` over `rust-test-standards` afterward.
