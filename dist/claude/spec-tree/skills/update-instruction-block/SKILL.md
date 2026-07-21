---
name: update-instruction-block
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree instruction surface from the installed spec-tree template, or reconciling a `shared` region that differs between the two files. NEVER hand-edit the router block to a new template version, or hand-merge a `shared` region to reconcile a cross-file difference, without this skill.
argument-hint: "[--repo-root <path>] [--languages <csv>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py":*), Bash(git log:*), Read, Edit, AskUserQuestion
---

<objective>
Both root harness instruction files — `CLAUDE.md` and `AGENTS.md` — carry a current managed Spec Tree router block, first in the file, rendered to the installed template version, language-filtered to the extensions the project's tests use and harness-filtered per file, and every `shared` region is byte-identical across the two files.
</objective>

<dependencies>

- Python 3.13 or 3.14 from a managed interpreter, matching the marketplace's shipped-script support window. The bundled script uses `StrEnum`, which is available throughout that declared window.

</dependencies>

<context>
Each root file is three content kinds, because one repository is worked by both Claude Code and Codex, each harness reads its own root filename, and root instructions survive compaction:

1. A generated **router block**, always first, delimited by an opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker and a closing `<!-- /SPEC-TREE -->`. It carries the product-neutral WHEN-to-invoke routing and a concrete instruction to read the whole file; the body is shared, the spans that differ by agent harness render per file, and the only per-product variation inside it is the enabled-language list. The router is regenerated in full on every update; a re-render overwrites any hand-edit inside it. It carries no per-product command — a product's commands are content the reading agent reaches through the router's read-the-whole-file instruction.
2. **`shared` regions**, delimited by `<!-- SPEC-TREE:shared {name} -->` and `<!-- /SPEC-TREE:shared {name} -->`, present in both root files under the same name and kept byte-identical. On first encounter the bootstrap pass wraps at most one shared region — the biggest contiguous identical span, only when it exceeds 80% of the larger file. A diverged region is reconciled by whole-side replacement from the more-recently-committed file, never by merging the two bodies.
3. **Independent content**, everything outside the router block and every shared region, free to differ per file and preserved verbatim.

Router generation and the recency reconcile are deterministic and need no agent judgment: the render is a pure string transformation, and the reconcile takes the git-more-recent side. The parse, filter, render, biggest-identical-span, shared-region, and recency logic lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, the single home for that deterministic logic; this skill body carries no copy of it. The cases the generator does not resolve — a recency tie, a region present in only one file, a malformed shared fence with no matching close, or a root file with uncommitted changes — are the ambiguities this skill surfaces to the operator. An operator-selected tie break remains a whole-side replacement, never a content merge.

The canonical runtime template is the rendered, delimiter-free file bundled at `${CLAUDE_SKILL_DIR}/templates/instruction-block.md` in the installed plugin. Its authored source is build input and is never a direct generator input; the plugin build resolves its runtime macros before emitting this bundled file. The generator rejects any unresolved build-template delimiter before filtering, rendering, or writing. The runtime template's frontmatter `template_version` is the installed version; the router block records its own version and language list inline in its opening marker. A router block is stale when its version is numerically below the installed one, when its recorded `languages` differ from the languages the project's tests use, or when it still carries a retired marker; the surface is also stale when a `shared` region diverges between the two files, is present in only one, or is malformed (an open fence with no matching close). The enabled-language set derives deterministically from the test-file extensions under `spx/**/tests/`.
</context>

<workflow>

1. **Resolve the paths and optional language override.** Template: `${CLAUDE_SKILL_DIR}/templates/instruction-block.md`. Parse the raw invocation string `$ARGUMENTS` exactly once as optional flags: `--repo-root <path>` and `--languages <csv>`, accepted in either order. Preserve each shell-quoted value as one value, including a repository path containing spaces. Reject positional tokens, unknown or duplicate flags, and a flag with no value; report `usage: /update-instruction-block [--repo-root <path>] [--languages <csv>]` and stop. Bind `<repo-root>` to the `--repo-root` value when supplied, otherwise to the current working directory. Bind `<languages-option>` to `--languages "<csv>"` when supplied, otherwise to an empty string so the generator detects languages from the project's test extensions. Because `CLAUDE.md` and `AGENTS.md` are worktree-sensitive, confirm `<repo-root>` is the repository worktree the operator means to update rather than assuming another checkout. Before mutation, read each root file that exists and retain its independent-content and `shared`-region bodies for the Step 5 comparison; record `missing` for either path that does not exist. The generator writes the router block into `<repo-root>/CLAUDE.md` and `<repo-root>/AGENTS.md`, bootstraps a `shared` region, and removes the retired generated instruction files under `<repo-root>/spx/` when present.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two root instruction files, and `stale` also when a `shared` region diverges between the two files, is present in only one, or is malformed (an open fence with no matching close). The enabled-language set is detected from `<repo-root>/spx/**/tests/` extensions unless the optional `--languages` flag supplies the comma-separated override carried by `<languages-option>`. Any invocation that exits non-zero prints an actionable `error: …` line to stderr (missing or non-directory `--repo-root`, a symlink whose target escapes the repository, a template with no `template_version`) — report that exact line and stop rather than continuing.

