# Status Derivation

## Purpose

This decision governs how node status is determined across the spec tree. Status must be a derived property — computed from observable evidence — never a stored label.

## Context

**Business impact:** Accurate status enables teams to trust the spec tree as a progress dashboard. If status can be manually set, it drifts from reality, and the tree becomes another stale tracking artifact.

**Technical constraints:** The spec tree can contain hundreds of nodes. Status computation must be fast enough to run on every CLI invocation without caching.

## Decision

Node status is derived exclusively from the presence and pass/fail state of co-located tests. No status field exists in any file.

## Rationale

Stored status requires someone (human or agent) to keep it synchronized with reality. This synchronization always drifts. By deriving status from tests, accuracy is guaranteed — the status is literally "do the tests pass?" Alternatives considered: `status.yaml` per node (rejected: manual synchronization), CI badge integration (rejected: adds external dependency).

## Trade-offs accepted

| Trade-off                           | Mitigation / reasoning                                                 |
| ----------------------------------- | ---------------------------------------------------------------------- |
| Must run tests to know status       | Test execution is fast for unit tests; integration tests can be cached |
| No "in progress" or "blocked" state | These are workflow states, not product states — track in product tools |

## Invariants

- Status is a pure function of test results — same test results always produce the same status
- Adding tests can only improve status precision, never degrade it

## Compliance

### Recognized by

Status values appear only in CLI output and computed data structures, never in committed files.

### MUST

- Compute status fresh on every invocation — ensures accuracy
- Use only test pass/fail as input — no other signals

### NEVER

- Store status in any committed file — prevents drift
- Allow manual status override — defeats the derivation principle
