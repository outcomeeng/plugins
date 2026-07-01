---
name: update-spx
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree sections from the installed spec-tree template. NEVER hand-edit either managed section to a new template version without this skill.
allowed-tools: Bash(python3:*update_spx.py*), Read
---

<objective>
Both root harness guide files — `CLAUDE.md` and `AGENTS.md` — carry current managed Spec Tree sections rendered to the installed template version, language-filtered to the extensions the project's tests use and harness-filtered per file.
</objective>

<context>
The guide is a managed section in two root files because one repository is worked by both Claude Code and Codex, each harness reads its own root filename, and root instructions survive compaction. Both sections render from one template: the body is shared, the spans that differ by agent harness are authored as per-harness blocks rendered into each file, and the only per-product variation inside the section is the enabled-language list. Generation is deterministic and needs no agent judgment; the regenerate-and-diff gate keeps the sections current on every commit, and this skill is the manual trigger over the same generator. The parse, compare, filter, section replacement, and render logic lives in `${CLAUDE_SKILL_DIR}/scripts/update_spx.py`, governed by the node's Guide Render Model ADR.

The canonical template is the single copy in the understanding skill at `${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md`. Its frontmatter `template_version` is the installed version; each managed section carries its own `template_version` plus the `languages` list in metadata comments. A section is stale when its version is numerically below the installed one, or when its recorded `languages` differ from the languages the project's tests use. The enabled-language set is read deterministically from the test-file extensions under `spx/**/tests/` — no agent decides it.
</context>

<workflow>

1. **Resolve the paths.** Template: `${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md`. Repository root: the product's root directory, referred to below as `<repo-root>`; the generator writes managed sections into `<repo-root>/CLAUDE.md` and `<repo-root>/AGENTS.md` and removes the retired generated guide files under `<repo-root>/spx/` when present.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md" --repo-root <repo-root> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two root guide files. The enabled-language set is detected from `<repo-root>/spx/**/tests/` extensions; pass `--languages <csv>` only to override the detection.

3. **Act on the status.**

   - **`current`** — report that both guides are up to date. Stop.
   - **`stale` or `absent`** — regenerate both files:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md" --repo-root <repo-root> --write
     ```

     New template sections arrive, each root file preserves product-owned prose outside the managed markers, each managed section is scoped to the detected languages and its own harness, symlinked root guides are replaced by regular file copies, and obsolete `spx/` guide files are removed.

4. **Report.** State the version transition, detected enabled-language list, root guide files written, and whether obsolete `spx/` guides were removed.

</workflow>

<constraints>
- NEVER edit the deterministic parse, compare, filter, section replacement, or render logic here — it lives in `${CLAUDE_SKILL_DIR}/scripts/update_spx.py`, governed by the node's Guide Render Model ADR.
- NEVER write only one of the two root guide files — `CLAUDE.md` and `AGENTS.md` are updated together, and symlinked root guides are replaced by regular file copies.
- NEVER preserve retired generated guide files under `spx/` after regeneration — the root managed section is the canonical guide surface.
- NEVER hand-merge or section-diff a managed section against the template — re-render is the update mechanism.
- NEVER substitute a product-specific string into a managed section — the section carries template content, language filtering, and per-harness blocks only.
- The template has one home, the understanding skill's `templates/`. Read it through `${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md`; never copy it into this skill.
</constraints>

<success_criteria>

- Both root `CLAUDE.md` and root `AGENTS.md` exist and carry managed sections with the installed `template_version` after a regenerate.
- Enabled-language blocks render and disabled-language blocks are omitted, per the languages the project's tests use.
- Each managed section carries only its own harness's blocks; the other harness's blocks are dropped.
- Sections newly introduced by the template propagate into both guides on regenerate.
- Product-owned root guide content outside the managed markers is preserved.
- Root guide symlinks are replaced by regular file copies.
- Retired generated guide files under `spx/` are absent after regeneration.
- No deterministic logic is duplicated in this skill body.

</success_criteria>
