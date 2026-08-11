<contents>

- `<overview>` — what Level 2 covers
- `<what_belongs_here>` — concern-to-tooling table
- `<harness_rule>` — what to identify before writing the test
- `<file_placement>` — co-located spec test path
- `<cli_binary_pattern>` — real binary through a command harness
- `<async_adapter_pattern>` — real database through a container harness
- `<containerized_collaborator_pattern>` — real queue through a container harness
- `<anti_patterns>` — Level 2 rejections

</contents>

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
use <product>_testing::fixtures::projects::empty_project_path;
use <product>_testing::harnesses::commands::product_binary;
use <product>_testing::harnesses::filesystem::TempProduct;

#[test]
fn init_command_writes_project_files() {
    let project = TempProduct::seeded_from(empty_project_path());

    product_binary().arg("init").current_dir(project.path()).assert().success();

    assert!(project.path().join(product::init::MANIFEST_FILE).exists());
}
```

</cli_binary_pattern>

<async_adapter_pattern>

```rust
use <product>_testing::generators::users::any_valid_user;
use <product>_testing::harnesses::database::PostgresHarness;

#[tokio::test]
async fn repository_persists_and_loads_user() {
    let database = PostgresHarness::start().await;
    let repository = UserRepository::new(database.pool());
    let user = any_valid_user();

    repository.save(&user).await.unwrap();
    let loaded = repository.load(user.id()).await.unwrap();

    assert_eq!(loaded, user);
}
```

</async_adapter_pattern>

<containerized_collaborator_pattern>

```rust
use <product>_testing::generators::jobs::any_pending_job;
use <product>_testing::harnesses::queue::QueueHarness;

#[tokio::test]
async fn worker_consumes_real_queue_messages() {
    let queue = QueueHarness::start().await;
    let job = any_pending_job();
    queue.publish(&job).await.unwrap();

    run_worker_once(queue.connection()).await.unwrap();

    assert_eq!(queue.depth().await.unwrap(), 0);
}
```

</containerized_collaborator_pattern>

<anti_patterns>

- marking a test as L2 when a hand-written Level 1 seam would give stronger evidence
- shelling out from the test to inspect source text
- reaching real network services from a Level 2 test
- missing cleanup for tempdirs, containers, or local service state

</anti_patterns>
