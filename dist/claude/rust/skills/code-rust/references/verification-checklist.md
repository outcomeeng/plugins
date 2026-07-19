<overview>
Before declaring implementation complete, confirm that mechanical checks and code-shape review both pass.
</overview>

<required_checks>

- [ ] `cargo fmt --check` passes
- [ ] `cargo clippy --all-targets --all-features -- -D warnings` passes
- [ ] `cargo test --all-targets` passes
- [ ] no temporary debug code remains
- [ ] no TODO or FIXME comments were added as escape hatches
- [ ] new behavior is covered by tests or an explicit review constraint

</required_checks>

<optional_checks>

- [ ] `cargo llvm-cov` run when the repository uses coverage as evidence
- [ ] benchmark or profiling evidence collected when the change is performance-sensitive

</optional_checks>

<tool_commands>

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```

If the repository publishes stricter wrapper commands in `CLAUDE.md` or `README.md`, use those instead of the fallback commands above.
</tool_commands>

<review_focus>
<type_and_ownership_quality>

- invalid states represented with types where practical
- clones introduced only when ownership requires them
- public boundaries expose deliberate types, not placeholders

</type_and_ownership_quality>

<code_quality>

- errors preserve enough context to debug or act
- process, network, time, and storage boundaries use explicit seams
- no dead code or commented-out code blocks remain

</code_quality>

<testing>

- tests prove behavior rather than implementation details
- edge cases and regressions are named clearly
- property claims use property-based tests
- compile-time claims use compile-fail evidence where appropriate

</testing>
</review_focus>
