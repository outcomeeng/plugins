# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment applied: `sync.md` declares the checkout-bounded model. The superseded assertions are
removed — Codex cache-topology inspection, user-scope marketplace-registration reconciliation,
canonical default-branch-worktree source resolution, and the file-backed single-flight lock that
serialized user-scope cache repair.

Release-path alignment applied: `spx/local/merging.md` declares no release action, and the root
guides state the same delivery model. A merge to the default branch on origin is the publication.

## Pending: retire sync rather than rewrite it

Both agents resolve from the `outcomeeng/plugins` marketplace this checkout declares, so no local
worktree serves plugin content and nothing refreshes a maintainer's installation. Synchronization has
no remaining subject, and the earlier plan to rewrite it checkout-bounded is superseded.

- Remove the `sync-marketplace`, `push-marketplace`, and `marketplace-source-root` recipes from
  `Justfile`. `marketplace-source-root` already exits non-zero: it resolves a Claude Directory source
  that no longer exists.
- Remove `outcomeeng/distribution/sync.py` and `outcomeeng/distribution/push.py`'s sync step.
- Remove `outcomeeng/distribution/marketplace_sources.py`, whose `configured_local_marketplace_root`
  requires both agents to resolve one shared local root — a predicate no longer satisfiable — and
  `outcomeeng/distribution/codex_cache.py`, whose compatibility-symlink repair mutated user-scope
  state the governing decision places outside the toolchain's reach.
- Repoint `just check-installed`: it reads `~/.claude/plugins/cache/` and resolves the Codex root
  through `marketplace_sources`. Frontmatter validity of the generated trees is already covered by
  `just check-skills`, so establish whether the recipe has an independent subject before keeping it.
- Re-scope this node. Its spec declares synchronization orchestration; if nothing remains to
  orchestrate, the node is a `/refactor` question rather than an implementation one, and its
  assertions and tests retire with the modules.

## Pending: install completeness in a disposable home

`spx/12-marketplace-state.adr.md` asserts install completeness is verified by an isolated harness
provisioning each registered agent in a disposable home and mutating no user-scope state. No test on
`origin/main` establishes it. `work/sync-marketplace-cutover` carries an implementation —
`outcomeeng_testing/harnesses/marketplace_runtime.py` and
`spx/13-infrastructure.enabler/32-installation.enabler/tests/test_install_completeness.compliance.l2.py` —
whose predicates live in the test file and whose harness exposes observations only. Salvage it into
the installation node; it needs a real `codex` binary, so confirm CI provisioning before linking the
assertion.
