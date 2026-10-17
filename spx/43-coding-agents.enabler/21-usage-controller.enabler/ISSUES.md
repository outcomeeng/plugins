# ISSUES — usage controller

Known imperfections in the usage-controller node that no single changeset settles. Each entry names the file, the cited reference, the rule it strains, the evidence, the reason it is accepted, and the condition under which the entry closes.

## usage-controller.md:25 — prowl-adapter-access-path

Status: `accepted`. Resolved by outcomeeng/changes#476.

Line 25 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) states that the control-positions skill acts on panes only through the operation surface of [`spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`](spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md) by a `__file__`-relative import. [`spx/43-coding-agents.enabler/18-prowl-environment.enabler/15-prowl-adapter.adr.md`](spx/43-coding-agents.enabler/18-prowl-environment.enabler/15-prowl-adapter.adr.md), line 38, states: "ALWAYS: `/operate-prowl` owns all bundled-script access; composing skills invoke the capability through the runtime skill surface rather than manufacturing a cross-skill filesystem path ([audit])". The same tension is filed for the sibling nodes in [`spx/43-coding-agents.enabler/ISSUES.md`](spx/43-coding-agents.enabler/ISSUES.md) under the adapter decisions' bundled-script ownership lines, and the root decision [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) permits the same-plugin `__file__`-relative import.

**Finding.** DEBT [consistency] at `usage-controller.md:25`, raised in https://github.com/outcomeeng/plugins/pull/665#issuecomment-6232653590. Required: either phrase the access path as invoking `/operate-prowl` as a capability, consistent with the ADR text as committed, or make this assertion depend explicitly on outcomeeng/changes#476 resolving the ADR wording, so the eventual audit gate on the Prowl adapter decision does not reject the implementation on its face.

**Why accepted.** The Plugins Maintainer ruling (https://github.com/outcomeeng/changes/issues/416#issuecomment-6234943244) accepts the finding and keeps the record unchanged. The assertion states the root decision's permitted access path, and outcomeeng/changes#476 restates the adapter decisions' import statements to cite the root rule, which removes the contradiction at its source. The node spec text stays as the Change record states it.

**Settlement condition.** outcomeeng/changes#476 restates the Prowl adapter decision's bundled-script ownership line so that it agrees with the `__file__`-relative import this assertion states.

## usage-controller.md:14,21 — pass-overlap-exclusion

Status: `accepted`.

Lines 14 and 21 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) bound a pass at five minutes, schedule the next launchd firing thirty minutes later, and allow one pass on request. Neither assertion declares exclusion between a running pass and the next scheduled or on-request pass. The sibling [`spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md`](spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md), line 20, declares the established pattern for a launchd-scheduled worker: "excludes overlapping work", backed by `tests/test_lock.compliance.l1.py`.

**Impact**: two overlapping passes could issue conflicting compact, pause, resume, or stop actions against the same position from stale reads of its share and spend.

**Finding.** DEBT [consistency] at `usage-controller.md:14,21`, raised in https://github.com/outcomeeng/plugins/pull/665#issuecomment-6232653590. Required: add an explicit overlap-exclusion guarantee to the scheduled-pass or launchd-job assertion, matching the sibling consumption-control pattern.

**Why accepted.** The Plugins Maintainer ruling (https://github.com/outcomeeng/changes/issues/416#issuecomment-6234943244) accepts the finding and keeps the record unchanged. The node spec text stays as the Change record states it.

**Settlement condition.** The scheduled-pass or launchd-job assertion of the node declares that a running pass excludes the next scheduled and on-request pass, matching the consumption-control pattern.

## usage-controller.md:18 — stable-data-root-citation

Status: `accepted`.

Line 18 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) anchors the storage location of the position records to "the stable data root of `spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md`". [`spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md`](spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md) declares "stable versioned assets" and a detector-scoped "detector state root", and declares no "stable data root".

**Impact**: the assertion cites a concept its provider does not declare, so the audit gate that later checks the implementation against this assertion has no resolvable root to check.

**Finding.** DEBT [consistency] at `usage-controller.md:18`, raised in https://github.com/outcomeeng/plugins/pull/665#issuecomment-6235016647. Required: either point the assertion at wherever a general-purpose stable data root actually is declared (or have `consumption-control.md` declare one explicitly), or replace the citation with the concrete root `control-positions` itself owns, so the audit gate that will later check implementation against this assertion has a resolvable target.

**Why accepted.** The Maintainer ruling (https://github.com/outcomeeng/changes/issues/416#issuecomment-6235170743) accepts the finding. The node declares `malleability: spec`, and the root the records live under is settled when the controller is implemented or the node hardens. The node spec text stays as the Change record states it.

**Settlement condition.** The assertion names a root that `consumption-control.md` declares, or a root `control-positions` owns.

## usage-controller.md:19 — skip-list-title-key

Status: `accepted`.

Line 19 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) sets the configuration contract so that `control-positions.toml` sets the skip list by pane title or worktree path. Line 25 states the controller acts on panes only through the operation surface of [`spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`](spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md). That node, at line 37 (audit), states operator-target resolution never asks for a pane UUID and never selects by focus, position, or title. The sibling [`spx/43-coding-agents.enabler/21-agent-communication.enabler/agent-communication.md`](spx/43-coding-agents.enabler/21-agent-communication.enabler/agent-communication.md), line 51, declares the same NEVER, linked to `tests/test_agent_message.compliance.l1.py`.

**Impact**: a skip list keyed by pane title is a selection-by-title mechanism, the case the Prowl operation surface and its sibling forbid, so the audit gate that later checks the Prowl operation surface could reject the implementation.

