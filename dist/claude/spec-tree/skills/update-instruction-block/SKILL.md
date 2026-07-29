---
name: update-instruction-block
description: >-
  ALWAYS invoke this skill when manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree instruction surface from the installed spec-tree template, or reconciling a `shared` region that differs between the two files. NEVER hand-edit the router block to a new template version, or hand-merge a `shared` region to reconcile a cross-file difference, without this skill.
argument-hint: "[--repo-root <path>] [--languages <csv>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py":*), Bash(git log:*), Read, Skill, Edit, AskUserQuestion
---

<objective>
Both root harness instruction files — `CLAUDE.md` and `AGENTS.md` — carry a current managed Spec Tree router block first in the file, and every `shared` region is byte-identical across the two files.
</objective>

<dependencies>

- Python 3.13 or 3.14 from a managed interpreter, with 3.13 as the floor. The bundled script uses `StrEnum`, which is available throughout that window.

</dependencies>

<context>
Each root file is three content kinds, because one repository is worked by both Claude Code and Codex, each harness reads its own root filename, and root instructions survive compaction:

1. A generated **router block**, always first, delimited by an opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker and a closing `<!-- /SPEC-TREE -->`. It carries the product-neutral WHEN-to-invoke routing and a concrete instruction to read the whole file; the body is shared, it renders at the installed template version, the spans that differ by agent harness render per file, and the only per-product variation inside it is the enabled-language list, filtered to the languages the project's own test-file extensions declare. The router is regenerated in full on every update; a re-render overwrites any hand-edit inside it. It carries no per-product command — a product's commands are content the reading agent reaches through the router's read-the-whole-file instruction.
2. **`shared` regions**, delimited by `<!-- SPEC-TREE:shared {name} -->` and `<!-- /SPEC-TREE:shared {name} -->`, present in both root files under the same name and kept byte-identical. On first encounter the bootstrap pass wraps at most one shared region — the biggest contiguous identical span, only when it exceeds 80% of the larger file. A diverged region is reconciled by whole-side replacement from the more-recently-committed file, never by merging the two bodies.

   First encounter can run one step before that span is measured. A root file whose body names the other root instruction file and stays within an absolute character bound is a **delegation candidate**. Both conditions are facts about the file.

   Whether such a body *also* carries an instruction of its own is a question about its prose, and no pattern over the text answers it. Adoption replaces a whole body, so a wrong reading costs that file its instructions. The generator therefore never decides it: it reports the candidate, holds the surface `stale`, and leaves every body standing.

   Only an operator answer naming the side both files take performs the adoption. After it, the two bodies are identical and the span wrap covers all of it. When both files name each other, both are reported and neither is adopted — no answer names a side, and neither body carries content the other could take.
3. **Independent content**, everything outside the router block and every shared region, free to differ per file and preserved verbatim.

Router generation and the recency reconcile are deterministic and need no agent judgment: the render is a pure string transformation, and the reconcile takes the git-more-recent side. The parse, filter, render, biggest-identical-span, shared-region, and recency logic lives in `${CLAUDE_SKILL_DIR}/scripts/instruction_block.py`, the single home for that deterministic logic; this skill body carries no copy of it. The cases the generator does not resolve — a recency tie, a region present in only one file, a malformed shared fence (unclosed, or one name opened twice), a body that may be nothing but a pointer at the other root file, or a root file with uncommitted changes — are the ambiguities this skill surfaces to the operator. An operator-selected tie break remains a whole-side replacement, never a content merge.

The canonical runtime template is the rendered, delimiter-free file bundled at `${CLAUDE_SKILL_DIR}/templates/instruction-block.md` in the installed plugin. Its authored source is build input and is never a direct generator input; the plugin build resolves its runtime macros before emitting this bundled file. The generator rejects any unresolved build-template delimiter before filtering, rendering, or writing. The runtime template's frontmatter `template_version` is the installed version; the router block records its own version and language list inline in its opening marker. A router block is stale when its version is numerically below the installed one, when its recorded `languages` differ from the languages the project's tests use, or when it still carries a retired marker; the surface is also stale when a `shared` region diverges between the two files, is present in only one, or is malformed (an open fence with no matching close, or one name opened twice), and while a reported delegation candidate is unresolved. The enabled-language set derives deterministically from the test-file extensions under `spx/**/tests/`.
</context>

<workflow>

