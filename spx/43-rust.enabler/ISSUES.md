# Issues: Rust Enabler

## 1. Compliance assertions embed the full workspace-member crate spec inline

`spx/43-rust.enabler/rust.md` Compliance rules restate the full per-language test-infrastructure layout (Cargo package name, import-path module names, `[dev-dependencies]` registration) on every assertion. The Python and TypeScript siblings cite `spx/15-test-infrastructure.pdr.md` and quote only the rule-specific surface.

Replacing the inline restatements with PDR citations would keep the assertions terse, eliminate drift between the rust spec and the PDR, and keep the rule-specific surface visible to the rust auditor without losing the per-language context. The current verbose form is not wrong — spec assertions are machine-read and length is not in itself a defect — but it diverges from the sibling-language style.

Surfaced by `claude-review` on PR 14 round 3 (2026-05-13).
