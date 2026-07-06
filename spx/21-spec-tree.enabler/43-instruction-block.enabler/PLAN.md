# Plan: Instruction Block Redesign — validator + shared regions

Captured from a design session. This is the agreed shape to record in
`21-render-model.adr.md`, then flow down to the node spec, tests, and generator.
It is coordination, not spec truth — reconcile against the ADR before acting.

## Why

The current render model treats the rendered `CLAUDE.md` / `AGENTS.md` as its own
database: it renders product commands into fenced slots, then parses them back out
and reconciles them across two files. That parser (parse/set/ensure-slot-fences,
reconcile, sibling-fill, `--fill-slot`, fence-line anchoring, whitespace compare)
is the entire recurring-defect surface. PR #408 deepens it. The redesign inverts
the model so the fragile parser does not exist.

## The three content kinds in each root file

1. **Our block** — generated, per-harness. **Always at the very top.** Carries a
   concrete instruction to read the entire file (Codex especially, which otherwise
   won't). Regenerated deterministically; a re-render overwrites any hand-edit.
2. **`shared` regions** — spans kept byte-identical across both files. The dominant
   content, because in almost all repos the two files are identical.
   - Syntax: `<!-- SPEC-TREE:shared {name} -->` … `<!-- /SPEC-TREE:shared {name} -->`,
     present in both files with the same name; bodies kept identical.
   - On divergence: take the git-more-recently-edited side and write it whole into
     the other file. **Whole-side replacement only — never merge contents** (merging
     would need semantic judgment and could never become a hook).
3. **Independent content** — everything else. Per-file, free to differ, untouched.

## Operating discipline

- Read the **last committed git state**. Never touch uncommitted local changes —
  if the working tree is dirty for either file, stop and surface it.
- The script is a small validator (~20 lines, thoroughly fixture-tested). It
  **fixes the deterministic cases** (regenerate our block; sync a `shared` region by
  recency) and **refuses/escalates** anything that would require guessing, handing
  the exception to the `/update-instruction-block` skill for operator reconciliation.

## Bootstrap (first encounter, operator unaware of `shared`)

Make one minimal assumption, then stop:

- Insert our block at the top of each file.
- Compute the single biggest contiguous identical span across the two files. If it
  covers **> 80%** of the file, wrap that **one** span as a `shared` block. At most
  one block, never more.
- Otherwise wrap nothing — just insert our block; leave content alone.
- 80% is measured against the **larger** of the two files, so a one-sided addition
  cannot inflate the ratio.

After this first pass the operator sees `shared` in the file and owns granularity
from then on; the 80%/one-block rule never runs again.

## Five initial situations → target

Target: both files exist as regular files; our block at top of each (per-harness,
current); `shared` regions identical across both; everything else per-file.

1. **Only one file** — create the other identical; content is 100% identical → one
   `shared` block + our block at top. Deterministic.
2. **Symlink to the other** — convert both to real files (identical by
   construction) → one `shared` block + our block at top. Deterministic.
3. **Both identical, no block** — wrap content `shared`, insert our block. Deterministic.
4. **Both identical, old block** — replace old block with ours at top, wrap the rest
   `shared`. Deterministic.
5. **Both differ** — biggest contiguous identical span > 80% → our block + that one
   `shared` block, differing remainder left per-file; ≤ 80% → our block only.
   Deterministic to create; operator marks further `shared` later.

## Agent → deterministic trajectory

The skill is temporary scaffolding over rules that are mostly deterministic already.
Every "agent asks the operator" is a default not yet frozen (shared-region git-date
tie, one-sided `shared` fence, malformed fence). As those defaults stabilize, the
skill has nothing left to ask and the whole thing runs as a pre-commit hook and a
workflow with no agent. The whole-side-replacement rule (never semantic merge) is
what keeps every step hook-able.

## Supersedes

PR #408's command-slot machinery. The four commands (`author`, `verify`, `gate`,
`merge`) become **one `shared` section** — no slot type, no per-slot fences, no
sibling-fill, no `--fill-slot`, no cross-file reconcile heuristics. Deletes
`parse_command_slot`, `set_command_slot`, `ensure_slot_fences`,
`reconcile_command_slots`, `command_slot_conflicts`, `_find_fence_line`,
`_next_fence_index`, and the whole edge-case class.

