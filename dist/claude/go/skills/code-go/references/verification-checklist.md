<overview>
Before declaring implementation complete, confirm that mechanical checks and code-shape review both pass.
</overview>

<required_checks>

- [ ] `gofmt -l .` prints nothing
- [ ] `go vet ./...` passes
- [ ] the repository's linter (`staticcheck ./...` or `golangci-lint run`) passes
- [ ] `go test -race ./...` passes
- [ ] no temporary debug code remains
- [ ] no TODO or FIXME comments were added as escape hatches
- [ ] new behavior carries the test, eval, or pathless audit evidence selected by `/verify`
- [ ] every selected eval meets its declared completion threshold
- [ ] the completion report has one `Audit requirements` row with status `preserved` per audit row from `/verify`, or reports `none selected` when no audit row exists

</required_checks>

<optional_checks>

- [ ] `go test -cover -coverprofile` run when the repository uses coverage as evidence
- [ ] benchmark or profiling evidence collected when the change is performance-sensitive

</optional_checks>

<tool_commands>

```bash
test -z "$(gofmt -l .)"
go vet ./...
staticcheck ./...
go test -race ./...
```

If the repository publishes stricter wrapper commands in `CLAUDE.md` or `README.md`, use those instead of the fallback commands above.
</tool_commands>

<review_focus>
<type_and_concurrency_quality>

- invalid states represented with types and validating constructors where practical
- every goroutine has an owner and an exit condition; every blocking call takes a context
- exported boundaries expose deliberate types, not placeholders

</type_and_concurrency_quality>

<code_quality>

- errors are wrapped with `%w` and preserve enough context to debug or act
- process, network, time, and storage boundaries use explicit seams
- no dead code or commented-out code blocks remain

</code_quality>

<testing>

- tests prove behavior rather than implementation details
- each `Test*` body carries its own comparison and failure call, never a bare `t.Helper()` call that both acts and judges — the shape `${CLAUDE_SKILL_DIR}/references/test-patterns.md` `<anti_patterns>` names first
- edge cases and regressions are named clearly
- property claims use property-based tests
- compile-time claims use toolchain-oracle evidence where appropriate

</testing>
</review_focus>
