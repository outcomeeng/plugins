# Known issues — decisions enabler

## Local review gate has no backing spec assertion

The `/opening-pr` skill (`plugins/spec-tree/skills/opening-pr/SKILL.md`) declares a mandatory local review gate as Step 3 of its pre-flight, but the policy lives only in skill prose. There is no spec assertion in `spx/` that declares the gate as durable product truth, and no ADR/PDR that records the rationale (stricter-than-remote, FOLLOW-UP deferred only on scope-widening).

**Source:** changes-reviewer finding F-001 on PR for `feat/local-review-gate` (2026-05-24), rule `plugins/spec-tree/skills/understanding/SKILL.md:spec-assertions-govern-durable-policy`.

**Why deferred from that PR:** authoring the spec assertion requires identifying the governing enabler (likely under `spx/21-spec-tree.enabler/76-pr-workflow.enabler/` or similar), running `/decomposing` if a new node is required, and writing the compliance rule. That work has its own scope and decomposition concerns that don't belong in a prose-edit PR.

**Required action:** Author the spec assertion that declares the local review gate as a compliance rule for the `/opening-pr` skill. Pick the right governing node (`/contextualizing` first), then `/authoring` the assertion. The PR that lands the assertion should also add a `[review]` evidence link pointing at the gate's outcome — the assertion's verification is whether `/opening-pr` actually invokes the reviewer before pushing.
