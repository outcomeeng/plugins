# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

The decision bounds the marketplace toolchain to the invocation checkout: it reconciles only
that checkout's committed runtime configuration and never mutates a developer's user-scope
marketplace registrations, plugin caches, or agent directories. Install completeness is
established by an isolated harness that provisions real runtimes in disposable homes.

`installation.md` carries its full assertion set, and every assertion keeps its linked
evidence. The node is passing.

Pending alignment — remove only what the decision directly supersedes:

- Codex plugin-cache preservation: compatibility symlinks, version-directory topology, orphan
  and unmanaged-plugin pruning, reconciliation-timestamp freshness.
- User-scope marketplace-source reconciliation, registration repair, and plugin-selection
  restore.
- The `validate_install` assertions that verify user-scope cache topology and cache listing.

Preserve the assertions the decision does not govern. The Codex installed-set CLI payload
contract is the clearest: the isolated harness still reads a runtime's installed plugins
through `codex plugin list --json`, and a changed CLI contract must raise rather than yield a
silent empty set. The decision changes where install state lives, not how a payload parses.

Declare the decision's new truth as assertion text, then route each assertion through `/test`
for its verification type and assertion type. Authoring writes assertion text and marks that
evidence is required; `/test` alone selects which tag the evidence resolves to.

Pending implementation:

- Build the isolated real-runtime installation harness — real `claude` and `codex` binaries in
  disposable runtime homes — that verifies every catalog plugin installs and enables while
  mutating no user-scope state.
- Remove the superseded user-scope installation implementation in the production cutover of
  `just sync-marketplace`.

`spx/EXCLUDE` is node-granular. Excluding this node to admit a not-yet-implemented harness
assertion also stops running its seven passing test files, so a node cannot be passing for its
existing assertions and specified for a new one at the same time. The harness assertion belongs
in a node of its own.
