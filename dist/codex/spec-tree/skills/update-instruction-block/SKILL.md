---
name: update-instruction-block
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree instruction surface from the installed spec-tree template, or reconciling a command slot that differs between the two files. NEVER hand-edit the router block to a new template version, or hand-edit a command slot to reconcile a cross-file difference, without this skill.
allowed-tools: Bash(python3:*instruction_block.py*), Bash(git log:*), Bash(git blame:*), Read
---

<objective>
Both root harness instruction files — `CLAUDE.md` and `AGENTS.md` — carry a current managed Spec Tree router block rendered to the installed template version, language-filtered to the extensions the project's tests use and harness-filtered per file, and every fixed command slot is present with a body identical across the two files.
</objective>

<context>
Each root file's managed surface is three region kinds, because one repository is worked by both Claude Code and Codex, each harness reads its own root filename, and root instructions survive compaction:

1. A generated **router block**, delimited by an opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker and a closing `<!-- /SPEC-TREE -->`. It carries the product-neutral WHEN-to-invoke routing; the body is shared, the spans that differ by agent harness render per file, and the only per-product variation inside it is the enabled-language list. The router is regenerated in full on every update.
2. Named **per-product command slots** over the fixed set `author`, `verify`, `gate`, `merge`, each delimited by `<!-- SPEC-TREE:{slot} -->` and `<!-- /SPEC-TREE:{slot} -->`. A slot holds this product's operational command for a spec-tree phase; its body is product-owned and preserved verbatim across a re-render. An absent slot fence is scaffolded with a placeholder; a slot filled in one file and empty or placeholder in the other is filled from the filled sibling. A slot's body is identical in both files.
3. The product's own **out-of-fence prose**, preserved verbatim.

Router generation and the mechanical slot cases are deterministic and need no agent judgment; the regenerate-and-diff gate keeps the surface current on every commit, and this skill is the manual trigger over the same generator. The parse, compare, filter, router replacement, slot-preservation, sibling-fill, and render logic lives in `${SKILL_DIR}/scripts/instruction_block.py`, the single home for that deterministic logic; this skill body carries no copy of it.

The one case the generator does not resolve is a slot filled with **different** bodies in the two files — a conflict. Choosing which body is current is git-recency judgment this skill makes; the generator only reports the conflict and applies the chosen body.

The canonical template is the single copy in the understanding skill at `${SKILL_DIR}/../understand/templates/instruction-block.md`. Its frontmatter `template_version` is the installed version; the router block records its own version and language list inline in its opening marker. A router block is stale when its version is numerically below the installed one, when its recorded `languages` differ from the languages the project's tests use, when it still carries a retired marker, when a fixed command slot's fence is missing from a root file, or when a command slot differs between the two files. The enabled-language set is read deterministically from the test-file extensions under `spx/**/tests/` — no agent decides it.
</context>

<workflow>

1. **Resolve the paths.** Template: `${SKILL_DIR}/../understand/templates/instruction-block.md`. Repository root: the product's root directory, referred to below as `<repo-root>`; the generator writes the router block and command slots into `<repo-root>/CLAUDE.md` and `<repo-root>/AGENTS.md` and removes the retired generated instruction files under `<repo-root>/spx/` when present.

