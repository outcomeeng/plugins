# Agent Authority over PR Lifecycle Actions

## Purpose

This decision governs which PR-lifecycle actions the spec-tree plugin's PR-management skills authorize the agent to perform autonomously and which require explicit human instruction. Scope: every product that installs the spec-tree plugin, with overlay points for projects whose risk profile requires stricter gating.

## Context

**Business impact:** A pull request has two CI-cost gates that double as reviewer-attention signals: promoting from draft to ready (expensive verification fires) and merging (the change publishes to the base branch). Both gates are decidable from observable PR state — closure-gate result, required-check rollup, current-head review state, latest-push timestamp, branch hygiene. Splitting authority so that one action is autonomous and the other is human-gated stalls every PR loop at the boundary between them: a PR whose state proves it shippable is held at the promote step because the authority model differs from the merge step. The stall consumes operator attention on PRs whose gate has already converged, and the redundant authorization carries no information the gate has not already captured.

**Technical constraints:** Agent authority must derive from finite-time-observable predicates so the skill can encode them as a gate. The observable predicates are: closure-gate result from the project-specific command, required-check terminal-greenness on `statusCheckRollup`, current-head three-severity review on at least one inspected surface with no unresolved `BLOCKING` or `DEBT`, latest-push timestamp at least five minutes prior to evaluation, branch hygiene including upstream safety, and the absence of project-declared production-class markers on the PR. The spec-tree plugin's `/standardizing-merging` and `/managing-pr` skills are the surfaces where authority is expressed to consumer agents; their overlay model (`spx/local/merging.md` per `/standardizing-merging` `<repo_local_overlay>`) is the durable mechanism through which a consuming project tightens authority below the skill default.

## Decision

The spec-tree plugin's PR-management skills declare a single named gate — the **PR authority gate** — that governs both draft → ready promotion and merge for non-production PRs. The gate's predicates are evaluated per action at the moment that action becomes applicable: promotion is evaluated against the predicates observable on the draft PR, and merge is evaluated against the predicates observable on the ready PR after its checks have converged. When the gate authorizes the applicable action, the agent performs that action without separate explicit human instruction. Production-class PRs and projects whose overlays declare promotion or merge as human-authorized fall back to explicit-instruction handling for the action the overlay names.

## Rationale

**One gate covers both actions.** The same observable predicates determine whether a PR is shippable. Splitting promotion and merge into two gates with different authority models produces the stall: a PR with observable green state holds at promotion because authority diverges from merge, even though no new predicate evaluates between the two steps. Unifying authority resolves the stall and locates the agent's reasoning in one auditable place.

**Authority derives from observable predicates, not chat-text intent.** An explicit chat instruction ("mark ready", "merge it") encodes a human's assertion that the PR's state proves it ready. The PR authority gate names that state directly: closure gate passed, checks green, review clear, settle window elapsed, branch hygiene holds, no production-class markers. The instruction remains a valid authority signal — an overlay may declare human-instruction the required authority for either action — but it is one form of authority, not the only one.

**Overlay-overridable.** Different products carry different risk profiles. A production-rollout repository rationally treats merge as a deliberate human decision under compliance or staged-rollout policy; a documentation marketplace rationally treats every PR as autonomous when CI is green. The skill ships the autonomous-gate default; each consuming project declares stricter requirements in its overlay when its risk profile demands them.

**Production-class exception is explicit, not implicit.** The gate excludes PRs the project recognizes as production-class. The recognition mechanism (label, branch prefix, file pattern, manifest declaration) is per-project; the exclusion is part of the gate, not commentary on it. A production-class PR triggers explicit-instruction handling regardless of the other predicates. When a project declares no recognition mechanism and the PR cannot be classified, the skill withholds autonomous authority rather than guess.

Alternatives rejected:

- **Keep promotion human-gated and merge autonomous.** Splits one decision across two authority models; produces the stall the gate exists to prevent.
- **Require explicit instruction for both promotion and merge.** Forecloses the autonomous-merge path the marketplace already authorizes through the gate-green-autonomous default. Imposes operator latency on PR loops whose state already proves the conditions the instruction would assert.
- **Implicit gate with no overlay override.** Removes consumers' ability to declare stricter authority where compliance, staged rollout, or audit policy requires human merge decisions.

## Trade-offs accepted

