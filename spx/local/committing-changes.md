# Marketplace Commit Rules

This file is loaded by the `/committing-changes` skill when working in this repository. It contains rules specific to committing changes to the Outcome Engineering plugin marketplace.

## Version Management

All plugins follow semantic versioning: `MAJOR.MINOR.PATCH`

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

**CRITICAL: Version bumps must be in the SAME commit as the changes that warrant them.**

❌ **WRONG** — separate commits:

```bash
git commit -m "refactor(skills): simplify descriptions"
git commit -m "chore: bump versions"
```

✅ **CORRECT** — single atomic commit:

```bash
# 1. Make your changes to skills/commands/etc
# 2. Update version numbers in the relevant plugin.json files
# 3. Stage everything together
git add plugins/{plugin-name}/ plugins/*/.claude-plugin/plugin.json
# 4. Create ONE commit with both the changes and version bumps
git commit -m "refactor(skills): simplify descriptions

- Simplified descriptions from formal jargon to natural language
- Patch version bump"
```

Only create a separate version bump commit when bumping WITHOUT any code/doc changes (rare).

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
2. **Determine version bump type**: MINOR for new items or major functional changes; PATCH for everything else
3. **Update plugin.json** in the same working session:
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

   If `.codex-plugin/plugin.json` exists for that plugin, include it in the same commit.

Run `just check` before committing. The pre-commit hook also validates, but catching errors earlier is faster.
