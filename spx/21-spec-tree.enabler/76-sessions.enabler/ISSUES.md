# Issues: Session Management Enabler

## 1. Session-handoff tests are not isolated from the ambient worktree git context (DEBT)

`tests/test_sessions.scenario.l1.py` invokes `spx session handoff` as a subprocess without isolating the git work context it inspects. The handoff guard added by the session-external-state work rejects any context that is not the root worktree, or a linked worktree with a clean working tree detached at the tip of `origin/<default branch>` — raising `SessionHandoffBaseError: Cannot create a handoff session from this git work context`.

As a result, `just check` fails these scenarios whenever it runs from a **linked worktree checked out on a feature branch** — the normal state during PR work. 22 of 30 scenarios in the file fail this way; the suite passes only when the ambient worktree happens to be the root worktree or is detached at `origin/<default branch>` (e.g., a clean CI checkout).

Surfaced while running `just check` for `fix/merging-review-by-shape` (PR #104) from a linked worktree on the feature branch. Not caused by that PR — its diff touches no sessions code; the failure is the handoff guard reading the ambient worktree state.

Required handling:

- Isolate each test's git context — run `spx session handoff` against a controlled temporary repository (`git init` a `tmp_path` set up in the state the handoff expects), not the ambient worktree, so the suite passes regardless of the developer's worktree branch state.
- Until then, the sessions suite cannot pass locally from a feature-branch linked worktree; the clean-checkout CI run is the faithful surface for it.
