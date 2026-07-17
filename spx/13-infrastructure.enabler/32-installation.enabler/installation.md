# Installation

PROVIDES checkout-bounded reading of the Codex runtime's installed plugin set
SO THAT marketplace install verification and the isolated installation harness
CAN confirm which plugins Codex reports installed without misreading a changed CLI contract as an empty or stale set

Install verification and the isolated installation harness read the Codex runtime's installed plugin set through its CLI. The read is bounded to observation: it reports what the runtime holds and never reconciles, repairs, or refreshes a developer's user-scope marketplace registrations, plugin caches, or agent directories, per `spx/12-marketplace-state.adr.md`.

## Assertions

### Conformance

- ALWAYS: the Codex installed set is read from `codex plugin list --json --marketplace <marketplace>` and parsed as the `name` and `version` of each entry in the `installed` array, scoped to the queried marketplace; a payload that is not an object, lacks an `installed` array of named entries, or omits a string version raises rather than yielding a silent empty set or stale target, so a changed CLI contract is detected instead of misread ([test](tests/test_installed_set.conformance.l1.py))
