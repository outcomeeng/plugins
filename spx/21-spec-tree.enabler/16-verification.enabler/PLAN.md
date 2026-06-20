# PLAN: Verification run-journal migration

## Why

`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` replaces the prior shared-architecture decision (universal thread-store persistence, an end-of-run JSON result, and the verdict toolchain) with the append-only run-journal contract: a run is one event journal that is its sole source of truth, every surface is a projection rendered from the journal, and the skill emits through one backend-neutral channel that binds the backend — a local run-journal file or a hosted pull-request comment — at the edge. The journal and its backends are owned by the `spx` CLI's local state store and its run-journal verbs. This node's children and the entangled auditing decision still declare the superseded stack; truth flows down, so align them to the new contract.

## Gate status — UNBLOCKED (the `spx` run-journal verbs are published)

The earlier note that this migration was "gated on unpublished `spx` CLI run-journal verbs" is **stale**. The `spx` CLI now exposes the audit run-journal channel, and it is available per the published-capability rule (`AGENTS.md` "Depend on an `spx` CLI capability only after it is PUBLISHED and the floor is advanced"): installed `spx 0.5.6` = `REQUIRED_SPX_VERSION` floor `0.5.6` (`outcomeeng/validation/spx_version.py`) = CI pin `SPX_VERSION 0.5.6` (`.github/workflows/check.yml`). The marketplace skills can bind the backend-neutral channel now.

**The channel (`spx audit`, the audit-side run journal):**

| Verb       | Signature                                                                                           | Contract role                      |
| ---------- | --------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `init`     | `--branch <name> --head-sha <sha> --json` → prints run-file path                                    | open the journal for a branch/head |
| `progress` | `--run-file <path> --step <step> --message <text> --json`                                           | append one lifecycle event         |
| `close`    | `--run-file <path> --status <approved\|rejected\|failed\|interrupted> --verdict-path <path> --json` | seal with a terminal verdict       |
| `status`   | `--branch <name> --json`                                                                            | latest projection for a branch     |
| `list`     | `--branch <name> --json`                                                                            | list run state for a branch        |

The fixed `--step` enum is `changeset-determined`, `diff-analyzed`, `additional-file-inspected`, `verdict-created`, `files-passed-format-check`, `done`. `close --verdict-path` attaches rendered verdict evidence — so verdict *rendering* survives as a projection even as the journal (init/progress/close) becomes the source of truth; this is the key nuance for downstream item (1). A `review`-side channel (`spx review …`) is the reviewing analogue; confirm its verbs with `spx review --help` before migrating `review-changes`.

## Downstream work (lower layers now lag the ADR) — sequenced

Truth flows down from `13-run-journal.adr.md`. Each item below is a node-level change with its own audit gate; sequence them so a superseded surface is never left half-migrated. **`/contextualize` each target node before editing it.**

1. **Re-scope `15-verdict-toolchain.enabler` to a projection.** Today its `verdict.py` schema + `emit_verdict.py`/`read_verdict.py`/`aggregate_verdicts.py`/`pass_results.py` CLIs ARE the end-of-run single-result model. Under the journal contract the canonical run state is the event journal and every surface is a render. Do NOT prune wholesale: `spx audit close --verdict-path` still consumes a rendered verdict file, so the verdict schema + renderer survive as the *projection* the channel attaches. Re-scope the node's spec so the toolchain is declared as "the verdict projection a closed journal renders," not "the canonical run result." Sequence with `/refactor`; gate with `/audit-adr` on any decision text and `/audit-tests` on the surviving `verdict.py` tests.

