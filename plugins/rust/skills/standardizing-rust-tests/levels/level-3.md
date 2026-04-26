<overview>
Level 3 tests prove Rust behavior against real external collaborators: remote APIs, deployed services, browser UI, shared environments, credentialed sandboxes, or managed infrastructure outside the local test process.
</overview>

<when_to_use>
Use Level 3 only when the assertion includes the real collaborator as part of the product claim.

Typical Level 3 claims:

- a deployed Rust service satisfies a public HTTP contract
- a Rust CLI works against a real remote API sandbox
- a browser workflow served by Rust reaches the expected state
- a SaaS callback, webhook, or credentialed round-trip through the real provider
- a distributed workflow depends on infrastructure the local suite cannot stand up

</when_to_use>

<rust_patterns>
Use Rust-native harnesses at the boundary the product owns:

- `reqwest` or the repository's client for remote HTTP contracts
- `assert_cmd` for a CLI that talks to a real sandbox or deployed service
- browser automation when the Rust product serves or governs browser UI
- provider SDKs only when the SDK itself is part of the product boundary
- structured fixtures for requests, responses, cleanup ids, and expected contract data

</rust_patterns>

<requirements>
Every Level 3 test must declare:

- what external collaborator it uses
- what credentials or sandbox state it requires
- how test data is isolated from production data
- how cleanup happens after failure
- expected runtime and retry policy
- whether it runs in the default validation lane or a separate credentialed lane

</requirements>

<examples>
Remote API contract:

```rust
#[tokio::test]
#[ignore = "requires REGISTRY_SANDBOX_TOKEN"]
async fn package_can_be_published_and_fetched() {
    let client = registry_client_from_env().unwrap();
    let package_name = unique_package_name("l3");

    client.publish_fixture(&package_name).await.unwrap();
    let fetched = client.fetch_package(&package_name).await.unwrap();

    assert_eq!(fetched.name, package_name);
}
```

CLI against a real sandbox:

```rust
#[test]
#[ignore = "requires sandbox credentials"]
fn sync_command_uploads_to_remote_sandbox() {
    let temp = tempfile::tempdir().unwrap();
    write_fixture_project(temp.path());

    assert_cmd::Command::cargo_bin("syncer")
        .unwrap()
        .current_dir(temp.path())
        .args(["sync", "--target", "sandbox"])
        .assert()
        .success()
        .stdout(predicates::str::contains("uploaded"));
}
```

</examples>

<anti_patterns>

- credential-gated tests that silently pass when credentials are missing
- remote calls in the default lane without isolation and cleanup
- Level 3 tests used for logic that can be proved at Level 1
- browser automation for non-browser product claims
- shared sandbox fixtures that collide across concurrent runs

</anti_patterns>

<repo_local_overlays>
Project instructions or `spx/local/rust-tests.md` may disable Level 3 for a repository. When they do, route local binary and fixture flows to Level 2 and surface true remote-collaborator assertions as product decisions.
</repo_local_overlays>
