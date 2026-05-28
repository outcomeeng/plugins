# Marketplace Commit Rules

This file is loaded by the `/committing-changes` skill when working in this repository. It contains rules specific to committing changes to the Outcome Engineering plugin marketplace.

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
- ✅ Adding new skills (e.g., new `/designing-frontend` skill)
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

## Files to Update When Bumping Version

**Plugin manifest version** (update every manifest that exists for the plugin you changed):

```bash
src/plugins/{plugin-name}/.claude-plugin/plugin.json
src/plugins/{plugin-name}/.codex-plugin/plugin.json  # if it exists
```

```json
{
  "name": "{plugin-name}",
  "version": "0.4.0"
}
```

**Marketplace catalogs** — update both when adding a plugin; update descriptions when they change:

| File                               | Surface     |
| ---------------------------------- | ----------- |
| `.claude-plugin/marketplace.json`  | Claude Code |
| `.agents/plugins/marketplace.json` | Codex       |

`just check` runs `validate_plugins`, which exits non-zero if a plugin directory is missing from either catalog.

Always validate after any changes:

```bash
just check
```

## Version Bump Workflow

**CRITICAL: bump once in the first plugin-distribution commit on a branch, then
do not bump again during PR review.**

Only the version that will land on main matters. The correct workflow is:

1. At branch start, compare the touched plugin's manifest version to the target
   base branch, normally `origin/main`.
2. If the branch changes only `spx/`, coordination notes, repository instructions,
   tests, validation config, or local overlays, do not bump any plugin version.
3. If the branch changes a plugin distribution surface, choose the semantic
   version bump for the whole PR: MINOR for new items or major functional
   changes; PATCH for everything else.
4. Commit the plugin changes and all manifest version updates together in the
   first commit that changes that plugin.
5. During review, keep that selected PR version unchanged. Follow-up commits fix
   code, docs, specs, and review feedback without incrementing the version again.
6. If review changes materially expand the PR from PATCH scope to MINOR scope
   (for example, adding a new skill or command), re-select the branch version
   once to the correct semantic target and keep that new version fixed for the
   rest of review.
7. When the PR merges, main receives the already-bumped version with no separate
   release commit.

If the branch is rebased or retargeted after main has already advanced the same
plugin version, re-evaluate the version against the new base as part of that base
sync. Do not bump merely because another review commit was added.

❌ **WRONG** — version bump is separated from the first plugin change:

```bash
git commit -m "refactor(skills): simplify descriptions"
git commit -m "chore: bump versions"
```

❌ **WRONG** — review feedback increments the already-selected PR version:

```bash
git commit -m "docs(plugin): refine skill guidance"      # bumps 0.4.2 → 0.4.3
git commit -m "docs(plugin): address review feedback"    # bumps 0.4.3 → 0.4.4
```

✅ **CORRECT** — first commit bumps once; review commits keep that version:

```bash
# 1. Make your changes to skills/commands/etc
# 2. Update every manifest for the changed plugin
# 3. Stage the plugin changes and manifest updates together
git add src/plugins/{plugin-name}/ dist/claude/{plugin-name}/ dist/codex/{plugin-name}/
git commit -m "docs({plugin-name}): refine skill guidance"

# Later review feedback edits do not bump again.
git add src/plugins/{plugin-name}/ dist/claude/{plugin-name}/ dist/codex/{plugin-name}/
git commit -m "docs({plugin-name}): address review feedback"
```

## Version Bump Examples

| Change                                  | Old   | New   | Reason                               |
| --------------------------------------- | ----- | ----- | ------------------------------------ |
| Add `/handoff` command                  | 0.2.0 | 0.3.0 | New command = MINOR                  |
| Add self-organizing handoff             | 0.3.0 | 0.4.0 | Major functional change = MINOR      |
| Fix typo in an installed skill          | 0.4.0 | 0.4.1 | Plugin-surface documentation patch   |
| Refactor pickup logic                   | 0.4.1 | 0.4.2 | Refactoring = PATCH                  |
| Improve error messages                  | 0.4.2 | 0.4.3 | Small enhancement = PATCH            |
| Add `/designing-frontend`               | 0.4.3 | 0.5.0 | New skill = MINOR                    |
| Add `spx/.../PLAN.md`                   | 0.4.3 | 0.4.3 | Coordination note, no plugin surface |
| Update `spx/.../ISSUES.md`              | 0.4.3 | 0.4.3 | Coordination note, no plugin surface |
| Edit `spx/43-python.enabler/python.md`  | 0.4.3 | 0.4.3 | Spec-only, no plugin surface         |
| Edit `spx/local/committing-changes.md`  | 0.4.3 | 0.4.3 | Local workflow overlay, no plugin    |
| Edit `AGENTS.md` without plugin changes | 0.4.3 | 0.4.3 | Product instruction, no plugin       |

## After Adding/Modifying Commands or Skills

1. **Make your changes** to skills, commands, templates, etc.
2. **Determine whether a plugin distribution surface changed.** If the change is
   confined to `spx/`, `AGENTS.md`, `spx/local/`, tests, validation config, or
   generated repository docs, do not bump a plugin version.
3. **When a plugin distribution surface changed, determine the branch-level
   version bump against the target base branch**: MINOR for new items or major
   functional changes; PATCH for everything else.
4. **Update plugin.json once, in the first plugin-distribution commit on the branch**:
   - `src/plugins/{plugin-name}/.claude-plugin/plugin.json`
   - `src/plugins/{plugin-name}/.codex-plugin/plugin.json` (when it exists)
5. **Update marketplace catalogs**:
   - When **adding a new plugin**: add an entry to **both** `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex). `just check` fails if either catalog is missing the plugin.
   - When **changing a description**: update `.claude-plugin/marketplace.json` only (Codex catalog has no description field).
6. **Regenerate derived files**: Run `just build-skills` so `dist/claude/` and `dist/codex/` match the authored source.
7. **Document changes**: Update `AGENTS.md` and generated docs when adding new commands/skills to the catalog-facing surfaces.
8. **Update bootstrapping template**: If the change affects skill structure, commands, or conventions that new projects inherit, update `src/plugins/spec-tree/skills/bootstrapping/templates/spx-claude.md`
9. **Stage and commit the plugin distribution change and manifest bump together** in ONE commit:

   ```bash
   git add src/plugins/{plugin-name}/ dist/claude/{plugin-name}/ dist/codex/{plugin-name}/ src/plugins/{plugin-name}/.claude-plugin/plugin.json
   git commit -m "type(scope): your changes including version bump"
   ```

   If `.codex-plugin/plugin.json` exists for that plugin, include it in the same
   commit. For later review commits on the same PR, do not change the manifest
   version again.

Run `just check` before committing. The pre-commit hook also validates, but catching errors earlier is faster.
