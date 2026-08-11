<contents>

- `<overview>` — what Level 3 covers
- `<when_to_use>` — claims that require a real external collaborator
- `<rust_patterns>` — Rust-native tooling at the owned boundary
- `<requirements>` — what every Level 3 test declares
- `<examples>` — remote API, sandboxed CLI, and browser workflow
- `<anti_patterns>` — Level 3 rejections
- `<repo_local_overlay>` — product truth that disables Level 3

</contents>

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
The harness owns credential resolution, sandbox isolation, and cleanup on `Drop`. The `#[test]` owns the contract claim, so a reader sees the whole pass/fail predicate without opening the harness.

Remote API contract:

```rust
use <product>_testing::generators::packages::any_publishable_package;
use <product>_testing::harnesses::registry::SandboxRegistry;

#[tokio::test]
async fn package_can_be_published_and_fetched() {
    let registry = SandboxRegistry::connect().await;
    let package = any_publishable_package();

    registry.publish(&package).await.unwrap();
    let fetched = registry.fetch(package.name(), package.version()).await.unwrap();

    assert_eq!(fetched.checksum(), package.checksum());
}
```

CLI against a real sandbox:

```rust
use <product>_testing::generators::payloads::any_syncable_tree;
use <product>_testing::harnesses::commands::product_binary;
use <product>_testing::harnesses::sandbox::RemoteSandbox;

#[test]
fn sync_command_uploads_to_remote_sandbox() {
    let sandbox = RemoteSandbox::claim();
    let tree = any_syncable_tree();

    let outcome = product_binary()
        .arg(product::sync::COMMAND)
        .arg(tree.path())
        .arg(sandbox.url())
        .output()
        .unwrap();

    assert!(outcome.status.success());
    assert_eq!(sandbox.listing().unwrap(), tree.expected_listing());
}
```

Browser workflow:

```rust
use <product>_testing::generators::accounts::any_enrolled_account;
use <product>_testing::harnesses::browser::BrowserSession;

#[tokio::test]
async fn login_flow_reaches_dashboard() {
    let session = BrowserSession::start().await;

    session.log_in_as(&any_enrolled_account()).await.unwrap();

    assert_eq!(session.current_route().await.unwrap(), product::routes::DASHBOARD);
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

<repo_local_overlay>
Product specs or decisions may disable Level 3 for a repository. A repo-local `spx/local/rust-tests.md` overlay may point to that declaration and route Rust testing skills accordingly. When Level 3 is disabled by product truth, route local binary and fixture flows to Level 2 and surface true remote-collaborator assertions as product decisions.
</repo_local_overlay>
