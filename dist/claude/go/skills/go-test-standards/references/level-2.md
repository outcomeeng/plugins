<contents>

- `<overview>` — what Level 2 covers
- `<what_belongs_here>` — concern-to-tooling table
- `<harness_rule>` — what to identify before writing the test
- `<file_placement>` — co-located spec test path and build constraint
- `<installed_binary_pattern>` — an acquired binary through a command harness
- `<database_adapter_pattern>` — real database through a container harness
- `<containerized_collaborator_pattern>` — real queue through a container harness
- `<anti_patterns>` — Level 2 rejections

</contents>

<overview>
Level 2 covers behavior that needs a local service, container, or an installed product binary. The code under test still runs on the developer machine; the difference is that the boundary is real and obtained outside the ordinary `go test` cycle.
</overview>

<what_belongs_here>

| Concern                           | Typical tooling                          |
| --------------------------------- | ---------------------------------------- |
| an installed or downloaded binary | harness-resolved binary, `os/exec`       |
| local databases or queues         | `testcontainers-go`, repo-native harness |
| protocol adapters                 | real local server, local sockets         |
| local browsers                    | a browser harness against a local server |

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
- marking a binary the harness builds with `go build` in-cycle as L2 — that is Level 1
- shelling out from the test to inspect source text
- reaching real network services from a Level 2 test
- missing `t.Cleanup` for containers or local service state

</anti_patterns>
