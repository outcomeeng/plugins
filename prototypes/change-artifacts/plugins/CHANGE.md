---
artifact: Change
status: draft
repository: outcomeeng/plugins
change_id: pending
branch: pending
depends_on:
  - repository: "@outcomeeng/spx"
    change_id: pending
---

# Change-backed Spec Tree coordination

## Intent

Adopt `Change` and `Baton` as the Spec Tree methodology's durable intent and cross-agent continuation model. Prohibit `PLAN.md`, rename session files (`spx session {handoff|pickup}`) to `Handoff`, and strip them of any content. While `ISSUES.md` remains a valid coordination note, it must meet strict format standards, allowing only verified product gaps and deviations, and derive verification from repository truth at an exact Git SHA.

This Change depends on the SPX Change that provides cross-worktree Change storage, atomic baton ownership, revival, archival lineage, and SHA-bound discovery for all five verification types. Adoption begins after that capability is published and the repository's required SPX version advances to the release containing it.

## Artifact boundaries

The methodology uses three coordination concepts with separate purposes:

| Artifact    | Purpose                                                                                      |
| ----------- | -------------------------------------------------------------------------------------------- |
| Change      | Operator-readable, signed, durable intent and lineage from initial prompt through production |
| Baton       | Machine-owned availability, ownership, next entry verb, and optional external state          |
| `ISSUES.md` | Verified current gaps or deviations from governing product truth                             |

Changes own durable intent and planning. Batons transfer responsibility. Runtime planning state exists only for the active session and disappears with it. Repository truth and SHA-bound verification determine the work required.

## Change-backed handoff

Every handoff belongs to exactly one Change and exists as that Change's `handoff/baton.json` only between agent sessions.

The baton contains roughly:

```json
{
  "schema_version": 1,
  "change_id": "019f...",
  "next_step": "/decompose",
  "transient_state": null
}
```

The baton contains no instructions, plans, copied decisions, copied specs, skill sequences, implementation prescriptions, or verification forecasts.

`transient_state` is omitted or `null` when repository and external state are sufficient. When present, it describes only external or ephemeral state such as an unavailable service, an external release dependency, or another condition that repository truth cannot derive. It references governing product truth when applicable.

## Finite next-step vocabulary

`next_step` contains exactly one top-level methodology entry verb from a finite, source-owned set.

Eligible verbs are methodology routers such as `/interview`, `/author`, `/decompose`, `/refactor`, `/align`, `/verify`, `/slice`, `/apply`, and `/merge`, subject to refinement of the final set.

The field rejects:

- multiple skills or an ordered sequence;
- arguments or prose;
- language-specific implementation or test skills;
- audit and reviewer agents;
- internal composition skills;
- lifecycle prerequisites that the selected router performs automatically;
- agent identifiers such as `spec-tree:test-evidence-auditor`.

Pickup loads current product context and current methodology before acting on the one entry verb. The active skill owns any composition and later routing. A handoff never predicts the internal skill order.

## Workflow and verification vocabulary

Methodology forecasts use only canonical categories:

| Concept              | Canonical vocabulary                                                                     |
| -------------------- | ---------------------------------------------------------------------------------------- |
| Direct routing       | Exact eligible skill invocation                                                          |
| Verification types   | `audit`, `validate`, `review`, `evaluate`, `test`                                        |
| Assertion evidence   | `[audit]`, `[eval]`, `[test]`                                                            |
| Delivery phases      | `VERIFY`, `PREVIEW`, `MERGE`, `DEPLOY`, `RELEASE`, `CLOSE`                               |
| Authorization points | `VERIFICATION_READINESS`, `MERGE_READINESS`, `DEPLOYMENT_READINESS`, `RELEASE_READINESS` |

The methodology does not invent umbrella workflow categories such as “testing workflow,” “evidence workflow,” “audit workflow,” “implementation workflow,” or “downstream gates.” Evidence names artifacts or results that back assertions. Implementation names changes to product artifacts. Skill ordering comes only from the active workflow's explicit route.

## PLAN.md prohibition

The methodology never creates or retains `PLAN.md` anywhere in a product tree.

Planning has two homes:

- durable planning that must survive an agent session lives in the Change;
- disposable execution planning for the active session lives in runtime state and disappears when the session ends.