2. **Decide `21-thread-store.enabler`'s fate.** Its CRUD-overwrite facade (`write` overwrites; `read`/`delete`/`list`) does not match the append/sequence/cursor/seal journal contract. `review-changes` persists through it today and works — leave reviewing intact until it migrates. Choose: (a) supersede thread-store with the `spx` run-journal channel and migrate `review-changes` onto `spx review`, or (b) reframe thread-store as one Appendable backend bound at the edge. Recommendation: (a) — the channel is the new source of truth; thread-store's branch-slug derivation already re-exports from `14-version-control.enabler/15-changeset-scope.enabler`, so nothing unique is lost. **Safety property the replacement MUST preserve:** the review-result head-identity gap tracked in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md` (a `review-result.json` keyed by branch slug alone, with no head/base OID, lets a reused-worktree or stale-branch read return the wrong diff's record) — whatever supersedes thread-store must key records by review-diff identity (head/base OID), not branch slug alone. Gate with `/audit-adr`/`/audit-tests`.

3. **Rework `spx/21-spec-tree.enabler/17-auditing.adr.md` onto the journal.** It still encodes the old machinery end to end: the `verdict.py` toolchain, the `.spx/audits/<lang>/<branch-slug>.md` orchestrator state + lockfile, the PR-comment-as-database recovery (`AUDIT_VERDICT_JSON_BEGIN` delimiter), and the four `/audit`-family wrapper agents that drive them. Realign: orchestrator state, CI state, and the PR comment all become journal + projections through the `spx audit` channel; the wrapper agents `init`/`progress`/`close` rather than persisting verdicts. **NOTE: this ADR was just edited (PR #275, the auditor collapse) to add the generic-auditor composition; preserve that composition content and layer the journal rework on top — do not revert the collapse.** Gate with `/align` then `/audit-adr`.

4. **Give the surviving wrapper agents the journal-conformant shape.** Per `13-run-journal.adr.md`: every wrapper agent declares `model: sonnet` or `model: inherit`, `tools: Bash, Read, Skill`, and `skills:` listing the skill. The collapse left `adr-auditor`/`test-evidence-auditor` at `tools: Read, Glob, Grep, Skill` (+ `pdr-auditor` at `Read, Glob, Grep`) — the pre-conformance shape. Moving them to `tools: Bash, Read, Skill` is coherent ONLY once the audit skills do their searching via `Bash`/the channel rather than the agent's `Glob`/`Grep`; sequence this AFTER item (3) so the skills and agents move together. The `/audit`-family agents (`auditor` etc.) already carry `Read, Bash, Glob, Grep, Skill` — reconcile their `tools` against the ADR's `Bash, Read, Skill` as part of this item (decide whether the ADR's wrapper-tool list admits `Glob`/`Grep` or mandates Bash-only search). Add the deterministic structural `[test]`s the `ISSUES.md` "machine-checkable assertions" item names (agent-file location, `tools:` field, `skills:` field) and retag those from `[audit]` to `[test]`.

5. **Re-home the verdict-vocabulary reference in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`.** Its in-slice-unresolved-work assertion cites `15-verdict-toolchain.enabler/verdict-toolchain.md` for the `REJECTED`/`UNKNOWN`/`FAIL`/`REJECT` tokens. When item (1) reframes the toolchain as a projection, update the merging assertion to cite the journal's terminal-event/projection vocabulary (`close --status approved|rejected|failed|interrupted`).

6. **Decide reviewing's result-delivery governance.** `spx/15-audit-result-delivery.pdr.md` decides observable result delivery for **audit** runs; `13-run-journal.adr.md` applies the journal contract to **both** agentic types, but no PDR declares reviewing's incremental-reveal behavior. Either broaden `15-audit-result-delivery.pdr.md` to cover both types, or author a separate reviewing-result-delivery decision. Record the choice when item (2) migrates reviewing.

`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` survives unchanged — the journal contract still derives branch, slug, base ref, and the changed-file set from it.

## Deferred

The verdict-terminology follow-up (align the overall-verdict token `REJECT` → `REJECTED` to the `verdict-toolchain.md` `Status` enum) is subsumed by item (1): when the journal's terminal event (`close --status`) and its projection define the result vocabulary, reconcile the `verdict.py` `Status`/`Severity` enums to the channel's `approved|rejected|failed|interrupted` terminal statuses in the same change.

## Pre-flight for the next session

1. `/understand`, then `/contextualize spx/21-spec-tree.enabler/16-verification.enabler`.
2. `spx audit --help` and `spx review --help` to confirm the live channel verbs (this plan captured `spx 0.5.6`).
3. Start with item (1) (`/refactor` the verdict-toolchain node to a projection) — it unblocks (3) and (4). Items are spec-leading: each aligns a lower layer to `13-run-journal.adr.md`, which already declares the end state in atemporal voice.
