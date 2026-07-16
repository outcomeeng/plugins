# Installation

PROVIDES checkout-scoped plugin marketplace configuration reconciliation and install verification
SO THAT Codex and Claude Code users working from this repository
CAN establish a consistent committed marketplace configuration and confirm install completeness without mutating user-scope registrations, plugin caches, or agent directories.

Installation reconciles only the invocation checkout's committed runtime marketplace configuration and verifies that every catalog plugin installs and enables through an isolated real-runtime harness that provisions real runtimes in disposable homes. It never preserves, retargets, or mutates a developer's user-scope plugin caches, marketplace registrations, or agent directories.

## Assertions

### Compliance

- NEVER: installation mutates a path outside the invocation checkout — a developer's user-scope marketplace registrations, plugin caches, and agent directories are unchanged after every run ([audit])
- ALWAYS: installation reconciles only the checkout's committed runtime marketplace configuration for each runtime — never a user-scope registration, plugin cache, or agent directory ([audit])
- ALWAYS: install completeness — every catalog plugin installed and enabled in both runtimes — is verified by an isolated harness that provisions real `claude` and `codex` binaries in disposable runtime homes and mutates no user-scope state ([audit])
