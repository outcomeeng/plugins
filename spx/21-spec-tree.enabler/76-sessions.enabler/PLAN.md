# PLAN: Wire the spx CLI half of the session-scope accumulator

## Why this plan exists

The spec-tree plugin now specifies `.spx/sessions/$CLAUDE_SESSION_ID/` (or `$CODEX_THREAD_ID/` under Codex) as the authoritative accumulator for every session an agent has claimed during a runtime. The marketplace side is in place after commit `ad7d696`:

- `src/plugins/spec-tree/bin/session-start` no longer mkdirs the per-runtime directory. It is created lazily on first claim.
- `src/plugins/spec-tree/skills/handoff/references/scope-resolution.md` reads the filesystem as primary source of truth and cross-checks against `<SESSION_SCOPE>` / `<PICKUP_CHECKPOINT>` / `<PICKUP_CLAIM>` markers.
- `src/plugins/spec-tree/skills/pickup/SKILL.md` documents the dual accumulator (filesystem symlink + marker).

The corresponding `spx` CLI changes have not landed. Until they do, the filesystem source is empty on every runtime, the algorithm falls through to marker-based scope recovery, and context compaction still risks dropping scope — the exact failure mode this work eliminates.

This plan hands the CLI implementation off to an agent working in `~/Code/outcomeeng/spx/`.

## Target behavior

**On every successful `spx session pickup`:**

```text
1. mv todo/<id>.md → doing/<id>.md          (existing behavior, unchanged)
2. Resolve $RUNTIME_ID:
     prefer $CLAUDE_SESSION_ID
     fall back to $CODEX_THREAD_ID
     if neither set → skip steps 3-4 (degraded, keep going)
3. mkdir -p .spx/sessions/$RUNTIME_ID/
4. ln -sfn ../doing/<id>.md .spx/sessions/$RUNTIME_ID/<id>.md
```

Relative symlink is deliberate — absolute paths break when the repo is checked out at a different root.

**On every successful `spx session archive <id>`:**

```text
1. For every directory D under .spx/sessions/ that is NOT todo/, doing/, archive/:
     if D/<id>.md exists → rm D/<id>.md
   (scan is necessary because the archiving runtime may differ from the claiming runtime)
2. mv doing/<id>.md → archive/<id>.md    (existing behavior, unchanged)
```

**Unchanged:** `spx session list`, `spx session show`, `spx session handoff`, `spx session release`, `spx session prune`, `spx session delete`, `spx session todo`.

## Contract specifics

