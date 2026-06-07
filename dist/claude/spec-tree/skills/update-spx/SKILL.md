---
name: update-spx
description: >-
  ALWAYS invoke this skill when updating, refreshing, or scaffolding a product's spx/CLAUDE.md from the installed spec-tree template. NEVER hand-edit spx/CLAUDE.md to a new template version without this skill.
allowed-tools: Bash, Read, AskUserQuestion
---

<objective>
Keep a product's spx-level directory guide current with the installed spec-tree template by rendering it from the template and the guide's declared customization config — the product name and the enabled-language list in the guide's frontmatter. An update re-renders the new template with that config, so new template content arrives automatically and disabled-language blocks stay out, while the product name and language selection are preserved. The deterministic parse, compare, and render logic lives in `scripts/update_spx.py`; this skill orchestrates file access, the scaffold prompt, and the report.
</objective>

<context>
The canonical template is the single copy in the understanding skill at `${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md`. Its frontmatter `template_version` is the installed version; the guide carries its own `template_version` plus `product_name` and `languages`. The product is stale when its version is numerically below the installed one.

The spx-level guide is `spx/CLAUDE.md`. Where `spx/CLAUDE.md` is a symlink to `spx/AGENTS.md`, reads and writes follow the link; in a repo that ships only `spx/AGENTS.md`, target that file. Resolve the actual guide path before reading or writing.

`/understanding` reports staleness once per session and `/handoff` carries that marker into its persistence proposal. This skill applies the update.
</context>

<workflow>

1. **Resolve the paths.** Template: `${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md`. Guide: the product's spx-level guide (`spx/CLAUDE.md`, or `spx/AGENTS.md` where that is the real file), referred to below as `<guide>`.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md" --product <guide> --check
   ```

   The output is one of `current`, `stale`, or `absent`.

3. **Act on the status.**

   - **`current`** — report that the guide is up to date. Stop.
   - **`stale`** — re-render in place; the helper reads the guide's existing `product_name` and `languages` and re-renders the new template with them:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md" --product <guide> --write
     ```

     New template sections arrive, disabled-language blocks stay out, the product name and language selection are preserved, and `template_version` is set to the installed version.
   - **`absent`** — scaffold. When interactive, ask the user for the product name and the enabled languages with `AskUserQuestion`, then render with them:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md" --product <guide> --name "<product name>" --languages <comma-separated-languages> --write
     ```

     When running non-interactively — the `spx-updater` agent in the background — omit `--name`/`--languages`; the scaffold leaves the `{product-name}` placeholder and no enabled languages, and the report states that the product name and language list must be set.

4. **Report.** State the version transition and that the product name and language selection were preserved (update), or the scaffold and the pending product-name and language fill.

</workflow>

<constraints>
- NEVER edit the deterministic parse, compare, or render logic here — it lives in `scripts/update_spx.py`, governed by the node's Guide Render Model ADR.
- NEVER hand-merge or section-diff the guide against the template — the guide is rendered from the template plus its declared config; re-render is the update mechanism.
- The customization surface is the guide's frontmatter config (`product_name`, `languages`); a re-render reflects only the template and that config, so unmodeled hand-prose edits to the guide body do not survive.
- The template has one home, the understanding skill's `templates/`. Read it through `${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md`; never copy it into this skill.

</constraints>

<success_criteria>

- The guide's `template_version` matches the installed template after an update.
- Enabled-language blocks render and disabled-language blocks are omitted, per the guide's `languages`.
- Sections newly introduced by the template propagate into the guide on update; the product name and language selection are preserved.
- A product with no guide gets a scaffold with the product name and languages set when interactive, or the placeholder when not.
- No deterministic logic is duplicated in this skill body.

</success_criteria>
