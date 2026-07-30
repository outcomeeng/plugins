# Claim Verification

PROVIDES the read-only reconciliation of a session document's recorded claims against current repository and external state, resolving each claim to exactly one of `Confirmed`, `Discrepancy`, or `Unverifiable`
SO THAT the resumption flow
CAN present observed state in place of a recorded snapshot the base, the working tree, or an external system has since moved past

## Assertions

### Mappings

- A claim the script compares against current state maps to `Confirmed` when current state matches the recorded claim and `Discrepancy` when it differs: an injected `specs`/`files` path resolves to one of those two by its existence in the current checkout, while session loading, `git_ref` reachability, and the working-tree state additionally map to `Unverifiable` when the underlying command cannot run ([test](tests/test_pickup_verification.mapping.l1.py))
- A claim the script can only observe current state for — a node's `spx spec status` and an external PR id, whose recorded baseline lives in session prose the script does not parse — maps to `Confirmed` with the current value surfaced for reconciliation against that prose, and `Unverifiable` when the observing command cannot run ([test](tests/test_pickup_verification.mapping.l1.py))

### Compliance

- ALWAYS: `/pickup` reconciles every recorded session claim against current repository and external state before the post-context checkpoint by running the pickup skill's `scripts/verify_session_claims.py <session-id>` (through the runtime's skill-directory variable), and presents one verdict per claim — `Confirmed`, `Discrepancy`, or `Unverifiable` — in place of the recorded snapshot ([audit])
- ALWAYS: the verification script obtains session frontmatter from `spx session show --json`, resolves node status from `spx spec status`, reaches `spx`, `gh`, and `git` only through a dependency-injected runner, and emits `Unverifiable` for any check it cannot run ([test](tests/test_pickup_verification.compliance.l1.py))
- ALWAYS: node-status claim evidence is the target node's own record from the `spx spec status --format json` node tree — located by the node's tree-relative id, carrying that record's scalar fields, and excluding its child subtree ([test](tests/test_pickup_verification.compliance.l1.py))
- ALWAYS: a claimed node absent from the `spx spec status --format json` projection resolves to `Unverifiable` with evidence naming the absent node, never a synthesized status ([test](tests/test_pickup_verification.compliance.l1.py))
- NEVER: `/pickup` presents a recorded session-file claim as current state without a verdict from the verification pass ([audit])
- NEVER: the verification pass executes a node's test suite or mutates the working tree, the index, or any session file — reconciliation observes, it does not change state ([test](tests/test_pickup_verification.compliance.l1.py))
