---
name: update-spx
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's two spx-level guide files (spx/CLAUDE.md and spx/AGENTS.md) from the installed spec-tree template. NEVER hand-edit either guide file to a new template version without this skill.
allowed-tools: Bash(python3:*), Read
---

<objective>
Both spx-level directory guides — `spx/CLAUDE.md` and `spx/AGENTS.md` — regenerated to the installed template version, language-filtered to the extensions the project's tests use and runtime-filtered per file.
</objective>

<context>
The guide is two generated files because one repository is worked by both Claude Code and Codex and each reads its own filename. Both render from one template: the body is shared, the spans that differ by agent runtime are authored as per-runtime blocks rendered into each file, and the only per-product variation is the enabled-language list. Generation is deterministic and needs no agent judgment; the regenerate-and-diff gate keeps the guides current on every commit, and this skill is the manual trigger over the same generator. The parse, compare, filter, and render logic lives in `scripts/update_spx.py`, governed by the node's Guide Render Model ADR.

The canonical template is the single copy in the understanding skill at `${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md`. Its frontmatter `template_version` is the installed version; each guide carries its own `template_version` plus the `languages` list. A guide is stale when its version is numerically below the installed one, or when its recorded `languages` differ from the languages the project's tests use. The enabled-language set is read deterministically from the test-file extensions under `spx/**/tests/` — no agent decides it.
</context>

<workflow>

1. **Resolve the paths.** Template: `${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md`. Guide directory: the product's `spx/` directory, referred to below as `<spx-dir>`; the generator writes `<spx-dir>/CLAUDE.md` and `<spx-dir>/AGENTS.md`.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md" --spx-dir <spx-dir> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two guide files. The enabled-language set is detected from `<spx-dir>/**/tests/` extensions; pass `--languages <csv>` only to override the detection.

3. **Act on the status.**

   - **`current`** — report that both guides are up to date. Stop.
   - **`stale` or `absent`** — regenerate both files:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md" --spx-dir <spx-dir> --write
     ```

     New template sections arrive, each file is scoped to the detected languages and its own runtime, and `template_version` is set to the installed version.

4. **Report.** State the version transition and the detected enabled-language list both guides were scoped to.

</workflow>

<constraints>
- NEVER edit the deterministic parse, compare, filter, or render logic here — it lives in `scripts/update_spx.py`, governed by the node's Guide Render Model ADR.
- NEVER write only one of the two guide files — `spx/CLAUDE.md` and `spx/AGENTS.md` are generated together, and neither is a symlink to the other.
- NEVER hand-merge or section-diff a guide against the template — re-render is the update mechanism.
- NEVER substitute a product-specific string into a guide — the guide carries template content, language filtering, and per-runtime blocks only.
- The template has one home, the understanding skill's `templates/`. Read it through `${CLAUDE_SKILL_DIR}/../understand/templates/spx-claude.md`; never copy it into this skill.
</constraints>

<success_criteria>

- Both `spx/CLAUDE.md` and `spx/AGENTS.md` exist and carry the installed `template_version` after a regenerate.
- Enabled-language blocks render and disabled-language blocks are omitted, per the languages the project's tests use.
- Each guide carries only its own runtime's blocks; the other runtime's blocks are dropped.
- Sections newly introduced by the template propagate into both guides on regenerate.
- No deterministic logic is duplicated in this skill body.

</success_criteria>