**Finding.** DEBT [consistency] at `usage-controller.md:19`, raised in the review of the Change at https://github.com/outcomeeng/changes/issues/416. Required: either drop pane title as a skip-list key, since worktree path alone identifies a pane through the supported resolution path, or state in the assertion why title-based skipping is exempt from the subtree-wide NEVER.

**Why accepted.** The Plugins Maintainer accepted the finding by operator decision. The Author tracks it as a separate larger concern: it needs a ruling on whether the skip list keys on pane title or only on worktree path, which is a change to the node's assertion text that this Change does not make. The node spec text stays as the Change record states it.

**Settlement condition.** The assertion keys the skip list on worktree path alone, or states why title-based skipping is exempt from the subtree-wide NEVER.

## usage-controller.md:14-25 — assertion-count-decomposition

Status: `accepted`.

The node carries 12 assertion bullets, lines 14 through 25 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md). The decompose skill's structural-quality checklist (`src/plugins/spec-tree/skills/decompose/SKILL.md`, Step 11) requires that no node exceed about 7 assertions without a recursive-decomposition issue, and the router decomposes an existing node with more than 7 assertions.

**Impact**: the node mixes independent concerns (scheduling and overlap, compaction and pause and resume thresholds, stop and ceiling, configuration, durable records) in one spec, so each concern is judged, evidenced, and changed together.

**Finding.** DEBT [architecture] at `usage-controller.md`, raised in the review of the Change at https://github.com/outcomeeng/changes/issues/416. Required: either decompose the node along its concern lines, or record why the node stays whole above the guideline.

**Why accepted.** The Plugins Maintainer accepted the finding by operator decision. The Author tracks it as a separate larger concern: it needs a decomposition of the node along its concern lines, each child a change to the node's assertions that this Change does not make. The node stays whole until that decomposition runs.

**Settlement condition.** The node is decomposed along its concern lines into children that each hold about 7 assertions or fewer, or a recorded ruling states why the node stays whole.

## usage-controller.md:20,25 — parser-worktree-lookup-citation

Status: `accepted`.

Lines 20 and 25 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) state that the controller takes a position's tokens only from the parser of [`spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md`](spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md), identified by the pane's worktree, and that it reads token counts only through the consumption-control parser. [`spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md`](spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md) declares its measurement model over requests, sessions, models, and native parent/subagent relationships, and declares no parser entity and no worktree-keyed lookup. The words parser and worktree appear nowhere in that node's spec, its `ISSUES.md`, or its tests directory, and no decision record in that enabler directory supplies the term. The shipped `control-token-spend` skill likewise has no worktree-keyed query path in its scripts.

**Impact**: the assertions cite an entity and a lookup their provider does not declare, so the audit gate that later checks the controller's implementation against them has no resolvable target in the cited provider.

**Finding.** DEBT [consistency] at `usage-controller.md:20`, raised in https://github.com/outcomeeng/plugins/pull/665#issuecomment-6236110601. Required: either point the assertion at the identity axis `consumption-control.md` declares, such as the session resolved from a pane's worktree through the cwd or project identity its collection invocation uses, or have `consumption-control.md` declare the parser entity and its worktree-keyed lookup explicitly.

**Why accepted.** The Plugins Maintainer ruling in the Change at https://github.com/outcomeeng/changes/issues/416 accepts the finding on the same terms as the findings recorded above. The node declares `malleability: spec`, and the identity axis the controller reads through is settled when the controller is implemented or the node hardens. The node spec text stays as the Change record states it.

**Settlement condition.** The assertions point at the identity axis `consumption-control.md` declares, or `consumption-control.md` declares the parser entity and its worktree-keyed lookup.

## usage-controller.md — other-skill-compacts-prowl-position

Status: `accepted`.

The NEVER assertion of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) states that no shipped coding-agents skill other than `control-positions` instructs a position to compact another position whose pane Prowl hosts. The shipped `direct-positions` skill (`src/plugins/coding-agents/skills/direct-positions/SKILL.md`) carries a `compact <position>` row in its arguments table, an act step, and a controller-pass bullet in its passes. Each instructs `act --operation compact`, which reaches the pane through `operate-prowl` for any position whose environment is prowl, and the controller-pass bullet tells the reader to run act with `--operation compact` for each compact-recommended position. The `orchestrate-change` skill (`src/plugins/coding-agents/skills/orchestrate-change/SKILL.md`, Check step 3, first bullet) sends `/compact` when remaining context is at or below 10%, but only to herdr panes, so it does not strain the assertion.

**Impact**: a reader following `direct-positions` can compact a Prowl-hosted position from outside `control-positions`, so the controller is not the sole compacting actor for Prowl panes and the assertion does not hold of the shipped skills.

**Finding.** DEBT [consistency] at `src/plugins/coding-agents/skills/direct-positions/SKILL.md` (arguments table row `compact <position>`, act step, controller-pass bullet in passes) and `src/plugins/coding-agents/skills/orchestrate-change/SKILL.md` (Check step 3, first bullet), raised in assertion-audit run 2026-10-17_17-22-22-076-b5831a95edb6, ordinal 11, severity blocking, rule `other-skill-compacts-prowl-position`. Required: no shipped coding-agents skill other than `control-positions` instructs a position to compact another position whose pane Prowl hosts; `direct-positions` restricts its compact path to herdr panes or drops it for Prowl-hosted positions.

**Why accepted.** The Plugins Maintainer, relaying the operator's choice, accepts the finding as debt and keeps the assertion text and the skill text unchanged. The compaction path in `direct-positions` is removed together with the `direct-positions` skill once the controller job is installed and configured.

**Settlement condition.** Compaction leaves the `direct-positions` skill, the `position-direction` and `position-overrides` specs, and their tests once the controller job is installed and configured, through a Proposed Change under outcomeeng/changes#445.