- **Symlink format**: relative, exactly `../doing/<id>.md`. A symlink ending in anything else is invalid and must be treated as a bug, not as data.
- **Dangling symlinks**: `spx session pickup` on a previously-dangling id must first remove the old symlink, then create the new one. Never overwrite without validating.
- **Runtime id collision**: if two conversations happen to produce the same `$CLAUDE_SESSION_ID` (should not occur — Claude session ids are per-conversation), the second pickup silently shares the same directory. This is acceptable degraded behavior; no special handling required.
- **File permissions**: the per-runtime directory and its symlinks inherit umask. Do not chmod explicitly.
- **Concurrency**: pickup and archive are already atomic at the queue level. The accumulator steps happen before/after the queue move — a crash between queue move and symlink create leaves a session in `doing/` without a symlink (scope-resolution.md's "markers are a superset of filesystem" case — the marker cross-check catches this). A crash between symlink remove and archive move leaves a symlink with a target in `archive/` (resolution: the filesystem step classifies it as "already archived" and skips it). Both are acceptable recovery paths.

## Work breakdown with audit gates

### Step 1 — Spec the new behavior

**Target node**: `spx/41-validation.enabler/21-validation-cli.enabler/` already hosts the CLI dispatch spec. The session subcommands live under a different enabler — confirm by `/contextualizing spx/` in the `spx` repo on first entry.

1. Invoke `/contextualizing` on the target enabler under the `spx` repo's spec tree. Resolve the authoritative node.
2. Amend the spec to declare the two new assertions (pickup-creates-symlink, archive-removes-symlink) plus the per-session-dir scanning rule.
3. **Audit gate**: run `/auditing-product-decisions` on any PDR changes and `/aligning` across the affected subtree.

### Step 2 — Tests first (TDD)

Per the spx repo's test-language ADR (TypeScript + Vitest), write tests in the target node's `tests/` directory following `<subject>.<evidence>.<level>[.<runner>].test.ts`:

- `pickup.scenario.l1.test.ts` — claim-then-inspect-symlink round-trip; $CLAUDE_SESSION_ID and $CODEX_THREAD_ID paths; neither-set degraded path.
- `archive.scenario.l1.test.ts` — archive-removes-own-symlink; archive-removes-cross-runtime-symlink (simulate second runtime directory); archive-of-untracked-id (no symlink exists).
- `accumulator.property.l1.test.ts` — property: for any sequence of pickup(id_i) and archive(id_i) operations with a fixed runtime id, the set `{readlink(S) for S in .spx/sessions/$RUNTIME_ID/}` equals the set of picked-up-but-not-yet-archived ids.
- `symlink-recovery.scenario.l1.test.ts` — pre-existing dangling symlink with a newly-claimed matching id; crash-between-move-and-symlink recovery.

**Audit gate**: run `/auditing-tests` (via `/spec-tree:test-evidence-auditor` agent) to confirm coupling, falsifiability, alignment, coverage. Every new test must pass the 4-property evidence check.

### Step 3 — Implementation

- `src/commands/session/pickup.ts` (or wherever the handler lives) — add the resolve-runtime-id + mkdir -p + ln -sfn after the existing move.
- `src/commands/session/archive.ts` — add the scan-and-unlink step before the existing move.
- Factor the runtime-id resolution into a helper under `src/lib/` so other session commands can reuse it without duplicating env-var priority logic.

**Audit gate**: `spx validation all` in the spx repo after each file. Zero new findings.

### Step 4 — End-to-end verification in the marketplace repo

Return to `~/Code/outcomeeng/plugins/`. Install the updated `spx` via `pnpm link`. Then:

1. In a fresh conversation, `/pickup` some test session. Verify `.spx/sessions/$CLAUDE_SESSION_ID/<id>.md` exists as a symlink pointing at `../doing/<id>.md`.
2. `/handoff`. Confirm workflow 04 resolves scope from the filesystem (the verdict output should name the symlink's id) and the symlink is removed after `spx session archive`.
3. Inspect `.spx/sessions/$CLAUDE_SESSION_ID/`. It must be empty or removed after closure.
4. Context-compaction test: claim a session, run `/compact`, then `/handoff`. Scope must still resolve correctly via the filesystem even though the `<SESSION_SCOPE>` marker is gone.

## Touch points in the marketplace repo

Nothing else to change here. The plugin-side contract is already merged. If the spx agent finds a drift between what this PLAN.md describes and what `references/scope-resolution.md` prescribes, the `references/scope-resolution.md` is authoritative — update this PLAN.md, not the reference.

## Pointers

- Marketplace commit implementing the plugin-side contract: `ad7d696`
- Authoritative algorithm: [`src/plugins/spec-tree/skills/handoff/references/scope-resolution.md`](../../../src/plugins/spec-tree/skills/handoff/references/scope-resolution.md)
- SessionStart hook (lazy-create expectation): [`src/plugins/spec-tree/bin/session-start`](../../../src/plugins/spec-tree/bin/session-start)
- Current spx session command handlers (paths observed during plan drafting; confirm on entry): `src/commands/session/pickup.ts`, `src/commands/session/archive.ts`, `src/domains/session/index.ts`

---

# PLAN: Spec and test alignment for SPX PR #92 branch-prefill behavior

## Why this plan exists

SPX PR #92 revised `spx session handoff` to be worktree-aware. The old behaviour (reject all detached HEAD) has been replaced by a four-case model that this node's spec does not yet declare. 11 tests fail against the updated CLI because the test helper calls `spx session handoff` without setting up the required git context.

SPX PR #92 branch-prefill model:

| Context                                                                          | Allowed?                        | `branch` field recorded |
| -------------------------------------------------------------------------------- | ------------------------------- | ----------------------- |
| Main checkout, named branch                                                      | Yes                             | branch name             |
| Main checkout, detached HEAD                                                     | No — `SessionDetachedHeadError` | —                       |
| Linked worktree, detached at `git symbolic-ref --short refs/remotes/origin/HEAD` | Yes                             | base commit SHA         |
| Linked worktree, any other state                                                 | No — `SessionWorktreeBaseError` | —                       |

Additionally, `src/plugins/spec-tree/skills/handoff/SKILL.md` has stale text in `<arguments>` claiming `spx session release` is not supported (it has been supported since PR #96).

## Step 1 — Spec: add scenario assertions to `sessions.md`

Add four new scenario assertions covering the four branch-prefill cases above. All use `[test]` evidence pointing at `tests/test_sessions.scenario.l1.py`. Add one new compliance assertion:

- ALWAYS: for a linked worktree invocation, the `/handoff` skill checks the current branch
  from its context injection; when empty (detached HEAD), it runs
  `git switch --detach $(git symbolic-ref --short refs/remotes/origin/HEAD)` to reach the
  allowed linked-worktree state before calling `spx session handoff` ([review])

## Step 2 — Create `21-skill-surface.enabler/` child node

New enabler node at `spx/21-spec-tree.enabler/76-sessions.enabler/21-skill-surface.enabler/` with `skill-surface.md` declaring the `/handoff` and `/pickup` skill invocation surfaces:

- `/handoff` surfaces `spx session list` at invocation via context injection ([review])
- `/pickup` surfaces `spx session todo` at invocation via context injection ([review])
- `/handoff` declares `argument-hint: "[--no-session] [--prune]"` ([review])
- `/pickup` declares `argument-hint: "[--list] [--auto-continue]"` ([review])
- ALWAYS: `--prune` deletes archive sessions only after canonical continuation is written ([review])
- NEVER: session workflows exposed through slash-command shims ([review])

Use `/authoring` to create the node at index 21 (no lower-index siblings exist under this enabler).

**Audit gate**: `/aligning` on `sessions.md` and `skill-surface.md` after authoring.

## Step 3 — Fix `handoff/SKILL.md` stale text

In `src/plugins/spec-tree/skills/handoff/SKILL.md` `<arguments>`, replace:

> Putting a claimed session back in TODO is a separate manual operation (not currently supported by `spx session`).

with:

> To return a wrongly-claimed session to the todo queue without archiving it, run `spx session release <id>`.

Regenerate dist after any `src/plugins/` change: `just build-skills`.

## Step 4 — Fix tests in `test_sessions.scenario.l1.py`

### 4a. Add `sessions_env` fixture

Creates a minimal git repo that mirrors the linked-worktree-at-default-branch state `spx session handoff` accepts: init with remote `origin`, one commit on `main`, detach HEAD at `origin/main`. Returns `(git_repo, sessions_dir)`.

```python
@pytest.fixture
def sessions_env(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    # bare remote so origin/HEAD resolves
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(remote)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "init", "-b", "main", str(repo)], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "t@t.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "origin", str(remote)],
        check=True,
        capture_output=True,
    )
    (repo / ".gitignore").write_text(".spx/\n")
    subprocess.run(
        ["git", "-C", str(repo), "add", ".gitignore"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "init"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "push", "-u", "origin", "main"],
        check=True,
        capture_output=True,
    )
    # detach at origin/main — the state spx accepts for a linked worktree
    subprocess.run(
        ["git", "-C", str(repo), "switch", "--detach", "origin/main"],
        check=True,
        capture_output=True,
    )
    return repo, tmp_path / "sessions"
```

### 4b. Update `_handoff` to accept `cwd`

Add `cwd: Path | None = None` parameter, pass to `subprocess.run`.

### 4c. Update all 11 failing test methods

Each currently uses `(self, tmp_path)` and passes `tmp_path / "sessions"` directly. Change to `(self, sessions_env)`, unpack `git_repo, sessions_dir = sessions_env`, pass `cwd=git_repo`.

### 4d. Add new test classes

- `TestHandoffRejectsDetachedHeadInMainCheckout` — named-branch repo, detach HEAD, assert `SessionDetachedHeadError`
- `TestHandoffRejectsWorktreeNotAtDefault` — repo with origin but worktree checked out on a named branch (not detached), assert `SessionWorktreeBaseError` — NOTE: only add once SPX PR #92 lands and the error is confirmed
- `TestHandoffSucceedsInWorktreeAtDefault` — `sessions_env` fixture (detached at origin/main), assert zero exit and `branch` field in frontmatter contains a SHA not a branch name
- `TestHandoffSucceedsInMainCheckoutOnNamedBranch` — named-branch repo (not detached), assert zero exit and `branch` field in frontmatter contains the branch name

### 4e. Cleanup

- Remove dead `SESSION_RESUME = BIN_DIR / "session-resume"` variable (line 32)
- Strip assertion-count list from module docstring; replace with one-line description

## Step 5 — Delete ISSUES.md item #1

Remove item #1 (multi-ID pickup) from `spx/21-spec-tree.enabler/76-sessions.enabler/ISSUES.md` — it is not a spec concern for this node.

## Step 6 — Validation

```bash
just test spx/21-spec-tree.enabler/76-sessions.enabler/tests/
just check
```

All 11 previously failing tests must pass. No new failures.

## Pointers

- SPX PR #92: worktree-aware branch prefill, `SessionDetachedHeadError` / `SessionWorktreeBaseError`
- Failing tests: `spx/21-spec-tree.enabler/76-sessions.enabler/tests/test_sessions.scenario.l1.py` (11 failures, all `SessionDetachedHeadError`)
- Skill to fix: `src/plugins/spec-tree/skills/handoff/SKILL.md` `<arguments>` line 79
- Build: `just build-skills` after any `src/plugins/` edit
