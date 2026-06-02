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

## RESOLVED: scenario-test hermeticity (was "SPX PR #92 branch-prefill alignment")

A prior plan section assumed `spx session handoff` rejects detached HEAD in a main checkout (`SessionDetachedHeadError`) and recorded a `branch` field, and proposed adding four branch-prefill scenario assertions to `sessions.md`, a `21-skill-surface.enabler/` child, and an inline `sessions_env` fixture. That model is stale against the installed `spx` 0.5.2 and the test-infrastructure PDR. It has been replaced by a harness fix.

**What was actually wrong.** The scenario tests shell out to the real `spx session handoff`, which gates on the runner's git work context. The helpers passed no `cwd`, so the tests inherited the ambient git state of wherever pytest ran — green in a root checkout or a worktree detached at `origin/HEAD`, red in a linked worktree on a feature branch or a non-git sandbox. The suite's truth depended on an uncontrolled external input.

**The fix.** `outcomeeng_testing/harnesses/git_context.py` provisions a controlled, spx-accepted git context (a clean root worktree on a named branch); `test_sessions.scenario.l1.py` runs every session-command subprocess with `cwd` set to it. The suite is now hermetic — verified passing from a non-git directory.

**Boundary — do not re-add branch-prefill assertions here.** The git-context contract is owned by the external `spx` CLI repo (`~/Code/outcomeeng/spx/`), not this node's spec. This node specifies the plugin surface (handoff/pickup skills, the post-compact hook); its tests merely establish the precondition the external tool requires. The current `spx` 0.5.2 contract, for reference: handoff is accepted from a root worktree (on a branch → records the branch name; detached → records the HEAD SHA) or a clean linked worktree detached at the tip of `origin/<default>` (records that SHA), and refused from any other linked-worktree state or a non-git directory with `SessionHandoffBaseError` — a single error class, not the two the old plan named.

**Already done as part of the fix:** the dead `SESSION_RESUME` reference and the stale assertion-count docstring were removed from `test_sessions.scenario.l1.py`; the stale "release not supported" note in `src/plugins/spec-tree/skills/handoff/SKILL.md` `<arguments>` was corrected to point at `spx session release <id>`.
