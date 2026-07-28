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

- ✅ Adding new skills (e.g., new `/design-frontend` skill)
- ✅ Adding new thin agents
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

The `bump*` recipes take two **positional** arguments — `base_ref` (default `origin/main`) then `segment` (default: auto-detected): `just bump <base_ref> <segment>`. Pass a different base for a stacked branch (`just bump origin/<base>`); force a segment by giving both arguments, since `segment` is the second positional — `just bump origin/main minor`. `just bump --segment minor` and `just bump segment=minor` are NOT valid recipe syntax (`--segment` is the underlying Python flag, not the `just` parameter). Run `just bump` BEFORE `just build-skills` so the regenerated `dist/` manifests carry the bumped version.

**Segment auto-detection is structural.** `just bump` keys on structure, not on a change's semantic weight: a plugin that gains, loses, or renames a skill, thin agent, or manifest detects `minor`; every other plugin-distribution change detects `patch`. One run can write `minor` for one changed plugin and `patch` for another. It NEVER selects `major`. It also cannot recognize a non-structural change the policy still treats as `minor` — a **major functional change** or **significant user experience improvement** per `## Version Management` (for example a new claim mechanism inside an existing skill) gains no skill, agent, or manifest, so `just bump` detects `patch`; pass `just bump origin/main minor` for it. Giving an explicit positional `segment` (`major`/`minor`/`patch`) forces that segment for every changed plugin and warns on stderr for any plugin whose detected segment differed. In `## Version Bump Examples` below, the structural rows (new skill, new thin agent) are what auto-detection produces; a row marked "not structural" needs the positional `minor` override.

**`bump-check` is local, not a CI gate.** The quality gate (`just check-full`) does not run `bump-check`, so a missing or wrong version is NOT caught by CI — run `just bump` (or at least `just bump-check`) yourself before pushing.

**Marketplace catalogs** are separate from the version bump and are still hand-edited only when ADDING or REMOVING a plugin (not on every version change):

| File                               | Surface     |
| ---------------------------------- | ----------- |
| `.claude-plugin/marketplace.json`  | Claude Code |
| `.agents/plugins/marketplace.json` | Codex       |

`just check-full` runs `validate_plugins`, which exits non-zero if a plugin directory is missing from either catalog.

## Version Bump Workflow

**Bump once per branch, in the first plugin-distribution commit; do not bump again during PR review.** Only the version that lands on `main` matters.

1. Make the plugin changes.
2. Run `just bump`, then `just build-skills`. `just bump` bumps every changed-but-unbumped plugin and SKIPS (with a diagnostic) any plugin already bumped on this branch — so re-running it after a later commit bumps a newly-changed plugin without disturbing the ones already set. A branch that changes only `spx/`, coordination notes, repository instructions, tests, validation config, or local overlays bumps nothing. Detection is structural (see **Segment auto-detection is structural** above): if the change is a major functional change or significant UX improvement per `## Version Management` but `just bump-dry` shows `patch`, re-run `just bump origin/main minor`.
3. Stage the plugin source, the regenerated `dist/`, and the manifests `just bump` wrote, then commit them together via `/commit-changes`.
4. During review, leave the version alone — follow-up commits that fix code, docs, specs, or review feedback do not bump again, and re-running `just bump` is a no-op for an already-bumped plugin.
5. If review materially changes the PR's class (for example adds or removes a skill or thin agent, turning a `patch` into a `minor`), re-select the segment by restoring that plugin's manifests to their base version first, then bumping once:

   ```bash
   git checkout <base_ref> -- src/plugins/<name>/.claude-plugin/plugin.json src/plugins/<name>/.codex-plugin/plugin.json
   just bump <base_ref> <segment>
   ```

   `just bump` alone cannot re-select: it skips a plugin whose working-tree version is already ahead of the base, and an explicit `segment` does not override that skip. Restoring first leaves the branch carrying exactly one bump from the base at the corrected segment, which is what the skip protects. Then leave it fixed.
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

| Change                                  | Old   | New   | Reason                                                                               |
| --------------------------------------- | ----- | ----- | ------------------------------------------------------------------------------------ |
| Add an implementation-auditor agent     | 0.2.0 | 0.3.0 | New thin agent = MINOR                                                               |
| Add self-organizing handoff             | 0.3.0 | 0.4.0 | Major functional change = MINOR — not structural, pass `just bump origin/main minor` |
| Fix typo in an installed skill          | 0.4.0 | 0.4.1 | Plugin-surface documentation patch                                                   |
| Refactor pickup logic                   | 0.4.1 | 0.4.2 | Refactoring = PATCH                                                                  |
| Improve error messages                  | 0.4.2 | 0.4.3 | Small enhancement = PATCH                                                            |
| Add `/design-frontend`                  | 0.4.3 | 0.5.0 | New skill = MINOR                                                                    |
| Retire a thin agent                     | 0.5.0 | 0.6.0 | A lost thin agent is structural = MINOR                                              |
| Add `spx/.../PLAN.md`                   | 0.6.0 | 0.6.0 | Coordination note, no plugin surface                                                 |
| Update `spx/.../ISSUES.md`              | 0.6.0 | 0.6.0 | Coordination note, no plugin surface                                                 |
| Edit `spx/43-python.enabler/python.md`  | 0.6.0 | 0.6.0 | Spec-only, no plugin surface                                                         |
| Edit `spx/local/commit-changes.md`      | 0.6.0 | 0.6.0 | Local workflow overlay, no plugin                                                    |
| Edit `AGENTS.md` without plugin changes | 0.6.0 | 0.6.0 | Product instruction, no plugin                                                       |
