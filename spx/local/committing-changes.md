# Marketplace Commit Rules

This file is loaded by the `/committing-changes` skill when working in this repository. It contains rules specific to committing changes to the Outcome Engineering plugin marketplace.

## Version Management

Feature branches do not bump plugin versions. Plugin manifest versions stay equal
to the target base branch, normally `origin/main`, unless the user explicitly
asks for a release/version change.

When a dedicated release/version change is requested, plugins follow semantic
versioning: `MAJOR.MINOR.PATCH`

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

## Files to Update for an Explicit Release/Version Change

**Plugin manifest version** (update every manifest that exists for the plugin being released):

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

**CRITICAL: do not bump plugin manifest versions in ordinary feature branches.**

Only the version on the main branch matters. When a PR changes skills, commands,
templates, documentation, or implementation, keep every touched plugin manifest
at the same version as the target base branch, normally `origin/main`. Do not
increment versions to describe feature-branch commits or review rounds.

Only bump a plugin version when the user explicitly asks for a release/version
change or the repository is performing a dedicated release workflow. In that
case, make the version change on the release path against main and update every
manifest that exists for the released plugin.

❌ **WRONG** — feature PR includes a version-only commit:

```bash
git commit -m "refactor(skills): simplify descriptions"
git commit -m "chore: bump versions"
```

❌ **WRONG** — feature PR bundles an unnecessary version bump with docs/code:

```bash
git commit -m "refactor(skills): simplify descriptions and bump plugin version"
```

✅ **CORRECT** — feature PR leaves versions unchanged from main:

```bash
# 1. Make your changes to skills/commands/etc
# 2. Confirm touched plugin.json versions still match origin/main
# 3. Stage the actual feature changes
git add plugins/{plugin-name}/
git commit -m "refactor(skills): simplify descriptions"
```

For an explicit release/version request, keep the version bump atomic with the
release change and explain the requested release category in the commit message.

## Explicit Release/Version Examples

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
2. **Preserve manifest versions**: keep `plugin.json` versions equal to the target base branch unless the user explicitly requested a release/version change
3. **When an explicit release/version change was requested, update plugin.json** in the same working session:
   - `plugins/{plugin-name}/.claude-plugin/plugin.json`
   - `plugins/{plugin-name}/.codex-plugin/plugin.json` (when it exists)
4. **Update marketplace catalogs**:
   - When **adding a new plugin**: add an entry to **both** `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex). `just check` fails if either catalog is missing the plugin.
   - When **changing a description**: update `.claude-plugin/marketplace.json` only (Codex catalog has no description field).
5. **Document changes**: Update `CLAUDE.md` if adding new commands/skills to the plugin tables
6. **Update bootstrapping template**: If the change affects skill structure, commands, or conventions that new projects inherit, update `plugins/spec-tree/skills/bootstrapping/templates/spx-claude.md`
7. **Stage and commit the change set together**:

   ```bash
   git add plugins/{plugin-name}/ plugins/{plugin-name}/.claude-plugin/plugin.json
   git commit -m "type(scope): your changes"
   ```

   Include plugin manifests only when they were intentionally changed by an
   explicit release/version request.

Run `just check` before committing. The pre-commit hook also validates, but catching errors earlier is faster.
