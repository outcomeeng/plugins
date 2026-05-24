# Known issues — decisions enabler

## Local review gate has no backing spec assertion

The `/opening-pr` skill (`plugins/spec-tree/skills/opening-pr/SKILL.md`) declares a mandatory local review gate as Step 3 of its pre-flight, but the policy lives only in skill prose. There is no spec assertion in `spx/` that declares the gate as durable product truth, and no ADR/PDR that records the rationale (stricter-than-remote, FOLLOW-UP deferred only on scope-widening).

**Source:** changes-reviewer finding F-001 on PR for `feat/local-review-gate` (2026-05-24). The governing principle: skill behavior changes that constitute durable product policy should be declared as spec assertions, per the truth hierarchy in `plugins/spec-tree/skills/understanding/references/durable-map.md` (`<truth_hierarchy>`: PDR/ADR → Spec → Test → Code; specs declare product truth).

**Why deferred from that PR:** authoring the spec assertion requires identifying the governing enabler (likely under `spx/21-spec-tree.enabler/76-pr-workflow.enabler/` or a sibling, to be confirmed via `/contextualizing`), running `/decomposing` if a new node is required, and writing the compliance rule. That work has its own scope and decomposition concerns that don't belong in a prose-edit PR.

**Location caveat:** this entry sits under `32-decisions.enabler/` because the deferred decision (whether/where to author the spec assertion) is a meta-decision about the methodology. Once the governing node for the local review gate's spec assertion is identified via `/contextualizing`, this entry should move (or be re-authored) under that node's `ISSUES.md`.

**Required action:** Author the spec assertion that declares the local review gate as a compliance rule for the `/opening-pr` skill. Pick the right governing node (`/contextualizing` first), then `/authoring` the assertion. The PR that lands the assertion should also add a `[review]` evidence link pointing at the gate's outcome — the assertion's verification is whether `/opening-pr` actually invokes the reviewer before pushing.
