---
name: update-instruction-block
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree instruction block from the installed spec-tree template. NEVER hand-edit either instruction block to a new template version without this skill.
allowed-tools: Bash(python3:*instruction_block.py*), Read
---

<objective>
Both root harness instruction files — `CLAUDE.md` and `AGENTS.md` — carry a current managed Spec Tree instruction block rendered to the installed template version, language-filtered to the extensions the project's tests use and harness-filtered per file.
</objective>

<context>
The instruction block is a managed block in two root files because one repository is worked by both Claude Code and Codex, each harness reads its own root filename, and root instructions survive compaction. Both blocks render from one template: the body is shared, the spans that differ by agent harness are authored as per-harness blocks rendered into each file, and the only per-product variation inside the block is the enabled-language list. Generation is deterministic and needs no agent judgment; the regenerate-and-diff gate keeps the blocks current on every commit, and this skill is the manual trigger over the same generator. The parse, compare, filter, block replacement, and render logic lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, governed by the node's Instruction Block Render Model ADR.

The canonical template is the single copy in the understanding skill at `${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md`. Its frontmatter `template_version` is the installed version; each instruction block carries its own `template_version` plus the `languages` list in metadata comments. A block is stale when its version is numerically below the installed one, or when its recorded `languages` differ from the languages the project's tests use. The enabled-language set is read deterministically from the test-file extensions under `spx/**/tests/` — no agent decides it.
</context>

<workflow>

1. **Resolve the paths.** Template: `${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md`. Repository root: the product's root directory, referred to below as `<repo-root>`; the generator writes instruction blocks into `<repo-root>/CLAUDE.md` and `<repo-root>/AGENTS.md` and removes the retired generated instruction files under `<repo-root>/spx/` when present.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two root instruction files. The enabled-language set is detected from `<repo-root>/spx/**/tests/` extensions; pass `--languages <csv>` only to override the detection. Any invocation that exits non-zero prints an actionable `error: …` line to stderr (missing or non-directory `--repo-root`, a symlink whose target escapes the repository, a template with no `template_version`) — report that exact line and stop rather than continuing.

3. **Act on the status.**

   - **`current`** — report that both instruction files are up to date. Stop.
   - **`stale` or `absent`** — regenerate both files:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --write
     ```

     New template blocks arrive, each root file preserves product-owned prose outside the block markers, each instruction block is scoped to the detected languages and its own harness, symlinked root instruction files are replaced by regular file copies, and obsolete `spx/` instruction files are removed. When only one of the two root instruction files exists, the missing file is first seeded with a copy of the existing file's product-owned prose before its instruction block is inserted — the `absent` case can therefore create a file whose prose is copied from its sibling.

4. **Verify, then report.** Re-run the Step 2 `--check` command; it must now print `current` — this closing check, over the same granted script, confirms the write landed and the block is at the installed version. The root instruction files are git-tracked, so an unexpected change stays recoverable through the product's own version control before commit. Then report the version transition, detected enabled-language list, root instruction files written, and whether obsolete `spx/` instruction files were removed.

</workflow>

<constraints>
- NEVER edit the deterministic parse, compare, filter, block replacement, or render logic here — it lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, governed by the node's Instruction Block Render Model ADR.
- NEVER write only one of the two root instruction files — `CLAUDE.md` and `AGENTS.md` are updated together, and symlinked root instruction files are replaced by regular file copies.
- NEVER preserve retired generated instruction files under `spx/` after regeneration — the root instruction block is the canonical instruction surface.
- NEVER hand-merge or block-diff an instruction block against the template — re-render is the update mechanism.
- NEVER substitute a product-specific string into an instruction block — the block carries template content, language filtering, and per-harness spans only.
- The template has one home, the understanding skill's `templates/`. Read it through `${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md`; never copy it into this skill.
</constraints>

<success_criteria>

- Both root `CLAUDE.md` and root `AGENTS.md` exist and carry an instruction block with the installed `template_version` after a regenerate.
- Enabled-language blocks render and disabled-language blocks are omitted, per the languages the project's tests use.
- Each instruction block carries only its own harness's blocks; the other harness's blocks are dropped.
- Blocks newly introduced by the template propagate into both instruction files on regenerate.
- Product-owned root instruction-file content outside the block markers is preserved.
- Root instruction-file symlinks are replaced by regular file copies.
- Retired generated instruction files under `spx/` are absent after regeneration.
- No deterministic logic is duplicated in this skill body.

</success_criteria>
