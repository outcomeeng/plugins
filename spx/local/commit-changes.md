# Marketplace Commit Rules

This file is loaded by the `/commit-changes` skill when working in this repository. It contains rules specific to committing changes to the Outcome Engineering plugin marketplace.

## Version Management

Plugin version bumps happen only when a commit changes a plugin distribution
surface: authored files under `src/plugins/{plugin-name}/`, generated runtime
files under `dist/{runtime}/{plugin-name}/`, or marketplace catalog fields that
change how a plugin is discovered. The first commit on a branch that changes a
plugin distribution surface bumps that plugin's source manifests relative to the
target base branch, normally `origin/main`. That version then stays fixed for
the entire PR phase.

Spec Tree files under `spx/`, including node-local `PLAN.md` and `ISSUES.md`
coordination notes, do not bump marketplace plugin versions by themselves. They are
product coordination and product truth, not plugin release artifacts. Root
repository instructions such as `AGENTS.md`, local workflow overlays under
`spx/local/`, validation config, tests, and generated repository docs also do not
bump a plugin unless they accompany a plugin distribution-surface change.

Plugins follow semantic versioning: `MAJOR.MINOR.PATCH`

**MAJOR version (0.x.x → 1.x.x):**

- ⛔ **NEVER bump unless user explicitly requests it**
- Reserved for future stable release when all features are production-ready

**MINOR version (0.3.x → 0.4.x):**

- ✅ Adding new commands (e.g., new `/pickup` command)
- ✅ Adding new skills (e.g., new `/design-frontend` skill)
- ✅ Major functional changes (e.g., atomic claim mechanism in `/pickup`)
- ✅ Significant user experience improvements
- 🎯 **Use sparingly** — only for substantial additions or changes

**PATCH version (0.3.1 → 0.3.2):**

- ✅ **Most common** — default for most changes
- ✅ Bug fixes
- ✅ Refactoring existing code
- ✅ Documentation improvements inside an installed plugin surface
- ✅ Small enhancements to existing features
- ✅ Performance optimizations
- ✅ Internal implementation changes
- 🎯 **Use liberally** — when in doubt, use PATCH

**No plugin version bump:**

- ✅ Changes confined to `spx/`
- ✅ Node-local `PLAN.md` or `ISSUES.md` coordination files
- ✅ Product-level instructions such as `AGENTS.md` / `CLAUDE.md`
- ✅ Local workflow overlays under `spx/local/`
- ✅ Tests, validation config, or generated repository docs when no plugin
  distribution surface changed

The marketplace sync wrapper follows the same boundary: `spx/`-only,
coordination-note-only, product-instruction-only, local-overlay-only, test-only, and
validation-config-only commits do not refresh local marketplace caches.

## How to Bump: `just bump`

NEVER hand-edit a `version` field in a manifest. `just bump` is the sanctioned way to write plugin versions — it detects every plugin with changes under `src/plugins/<name>/**` since the base branch, classifies each plugin's change into a semver segment, and writes the new version into every manifest that plugin owns (`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`) in lockstep, so the dual manifests can never drift.

```bash
just bump-dry      # preview what would be written; touches nothing
just bump          # write the detected version into every changed plugin's manifests
just bump-check    # exit non-zero if any changed plugin still needs a bump (local verification)
```

The `bump*` recipes take `base_ref="origin/main"` by default; pass a different base for a stacked branch (e.g. `just bump origin/<base>`). Run `just bump` BEFORE `just build-skills` so the regenerated `dist/` manifests carry the bumped version.

**Segment auto-detection.** A plugin that gains, loses, or renames a skill, command, agent, or manifest detects `minor`; every other plugin-distribution change detects `patch`. One `just bump` run can write `minor` for one changed plugin and `patch` for another. Auto-detection NEVER selects `major` — pass `--segment major` (or `minor`/`patch`) to force a segment for every changed plugin (`just bump --segment minor`); an explicit override warns on stderr for any plugin whose detected segment differed. The `## Version Bump Examples` below are the patterns this detection follows.