3. **Reconcile diverged `shared` regions first.** When Step 2 reported `current`, both instruction files are up to date — report and stop. Otherwise run the reconcile exactly once before regenerating: it operates on committed git state, and its own deterministic replacements may dirty a root file before it reports another ambiguity. Never invoke it a second time after it writes `reconciled: ...` output or after applying an operator-selected edit. Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --reconcile
   ```

   It takes the git-more-recently-committed side for each diverged region and prints `reconciled: {name}` for each it resolved by recency. It exits non-zero and prints every ambiguity it will not guess. Handle every reported ambiguity in one edit batch, never guessing:

   - **`dirty: {file}`** — the file carries uncommitted working-tree changes, so the reconcile operates on committed state and touches nothing. Report that the operator must commit or set aside the working-tree edit, then re-run the reconcile.
   - **`ambiguous (recency tie): {name}`** — recency cannot pick a side: the two files' regions carry an identical commit timestamp, or git cannot resolve a commit timestamp for the region's line range in either file. Read both complete region bodies and inspect `git log` on each file, then ask which harness's body is current. Replace the losing region body whole with the selected side through the runtime's file-editing tool. The edit is deterministic after the choice; never blend the bodies.
   - **`ambiguous (one-sided): {name}`** — a `shared` region is present in one file but not the other. Read both root files and inspect the region-touching history with `git log` before asking. Derive a recommendation from the surrounding content and history; when the evidence is inconclusive, recommend preserving the existing region by adding the same complete fenced body to the file that lacks it. Use `AskUserQuestion` with three choices: the evidence-backed reconciliation first and labeled `(Recommended)`, the opposing add-or-remove reconciliation second, and `Pause and inspect` third. After the operator chooses a reconciliation, apply that fence-only choice without blending region bodies. A reconcile never invents a region in the file that lacks its fence without this operator choice.
   - **`malformed: {name}`** — a `shared` fence is unclosed or duplicated, so the region's extent or identity is unknowable. Read both root files and inspect the nearest valid fences plus the region-touching history with `git log`. Derive the expected boundary when the evidence identifies one; otherwise recommend removing the stray fence while preserving its body as independent content. Use `AskUserQuestion` with three choices: the evidence-backed fence repair first and labeled `(Recommended)`, the alternative add-close-or-remove-fence repair second, and `Pause and inspect` third. Apply only the selected fence repair, never a content blend. The closing `--check` stays `stale` until this operator-selected repair resolves the malformed fence.

   After every listed ambiguity is resolved, continue directly to Step 4. Do not rerun `--reconcile`: its deterministic replacements and the selected edits are now uncommitted by design, and the closing `--check` verifies that every `shared` region is byte-identical.

4. **Regenerate both files.** With the committed `shared` regions reconciled, regenerate the router block for the `stale` or `absent` status:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --write
   ```

   The router block re-renders first in each file, each root file preserves its product-owned content and every `shared` region body, the router is scoped to the detected languages and its own harness, on first encounter the bootstrap pass wraps at most one `shared` region, symlinked root instruction files are replaced by regular file copies, and obsolete `spx/` instruction files are removed. When only one of the two root instruction files exists, the missing file is first seeded with a copy of the existing file's content before its router block is inserted.

