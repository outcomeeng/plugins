<contents>

- `<overview>` — what Level 1 covers
- `<what_belongs_here>` — concern-to-tooling table
- `<file_placement>` — co-located spec test path
- `<dependency_seam_pattern>` — narrow interface and function seams
- `<recorder_pattern>` — recording collaborator that exposes calls
- `<anti_patterns>` — Level 1 rejections

The tempdir and property patterns are worked inline in `SKILL.md` and are not repeated here.

</contents>

<overview>
Level 1 covers logic that can run with the Go stdlib, normal developer tooling, a product binary built in-cycle, and temporary local fixtures. The goal is fast, deterministic evidence with direct coupling to the governed code.
</overview>

<what_belongs_here>

| Concern                            | Typical tooling                          |
| ---------------------------------- | ---------------------------------------- |
| parsing, validation, encoding      | `testing`, `cmp.Diff`                    |
| tempdir-backed filesystem logic    | `t.TempDir()`                            |
| deterministic command building     | hand-written interface seams             |
| finite input/output mappings       | table-driven `t.Run` over a source-owned enumeration |
| universal invariants               | property harness wrapper over `rapid`    |
| HTTP client behavior               | `httptest.Server`                        |
| a binary built with `go build` in-cycle | harness-owned build, `os/exec`      |

</what_belongs_here>

<file_placement>
Level 1 `[test]` evidence lives in co-located spec files at
`spx/.../tests/<subject>.<evidence>.l1_test.go`. Keep the typed assertion file
there even when the governed production code is pure or package-local.

</file_placement>

<dependency_seam_pattern>
Use real Go seams with small interfaces defined where they are consumed, or function parameters.

```go
type CommandRunner interface {
    Run(ctx context.Context, program string, args ...string) (CommandOutput, error)
}

func BuildSyncArgs(cfg *SyncConfig) []string {
    return []string{"--delete", cfg.Source, cfg.Destination}
}

func SyncRepo(ctx context.Context, cfg *SyncConfig, runner CommandRunner) (SyncResult, error) {
    if _, err := runner.Run(ctx, "rsync", BuildSyncArgs(cfg)...); err != nil {
        return SyncResult{}, fmt.Errorf("sync repo: %w", err)
    }
    return SyncResult{Success: true}, nil
}
```

</dependency_seam_pattern>

<recorder_pattern>

```go
// internal/testinfra/harnesses/commands.go
package harnesses

type RecordedCall struct {
    Program string
    Args    []string
}

type RecordingRunner struct {
    Calls  []RecordedCall
    Result sync.CommandOutput
    Err    error
}

func (r *RecordingRunner) Run(_ context.Context, program string, args ...string) (sync.CommandOutput, error) {
    r.Calls = append(r.Calls, RecordedCall{Program: program, Args: append([]string(nil), args...)})
    return r.Result, r.Err
}
```

The recorder exposes `Calls`; the executed test asserts on them. It never compares them to an expectation itself.

</recorder_pattern>

<anti_patterns>

- generated mocks for the primary seam
- a real database or container when a pure seam would give stronger evidence
- golden files of hand-written fixtures instead of asserting structure
- filesystem writes outside `t.TempDir()`
- a package-level function variable reassigned in the test to intercept the function under test

</anti_patterns>
