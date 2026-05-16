# Claude Plugin Cache Preservation

## Purpose

This decision governs how the marketplace preserves prior plugin-version paths in the Claude Code local cache after `claude plugin marketplace upgrade`. It mirrors the Codex preservation decision in `spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md` for Claude's distinct cache topology.

## Context

**Business impact:** A Claude Code session resolves skills through versioned cache paths under `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Each `claude plugin marketplace upgrade` adds a new version directory alongside existing ones; prior version directories persist. A session that loaded skill X at version N keeps resolving X via `<plugin>/N/...` for its entire life. Working-tree edits therefore reach running sessions only through three explicit steps: bump the manifest version, run `claude plugin marketplace upgrade`, run `/reload-plugins`. The version bump exists solely to create a new cache directory the upgrade can populate — without it, no new directory exists and nothing reaches the session. The result is version-number churn disproportionate to semantic change: typo fixes, description tweaks, and documentation refreshes all force manifest bumps even when no version-meaningful change is involved.

**Technical constraints:**

- Claude Code resolves plugin paths through `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, where `<version>` matches the manifest's published version at marketplace-upgrade time.
- `claude plugin marketplace upgrade` creates a new version directory. It does not prune prior version directories. The cache grows monotonically.
- `/reload-plugins` re-indexes the cache directory tree and re-reads SKILL.md content (including frontmatter) from disk during registration. Skill invocations after a reload that have not already loaded the skill in this session read the current on-disk content.
- The runtime follows directory symlinks at the version level. A symlink at `<plugin>/<version>/` pointing elsewhere resolves transparently during reload-time indexing and during invocation-time content loading. The runtime preserves the symlinked path identity in resolution output rather than canonicalizing.
- Codex's resolver requires every published version path to exist on disk because Codex prunes prior versions during marketplace upgrade. Claude's resolver retains every version directory; the preservation problem there is shaped differently.

## Decision

After `claude plugin marketplace upgrade`, every prior plugin-version directory in `~/.claude/plugins/cache/<marketplace>/<plugin>/` is replaced with a symlink to the current plugin-version directory. The current version directory is the only real plugin content on disk; all other version paths resolve through the symlink to the same content. The preservation set is derived from the cache directory listing plus the manifest's current published version; it is not derived from any pre-upgrade snapshot.

## Rationale

Version-path resolution identifies content, not bytes. A prior-version path `<plugin>/<V_prior>/` under the symlink mechanism resolves through its symlink target to current content. Every in-flight session that resolved skill X via `<plugin>/<V_prior>/...` reads the current SKILL.md when the runtime next loads it from disk — after `/reload-plugins` for fresh invocations, after compaction for previously-loaded skills.

This removes the manifest version bump from the propagation path for non-semantic changes. A typo fix in a SKILL.md description reaches every running session through one cycle: edit the working tree, run the marketplace sync recipe (which rebuilds the symlinks against the new current version), run `/reload-plugins`. Manifest bumps remain meaningful for the changes the version number is supposed to communicate — backwards-incompatible API shifts, new required arguments, removed skills — but are no longer mandatory for changes that do not warrant a version increment.

The neighboring Codex decision's mechanism applies here with one structural simplification. Codex preserves a ten-day window because Codex prunes prior versions during marketplace upgrade — the window bounds an aggressively-shrinking preservation set. Claude does not prune; every prior version directory persists. The preservation set is therefore "every prior version present in the cache" rather than a windowed subset, and the symlink rewrite happens against the full cache directory listing for the plugin. Identical idempotence and bypass-resilience properties as the Codex mechanism: every recipe invocation recomputes the desired state from the cache listing plus the manifest version; a bypassed sync reverts to the pre-symlink frozen-content layout, which the next sync invocation repairs.