5. **Verify, then report.** Re-run the Step 2 `--check` command; it must now print `current` — this closing check confirms the write landed, the router block is at the installed version, and no `shared` region differs between the two files. Read both complete resulting root files and classify the Step 1 state. When either snapshot already carried a valid `shared` region, confirm each existing file's independent content is byte-identical. On first encounter with no valid `shared` region, confirm the bootstrap mapping from Step 4 instead: at most one new region exists; when the biggest identical whole-line span exceeds 80% of the larger file, that exact span is the region body; at or below the threshold, no region is added; and every byte outside newly inserted fence lines remains in its original file and order. When one file was missing, confirm the seeded copies map the existing snapshot's product content into the same single shared body; when both were missing, confirm neither result gained independent content. Then confirm each `shared` body is byte-identical across both files, the opening markers record the effective enabled-language set — detected by default or supplied through `--languages` — and each router carries only its own harness spans. When a root instruction file is tracked, its prior content remains recoverable through the product's version control before commit; when it is newly created or untracked, report that state and preserve the file for operator inspection. Then report the version transition, effective enabled-language list, root instruction files written, any `shared` region reconciled and the side chosen, and whether obsolete `spx/` instruction files were removed.

</workflow>

<examples>

**Stale router regenerated.** Before, `CLAUDE.md` and `AGENTS.md` carry a router version lower than the installed template version and both files share `<!-- SPEC-TREE:shared commands -->`. The opening check prints `stale`, reconcile prints no ambiguity, write replaces both router blocks, and the closing check prints:

```text
current
```

Afterward, both files carry the installed router version, the `commands` region body is unchanged and byte-identical, and independent content remains in its original file.

**Recency tie requires one choice.** Before, the `commands` region differs between `CLAUDE.md` and `AGENTS.md`, and both region-touching commits have the same timestamp. Reconcile exits non-zero with:

```text
ambiguous (recency tie): commands
```

After the operator selects `claude`, replace the complete `AGENTS.md` region body with the `CLAUDE.md` body through the runtime's file-editing tool. Run `--write` and the closing `--check`; no line from the prior `AGENTS.md` region is blended into the result.

</examples>

<failure_modes>

**Claude updated a different checkout instead of the requested repository worktree.** The root argument was described but never bound, so an explicit product path could be ignored. Bind `<repo-root>` from the `--repo-root` flag and confirm that path before the first check.

**Claude wrote before reconciling.** The write dirtied both root files, then reconcile refused to choose from uncommitted state. Reconcile the committed regions first, then run `--write`.

**Claude kept the instruction-block template under `understand`.** The updater depended on another skill's bundled path, which is unavailable through its own `${CLAUDE_SKILL_DIR}`. Keep the template in this skill's `templates/` directory and invoke every script and template through this skill's local token.

</failure_modes>

<constraints>
- NEVER edit the deterministic parse, filter, render, biggest-identical-span, shared-region, or recency logic here — it lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, the single home for that logic.
- NEVER write only one of the two root instruction files — `CLAUDE.md` and `AGENTS.md` are updated together, and symlinked root instruction files are replaced by regular file copies.
- NEVER preserve retired generated instruction files under `spx/` after regeneration — the root managed surface is the canonical instruction surface.
- NEVER hand-merge or block-diff a router block against the template — re-render is the update mechanism.
- NEVER substitute a product-specific string into the router block — the block carries template content, language filtering, per-harness spans, and the read-the-whole-file instruction only; a product's commands are content the reading agent reaches, not data the router resolves.
- NEVER merge the two bodies of a diverged `shared` region — the reconcile or operator-selected edit replaces the losing side's region whole from the winning side; a recency tie is resolved through one whole-side replacement, never a hand-blend.
- NEVER copy the template into another skill — `${CLAUDE_SKILL_DIR}/templates/instruction-block.md` is its single owned location.
- NEVER pass an authored build template carrying unresolved delimiters to the generator — runtime generation consumes the rendered, delimiter-free template bundled with the installed skill, and rejects unresolved delimiters before writing.

</constraints>

<success_criteria>

- The closing `--check` prints `current`, confirming both root files carry the installed-version router block, first in the file, with byte-identical `shared` regions and no divergence between the two files.
- The Step 5 complete-file comparison confirms each router contains every applicable section from the rendered installed template, including the read-the-whole-file instruction, the opening markers record the effective enabled-language set, and each root file carries only its own harness spans.
- The `--reconcile` stdout names every recency-selected whole-side replacement, its nonzero stderr names every tie, one-sided region, malformed fence, or dirty file, and the closing `--check` prints `current` only after no divergence remains.
- The Step 1/Step 5 comparison confirms established managed surfaces preserve independent content byte-for-byte; first-encounter surfaces wrap at most the exact biggest identical whole-line span above the 80% threshold while preserving every unfenced byte in its original file and order; a one-file start maps the recorded seed content into the same shared body; and a two-file-absent start creates no independent content. Successful `--write` followed by `--check` printing `current` confirms symlink replacement and retired `spx/` instruction-file removal.

</success_criteria>