Shrinks — but does not resolve — the standing ISSUES.md debt ("generator complexity
belongs in the SPX CLI"): deleting the command-slot parser reduces the surface, while the
shared-region reconcile and bootstrap keep enough complexity that ISSUES.md still tracks the
SPX-CLI migration as accepted debt.

## Implementation sequence

1. ~~Full `/contextualize` on this node, then rewrite `21-render-model.adr.md` to the
   model above.~~ **Done** — decision rewritten to router + shared-region + validator model.
2. ~~Update the node spec `instruction-block.md` assertions to match.~~ **Done** — slot
   assertions removed; shared-region, bootstrap, git-recency, dirty-tree assertions added.
3. Rewrite the four `l1` test suites for validator + bootstrap + shared-region sync.
   **Harness determination (via `/test`): all evidence is L1, no L2/L3, no mocks.** Three
   fixture flavors:
   - **A — content/string harness** (exists, `outcomeeng_testing/harnesses/instruction_block.py`):
     pure render/parse/staleness/span/prose over in-memory strings.
   - **B — filesystem topology harness** (exists, child node `54-instruction-block-harness.enabler`):
     tmp-dir topologies, symlink, `--template` rejection, `spx/` removal, bootstrap outcomes.
   - **C — git-backed fixture harness** (NEW, extends the child node): tmp `git init`, root
     files committed at controlled `GIT_*_DATE`, optional dirty working tree; drives the
     validator for recency reconciliation, whole-side replacement, recency-tie / one-sided
     escalation, dirty-tree no-op, and the drift gate's git-diff. Still L1.
4. Replace the generator with the validator + diff-and-wrap bootstrap + recency sync;
   delete the superseded parser. **Implementation done (compiles + smoke-tested):**
   - `src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py`
     rewritten — slot machinery deleted; added shared-region parse/set/diverged/one-sided,
     `biggest_identical_span` (difflib), `bootstrap_wrap`, `prepend_router_block` (router first),
     git edge (`_file_committed_timestamp`, `_working_tree_dirty`, `shared_recency_winner`,
     `reconcile_root_shared_regions`, `ReconcileReport`), `shared_region_drift`; CLI `--reconcile`
     added, `--fill-slot` removed. Recency is **per-file** (more-recently-committed side wins).
   - `outcomeeng/distribution/instruction_block.py` rewired: slot-conflict → shared-region drift.
   - `outcomeeng_testing/harnesses/instruction_block.py`: slot helpers removed; added
     `root_document_with_shared_region`, `write_both_root_files_with_shared_region`,
     `git_commit_at`; `SAMPLE_COMMAND_*` → `SHARED_REGION_*`.
   - **Remaining:** rewrite the four `l1` test suites against the new API; update the child
     harness node `54-instruction-block-harness.enabler` if needed; rewrite the
     `update-instruction-block` SKILL.md reconciliation workflow (skill-auditor gate) + the
     `instruction-block-updater` agent; rewrite the `understand/templates/instruction-block.md`
     template (drop slots, add read-whole-file instruction); `just build-skills` +
     `just build-instructions`; run node tests + ruff + mypy + check-skills to green.
   - Node stays OUT of `spx/EXCLUDE` — impl is built to green in this same changeset.
   - **Done.** All four `l1` suites + the child harness suites are green. Skill/agent/template
     rewritten; `just build-skills` + `just build-instructions` regenerated `dist/` and the root
     `CLAUDE.md`/`AGENTS.md`. The migrated root files carry the v0.23.0 router first and a
     byte-identical `SPEC-TREE:shared commands` region (dead slot fences removed) — dogfooding the
     new shared-region feature; `shared_region_drift` is empty.
   - **Gates run:** `develop:skill-auditor` and `develop:subagent-auditor` both pass on the
     rewritten `update-instruction-block` SKILL and `instruction-block-updater` agent, and
     `just check` is green. The change is committed on `work/instruction-block-render-model` as
     PR #412, driving `/merge`.
5. PR #408 (the superseded command-slot model) is closed as superseded by #412. The net
   `origin/main...HEAD` diff is the clean redesign (slot code added then removed nets out); only
   #408's commit history carried the slot commits.