2. **Detect status.** Run:

   ```bash
   python3 "${SKILL_DIR}/scripts/instruction_block.py" --template "${SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two root instruction files, and `stale` also when a fixed command slot's fence is missing from a root file or a command slot differs between them. The enabled-language set is detected from `<repo-root>/spx/**/tests/` extensions; pass `--languages <csv>` only to override the detection. Any invocation that exits non-zero prints an actionable `error: …` line to stderr (missing or non-directory `--repo-root`, a symlink whose target escapes the repository, a template with no `template_version`) — report that exact line and stop rather than continuing.

3. **Act on the status.**

   - **`current`** — report that both instruction files are up to date. Stop.
   - **`stale` or `absent`** — regenerate both files:

     ```bash
     python3 "${SKILL_DIR}/scripts/instruction_block.py" --template "${SKILL_DIR}/../understand/templates/instruction-block.md" --repo-root <repo-root> --write
     ```

     The router block re-renders, each root file preserves product-owned prose and every command-slot body, absent slot fences are scaffolded with placeholders, an empty or placeholder slot is filled from its filled sibling, the router is scoped to the detected languages and its own harness, symlinked root instruction files are replaced by regular file copies, and obsolete `spx/` instruction files are removed. When only one of the two root instruction files exists, the missing file is first seeded with a copy of the existing file's product-owned prose before its router block is inserted.

4. **Reconcile a conflicting command slot when one remains.** After `--write`, re-run `--check`. When it still reports `stale`, a command slot carries a different body in each file — the one case the generator does not resolve. For each conflicting slot, decide which file's body is current by git recency, then apply it:

   - Determine the more recently changed side by scoping the recency signal to the conflicting slot's own fence-delimited lines, never the whole file — an unrelated later commit to either root file (a routing-prose fix, a different slot's edit) skews a whole-file timestamp and would pick the wrong side without ever surfacing as a tie. Read the **author date** of the slot's body line in both files — the author date, not the committer date, because this product's merge flow rebases and a rebase rewrites committer dates while preserving when the edit was authored. Locate the slot's body line range in each file independently: the two root files diverge in length — the router carries a Codex-only harness span, so a slot's absolute line numbers sit lower in `CLAUDE.md` than in `AGENTS.md` — so a line range read from one file must never be reused against the other. Bound each file's body by its own `<!-- SPEC-TREE:{slot} -->` and `<!-- /SPEC-TREE:{slot} -->` fence, then read the author date of those lines. `git blame` over `CLAUDE.md`'s own body lines, and again over `AGENTS.md`'s own body lines, reports that author date directly; equivalently `git log -1 --format=%aI -L <start>,<end>:<file>` with each file's own `<start>,<end>` restricts the log to that slot's history in that file and prints the same field (`%aI` is the author date; never `%cI`, the committer date). The file whose slot body was authored later wins. If the two dates tie, or the evidence is contradictory, stop and ask the operator which body is current rather than guessing — a wrong pick silently overwrites a valid command, and the post-write check only confirms the two files now match, not that the correct side won.
   - Apply the winning body to both files:

     ```bash
     python3 "${SKILL_DIR}/scripts/instruction_block.py" --repo-root <repo-root> --template "${SKILL_DIR}/../understand/templates/instruction-block.md" --fill-slot <slot> --from <claude|codex>
     ```

     `--from claude` fills both files from `CLAUDE.md`'s slot body; `--from codex` fills both from `AGENTS.md`'s. The write is deterministic; only the `--from` choice is git-recency judgment.

5. **Verify, then report.** Re-run the Step 2 `--check` command; it must now print `current` — this closing check confirms the write landed, the router block is at the installed version, and no command slot differs between the two files. The root instruction files are git-tracked, so an unexpected change stays recoverable through the product's own version control before commit. Then report the version transition, detected enabled-language list, root instruction files written, any command slot reconciled and the `--from` side chosen, and whether obsolete `spx/` instruction files were removed.

</workflow>

<constraints>
- NEVER edit the deterministic parse, compare, filter, router replacement, slot-preservation, sibling-fill, or render logic here — it lives in `${SKILL_DIR}/scripts/instruction_block.py`, the single home for that logic.
- NEVER write only one of the two root instruction files — `CLAUDE.md` and `AGENTS.md` are updated together, and symlinked root instruction files are replaced by regular file copies.
- NEVER preserve retired generated instruction files under `spx/` after regeneration — the root managed surface is the canonical instruction surface.
- NEVER hand-merge or block-diff a router block against the template — re-render is the update mechanism.
- NEVER substitute a product-specific string into the router block — the block carries template content, language filtering, and per-harness spans only; per-product commands live in the preserved command slots.
- NEVER hand-edit a command slot's body to reconcile a conflict — decide the `--from` side by git recency and let `--fill-slot` apply it.
- NEVER copy the template into this skill — it has one home, the understanding skill's `templates/`, read through `${SKILL_DIR}/../understand/templates/instruction-block.md`.
</constraints>

<success_criteria>

- Both root `CLAUDE.md` and root `AGENTS.md` exist and carry a router block with the installed `template_version` after a regenerate.
- Enabled-language blocks render and disabled-language blocks are omitted, per the languages the project's tests use.
- Each router block carries only its own harness's blocks; the other harness's blocks are dropped.
- Sections newly introduced by the template propagate into both router blocks on regenerate.
- Every fixed command slot fence is present in both files, and each slot's body is identical across them.
- A command slot conflict is reconciled by git-recency judgment applied through `--fill-slot --from`, never a hand-edit.
- Product-owned root instruction-file content outside every fence is preserved.
- Root instruction-file symlinks are replaced by regular file copies.
- Retired generated instruction files under `spx/` are absent after regeneration.
- No deterministic logic is duplicated in this skill body.

</success_criteria>
