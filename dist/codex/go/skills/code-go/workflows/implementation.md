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
4. Identify the test, eval, or pathless audit evidence selected by `/verify`.

If the requirement is unclear, resolve that before implementation.
</phase>

<phase name="codebase_discovery">
Follow `<codebase_discovery>` in `SKILL.md` for what to read, what to search for, and what to confirm. Document the dependencies already available, the prior art worth following, and the repository conventions that govern the target area before moving on.

</phase>

<phase name="establish_selected_evidence">
For behavior changes, handle every type selected by `/verify`:

1. Test: locate the co-located test home, write or extend the test, and run the focused target to confirm the new case fails for the expected reason.
2. Evaluate: read the eval definition, cases, materialized prompt, real producer contract, selected product command, and declared threshold; run it to record the preimplementation score.
3. Audit: apply `<audit_requirement_handoff>` from `SKILL.md` and identify the semantic constraint's real subject; create no deterministic artifact.

</phase>

<phase name="implement_the_code">
Write the smallest coherent change that satisfies the governed behavior and selected evidence.

Prefer:

- small interfaces defined where they are consumed, or function seams, for real boundaries
- wrapped errors with `%w` and sentinel or typed errors at package boundaries
- unexported helpers for local complexity
- `context.Context` as the first parameter of every blocking function

Avoid:

- generated mocks
- speculative abstractions and interfaces with one implementation and no seam purpose
- package-level mutable state
- `//nolint` suppressions instead of real fixes

</phase>

<phase name="verify">
Run the full validation sequence:

```bash
test -z "$(gofmt -l .)"
go vet ./...
staticcheck ./...
go test -race ./...
```

If the repository publishes stricter commands, use them; `golangci-lint run` replaces `staticcheck` where the repository configures it. Also run every eval command selected by `/verify` and require its declared threshold; require the `Audit requirements` row count and `preserved` statuses to match `/verify`'s audit routing rows.
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
- selected tests were written or extended first, selected evals meet their thresholds, and the `Audit requirements` report matches `/verify`'s audit routing rows
- implementation follows existing repository seams and Go type discipline
- the repository validation sequence passed
- the final summary names changed behavior, evidence, and remaining trade-offs

</success_criteria>