The baton contains only the next eligible methodology entry verb and optional transient external state. `ISSUES.md` contains only verified gaps and deviations. Neither artifact carries a plan.

A deterministic validation rule rejects every `PLAN.md` path on every branch and in every tree state. Context loading and methodology skills never discover, read, create, update, reconcile, or remove plan notes during normal operation.

The prohibition begins after cross-worktree Change storage exists. Still-valid plan content migrates into Changes before all `PLAN.md` files are deleted. This ordering preserves durable pending intent without retaining a second planning surface.

## ISSUES.md policy

`ISSUES.md` contains verified current gaps and deviations from product truth. It carries no future plan, desired enhancement, unverified suspicion, general reminder, or stale continuation instruction.

Each issue records:

- governing decision or spec-node paths;
- the observed gap or deviation;
- the applicable verification type;
- the full subject Git SHA;
- the verification run token when one exists.

SHA-bound verification discovery determines whether an issue still holds. A resolved issue is removed before merge. An entry whose governing truth changes requires re-verification against the new subject SHA.

The exact issue schema, permissible prose, and evidence requirements remain refinement work.

## Handoff and pickup lifecycle

The current session lifecycle transitions to the Change baton protocol:

- creation establishes a Change and initial baton;
- pickup atomically acquires the baton;
- the current baton path names the owning agent session and PID;
- session end updates Change lineage and returns the baton to `handoff/baton.json`;
- a dead owner is revived by atomically moving the stale current baton;
- completion archives the Change and its full lineage.

Handoff and pickup skills become thin methodology surfaces over SPX Change commands. They do not maintain an independent instruction-bearing session schema.

## Verification and delivery

All five verification types are discoverable from the Change, baton, repository truth, and exact Git SHA. Methodology skills consume the deterministic SPX projection and execute only the work it reports as applicable and unsatisfied.

Verification records remain attached to their full subject SHA. A later source change makes prior SHA-bound evidence historical while preserving it in Change lineage.

Merge readiness additionally requires:

- deterministic validation reporting no `PLAN.md` anywhere in the product tree;
- every surviving `ISSUES.md` entry verified against the merge-ready SHA;
- the Change and branch identities matching the subject;
- the SPX verification projection reporting the applicable five-type state.

## Rollout

1. Publish the SPX Change and baton capability.
2. Advance the plugins repository's required SPX version.
3. Create Change-backed handoff and pickup behavior.
4. Migrate durable session content into Changes.
5. Migrate still-valid `PLAN.md` content into Changes and delete every `PLAN.md`.
6. Add deterministic validation rejecting `PLAN.md` on every branch and tree state.
7. Restrict `ISSUES.md` to SHA-backed verified gaps and deviations.
8. Consume deterministic five-type verification discovery from SPX.
9. Retire the instruction-bearing session format and its commands.

## Required outcomes

- Every continuation references exactly one operator-approved Change.
- Every handoff contains one eligible `next_step` and optional `transient_state` only.
- Current methodology determines composition after pickup.
- No `PLAN.md` exists anywhere in a product tree.
- Durable pending work survives as Change lineage.
- Every `ISSUES.md` entry is a verified current gap or deviation tied to a full Git SHA.
- All five verification types are discovered from SPX at the exact subject SHA.
- Methodology prose uses canonical routing, verification, evidence, phase, and gate vocabulary.
- Existing session and plan intent migrates without loss.

## Refinement boundary

The next refinement establishes:

- the governing product nodes and decisions;
- the final eligible `next_step` set;
- Change and baton command integration;
- handoff and pickup behavior during migration;
- `PLAN.md` migration and prohibition enforcement;
- the verified `ISSUES.md` schema;
- deterministic validation and merge predicates;
- generated instruction and plugin surfaces;
- session compatibility and retirement timing;
- operator review and sign-off points.

## Operator sign-off

- [ ] Intent approved
- [ ] Dependency on the SPX Change approved
- [ ] Refinement boundary approved
- [ ] Ready for node and decision mapping

## Lineage

### Initial

This draft consolidates the operator discussion that removes `PLAN.md` and instruction-bearing sessions in favor of operator-approved Changes, reduces handoff to one JSON baton, constrains routing and verification vocabulary, and reserves `ISSUES.md` for verified current deviations.
