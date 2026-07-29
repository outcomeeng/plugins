# Pickup Claim Verification

`/pickup` reconciles every recorded session claim against current repository and external state before it presents the session and before the post-context checkpoint, and presents one verdict per claim — `Confirmed`, `Discrepancy`, or `Unverifiable` — in place of the recorded snapshot. The reconciliation is performed by a single plugin-shipped, stdlib-only `python3` script — `scripts/verify_session_claims.py` under the pickup skill, invoked through each runtime's skill-directory variable — which reads session frontmatter through the published `spx session show --json` contract, reads session prose through `spx session show`, observes the current checkout, and emits the verdicts as structured output. The script reaches `spx session show`, `spx spec status`, `gh`, and `git` only through a dependency-injected command runner, performs no working-tree mutation, and runs no node test suite.

## Rationale

A session document is a pointer whose detail the resuming agent re-derives from the spec tree, not a source of truth (`spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler/60-session-document.enabler/session-document.md`, `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md`). Presenting its recorded fields as current state is the defect this decision removes: the base advances, a commit moves, a tree goes dirty, and the recorded snapshot silently misstates them. Reconciling each claim against observed state before the checkpoint makes the resuming agent act on what the repository supports, not on what was true at handoff time.

One script — rather than a sequence of agent-issued commands — makes the reconciliation deterministic, auditable, side-effect-free, and identical across every pickup, and reduces the agent's surface to running the script and rendering its verdicts. Session frontmatter is read through `spx session show --json` because the `spx` CLI owns the shared `.spx/` store in both single-worktree and bare-pool layouts; a plugin-shipped script does not construct worktree-local `.spx/sessions/...` paths and does not parse YAML with regular expressions. Node status is read from the installed `spx spec status` contract rather than by executing the node's tests, so the pass stays cheap and runs nothing.

A plugin-shipped stdlib script is chosen over a new `spx` CLI subcommand: a new CLI subcommand would bind `/pickup` to an unpublished cross-repository capability gated by the published-version floor, and would not be portable to consumer repositories that install the plugin without that CLI capability. Shipping the reconciliation logic inside the plugin keeps it self-contained and portable while still consuming the published `spx session show`, `spx spec status`, `gh`, and `git` contracts as subprocesses.

## Invariants

- A claim verdict is a pure function of the recorded claim and the observed current state; re-running the script against an unchanged checkout and unchanged external state yields the same verdict for that claim.

## Verification

### Audit

- ALWAYS: every `spx`, `gh`, and `git` invocation in the verification script is issued through a dependency-injected runner parameter typed as a Protocol -- enables `l1` verification of claim-checking logic without mocking ([audit])
- ALWAYS: the default runner implementation uses `subprocess` with array arguments, and tests inject a controlled runner -- no mocking ([audit])
- ALWAYS: the verification script is stdlib-only `python3` shipped under the pickup skill as `scripts/verify_session_claims.py`, invoked through the runtime's skill-directory variable -- portable to consumer repositories, no third-party packages, no `uv` ([audit])
- ALWAYS: the verification script obtains session frontmatter by session id through `spx session show --json`, and never constructs a worktree-local `.spx/sessions/...` path or parses session YAML directly ([audit])
- ALWAYS: each claim resolves to exactly one of `Confirmed`, `Discrepancy`, or `Unverifiable`, and a check that cannot run resolves to `Unverifiable` -- an unrun check is a visible verdict, never a silent omission ([audit])
- ALWAYS: the verification obtains session metadata from `spx session show --json` rather than parsing YAML frontmatter itself, so the producer that serializes the session format also parses it ([audit])
- ALWAYS: any `spx` session capability the verification depends on is covered by the plugins product's published-version floor and CI pin before the dependency ships to consumers ([audit])
- NEVER: the verification reads node status by executing a node's test suite -- node status comes from the `spx spec status` contract, keeping the pass read-only ([audit])
- NEVER: the verification mutates the working tree, the index, or any session file -- reconciliation observes, it does not change state ([audit])
- NEVER: the verification depends on an unpublished `spx` CLI capability -- every `spx session show` and `spx spec status` use is covered by the published spx version floor ([audit])
- NEVER: an `spx`, `gh`, or `git` call is issued through a direct `subprocess.run` without the dependency-injected runner -- prevents isolated testing ([audit])
