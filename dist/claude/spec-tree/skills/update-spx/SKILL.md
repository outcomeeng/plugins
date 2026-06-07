---
name: update-spx
description: >-
  ALWAYS invoke this skill when updating, refreshing, or scaffolding a product's spx/CLAUDE.md from the installed spec-tree template. NEVER hand-edit spx/CLAUDE.md to a new template version without this skill.
allowed-tools: Bash, Read, AskUserQuestion
---

<objective>
Keep a product's spx-level directory guide current with the installed spec-tree template by rendering it from the template and the project's enabled-language list. The guide carries no substituted strings; its only per-product variation is the `languages` frontmatter list, which scopes the rendered guide to the project's languages. An update re-renders the new template with that list, so new template content arrives automatically and disabled-language blocks stay out. The deterministic parse, compare, and render logic lives in `scripts/update_spx.py`; this skill orchestrates file access, the language list, and the report.
</objective>

<context>
The canonical template is the single copy in the understanding skill at `${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md`. Its frontmatter `template_version` is the installed version; the guide carries its own `template_version` plus the `languages` list. The guide is stale when its version is numerically below the installed one, or when its recorded `languages` no longer match the project's languages in use.

The spx-level guide is `spx/CLAUDE.md`. Where `spx/CLAUDE.md` is a symlink to `spx/AGENTS.md`, reads and writes follow the link; in a repo that ships only `spx/AGENTS.md`, target that file. Resolve the actual guide path before reading or writing.

`/understanding` detects the project's languages and reports staleness once per session, and `/handoff` carries that marker into its persistence proposal. This skill applies the update.
</context>

<workflow>

1. **Resolve the paths.** Template: `${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md`. Guide: the product's spx-level guide (`spx/CLAUDE.md`, or `spx/AGENTS.md` where that is the real file), referred to below as `<guide>`.

2. **Determine the enabled languages.** Identify the languages the project uses — from `/understanding`'s detection, or by inspecting the project's spec-tree test files and enabled language plugins. When interactive and the set is unclear, confirm it with `AskUserQuestion`. This is the comma-separated `<languages>` used below. (Running non-interactively without a known set — the background `spx-updater` agent — leaves `<languages>` unavailable; see the `absent` and non-interactive notes below.)

3. **Detect status.** Run, passing the determined languages so the check catches a language drift as well as a version gap:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md" --product <guide> --languages <languages> --check
   ```

   The output is one of `current`, `stale`, or `absent`. `stale` covers both a `template_version` behind the installed template and a recorded-language set that differs from `<languages>`.

4. **Act on the status.**

   - **`current`** — report that the guide is up to date. Stop.
   - **`stale`** — re-render in place, scoped to the enabled languages:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md" --product <guide> --languages <languages> --write
     ```

     New template sections arrive, the guide is scoped to `<languages>`, and `template_version` is set to the installed version.
   - **`absent`** — scaffold with the same `--write` command. When running non-interactively without a known language set, omit `--languages`; the scaffold renders no language sections, and the report states the language list must be set.

5. **Report.** State the version transition and the enabled-language list the guide was scoped to (update or scaffold), or that the language list is pending (non-interactive scaffold).

</workflow>

<constraints>
- NEVER edit the deterministic parse, compare, or render logic here — it lives in `scripts/update_spx.py`, governed by the node's Guide Render Model ADR.
- NEVER hand-merge or section-diff the guide against the template — the guide is rendered from the template and the enabled-language list; re-render is the update mechanism.
- NEVER substitute a product-specific string into the guide — the guide carries only template content and language filtering; the only per-product variation is the `languages` list.
- The template has one home, the understanding skill's `templates/`. Read it through `${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md`; never copy it into this skill.

</constraints>

<success_criteria>

- The guide's `template_version` matches the installed template after an update.
- Enabled-language blocks render and disabled-language blocks are omitted, per the guide's `languages`.
- Sections newly introduced by the template propagate into the guide on update; the language selection is preserved or updated to the project's current languages.
- A product with no guide gets a scaffold scoped to the supplied languages, or no language sections (with the pending-language report) when run non-interactively.
- No deterministic logic is duplicated in this skill body.

</success_criteria>
