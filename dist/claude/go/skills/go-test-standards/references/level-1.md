<contents>

- `<overview>` — what Level 1 covers
- `<what_belongs_here>` — concern-to-tooling table
- `<file_placement>` — co-located spec test path
- `<pure_function_pattern>` — a governed function called directly
- `<dependency_seam_pattern>` — the `sync` package seam the seam example calls
- `<seam_consumer_pattern>` — the executed test through a controlled runner
- `<recorder_pattern>` — recording collaborator that exposes calls
- `<tempdir_pattern>` — harness-owned temporary product, fixture by path
- `<property_pattern>` — generator domain, harness run policy, test-owned invariant
- `<compile_time_pattern>` — the toolchain as the oracle
- `<anti_patterns>` — Level 1 rejections

</contents>

<overview>
Level 1 covers logic that can run with the Go stdlib, normal developer tooling, a product binary built in-cycle, and temporary local fixtures. The goal is fast, deterministic evidence with direct coupling to the governed code.
</overview>

<what_belongs_here>

| Concern                                 | Typical tooling                                      |
| --------------------------------------- | ---------------------------------------------------- |
| parsing, validation, encoding           | `testing`, `cmp.Diff`                                |
| tempdir-backed filesystem logic         | `t.TempDir()`                                        |
| deterministic command building          | hand-written interface seams                         |
| finite input/output mappings            | table-driven `t.Run` over a source-owned enumeration |
| universal invariants                    | property harness wrapper over `rapid`                |
| HTTP client behavior                    | `httptest.Server`                                    |
| a binary built with `go build` in-cycle | harness-owned build, `os/exec`                       |

</what_belongs_here>

<file_placement>
Level 1 `[test]` evidence lives in co-located spec files at
`spx/.../tests/<subject>.<evidence>.l1_test.go`. Keep the typed assertion file
there even when the governed production code is pure or package-local.

</file_placement>

<pure_function_pattern>
Call the governed function directly and match the sentinel error it exports:

```go
func TestRejectsEmptyURLSets(t *testing.T) {
    _, err := config.Validate(config.Input{URLSets: nil})

    if !errors.Is(err, config.ErrNoURLSets) {
        t.Fatalf("Validate: got %v, want %v", err, config.ErrNoURLSets)
    }
}
```

</pure_function_pattern>

<dependency_seam_pattern>
Use real Go seams with small interfaces defined where they are consumed, or function parameters. This is the `sync` package the seam consumer below calls.

```go
package sync

type Mode int

const (
    ModePush Mode = iota
    ModePull
)

type Config struct {
    Remote string
    Mode   Mode
}

func NewConfig(remote string, mode Mode) *Config { return &Config{Remote: remote, Mode: mode} }

type CommandOutput struct{ Combined []byte }

type CommandRunner interface {
    Run(ctx context.Context, program string, args ...string) (CommandOutput, error)
}

type Result struct{ Success bool }

func BuildArgs(cfg *Config) []string {
    if cfg.Mode == ModePush {
        return []string{"push", cfg.Remote}
    }
    return []string{"pull", cfg.Remote}
}

func Repo(ctx context.Context, cfg *Config, runner CommandRunner) (Result, error) {
    if _, err := runner.Run(ctx, "git", BuildArgs(cfg)...); err != nil {
        return Result{}, fmt.Errorf("sync repo: %w", err)
    }
    return Result{Success: true}, nil
}
```

</dependency_seam_pattern>

<seam_consumer_pattern>
The executed test injects a controlled implementation the harness package owns — `harnesses.SuccessRunner()` returns a `sync.CommandRunner` whose `Run` reports success and records nothing — and asserts on the result:

```go
import "<module>/internal/testinfra/harnesses"

func TestCommandBuilderReportsSuccess(t *testing.T) {
    cfg := sync.NewConfig("origin", sync.ModePush)

    result, err := sync.Repo(context.Background(), cfg, harnesses.SuccessRunner())
    if err != nil {
        t.Fatalf("Repo: %v", err)
    }

    if !result.Success {
        t.Errorf("Success: got false, want true")
    }
}
```

</seam_consumer_pattern>

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

<tempdir_pattern>
The harness owns the temporary product and `t.TempDir()` owns cleanup; the fixture arrives by path; the `Test*` function calls the governed function and asserts:

```go
import (
    "<module>/internal/testinfra/fixtures"
    "<module>/internal/testinfra/harnesses"
)

func TestLoadsYAMLFromTempDir(t *testing.T) {
    product := harnesses.NewTempProduct(t).SeededFrom(fixtures.ValidSiteConfigPath())

    cfg, err := config.Load(product.Path())
    if err != nil {
        t.Fatalf("Load: %v", err)
    }

    if cfg.BaseURL != config.DefaultBaseURL {
        t.Errorf("BaseURL: got %q, want %q", cfg.BaseURL, config.DefaultBaseURL)
    }
}
```

</tempdir_pattern>

<property_pattern>
The harness runs the domain through `rapid.Check` and owns check count, seed, and replay; the invariant and its `t.Fatalf` stay in the closure:

```go
import (
    "pgregory.net/rapid"

    "<module>/internal/testinfra/generators"
    "<module>/internal/testinfra/harnesses"
)

func TestConfigRoundTrips(t *testing.T) {
    harnesses.RunProperty(t, generators.ValidConfigs(), func(t *rapid.T, cfg config.Config) {
        encoded := config.Encode(cfg)

        decoded, err := config.Decode(encoded)
        if err != nil {
            t.Fatalf("Decode: %v", err)
        }
        if diff := cmp.Diff(cfg, decoded); diff != "" {
            t.Fatalf("round trip mismatch (-want +got):\n%s", diff)
        }
    })
}
```

</property_pattern>

<compile_time_pattern>
The toolchain is the oracle: the executed test runs `go vet` on an inert fixture package under `internal/testinfra/fixtures/testdata/` and asserts on the diagnostic:

```go
import "<module>/internal/testinfra/fixtures"

func TestBuilderRejectsUntypedField(t *testing.T) {
    out, err := harnesses.GoVet(t, fixtures.CompileCasePath("builder_rejects_untyped_field"))

    if err == nil {
        t.Fatalf("go vet: got success, want a diagnostic")
    }
    if !strings.Contains(out, "cannot use") {
        t.Errorf("diagnostic: got %q, want it to name the type mismatch", out)
    }
}
```

</compile_time_pattern>

<anti_patterns>

- generated mocks for the primary seam
- a real database or container when a pure seam would give stronger evidence
- golden files of hand-written fixtures instead of asserting structure
- filesystem writes outside `t.TempDir()`
- a package-level function variable reassigned in the test to intercept the function under test

</anti_patterns>
