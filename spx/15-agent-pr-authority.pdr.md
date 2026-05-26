# Agent Authority over PR Lifecycle Actions

## Purpose

Governs which PR-lifecycle actions the spec-tree plugin's PR-management skills perform autonomously versus under explicit human instruction, and how the agent acts on a reviewer's findings. Scope: every product installing the spec-tree plugin, with overlay points for stricter per-project gating.

## Context

**Business impact:** Operator attention is the scarce resource. Holding a PR whose observable state already proves it shippable for a human merge decision spends that attention for no added signal; mishandling a review finding either stalls a sound change or ships a defect.

**Technical constraints:** Merge authority must derive from finite-time-observable predicates the skill can encode as a gate: closure-gate result from the project command, required-check terminal-greenness on `statusCheckRollup` for the pushed head, a current-head review on an inspected surface with every finding resolved, latest-push timestamp at least five minutes prior, branch hygiene including upstream safety, and no project-declared production-class markers. Each finding cites a rule the agent verifies against governance and the PDR/ADR decisions. `/standardizing-merging` and `/managing-pr` express authority to consumer agents; `spx/local/merging.md` (per `/standardizing-merging` `<repo_local_overlay>`) tightens it per project.

## Decision

The PR-management skills declare one named gate, the **PR authority gate**, authorizing autonomous merge of a non-production PR when its predicates hold: closure gate passed, required checks terminal-green on the pushed head, a current-head review exists with every finding resolved (applied in-PR or recorded as a deferred item), latest push at least five minutes old, branch hygiene holds, no production-class markers.

The agent acts on each finding by validity and phase, never by its severity label. **Validity:** the finding holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; the agent reads those fresh and drops a finding they do not support. **Phase:** before the opening push (`/opening-pr`) the agent applies every valid finding, splitting the changeset when a fix is too large to belong; with the PR open (`/managing-pr`) it applies every valid finding that does not substantively widen the PR and records the rest per the project's deferral guidance.

Production-class PRs, and overlays declaring merge human-authorized, fall back to explicit instruction.

## Rationale

**Authority from observable state.** The gate names the state a "merge it" instruction would assert: closure gate passed, checks green, findings resolved, settle elapsed, hygiene holds, non-production. The agent merges on the state itself. The instruction stays a valid authority signal an overlay may require, not the only one.

**The reviewer reports; the author decides.** Severity is the reviewer's label. Whether the agent acts on a finding turns on validity and phase, so a mislabeled finding neither blocks a sound change nor slips an in-scope fix.

**Overlay-overridable.** Risk profiles differ: a production-rollout repository treats merge as a deliberate human decision, a documentation marketplace treats every gate-green PR as autonomous. The skill ships the autonomous-merge default; each project declares stricter authority in its overlay.

**Production-class exception is explicit.** The recognition mechanism (label, branch prefix, file pattern, manifest declaration) is per-project; a production-class PR takes explicit-instruction handling regardless of the other predicates. When a project declares no mechanism and the PR cannot be classified, the skill withholds autonomous authority.

Alternatives rejected:

- **Gate the merge on finding severity (`no unresolved BLOCKING or DEBT`).** A label decides what only the author can: it stops a merge on an unsupported finding and merges past an in-scope one. Validity and phase decide; severity informs.
- **Require explicit instruction for every merge.** Imposes operator latency on PRs whose state already proves what the instruction would assert.
- **Implicit gate with no overlay override.** Removes a project's ability to require human merge under compliance or staged-rollout policy.

## Trade-offs accepted

| Trade-off                                                                 | Mitigation / reasoning                                                                                                                                                                                  |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finding validity is an agent judgment, not a mechanical predicate         | The finding cites a rule. The agent reads that rule, the governing skills, and the PDR/ADR decisions before acting, then drops any the citation refutes. These are the same sources a reviewer consults |
| The five-minute settle window is the only built-in last-look before merge | A project needing longer declares it in the overlay as a stricter merge-authority requirement                                                                                                           |
| The production-class exception relies on per-project recognition          | Each project declares its recognition mechanism in `spx/local/merging.md`; the skill withholds autonomous authority when classification is undecidable                                                  |
| Overlay-driven authority creates per-project variation                    | Intentional: risk profiles differ; the default is autonomous merge, deviations declared once per project                                                                                                |

## Product invariants

- The PR-management skills expose one named gate, the PR authority gate, authorizing autonomous merge for non-production PRs, with overlay-declared overrides.
- The merge the gate authorizes is decidable from observable PR state: an independent reader inspecting the same PR with the same overlay reaches the same verdict.
- The agent acts on a review finding by its validity and the current phase, never by its severity label; the reviewer never decides whether the change merges.
- Production-class recognition is project-declared; the skill carries no built-in rule that could silently authorize a production action.

## Compliance

### Recognized by

`plugins/spec-tree/skills/standardizing-merging/SKILL.md` declares the gate, its predicates, and the overlay-refinable merge-authority topic. `plugins/spec-tree/skills/managing-pr/SKILL.md` evaluates the gate and merges from its verdict. `plugins/spec-tree/skills/opening-pr/SKILL.md` and `/managing-pr` carry the validity-and-phase handling of findings. Absent an overlay declaration, the agent merges when the gate holds.

### MUST

- The agent merges a non-production PR without separate explicit human instruction once the gate's predicates hold: closure gate passed, required checks terminal-green on `statusCheckRollup` for the pushed head, a current-head review exists with every finding resolved (applied in-PR or recorded as a deferred item), latest push at least five minutes prior, branch hygiene including upstream safety, and no project-declared production-class markers ([review])
- The agent acts on each review finding by validity (its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions) and by phase (before push: apply every valid finding, splitting the changeset when a fix is too large; PR open: apply every valid finding that does not substantively widen the PR, record the rest per the project's deferral guidance), never by the finding's severity label ([review])
- The agent defers merge to explicit human instruction when the overlay declares merge human-authorized, and withholds autonomous merge when a PR cannot be classified and the overlay declares no production-class recognition mechanism ([review])
- When no current-head review exists because `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main", the agent fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review once they land; this applies to that skip cause only, not path-filter, branch-filter, or manual skips ([review])

### NEVER

- Gate the merge on a review finding's severity label: validity and phase decide whether the agent acts on a finding; the reviewer never decides whether the change merges ([review])
- Authorize merge on a production-class PR from gate evaluation alone; the production exception requires explicit human instruction ([review])
- Treat an agent-inferred "the work looks done" as the gate: the predicates are observable PR state, never large-language-model judgment ([review])
