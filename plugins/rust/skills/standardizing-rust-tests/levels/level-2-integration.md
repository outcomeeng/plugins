<overview>
Level 2 covers behavior that needs a real binary, async runtime, local service, or containerized collaborator. The code under test still runs on the developer machine; the difference is that the boundary is real.
</overview>

<what_belongs_here>

| Concern                          | Typical tooling                        |
| -------------------------------- | -------------------------------------- |
| CLI binary behavior              | `assert_cmd`, `predicates`             |
| async adapters with real runtime | `#[tokio::test]`                       |
| local databases or queues        | repo-native harness, `testcontainers`  |
| protocol adapters                | real HTTP server/client, local sockets |

</what_belongs_here>

<harness_rule>
Before writing a Level 2 test, identify the harness for every real dependency:

- how the service or binary starts
- how the fixture data is seeded
- how the test resets state
- which environment variables or ports it needs

If you cannot describe the harness precisely, stop and ask.
</harness_rule>

<file_placement>
Integration evidence belongs in `spx/.../tests/{slug}.integration.rs`.
</file_placement>

<cli_binary_pattern>

```rust
#[test]
fn init_command_writes_project_files() {
    let temp = tempfile::tempdir().unwrap();

    assert_cmd::Command::cargo_bin("herder")
        .unwrap()
        .current_dir(temp.path())
        .args(["init", "demo"])
        .assert()
        .success();

    assert!(temp.path().join("demo/Cargo.toml").exists());
}
```

</cli_binary_pattern>

<async_adapter_pattern>

```rust
#[tokio::test]
async fn repository_persists_and_loads_user() {
    let db = test_database().await;
    let repo = UserRepository::new(db.pool());

    repo.save(&user_fixture()).await.unwrap();
    let loaded = repo.find(UserId::new(1)).await.unwrap();

    assert_eq!(loaded.email(), "user@example.com");
}
```

</async_adapter_pattern>

<containerized_collaborator_pattern>

```rust
#[tokio::test]
async fn worker_consumes_real_queue_messages() {
    let harness = queue_harness().await;
    harness.push(job_fixture()).await;

    let result = run_worker_once(&harness.config).await.unwrap();

    assert_eq!(result.processed, 1);
}
```

</containerized_collaborator_pattern>

<anti_patterns>

- marking a test as integration when a hand-written Level 1 seam would give stronger evidence
- shelling out from the test to inspect source text
- reaching real network services from a Level 2 test
- missing cleanup for tempdirs, containers, or local service state

</anti_patterns>
