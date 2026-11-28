<contents>

- `<overview>` — what Level 2 covers
- `<what_belongs_here>` — concern-to-tooling table
- `<harness_rule>` — what to identify before writing the test
- `<file_placement>` — co-located spec test path and build constraint
- `<tempdir_pattern>` — harness-owned temporary product, fixture by path
- `<compile_time_pattern>` — the toolchain as the oracle
- `<installed_binary_pattern>` — an acquired binary through a command harness
- `<database_adapter_pattern>` — real database through a container harness
- `<containerized_collaborator_pattern>` — real queue through a container harness
- `<anti_patterns>` — Level 2 rejections

</contents>

<overview>
Level 2 covers behavior that crosses a local boundary: a file write or `t.TempDir()`, Git, any process — the toolchain, a binary built in-cycle, or an installed product binary — a local service, or a container. The code under test still runs on the developer machine; the difference is that the boundary is real.
</overview>

<what_belongs_here>

| Concern                              | Typical tooling                          |
| ------------------------------------ | ---------------------------------------- |
| tempdir-backed filesystem logic      | `t.TempDir()`                            |
| the toolchain as the oracle          | `go vet`, `go build` through a harness   |
| a binary built in-cycle or installed | harness-resolved binary, `os/exec`       |
| local databases or queues            | `testcontainers-go`, repo-native harness |
| protocol adapters                    | real local server, local sockets         |
| local browsers                       | a browser harness against a local server |

</what_belongs_here>

<harness_rule>
Before writing a Level 2 test, identify the harness for every real dependency:

- how the service or binary starts or is resolved
- how the fixture data is seeded
- how the test resets state, through `t.Cleanup`
- which environment variables or ports it needs

When the harness cannot be described precisely, stop and ask.
</harness_rule>

<file_placement>
Level 2 evidence belongs in `spx/.../tests/<subject>.<evidence>.l2_test.go`, whose first line is `//go:build l2`, so `go test ./...` skips it and `go test -tags l2 ./...` runs it.
</file_placement>

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

<installed_binary_pattern>

```go
//go:build l2

import (
    "<module>/internal/testinfra/fixtures"
    "<module>/internal/testinfra/harnesses"
)

func TestInitCommandWritesProjectFiles(t *testing.T) {
    project := harnesses.NewTempProduct(t).SeededFrom(fixtures.EmptyProjectPath())
    binary := harnesses.InstalledProductBinary(t)

    out, err := exec.Command(binary, initcmd.Command).Output()
    if err != nil {
        t.Fatalf("%s %s: %v", binary, initcmd.Command, err)
    }

    if _, err := os.Stat(filepath.Join(project.Path(), initcmd.ManifestFile)); err != nil {
        t.Errorf("manifest: %v", err)
    }
    _ = out
}
```

The command name and manifest filename come from the owning production package. The harness resolves the installed binary and fails through `t.Fatal` when it is absent.

</installed_binary_pattern>

<database_adapter_pattern>

```go
//go:build l2

import "<module>/internal/testinfra/harnesses"

func TestRepositoryPersistsAndLoadsUser(t *testing.T) {
    db := harnesses.StartPostgres(t)
    repo := users.NewRepository(db.Pool())
    user := users.New("u-1", "widget@example.com")

    if err := repo.Save(context.Background(), user); err != nil {
        t.Fatalf("Save: %v", err)
    }
    loaded, err := repo.Load(context.Background(), user.ID)
    if err != nil {
        t.Fatalf("Load: %v", err)
    }

    if diff := cmp.Diff(user, loaded); diff != "" {
        t.Errorf("Load mismatch (-want +got):\n%s", diff)
    }
}
```

</database_adapter_pattern>

<containerized_collaborator_pattern>

```go
//go:build l2

import "<module>/internal/testinfra/harnesses"

func TestWorkerConsumesRealQueueMessages(t *testing.T) {
    queue := harnesses.StartQueue(t)
    drained := queue.Depth(t)
    job := jobs.Pending("job-1")
    queue.Publish(t, job)

    if err := worker.RunOnce(context.Background(), queue.Connection()); err != nil {
        t.Fatalf("RunOnce: %v", err)
    }

    if got := queue.Depth(t); got != drained {
        t.Errorf("depth: got %d, want %d", got, drained)
    }
}
```

</containerized_collaborator_pattern>

<anti_patterns>

- marking a test as L2 when a hand-written Level 1 seam would give stronger evidence
- marking a test Level 1 that writes into `t.TempDir()`, runs Git, or starts any process, a binary built in-cycle included
- shelling out from the test to inspect source text
- reaching real network services from a Level 2 test
- missing `t.Cleanup` for containers or local service state

</anti_patterns>
