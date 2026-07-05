---
name: update-instruction-block
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree instruction surface from the installed spec-tree template, or reconciling a `shared` region that differs between the two files. NEVER hand-edit the router block to a new template version, or hand-merge a `shared` region to reconcile a cross-file difference, without this skill.
argument-hint: "[repo-root]"
allowed-tools: Bash(python3:*instruction_block.py*), Bash(git log:*), Read
---

<objective>
Both root harness instruction files — `CLAUDE.md` and `AGENTS.md` — carry a current managed Spec Tree router block, first in the file, rendered to the installed template version, language-filtered to the extensions the project's tests use and harness-filtered per file, and every `shared` region is byte-identical across the two files.
</objective>

<context>
Each root file is three content kinds, because one repository is worked by both Claude Code and Codex, each harness reads its own root filename, and root instructions survive compaction:

1. A generated **router block**, always first, delimited by an opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker and a closing `<!-- /SPEC-TREE -->`. It carries the product-neutral WHEN-to-invoke routing and a concrete instruction to read the whole file; the body is shared, the spans that differ by agent harness render per file, and the only per-product variation inside it is the enabled-language list. The router is regenerated in full on every update; a re-render overwrites any hand-edit inside it. It carries no per-product command — a product's commands are content the reading agent reaches through the router's read-the-whole-file instruction.
2. **`shared` regions**, delimited by `<!-- SPEC-TREE:shared {name} -->` and `<!-- /SPEC-TREE:shared {name} -->`, present in both root files under the same name and kept byte-identical. On first encounter the bootstrap pass wraps at most one shared region — the biggest contiguous identical span, only when it exceeds 80% of the larger file. A diverged region is reconciled by whole-side replacement from the more-recently-committed file, never by merging the two bodies.
3. **Independent content**, everything outside the router block and every shared region, free to differ per file and preserved verbatim.

Router generation and the recency reconcile are deterministic and need no agent judgment: the render is a pure string transformation, and the reconcile takes the git-more-recent side. The parse, filter, render, biggest-identical-span, shared-region, and recency logic lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, the single home for that deterministic logic; this skill body carries no copy of it. The cases the generator does not resolve — a recency tie, a region present in only one file, a malformed shared fence with no matching close, or a root file with uncommitted changes — are the ambiguities this skill surfaces to the operator, and applies the operator's tie break deterministically through `--reconcile --from`.

The canonical template is the single copy in the understanding skill at `${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md`. Its frontmatter `template_version` is the installed version; the router block records its own version and language list inline in its opening marker. A router block is stale when its version is numerically below the installed one, when its recorded `languages` differ from the languages the project's tests use, or when it still carries a retired marker; the surface is also stale when a `shared` region diverges between the two files, is present in only one, or is malformed (an open fence with no matching close). The enabled-language set is read deterministically from the test-file extensions under `spx/**/tests/` — no agent decides it.
</context>

<workflow>

1. **Resolve the paths.** Template: `${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md`. Repository root: the product's root directory, referred to below as `<repo-root>` — the current working directory unless the operator names a different product root; because `CLAUDE.md` and `AGENTS.md` are worktree-sensitive, confirm `<repo-root>` is the worktree the operator means to update rather than assuming the marketplace-source checkout. The generator writes the router block into `<repo-root>/CLAUDE.md` and `<repo-root>/AGENTS.md`, bootstraps a `shared` region, and removes the retired generated instruction files under `<repo-root>/spx/` when present.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two root instruction files, and `stale` also when a `shared` region diverges between the two files, is present in only one, or is malformed (an open fence with no matching close). The enabled-language set is detected from `<repo-root>/spx/**/tests/` extensions; pass `--languages <csv>` only to override the detection. Any invocation that exits non-zero prints an actionable `error: …` line to stderr (missing or non-directory `--repo-root`, a symlink whose target escapes the repository, a template with no `template_version`) — report that exact line and stop rather than continuing.