**`bump-check` is local, not a CI gate.** The quality gate (`just check`) does not run `bump-check`, so a missing or wrong version is NOT caught by CI — run `just bump` (or at least `just bump-check`) yourself before pushing.

**Marketplace catalogs** are separate from the version bump and are still hand-edited only when ADDING or REMOVING a plugin (not on every version change):

| File                               | Surface     |
| ---------------------------------- | ----------- |
| `.claude-plugin/marketplace.json`  | Claude Code |
| `.agents/plugins/marketplace.json` | Codex       |

`just check` runs `validate_plugins`, which exits non-zero if a plugin directory is missing from either catalog.

## Version Bump Workflow

**Bump once per branch, in the first plugin-distribution commit; do not bump again during PR review.** Only the version that lands on `main` matters.

1. Make the plugin changes.
2. Run `just bump`, then `just build-skills`. `just bump` bumps every changed-but-unbumped plugin and SKIPS (with a diagnostic) any plugin already bumped on this branch — so re-running it after a later commit bumps a newly-changed plugin without disturbing the ones already set. A branch that changes only `spx/`, coordination notes, repository instructions, tests, validation config, or local overlays bumps nothing.
3. Stage the plugin source, the regenerated `dist/`, and the manifests `just bump` wrote, then commit them together via `/commit-changes`.
4. During review, leave the version alone — follow-up commits that fix code, docs, specs, or review feedback do not bump again, and re-running `just bump` is a no-op for an already-bumped plugin.
5. If review materially expands the PR (for example adds a skill, turning a `patch` into a `minor`), run `just bump --segment minor` once to re-select the segment, then leave it fixed.
6. After a rebase or retarget onto an advanced base, re-run `just bump-dry` against the new base to re-evaluate — do not bump merely because another review commit was added.

When the PR merges, `main` receives the already-bumped version with no separate release commit.

❌ **WRONG** — hand-editing the `version` field (drifts the dual manifests, guesses the segment, has no CI guard):

```bash
# editing src/plugins/<name>/.claude-plugin/plugin.json "version" by hand — never do this
```

✅ **CORRECT** — let `just bump` detect the segment and write every manifest:

```bash
# 1. make the plugin changes
just bump          # detects the segment, writes every changed plugin's src manifests
just build-skills  # propagate the bumped version into dist/
# 2. then /commit-changes stages src + dist + the bumped manifests and commits together
```

## Version Bump Examples

| Change                                  | Old   | New   | Reason                               |
| --------------------------------------- | ----- | ----- | ------------------------------------ |
| Add `/handoff` command                  | 0.2.0 | 0.3.0 | New command = MINOR                  |
| Add self-organizing handoff             | 0.3.0 | 0.4.0 | Major functional change = MINOR      |
| Fix typo in an installed skill          | 0.4.0 | 0.4.1 | Plugin-surface documentation patch   |
| Refactor pickup logic                   | 0.4.1 | 0.4.2 | Refactoring = PATCH                  |
| Improve error messages                  | 0.4.2 | 0.4.3 | Small enhancement = PATCH            |
| Add `/design-frontend`                  | 0.4.3 | 0.5.0 | New skill = MINOR                    |
| Add `spx/.../PLAN.md`                   | 0.4.3 | 0.4.3 | Coordination note, no plugin surface |
| Update `spx/.../ISSUES.md`              | 0.4.3 | 0.4.3 | Coordination note, no plugin surface |
| Edit `spx/43-python.enabler/python.md`  | 0.4.3 | 0.4.3 | Spec-only, no plugin surface         |
| Edit `spx/local/commit-changes.md`      | 0.4.3 | 0.4.3 | Local workflow overlay, no plugin    |
| Edit `AGENTS.md` without plugin changes | 0.4.3 | 0.4.3 | Product instruction, no plugin       |