1. **Resolve the paths and optional language override.** Template: `${CLAUDE_SKILL_DIR}/templates/instruction-block.md`. Parse the raw invocation string `$ARGUMENTS` exactly once as optional flags: `--repo-root <path>` and `--languages <csv>`, accepted in either order. Preserve each shell-quoted value as one value, including a repository path containing spaces. Reject positional tokens, unknown or duplicate flags, and a flag with no value; report `usage: /update-instruction-block [--repo-root <path>] [--languages <csv>]` and stop. Bind `<repo-root>` to the `--repo-root` value when supplied, otherwise to the current working directory. Bind `<languages-option>` to `--languages "<csv>"` when supplied, otherwise to an empty string so the generator detects languages from the project's test extensions. Because `CLAUDE.md` and `AGENTS.md` are worktree-sensitive, confirm `<repo-root>` is the repository worktree the operator means to update rather than assuming another checkout. Before mutation, read each root file that exists and retain its independent-content and `shared`-region bodies for the Step 5 comparison; record `missing` for either path that does not exist. The generator writes the router block into `<repo-root>/CLAUDE.md` and `<repo-root>/AGENTS.md`, bootstraps a `shared` region, and removes the retired generated instruction files under `<repo-root>/spx/` when present.

2. **Detect status.** Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --check
   ```

   The output is one of `current`, `stale`, or `absent` — the worst status across the two root instruction files, and `stale` also when a `shared` region diverges between the two files, is present in only one, or is malformed (an open fence with no matching close, or one name opened twice), and while a reported delegation candidate is unresolved. The enabled-language set is detected from `<repo-root>/spx/**/tests/` extensions unless the optional `--languages` flag supplies the comma-separated override carried by `<languages-option>`. **GATE 1:** any invocation that exits non-zero prints an actionable `error: …` line to stderr (missing or non-directory `--repo-root`, a symlink whose target escapes the repository, a template with no `template_version`) — report that exact line and stop rather than continuing.

3. **Reconcile diverged `shared` regions first.** **GATE 2:** when Step 2 reported `current`, both instruction files are up to date — report and stop without writing. Otherwise run the reconcile exactly once before regenerating: it operates on committed git state, and its own deterministic replacements may dirty a root file before it reports another ambiguity. Never invoke it a second time after it writes `reconciled: ...` output or after applying an operator-selected edit. Run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --reconcile
   ```

   It takes the git-more-recently-committed side for each diverged region and prints `reconciled: {name}` for each it resolved by recency. It exits non-zero and prints every ambiguity it will not guess. Handle every reported ambiguity in one edit batch, never guessing.

   Every `ambiguous` and `malformed` report starts by reading both root files in full and deriving a recommendation from what they hold. Where a report turns on which side is newer — the recency tie, the one-sided region, and the malformed fence — that reading also inspects the region-touching history with `git log`. The delegating report never does: candidacy is decided from the file's current text alone, so no history can change its recommendation. Then use `AskUserQuestion` with three choices — the evidence-backed resolution first and labeled `(Recommended)`, the opposing resolution second, and `Pause and inspect` third. Apply only the selected resolution; never blend two region bodies. Each report below carries the same shape — what was *detected*, what the evidence *recommends* when it is inconclusive, and what *applying* the choice takes — so read only the report the reconcile named:

   - **`dirty: {file}`**
     - *Detected* — the file carries uncommitted working-tree changes, so the reconcile operates on committed state and touches nothing.
     - *Apply* — report that the operator must commit or set aside the working-tree edit, then re-run the reconcile. No choice is offered; there is nothing to decide until the tree is clean.
   - **`ambiguous (recency tie): {name}`**
     - *Detected* — recency cannot pick a side: the two files' regions carry an identical commit timestamp, or git cannot resolve a commit timestamp for the region's line range in either file.
     - *Recommend* — the side the surrounding independent content already agrees with.
     - *Apply* — rerun the reconcile with the winning side named, so the generator writes the region in the exact byte shape it emits everywhere else rather than reproducing that shape by hand: `python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --reconcile --from <claude|codex>`.
     - *Preconditions* — the rerun reads committed state and refuses a dirty root file, so when the first pass already resolved another diverged region by recency it left the root files dirty; commit those writes through `/commit-changes` first — never a raw `git commit`, which this skill grants no tool for — or the rerun reports `dirty: {file}` and applies nothing. And `--from` selects the named side for *every* diverged region in the pass, not only the tied one, so run it only when the operator's choice is correct for all of them; otherwise commit the recency-resolved regions first and rerun `--from` against the tie alone.
   - **`ambiguous (one-sided): {name}`**
     - *Detected* — a `shared` region is present in one file but not the other.
     - *Recommend* — preserve the existing region by adding the same complete fenced body to the file that lacks it.
     - *Apply* — with `Edit`; no generator flag seeds a region into the file missing its fence. The choice is fence-only: a reconcile never invents a region in a file that lacks its fence.
   - **`malformed: {name}`**
     - *Detected* — a `shared` fence is unclosed or duplicated, so the region's extent or identity is unknowable.
     - *Recommend* — inspect the nearest valid fences alongside the history and take the expected boundary when the evidence identifies one; where it does not, remove the stray fence and preserve its body as independent content.
     - *Apply* — with `Edit`; a malformed fence has no generator flag that repairs it. The closing `--check` stays `stale` until the selected repair resolves the fence.
   - **`ambiguous (delegating): {file}`**
     - *Detected* — the named file's body is small enough to be nothing but a pointer at the other root instruction file. Only reading it decides whether it is.
     - *Recommend* — read that body in full. If it does nothing but send the reader to the other file, adopt the other side's body. If it states anything of its own, however briefly, keep both bodies: adoption discards this one entirely.
     - *Apply an adopt choice* — rerun the write with the surviving side named: `python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --write --adopt <claude|codex>`.
     - *Apply a keep choice* — leave the bodies alone. The report recurs on every run until one body stops naming the other or grows past the bound; that recurrence is the safe resting state, not a failure.
     - *Refused when the named side is itself a pointer* — the expected shape when both files were reported, each naming the other. The rerun exits with `error: --adopt <harness> names a body that only points at the other root instruction file; no side carries content to adopt, so write the intended instructions into one file first`. Neither reading held content worth adopting, so no `--adopt` value succeeds while that holds — naming the opposite harness hits the same refusal, because the opposite body points back.
     - *Refused when the discarded side is not a pointer* — `error: --adopt <harness> would discard the body of <file>, which carries content of its own rather than a pointer at another root instruction file; adoption replaces a whole body, so no answer authorizes it`. `--adopt` applies only to the topology this report names; run outside one it would destroy a body no report ever offered up.
     - *After either refusal* — report the exact error line, leave both bodies standing, and wait for the operator to write the intended instructions into one file with `Edit` before rerunning the write.

   **GATE 3:** continue to Step 4 only after every listed ambiguity is resolved; an unresolved ambiguity never proceeds to a write. Do not rerun the plain `--reconcile`: its deterministic replacements and the selected edits are now uncommitted by design, and the closing `--check` verifies that every `shared` region is byte-identical. The `--reconcile --from <harness>` run the recency-tie branch names is not that rerun — it carries the operator's choice into the same pass and replaces git recency for the tied region.

