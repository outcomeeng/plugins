<required_reading>
Read these guides before or during remediation as needed:

- `references/outcome-engineering-patterns.md`
- `references/test-patterns.md`
- `references/verification-checklist.md`

</required_reading>

<process>
Use this workflow when the input is rejection feedback from review, tests, or validation.

<phase name="parse_the_rejection">
1. Read the feedback completely.
2. List every affected file and location.
3. Group related symptoms by root cause.

</phase>

<phase name="understand_the_root_cause">
Before fixing anything:

1. Read the affected code in context.
2. Read the governing spec, ADR, or PDR when the issue is about compliance.
3. Decide whether the real problem is in logic, seam design, ownership flow, error handling, or tests.

</phase>

<phase name="fix_the_root_cause">
Apply fixes systematically.

<type_and_ownership_issues>
Fix the shape of the data flow rather than cloning or boxing blindly.

```rust
// Wrong: clone-driven patch
let user = user.clone();

// Better: borrow or restructure ownership
fn render_user(user: &User) -> String {
    user.name.clone()
}
```

</type_and_ownership_issues>

<boundary_and_process_issues>
Fix the seam instead of asserting implementation details.

```rust
trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError>;
}
```

</boundary_and_process_issues>

<validation_and_lint_issues>
Fix the underlying issue. Do not add `#[allow(...)]` to hide it.
</validation_and_lint_issues>
</phase>

<phase name="add_regression_evidence">
If the rejection exposed a bug, add or extend the smallest test that proves the bug is fixed.

```rust
#[test]
fn rejects_empty_email() {
    let input = UserInput {
        name: "Ada".to_owned(),
        email: String::new(),
    };

    let error = parse_user(input).unwrap_err();

    assert!(matches!(error, ParseUserError::EmptyEmail));
}
```

</phase>

<phase name="re_verify">
Run the full validation sequence again:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```

</phase>

<phase name="prepare_for_re_review">
Summarize:

- issues addressed
- root cause fixed
- tests added or changed
- verification results

</phase>
</process>

<success_criteria>

- every rejection point was mapped to a root cause before edits
- fixes addressed the underlying design or logic issue rather than the symptom
- regression evidence was added when behavior was wrong
- the repository validation sequence passed after remediation
- the re-review summary names the resolved issues and evidence

</success_criteria>
