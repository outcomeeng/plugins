# Marketplace Commit Rules

This file is loaded by the `/committing-changes` skill when working in this repository. It contains rules specific to committing changes to the Outcome Engineering plugin marketplace.

## Version Management

Plugin version bumps happen at branch start, not at merge time. The first commit
that changes a plugin on a new branch bumps that plugin's manifests relative to
the target base branch, normally `origin/main`. That version then stays fixed for
the entire PR phase.

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
- ✅ Documentation improvements
- ✅ Small enhancements to existing features
- ✅ Performance optimizations
- ✅ Internal implementation changes
- 🎯 **Use liberally** — when in doubt, use PATCH

## Files to Update When Bumping Version

**Plugin manifest version** (update every manifest that exists for the plugin you changed):

```bash
plugins/{plugin-name}/.claude-plugin/plugin.json
plugins/{plugin-name}/.codex-plugin/plugin.json  # if it exists
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

**CRITICAL: bump once in the first plugin-changing commit on a branch, then do
not bump again during PR review.**

Only the version that will land on main matters. The correct workflow is:

1. At branch start, compare the touched plugin's manifest version to the target
   base branch, normally `origin/main`.
2. Choose the semantic version bump for the whole PR: MINOR for new items or
   major functional changes; PATCH for everything else.
3. Commit the plugin changes and all manifest version updates together in the
   first commit that changes that plugin.
4. During review, keep that selected PR version unchanged. Follow-up commits fix
   code, docs, specs, and review feedback without incrementing the version again.
5. If review changes materially expand the PR from PATCH scope to MINOR scope
   (for example, adding a new skill or command), re-select the branch version
   once to the correct semantic target and keep that new version fixed for the
   rest of review.
6. When the PR merges, main receives the already-bumped version with no separate
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
git commit -m "docs(typescript): refine test guidance"      # bumps 0.18.10 → 0.18.11
git commit -m "docs(typescript): address review feedback"   # bumps 0.18.11 → 0.18.12
```

✅ **CORRECT** — first commit bumps once; review commits keep that version:

```bash
# 1. Make your changes to skills/commands/etc
# 2. Update every manifest for the changed plugin
# 3. Stage the plugin changes and manifest updates together
git add plugins/{plugin-name}/
git commit -m "docs({plugin-name}): refine skill guidance"

# Later review feedback edits do not bump again.
git add plugins/{plugin-name}/
git commit -m "docs({plugin-name}): address review feedback"
```

## Version Bump Examples

| Change                      | Old   | New   | Reason                          |
| --------------------------- | ----- | ----- | ------------------------------- |
| Add `/handoff` command      | 0.2.0 | 0.3.0 | New command = MINOR             |
| Add self-organizing handoff | 0.3.0 | 0.4.0 | Major functional change = MINOR |
| Fix typo in handoff.md      | 0.4.0 | 0.4.1 | Documentation fix = PATCH       |
| Refactor pickup logic       | 0.4.1 | 0.4.2 | Refactoring = PATCH             |
| Improve error messages      | 0.4.2 | 0.4.3 | Small enhancement = PATCH       |
| Add `/designing-frontend`   | 0.4.3 | 0.5.0 | New skill = MINOR               |

## After Adding/Modifying Commands or Skills

1. **Make your changes** to skills, commands, templates, etc.
2. **Determine the branch-level version bump against the target base branch**: MINOR for new items or major functional changes; PATCH for everything else
3. **Update plugin.json once, in the first plugin-changing commit on the branch**:
   - `plugins/{plugin-name}/.claude-plugin/plugin.json`
   - `plugins/{plugin-name}/.codex-plugin/plugin.json` (when it exists)
4. **Update marketplace catalogs**:
   - When **adding a new plugin**: add an entry to **both** `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex). `just check` fails if either catalog is missing the plugin.
   - When **changing a description**: update `.claude-plugin/marketplace.json` only (Codex catalog has no description field).
5. **Document changes**: Update `CLAUDE.md` if adding new commands/skills to the plugin tables
6. **Update bootstrapping template**: If the change affects skill structure, commands, or conventions that new projects inherit, update `plugins/spec-tree/skills/bootstrapping/templates/spx-claude.md`
7. **Stage and commit EVERYTHING together** in ONE commit:

   ```bash
   git add plugins/{plugin-name}/ plugins/{plugin-name}/.claude-plugin/plugin.json
   git commit -m "type(scope): your changes including version bump"
   ```

   If `.codex-plugin/plugin.json` exists for that plugin, include it in the same
   commit. For later review commits on the same PR, do not change the manifest
   version again.

Run `just check` before committing. The pre-commit hook also validates, but catching errors earlier is faster.
