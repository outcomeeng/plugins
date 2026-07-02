# Issues: Apply Enabler

## 1. Apply flow omits Rust from language detection and per-node skill dispatch

`src/plugins/spec-tree/skills/apply/SKILL.md` declares language detection for TypeScript (`tsconfig.json`) and Python (`pyproject.toml` / `setup.py`) only, and its `<skill_map>` table lists TypeScript and Python branches only.

This conflicts with `spx/43-rust.enabler/rust.md`, which declares the complete Rust workflow (`/architect-rust`, `/test-rust`, `/code-rust`, `/audit-rust`, `/audit-rust-tests`, `/audit-rust-architecture`) and states that Rust audit skills are composed by the generic artifact-type auditors.

Required handling:

- Add Rust detection to `src/plugins/spec-tree/skills/apply/SKILL.md`, including the Rust project marker such as `Cargo.toml`.
- Add a Rust branch to the apply skill map for Steps 3-8: `architect-rust`, `audit-rust-architecture`, `test-rust`, `audit-rust-tests`, `code-rust`, and `audit-rust`.
- Keep the language-independent Steps 0-2, Step 9, and Step 10 shared across all language branches.
- Update generated plugin output with `just build-skills`.
- Gate the skill edit with `develop:skill-auditor`, `just check-skills`, and `just docs-check`, plus the spec-only lane if only Markdown/spec coordination changes remain.

Revisit condition: address during the audit-skill refactor or the next apply-flow language parity pass.
