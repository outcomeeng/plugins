<contents>

- `<overview>` — what Level 3 covers
- `<when_to_use>` — claims that require a real external collaborator
- `<go_patterns>` — Go-native tooling at the owned boundary
- `<requirements>` — what every Level 3 test declares
- `<examples>` — remote API, sandboxed CLI, and browser workflow
- `<anti_patterns>` — Level 3 rejections
- `<repo_local_overlay>` — product truth that disables Level 3

</contents>

<overview>
Level 3 tests prove Go behavior against real external collaborators: remote APIs, deployed services, browser UI, shared environments, credentialed sandboxes, or managed infrastructure outside the local test process. Their files carry `//go:build l3` as the first line.
</overview>

<when_to_use>
Use Level 3 only when the assertion includes the real collaborator as part of the product claim.

Typical Level 3 claims:

- a deployed Go service satisfies a public HTTP contract
- a Go CLI works against a real remote API sandbox
- a browser workflow served by Go reaches the expected state
- a SaaS callback, webhook, or credentialed round-trip through the real provider
- a distributed workflow depends on infrastructure the local suite cannot stand up

</when_to_use>

<go_patterns>
Use Go-native harnesses at the boundary the product owns:

- `net/http` or the repository's client for remote HTTP contracts
- a harness-resolved binary through `os/exec` for a CLI that talks to a real sandbox or deployed service
- browser automation when the Go product serves or governs browser UI
- provider SDKs only when the SDK itself is part of the product boundary
- structured fixtures for requests, responses, cleanup ids, and expected contract data

</go_patterns>

<requirements>
Every Level 3 test must declare:

- what external collaborator it uses
- what credentials or sandbox state it requires, failing through `t.Fatal` when a mandatory one is absent
- how test data is isolated from production data
- how cleanup happens after failure, through `t.Cleanup`
- expected runtime and retry policy
- whether it runs in the default validation lane or a separate credentialed lane

</requirements>

<examples>
The harness owns credential resolution, sandbox isolation, and cleanup through `t.Cleanup`. The `Test*` function owns the contract claim, so a reader sees the whole pass/fail predicate without opening the harness.

Remote API contract:

```go
//go:build l3

import "<module>/internal/testinfra/harnesses"

func TestPackageCanBePublishedAndFetched(t *testing.T) {
    registry := harnesses.ConnectSandboxRegistry(t)
    pkg := packages.New("widget", "1.0.0")

    if err := registry.Publish(context.Background(), pkg); err != nil {
        t.Fatalf("Publish: %v", err)
    }
    fetched, err := registry.Fetch(context.Background(), pkg.Name, pkg.Version)
    if err != nil {
        t.Fatalf("Fetch: %v", err)
    }

    if fetched.Checksum != pkg.Checksum {
        t.Errorf("checksum: got %q, want %q", fetched.Checksum, pkg.Checksum)
    }
}
```

CLI against a real sandbox:

```go
//go:build l3

import (
    "<module>/internal/testinfra/fixtures"
    "<module>/internal/testinfra/harnesses"
)

func TestSyncCommandUploadsToRemoteSandbox(t *testing.T) {
    sandbox := harnesses.ClaimRemoteSandbox(t)
    tree := fixtures.SyncableTreePath()
    binary := harnesses.ProductBinary(t)

    if _, err := exec.Command(binary, synccmd.Command, tree, sandbox.URL()).Output(); err != nil {
        t.Fatalf("%s: %v", synccmd.Command, err)
    }

    if diff := cmp.Diff(fixtures.SyncableTreeListing(), sandbox.Listing(t)); diff != "" {
        t.Errorf("listing mismatch (-want +got):\n%s", diff)
    }
}
```

Browser workflow:

```go
//go:build l3

import "<module>/internal/testinfra/harnesses"

func TestLoginFlowReachesDashboard(t *testing.T) {
    session := harnesses.StartBrowserSession(t)
    account := session.EnrolledAccount()

    if err := session.LogInAs(context.Background(), account); err != nil {
        t.Fatalf("LogInAs: %v", err)
    }

    if got := session.CurrentRoute(t); got != routes.Dashboard {
        t.Errorf("route: got %q, want %q", got, routes.Dashboard)
    }
}
```

</examples>

<anti_patterns>

- credential-gated tests that `t.Skip` when credentials are missing — a mandatory credential fails through `t.Fatal`
- remote calls in the default lane without isolation and cleanup
- Level 3 tests used for logic that can be proved at Level 1
- browser automation for non-browser product claims
- shared sandbox fixtures that collide across concurrent runs

</anti_patterns>

<repo_local_overlay>
Product specs or decisions may disable Level 3 for a repository. A repo-local `spx/local/go-tests.md` overlay may point to that declaration and route Go testing skills accordingly. When Level 3 is disabled by product truth, route local binary and fixture flows to Level 2 and surface true remote-collaborator assertions as product decisions.
</repo_local_overlay>
