<required_reading>
Read these guides as the change demands before or during the workflow:

- `references/outcome-engineering-patterns.md`
- `references/test-patterns.md`
- `references/verification-checklist.md`

</required_reading>

<process>
Execute these phases in order.

<phase name="understand_requirement">
Before writing code:

1. Read the user request, spec, ADR, or review feedback completely.
2. Identify the behavior that must change.
3. Identify interfaces, data types, and failure modes.
4. Identify the tests that will prove the change.

If the requirement is unclear, resolve that before implementation.
</phase>

<phase name="codebase_discovery">
Read:

- `README.md`, `docs/`, `CLAUDE.md`
- `Cargo.toml`
- `rust-toolchain.toml` when present

Search for:

- similar modules and patterns
- existing trait seams, error types, and tracing conventions
- nearby tests and fixtures that already exercise the area

Document for yourself before moving on:

- crates already available
- prior art worth following
- repository conventions that govern the target area

</phase>

<phase name="write_or_extend_tests_first">
For behavior changes:

1. Locate the right test home:
   - `spx/.../tests/{subject}.{evidence}.l1.rs`
   - `spx/.../tests/{subject}.{evidence}.l2.rs`
   - inline `#[cfg(test)]` if the module already owns that evidence
2. Write or extend the tests.
3. Run the relevant test target to confirm the new case fails for the expected reason.

</phase>

<phase name="implement_the_code">
Write the smallest coherent change that makes the test pass.

Prefer:

- narrow traits or function seams for real boundaries
- typed errors at library and domain boundaries
- module-private helpers for local complexity
- `crate::` paths for stable cross-module references

Avoid:

- generated mocks
- speculative abstractions
- long `super::super::` import chains in shared code
- lint suppressions instead of real fixes

</phase>

<phase name="verify">
Run the full validation sequence:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```

If the repository publishes stricter commands, use them.
</phase>

<phase name="summarize">
When the validation passes, summarize:

- files changed
- behavior added or fixed
- tests added or extended
- any deliberate constraint or trade-off that remains

</phase>
</process>

<success_criteria>

- the changed behavior, boundaries, and failure modes were identified before code edits
- tests were written or extended first when behavior changed
- implementation follows existing repository seams and Rust type discipline
- the repository validation sequence passed
- the final summary names changed behavior, evidence, and remaining trade-offs

</success_criteria>