| Trade-off                                                                                                                    | Mitigation / reasoning                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Autonomous promotion fires expensive CI on a gate-evaluation rather than on a human's deliberate signal                      | The closure-gate predicate of the gate replaces the human's "I just ran the local checks" assertion with an observable result; the CI spend is justified by the same underlying assertion in either path                    |
| The production-class exception relies on per-project recognition                                                             | Each consuming project declares its production-class recognition mechanism in `spx/local/merging.md`; recognition is auditable per project, and the skill withholds autonomous authority when classification is undecidable |
| The five-minute settle window is the only built-in opportunity for last-look human intervention between gate-green and merge | Operators who require a longer window declare it in the overlay as a stricter promotion-authority or merge-authority requirement                                                                                            |
| Overlay-driven stricter authority creates per-project variation                                                              | Variation is intentional: risk profiles differ. The skill default is the autonomous gate; deviations are declared once per project and are visible to every reviewer of that project                                        |

## Product invariants

- The spec-tree plugin's PR-management skills expose one named gate — the PR authority gate — covering both promotion and merge for non-production PRs, with overlay-declared overrides per action.
- Every action the gate authorizes (promotion, merge) is decidable from observable PR state at gate-evaluation time: an independent reader inspecting the same PR with the same overlay reaches the same authority verdict.
- Production-class PR recognition is project-declared; the skill carries no built-in recognition rule that could silently authorize a production action.

## Compliance

### Recognized by

`plugins/spec-tree/skills/standardizing-merging/SKILL.md` declares the PR authority gate by name, lists its predicates, and lists draft-promotion authority and merge authority as overlay-refinable topics in `<repo_local_overlay>`. `plugins/spec-tree/skills/managing-pr/SKILL.md` evaluates the gate once per inspection pass and authorizes both promotion and merge from a single verdict; its workflow tokens distinguish gate-green-autonomous from overlay-requires-human paths for each action. A consuming project's `spx/local/merging.md` may declare either action as human-authorized; absent such declaration, the agent runs `gh pr ready` and `gh pr merge` autonomously when the gate is satisfied.

### MUST

- `plugins/spec-tree/skills/standardizing-merging/SKILL.md` declares a named PR authority gate whose predicates are observable and finite-time-decidable: closure-gate result, required-check terminal-greenness on `statusCheckRollup`, current-head three-severity review with no unresolved `BLOCKING` or `DEBT` on at least one inspected surface, latest-push timestamp at least five minutes prior to evaluation, branch hygiene including upstream safety, and absence of project-declared production-class markers ([review])
- The gate authorizes both draft → ready promotion and merge from a single verdict for non-production PRs; the agent performs both actions without separate explicit human instruction when the gate is satisfied ([review])
- `plugins/spec-tree/skills/standardizing-merging/SKILL.md` `<repo_local_overlay>` enumerates both **Draft-promotion authority** and **Merge authority** as overlay-refinable topics, parallel to each other and to the gate's other overlay points ([review])
- `plugins/spec-tree/skills/managing-pr/SKILL.md` `<the_managing_flow>` distinguishes gate-green-autonomous promotion from overlay-requires-human promotion using named action tokens from /standardizing-merging `<action_tokens>`; the same flow distinguishes gate-green-autonomous merge from overlay-requires-human merge ([review])
- Production-class PR recognition mechanisms (label, branch pattern, file pattern, manifest declaration) are declared by each consuming project in its `spx/local/merging.md`; the skill withholds autonomous authority when a PR cannot be classified and the overlay declares no recognition mechanism ([review])
- `plugins/spec-tree/skills/standardizing-merging/SKILL.md` `<pr_authority_gate>` declares the reviewer-skipped-by-design exception: when the auto-review job reports `conclusion: skipped` with cause "PR head differs from main" (GitHub Actions' identical-workflow-content gate), the review predicate is satisfied by posting the configured `<trigger-phrase> review` comment to fire the mention-triggered reviewer; the exception is scoped to that specific skip cause and does not apply to path-filter, branch-filter, or manual skips ([review])
- `plugins/spec-tree/skills/standardizing-merging/SKILL.md` `<action_tokens>` includes `MENTION_REVIEW_NEEDED:<trigger-phrase>`, emitted by the managing flow when the reviewer-skipped-by-design exception applies; the trigger phrase is the consuming project's overlay-declared mention-reviewer phrase from `spx/local/merging.md`, defaulting to `@claude` per the upstream reviewer action's default ([review])

### NEVER

- Authorize draft → ready promotion or merge on a production-class PR from gate evaluation alone — the production exception requires explicit human instruction ([review])
- Maintain separate authority models for promotion versus merge that produce different verdicts from the same gate state — the gate's purpose is to unify them ([review])
- Treat an agent-inferred "the work looks done" as the gate — the gate's predicates are observable PR state, never LLM judgment ([review])
