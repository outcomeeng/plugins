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
3. Decide whether the real problem is in logic, seam design, concurrency ownership, error handling, or the test, eval, or audit evidence selected by `/verify`.

</phase>

<phase name="fix_the_root_cause">
Apply fixes systematically.

<type_and_ownership_issues>
Fix the shape of the data flow rather than copying or sharing state blindly.

```go
// Wrong: package-level state patched in
var current *User

// Better: pass the value the caller owns
func RenderUser(user *User) string {
    return user.Name
}
```

</type_and_ownership_issues>

<boundary_and_process_issues>
Fix the seam instead of asserting implementation details.

```go
type CommandRunner interface {
    Run(ctx context.Context, program string, args ...string) (CommandOutput, error)
}
```

</boundary_and_process_issues>

<validation_and_lint_issues>
Fix the underlying issue. Do not add `//nolint` to hide it.
</validation_and_lint_issues>
</phase>

<phase name="add_regression_evidence">
If the rejection exposed a behavior not covered by established evidence, return to `/verify` and its selected specialist. Add or extend a regression test only when test is selected; extend eval evidence only through the eval specialist; preserve a pathless audit requirement for its isolated verifier.

```go
func TestRejectsEmptyEmail(t *testing.T) {
    _, err := users.Parse(users.Input{Name: "Ada", Email: ""})

    if !errors.Is(err, users.ErrEmptyEmail) {
        t.Fatalf("Parse: got %v, want %v", err, users.ErrEmptyEmail)
    }
}
```

</phase>

<phase name="re_verify">
Run the full validation sequence again:

```bash
test -z "$(gofmt -l .)"
go vet ./...
staticcheck ./...
go test -race ./...
```

Run every eval command selected by `/verify` and require its declared threshold. Preserve every pathless audit requirement for re-review.

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
- missing regression evidence was established through `/verify` and the selected specialist
- the repository validation sequence passed after remediation
- the re-review summary names the resolved issues and evidence

</success_criteria>