Two alternatives were rejected. The first — leave prior versions as real directories with their original content — preserves bytes-on-disk pinning at the cost of forcing manifest bumps for every propagation, even when no semantic version change is intended. The bump-for-every-change cost is paid on every author iteration; the bytes-on-disk benefit applies only to the narrow set of users who pin to non-current versions and expect those versions to remain frozen across marketplace upgrades. The second — prune prior versions outright after a window, matching Codex's pruning step — frees cache disk but breaks both pinning and the no-bump propagation path; it inherits Codex's complexity without inheriting Codex's reason to prune, since Claude's resolver does not require pruning.

## Trade-offs accepted

| Trade-off                                                                                                               | Mitigation / reasoning                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Sessions that resolved through prior version paths receive current content rather than the bytes they originally loaded | Skill content already loaded into a session stays in session memory. Fresh invocations after `/reload-plugins` and post-compaction re-attachments read the symlink-resolved current content — both are explicit refresh signals the user controls                  |
| Pinning to a prior plugin version resolves to current content after the next marketplace sync                           | Bytes-on-disk pinning is not a product guarantee. Plugin versions published to the marketplace branch are the versioning contract; the cache layout is a resolution implementation detail. Users who require frozen bytes use the marketplace branch's git history |
| The marketplace sync recipe gains a cache-mutation step that touches every prior version directory for every plugin     | The mutation is bounded by plugin count × prior-version count, both small. Per-invocation cost is comparable to the existing manifest-and-`gh` shell-outs the recipe already performs                                                                              |
| A bypassed marketplace sync leaves prior versions as real directories until the next sync                               | The desired-state derivation is idempotent and recomputes from the cache listing plus the manifest version. A bypass has no permanent effect — the next sync invocation restores the symlink layout                                                                |
| Symlinks aimed at the current version directory break if the current version directory is later removed                 | The current version directory is the marketplace's authoritative resolution target and is preserved as a real directory by the same recipe. Removing the current version is itself a separate destructive operation outside this decision's scope                  |

## Product invariants

- For any plugin `P` with manifest current version `V_current`, `~/.claude/plugins/cache/<marketplace>/P/V_current/` resolves to the current published content immediately after the marketplace sync recipe completes.
- For any prior version `V_prior` whose directory exists in the cache, `~/.claude/plugins/cache/<marketplace>/P/V_prior/` is a symlink to `~/.claude/plugins/cache/<marketplace>/P/V_current/` after the same recipe.
- The post-sync cache state is a pure function of the cache directory listing and the manifest's current published version, independent of the cache state observed before the recipe ran.
- `/reload-plugins` plus a fresh skill invocation reads the current SKILL.md content regardless of which prior-version path the session originally resolved through.

## Compliance

### Recognized by

The marketplace sync recipe (`just push-marketplace` or `just sync-marketplace`) invokes a preservation step against the Claude cache. The step enumerates prior version directories under `~/.claude/plugins/cache/<marketplace>/<plugin>/`, removes each one, and replaces it with a symlink to the manifest's current version directory. Pinned and unpinned installs read content from the symlink target.

### MUST

- The Claude cache preservation step enumerates prior version directories from the cache directory listing and converts every one to a symlink targeting the current version directory ([review])
- The current plugin version directory remains a real directory, not a symlink ([review])
- Preservation runs during the same recipe invocation that publishes the new current version ([review])
- The step is idempotent — re-invocation with no version change leaves the cache state unchanged ([review])
- Preservation derives the symlink set from the cache directory listing plus the manifest's current published version, never from a pre-upgrade snapshot ([review])

### NEVER

- Prune prior version directories. Path resolution to current content relies on every prior version path existing as a symlink ([review])
- Compute the preservation set from a pre-upgrade snapshot. The set comes from the cache listing plus the manifest version ([review])
- Convert the current plugin version directory to a symlink. The current version directory is the authoritative resolution target ([review])
- Treat a symlinked prior version path as a pinning contract. Bytes-on-disk pinning is not preserved across marketplace syncs ([review])
