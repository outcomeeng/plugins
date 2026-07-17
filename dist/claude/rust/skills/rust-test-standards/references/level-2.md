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

When the harness cannot be described precisely, stop and ask.
</harness_rule>

<file_placement>
Integration evidence belongs in `spx/.../tests/{subject}.{evidence}.l2.rs`.
</file_placement>

<cli_binary_pattern>

```rust
use <product>_testing::fixtures::projects::empty_project;
use <product>_testing::harnesses::commands::assert_init_command_writes_project_files;

#[test]
fn init_command_writes_project_files() {
    assert_init_command_writes_project_files(empty_project());
}
```

</cli_binary_pattern>

<async_adapter_pattern>

```rust
use <product>_testing::fixtures::users::valid_user;
use <product>_testing::harnesses::database::assert_user_repository_roundtrip;

#[tokio::test]
async fn repository_persists_and_loads_user() {
    assert_user_repository_roundtrip(valid_user(), UserRepository::new).await;
}
```

</async_adapter_pattern>

<containerized_collaborator_pattern>

```rust
#[tokio::test]
async fn worker_consumes_real_queue_messages() {
    <product>_testing::harnesses::queue::assert_worker_consumes_real_queue_messages(
        job_fixture(),
        run_worker_once,
    ).await;
}
```

</containerized_collaborator_pattern>

<anti_patterns>

- marking a test as L2 when a hand-written Level 1 seam would give stronger evidence
- shelling out from the test to inspect source text
- reaching real network services from a Level 2 test
- missing cleanup for tempdirs, containers, or local service state

</anti_patterns>