3. **Reconcile diverged `shared` regions first.** When Step 2 reported `current`, both instruction files are up to date — report and stop. Otherwise reconcile before regenerating: the reconcile operates on committed git state, so it runs before `--write` (Step 4) dirties the working tree — a write-then-reconcile order would leave the files dirty and make the reconcile refuse its own uncommitted output. Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --reconcile
   ```

   It takes the git-more-recently-committed side for each diverged region and prints `reconciled: {name}` for each it resolved by recency. It exits non-zero and prints an ambiguity to stderr for each case it will not guess. Handle each ambiguity, never guessing:

   - **`dirty: {file}`** — the file carries uncommitted working-tree changes, so the reconcile operates on committed state and touches nothing. Report that the operator must commit or set aside the working-tree edit, then re-run the reconcile.
   - **`ambiguous (recency tie): {name}`** — recency cannot pick a side: the two files' regions carry an identical commit timestamp, or git cannot resolve a commit timestamp for the region's line range in either file. Ask the operator which harness's body is current (inspect `git log` on each file for context), then apply their choice deterministically:

     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --reconcile --from <claude|codex>
     ```

     `--from claude` applies `CLAUDE.md`'s diverged region bodies to both files; `--from codex` applies `AGENTS.md`'s. The write is deterministic; only the `--from` choice is the operator's tie break.
   - **`ambiguous (one-sided): {name}`** — a `shared` region is present in one file but not the other. Report it and ask the operator whether the region should be added to the file that lacks it or removed from the file that has it; a reconcile never invents a region in the file that lacks its fence.
   - **`malformed: {name}`** — a `shared` open fence has no matching closing fence, so the region's extent is unknowable. Report it and ask the operator to repair the fence (add the missing close on its own line) or remove the stray open fence; the generator never guesses where a region ends, so the closing `--check` stays `stale` until the operator resolves it.

4. **Regenerate both files.** With the committed `shared` regions reconciled, regenerate the router block for the `stale` or `absent` status:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --write
   ```

   The router block re-renders first in each file, each root file preserves its product-owned content and every `shared` region body, the router is scoped to the detected languages and its own harness, on first encounter the bootstrap pass wraps at most one `shared` region, symlinked root instruction files are replaced by regular file copies, and obsolete `spx/` instruction files are removed. When only one of the two root instruction files exists, the missing file is first seeded with a copy of the existing file's content before its router block is inserted.

5. **Verify, then report.** Re-run the Step 2 `--check` command; it must now print `current` — this closing check confirms the write landed, the router block is at the installed version, and no `shared` region differs between the two files. The root instruction files are git-tracked, so an unexpected change stays recoverable through the product's own version control before commit. Then report the version transition, detected enabled-language list, root instruction files written, any `shared` region reconciled and the side chosen, and whether obsolete `spx/` instruction files were removed.

</workflow>

<constraints>
- NEVER edit the deterministic parse, filter, render, biggest-identical-span, shared-region, or recency logic here — it lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, the single home for that logic.
- NEVER write only one of the two root instruction files — `CLAUDE.md` and `AGENTS.md` are updated together, and symlinked root instruction files are replaced by regular file copies.
- NEVER preserve retired generated instruction files under `spx/` after regeneration — the root managed surface is the canonical instruction surface.
- NEVER hand-merge or block-diff a router block against the template — re-render is the update mechanism.
- NEVER substitute a product-specific string into the router block — the block carries template content, language filtering, per-harness spans, and the read-the-whole-file instruction only; a product's commands are content the reading agent reaches, not data the router resolves.
- NEVER merge the two bodies of a diverged `shared` region — the reconcile replaces the losing side's region whole from the winning side; a recency tie is the operator's `--from` choice, never a hand-blend.
- NEVER copy the template into this skill — it has one home, the understanding skill's `templates/`, read through `${CLAUDE_SKILL_DIR}/../understand/templates/instruction-block.md`.

</constraints>

<success_criteria>

- The closing `--check` prints `current`, confirming both root files carry the installed-version router block, first in the file, with byte-identical `shared` regions and no divergence between the two files.
- The rendered router carries a concrete read-the-whole-file instruction, renders only the enabled-language blocks the project's tests select and only its own harness's blocks, and a section a newer template introduces appears in both.
- A diverged `shared` region ends reconciled by whole-side replacement — git recency, or the operator's `--from` tie break — and a recency tie, a one-sided region, a malformed shared fence, or a dirty root file was surfaced to the operator rather than guessed.
- Product content outside the router block and every shared region is preserved, symlinked root files are replaced by regular copies, and retired `spx/` instruction files are absent.

</success_criteria>
