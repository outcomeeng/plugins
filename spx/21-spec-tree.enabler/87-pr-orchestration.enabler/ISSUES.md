# Issues: PR Orchestration Enabler

## 1. Eval implementation absent for PR orchestration scenarios (FOLLOW-UP)

`pr-orchestration.md` defines the eval coverage model for the argument,
existing-changeset, clean-tree interview, local lifecycle overlay, and existing
open-PR modes. The node does not carry co-located eval implementations for
those cases, so the scenario assertions still rely on `[review]` evidence.
`[review]` fits LLM-driven orchestration behavior that no finite automated test
falsifies, but it leaves a structural regression (for example the skill body
losing its `<mode_detection>` block) undetected by the deterministic gate. The
Conformance assertions carry `[test]`, so the node's `tests/` directory covers
packaging and static routing properties only.

The eval lane can add scenarios mirroring the sibling
`spx/21-spec-tree.enabler/76-merging.enabler` gate evals:

- Add an `evals/<mode-slug>/` directory per mode with `eval.toml`,
  `cases.jsonl`, and `prompt.md` exercising mode detection from arguments
  and git state, the local overlay route, the existing-open-PR route, and the
  interview-first proposal boundary.
- Run them in the canonical CI execution surface and commit `history.jsonl`.

Surfaced by the local `changes-reviewer` on `feat/pr-skill`.

## 2. `/pr` surfaces lifecycle depth (open-vs-merge) as a proposal choice — it must not (FOLLOW-UP)

`pr-orchestration.md` declares (Compliance) that `/pr` "present[s] a proposal through the runtime's structured-question tool and obtain[s] confirmation before any mutating action," and the skill body's Step 2 states the flow "runs through merge and closure **unless the overlay or user instruction says otherwise**." So drive-to-merge-and-close is **already** the documented default; only `spx/local/merging.md` (or an explicit instruction in the invocation) shortens it.

**Observed failure (2026-06-10).** The agent turned that default into a menu: the Step 2 proposal offered "open then stop for review" versus "open and drive to merge" as co-equal structured-question options. The operator had to pick, and chose "stop" only for an unrelated reason (rebooting the machine) — not a standing preference. The lifecycle **depth** is not a per-invocation decision; surfacing it as one re-litigates the overlay's job on every run and adds a confirmation the operator never asked for.

**My stance / required handling.**

- Tighten Step 2 and add a Compliance NEVER to `pr-orchestration.md`: the proposal confirms **what ships** — the change, the branch, the commit shape — and states the route as a **fact** ("drives commit → open → merge → close"). It NEVER presents merge-vs-stop depth as a structured-question option.
- The route is shortened only by (a) `spx/local/merging.md` declaring a different lifecycle, or (b) an explicit "stop at open" / "push only" instruction **in the invocation**. Absent those, `/pr` drives to merge.
- An explicit ship instruction in the invocation ("run it now", "ship it", "open the PR") **satisfies** the mandatory pre-mutation confirmation — do not re-prompt for a confirmation the operator already gave. The pause exists to confirm intent that is genuinely ambiguous, never to re-ask a stated one.
- Net effect: an operator who wants a human in the loop before merge sets the overlay or says so; the default never stops short of merge and never asks whether to. This is a refinement of the existing `present a proposal … before any mutating action` assertion, not a removal of it — the safety pause stays; only the depth-as-a-question anti-pattern is forbidden.

Surfaced during the `feat/two-severity-review-taxonomy` PR flow (2026-06-10), where the agent also asked the operator twice more to confirm an already-stated "run it now" — the same re-prompting anti-pattern this item forbids.
