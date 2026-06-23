# Pickup Claim Verification

`/pickup` reconciles every recorded session-file claim against current repository and external state before it presents the session and before the post-context checkpoint, and presents one verdict per claim — `Confirmed`, `Discrepancy`, or `Unverifiable` — in place of the recorded snapshot. The reconciliation is performed by a single plugin-shipped, stdlib-only `python3` script — `scripts/verify_session_claims.py` under the pickup skill, invoked through each runtime's skill-directory variable — which obtains producer-parsed session metadata from `spx session show --json`, reads only body-scoped operational hints from the session file, and emits the verdicts as structured output. The script reaches `spx session show --json`, `spx spec status`, `gh`, and `git` only through a dependency-injected command runner, performs no working-tree mutation, and runs no node test suite.

## Rationale

A session document is a pointer whose detail the resuming agent re-derives from the spec tree, not a source of truth (`spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`, `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md`). Presenting its recorded fields as current state is the defect this decision removes: the base advances, a commit moves, a tree goes dirty, and the recorded snapshot silently misstates them. Reconciling each claim against observed state before the checkpoint makes the resuming agent act on what the repository supports, not on what was true at handoff time.

One script — rather than a sequence of agent-issued commands — makes the reconciliation deterministic, auditable, side-effect-free, and identical across every pickup, and reduces the agent's surface to running the script and rendering its verdicts. Node status is read from the installed `spx spec status` contract rather than by executing the node's tests, so the pass stays cheap and runs nothing.

A plugin-shipped stdlib script is chosen over an `spx` CLI subcommand for reconciliation, while session-format parsing stays with the producer that writes the format. `spx session show --json` is a published-floor dependency: the plugins product may consume it only after `REQUIRED_SPX_VERSION` and the CI `SPX_VERSION` pin name a published `@outcomeeng/spx` version that provides it. Shipping the reconciliation logic inside the plugin keeps the comparison policy portable while consuming the published `spx`, `gh`, and `git` contracts as subprocesses.

## Invariants

- A claim verdict is a pure function of the recorded claim and the observed current state; re-running the script against an unchanged checkout and unchanged external state yields the same verdict for that claim.

## Verification

### Audit

- ALWAYS: every `spx`, `gh`, and `git` invocation in the verification script is issued through a dependency-injected runner parameter typed as a Protocol -- enables `l1` verification of claim-checking logic without mocking ([audit])
- ALWAYS: the default runner implementation uses `subprocess` with array arguments, and tests inject a controlled runner -- no mocking ([audit])
- ALWAYS: the verification script is stdlib-only `python3` shipped under the pickup skill as `scripts/verify_session_claims.py`, invoked through the runtime's skill-directory variable -- portable to consumer repositories, no third-party packages, no `uv` ([audit])
- ALWAYS: each claim resolves to exactly one of `Confirmed`, `Discrepancy`, or `Unverifiable`, and a check that cannot run resolves to `Unverifiable` -- an unrun check is a visible verdict, never a silent omission ([audit])
- ALWAYS: the verification obtains session metadata from `spx session show --json` rather than parsing YAML frontmatter itself, so the producer that serializes the session format also parses it ([audit])
- ALWAYS: any `spx` session capability the verification depends on is covered by the plugins product's published-version floor and CI pin before the dependency ships to consumers ([audit])
- NEVER: the verification reads node status by executing a node's test suite -- node status comes from the `spx spec status` contract, keeping the pass read-only ([audit])
- NEVER: the verification mutates the working tree, the index, or any session file -- reconciliation observes, it does not change state ([audit])
- NEVER: the verification depends on an unpublished `spx` CLI capability -- no unpublished cross-repository dependency ([audit])
- NEVER: an `spx`, `gh`, or `git` call is issued through a direct `subprocess.run` without the dependency-injected runner -- prevents isolated testing ([audit])