4. **Regenerate both files.** With the committed `shared` regions reconciled, regenerate the router block for the `stale` or `absent` status:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --write
   ```

   The router block re-renders first in each file, each root file preserves its product-owned content and every `shared` region body, the router is scoped to the detected languages and its own harness, on first encounter the bootstrap pass wraps at most one `shared` region, symlinked root instruction files are replaced by regular file copies, and obsolete `spx/` instruction files are removed. When only one of the two root instruction files exists, the missing file is first seeded with a copy of the existing file's content before its router block is inserted.

5. **Verify, then report.** Re-run the Step 2 `--check` command; it must now print `current` — this closing check confirms the write landed, the router block is at the installed version, and no `shared` region differs between the two files. Read both complete resulting root files and classify the Step 1 state. When either snapshot already carried a valid `shared` region, confirm each existing file's independent content is byte-identical. On first encounter with no valid `shared` region, confirm the bootstrap mapping from Step 4 instead: at most one new region exists; when the biggest identical whole-line span exceeds 80% of the larger file, that exact span is the region body; at or below the threshold, no region is added; and every byte outside newly inserted fence lines remains in its original file and order. When one file was missing, confirm the seeded copies map the existing snapshot's product content into the same single shared body; when both were missing, confirm neither result gained independent content. When Step 3 reported a delegation candidate and the operator chose to adopt, confirm the write carried `--adopt`, the named body stands in both files, and the pointer survives in neither; when the operator chose to keep both bodies, or when both files were reported, confirm every Step 1 body survives verbatim and the report recurs — that recurrence is the resting state, not an unfinished step. Then confirm each `shared` body is byte-identical across both files, the opening markers record the effective enabled-language set — detected by default or supplied through `--languages` — and each router carries only its own harness spans. When a root instruction file is tracked, its prior content remains recoverable through the product's version control before commit; when it is newly created or untracked, report that state and preserve the file for operator inspection. Then report the version transition, effective enabled-language list, root instruction files written, any `shared` region reconciled and the side chosen, and whether obsolete `spx/` instruction files were removed.

</workflow>

<examples>

**Stale router regenerated.** Before, `CLAUDE.md` and `AGENTS.md` carry a router version lower than the installed template version and both files share `<!-- SPEC-TREE:shared commands -->`. The opening check prints `stale`, reconcile prints no ambiguity, write replaces both router blocks, and the closing check prints:

```text
current
```

Afterward, both files carry the installed router version, the `commands` region body is unchanged and byte-identical, and independent content remains in its original file.

**A pointer body waits for the operator.** Before, `AGENTS.md` carries the product's instructions under `# Widget Forge`, and `CLAUDE.md` carries the same heading and one line: `See [AGENTS.md](AGENTS.md) for build and test commands, architecture, packages, and testing conventions.` Neither file has a `shared` region, so the opening check prints `absent`. The reconcile reports:

```text
ambiguous (delegating): CLAUDE.md
```

Reading that body shows it sends the reader to `AGENTS.md` and states nothing else, so the recommendation is to adopt the `AGENTS.md` body. After the operator selects it, rerun the write with `--adopt codex`: the two bodies are then identical, the whole body becomes one `root` region under each harness's router, the pointer appears in neither file, and the closing check prints `current`. Had that line instead read `See [AGENTS.md](AGENTS.md) for commands and also run the extra credentialing step before deploys.`, the report would be identical — the body is the same size and still names the other file — and only reading it reveals the instruction that adoption would destroy. That is why the write never resolves this itself.

**An adopt answer outside a delegation is refused.** Before, `CLAUDE.md` carries the product's build and test commands under `# Widget Forge` and `AGENTS.md` carries a different body of its own under the same heading — two independent files, neither one a pointer at the other. No reconcile reported a delegating ambiguity here, because there is none. A caller nonetheless runs the write with `--adopt claude`, and it exits `2` with:

```text
error: --adopt claude would discard the body of AGENTS.md, which carries content of its own rather than a pointer at another root instruction file; adoption replaces a whole body, so no answer authorizes it
```

Afterward both files stand exactly as they were. Adoption replaces a whole body, so it is authorized only where a report named that body a pointer; applied here it would have destroyed the `AGENTS.md` instructions with a zero exit and no warning. Report the error and leave the surface alone — the two files are independent by design, which is a resting state, not drift.

**Recency tie requires one choice.** Before, the `commands` region differs between `CLAUDE.md` and `AGENTS.md`, and both region-touching commits have the same timestamp. Reconcile exits non-zero with:

```text
ambiguous (recency tie): commands
```

After the operator selects `claude`, commit whatever the first pass already resolved so the root files are clean, then carry the choice into the reconcile with `python3 "${CLAUDE_SKILL_DIR}/scripts/instruction_block.py" --template "${CLAUDE_SKILL_DIR}/templates/instruction-block.md" --repo-root <repo-root> <languages-option> --reconcile --from claude`, which prints `reconciled: commands` and writes the `CLAUDE.md` body whole into `AGENTS.md`. Run `--write` and the closing `--check`; no line from the prior `AGENTS.md` region is blended into the result.

Whole-side replacement is what that last sentence rules out. Given these two `commands` bodies:

```text
CLAUDE.md                           AGENTS.md
<!-- SPEC-TREE:shared commands -->  <!-- SPEC-TREE:shared commands -->
- build: make all                   - build: make release
- test: make check                  - lint: make lint
<!-- /SPEC-TREE:shared commands --> <!-- /SPEC-TREE:shared commands -->
```

the winning side's body replaces the losing side's entirely, so both files end with `- build: make all` and `- test: make check`. A merged body carrying `- build: make all`, `- test: make check`, and `- lint: make lint` is the blend this skill never produces — the losing side's `lint` line is dropped, not preserved.

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

- Running `--check` after Step 4 prints `current`, the reading under which both root files carry the installed-version router block first with no `shared`-region divergence between them.
- Re-rendering the installed template for the effective enabled-language set and the file's own harness reproduces that file's router block exactly — the diff against the written block is empty, so the block carries every applicable section including the read-the-whole-file instruction, the opening markers record that language set, and no span belonging to the other harness appears.
- The `--reconcile` stdout names every recency-selected whole-side replacement, its nonzero stderr names every tie, one-sided region, malformed fence, or dirty file, and the closing `--check` prints `current` only after no divergence remains.
- Diffing each file's Step 1 and Step 5 text outside the router and `shared`-region bounds returns empty, and the Step 5 classification for the observed topology holds against that diff. Successful `--write` followed by `--check` printing `current` confirms symlink replacement and retired `spx/` instruction-file removal.

</success_criteria>
