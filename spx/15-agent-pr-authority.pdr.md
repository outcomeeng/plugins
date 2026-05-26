# Agent Authority over PR Lifecycle Actions

## Purpose

Governs which PR-lifecycle actions the spec-tree plugin's PR-management skills perform autonomously, expressed as a finite, ordered set of named **gates**. A **gate** is a named authorization over one lifecycle transition, decided from defined predicates; a **predicate** is a condition a gate reads. Predicates are never themselves called gates. Scope: every product installing the spec-tree plugin, with overlay points for stricter per-project gating.

## Context

**Business impact:** Operator attention is the scarce resource. Holding a change whose observable state already proves it shippable for a human decision spends that attention for no added signal; mishandling a review finding either stalls a sound change or ships a defect. A vocabulary that names one concept many ways (gate, stage, check, predicate used interchangeably) makes the authority model impossible to encode consistently across the skills that implement it.

**Technical constraints:**

- The agent performs two PR-lifecycle transitions — opening the PR and merging it — and the merge carries a production-relevance permission. Three gates govern them: `REVIEW_READINESS` authorizes the open, and `MERGE_READINESS` together with `PRODUCTION_READINESS` authorizes the merge.
- Verification splits into **deterministic** kinds (validation and testing — a local command produces a pass/fail with no model judgment) and **review** kinds (an LLM reviewer produces findings). `REVIEW_READINESS` consumes both locally; `MERGE_READINESS` consumes the review kind again on the opened PR, where it is observable.
- Merge authority must derive from finite-time-observable predicates the skill can encode: the current-head CI review's findings, required-check terminal-greenness on `statusCheckRollup`, branch hygiene including upstream safety, and the project's production-relevance recognition. An independent reader inspecting the same PR with the same overlay reaches the same `MERGE_READINESS` and `PRODUCTION_READINESS` verdict.
- Each finding cites a rule the agent verifies against governance and the PDR/ADR decisions. `/standardizing-merging`, `/opening-pr`, and `/managing-pr` express the gates to consumer agents; `spx/local/merging.md` (per `/standardizing-merging` `<repo_local_overlay>`) tightens them per project.

## Decision

The PR-management skills declare exactly three gates, evaluated in order. One word — **gate** — names each; every condition a gate reads is a **predicate**, never a gate.

**`REVIEW_READINESS`** authorizes opening the PR. It holds when both predicates hold:

- **deterministic verification passes** — every validation and testing check the project's full verification command runs (for example `just check` / `pnpm test`) reports success; and
- **the local review has converged** — the `reviewing-changes` skill (via the `changes-reviewer` agent or the `/review-changes` command), iterated over as many rounds as it takes, leaves no finding unaddressed: each is applied in-PR or recorded as out-of-PR scope in the owning node's `ISSUES.md` or `PLAN.md`.

The moment `REVIEW_READINESS` holds, the PR is created `ready_for_review` — not draft. Opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI `spec-tree-review`). Draft state is not used as a gating mechanism; there is no separate promotion transition.

**`MERGE_READINESS`** authorizes merge. It holds when both predicates hold:

- **the current-head CI `spec-tree-review` reports no valid finding** — validity judged below; and
- **every other required check is terminal-green** — defined below.

`MERGE_READINESS` carries no time-based settle: a clean review arriving two minutes after open makes the gate hold two minutes after open.

**`PRODUCTION_READINESS`** permits the merge to execute. It holds when **either** the change is not production-relevant (per the project's production-relevance recognition mechanism) **or** the operator has explicitly approved the merge. The agent computes and pursues `MERGE_READINESS` identically for every PR; it executes the merge only when `PRODUCTION_READINESS` also holds. A project requiring human approval for every merge declares its recognition mechanism to classify every change as production-relevant.

**terminal-green.** A required check in `statusCheckRollup` is either a check run (`status` reaches `COMPLETED`, then `conclusion` is one of `SUCCESS`, `FAILURE`, `CANCELLED`, `TIMED_OUT`, `SKIPPED`, `NEUTRAL`, `ACTION_REQUIRED`, …) or a status context (`state` is one of `EXPECTED`, `PENDING`, `SUCCESS`, `ERROR`, `FAILURE`). A check is **terminal** when it has reached a final state — `status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}` — as opposed to a still-running `QUEUED` / `IN_PROGRESS` / `PENDING` / `EXPECTED`. A check is **green** when its `conclusion == SUCCESS` (or `state == SUCCESS`). A check is **terminal-green** when it is both: it has finished, and it finished with success. The distinction from plain "green" is that a check that has not finished has no conclusion yet — it is neither green nor red, only not terminal. A required check that is non-terminal, terminal-but-not-success, or absent from the rollup is not terminal-green and blocks `MERGE_READINESS`.

**Acting on findings (validity and phase, never severity).** The agent acts on each review finding by its **validity** — the finding holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; the agent reads those fresh and drops a finding they do not support — and by **phase**: at `REVIEW_READINESS` (before the PR opens) it applies every valid finding that belongs and splits out of the changeset any finding whose fix is too large to belong — the split work leaves this PR's diff and is captured in the owning node's `ISSUES.md` or `PLAN.md`; at `MERGE_READINESS` (PR open) it fixes every valid finding the CI review surfaces and re-pushes, with no deferral — deferral is a before-open decision, so a valid finding on the open PR is fixed, never recorded-and-left. A finding's severity label never decides whether the agent acts on it, and the reviewer never decides whether the change merges. A finding the agent drops as unbacked is not "valid"; every valid finding is either fixed or, before open, split out of the diff. So the current-head CI review of an open PR shows no valid finding: `MERGE_READINESS` reads "no *valid* finding" literally — every valid concern about the shipped diff is fixed, and every deferred concern is split out before the PR opens.

**Reviewer-skipped-by-design.** When the CI `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main" (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. The agent fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review once they land. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

## Rationale

**Three gates, one word.** Naming each lifecycle authorization a "gate" and every condition it reads a "predicate" gives the model one word per concept. An overloaded vocabulary — gate / stage / check / predicate used for the same and for different things — cannot be encoded once and reused. The set is finite and ordered: open, merge, execute-merge.

**Open ready, not draft.** `REVIEW_READINESS` covers the local review and the deterministic verification before the PR opens, so a draft phase adds no signal — it only delays the CI reviews that wait for ready (Codex) and re-runs the same `spec-tree-review` the author runs locally. Opening ready fires every CI review simultaneously. The CI `spec-tree-review` is the observable record an independent reader (and `MERGE_READINESS`) verifies on the PR; the local review is the pre-open gate that earns the right to open.

**No settle window.** A fixed wait is a proxy for "give review automation time to respond". `MERGE_READINESS` instead reads the event directly: the gate holds when the current-head review has landed with no valid finding and every other required check is terminal-green. A clean review that arrives quickly merges quickly; a missing review keeps the gate open because the predicate is unmet, not because a timer has not elapsed.

**The reviewer reports; the author decides.** Severity is the reviewer's label. Whether the agent acts on a finding turns on validity and phase, so a mislabeled finding neither blocks a sound change nor slips an in-scope fix. `MERGE_READINESS` reads resolution, never a severity value.

**Production-relevance is a separate, explicit gate.** Merge effort is identical for every PR; only execution waits. A non-production-relevant change merges autonomously on `MERGE_READINESS`; a production-relevant one reaches `MERGE_READINESS` autonomously and then waits for operator approval. The recognition mechanism (label, branch prefix, file pattern, manifest declaration) is per-project; a project that wants every merge approved declares every change production-relevant.

Alternatives rejected:

- **One gate instead of three.** Collapsing open, merge, and production approval into a single "PR authority gate" hides that the agent authorizes three distinct transitions and forces the merge gate to carry open-time and approval-time predicates that drift.
- **Gate any decision on finding severity (`no unresolved BLOCKING or DEBT`).** A label decides what only the author can: it stops a merge on an unsupported finding and merges past an in-scope one. Validity and phase decide; severity informs.
- **A time-based settle as a merge predicate.** It delays clean PRs and gives no guarantee for slow ones; reading the review-landed event directly is both faster and stricter.
- **Always-draft with a gated promotion to ready.** It adds a fourth authorization with no signal once `REVIEW_READINESS` covers the local review, and re-runs `spec-tree-review` in a draft phase the author already covers locally.
- **Require explicit instruction for every merge.** Imposes operator latency on PRs whose state already proves what the instruction would assert; the production-relevance gate already captures the cases that need a human.

## Trade-offs accepted

| Trade-off                                                                    | Mitigation / reasoning                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finding validity is an agent judgment, not a mechanical predicate            | The finding cites a rule. The agent reads that rule, the governing skills, and the PDR/ADR decisions before acting, then drops any the citation refutes — the same sources a reviewer consults                                 |
| The CI `spec-tree-review` duplicates the local review the author already ran | The duplication is deliberate: the local review is the `REVIEW_READINESS` gate (not observable on a PR that does not yet exist); the CI review is the observable `MERGE_READINESS` predicate any independent reader can verify |
| `terminal-green` requires enumerating the rollup state model                 | The definition is given once here and reused verbatim; it collapses every check to two questions — has it finished, and did it succeed                                                                                         |
| Production-relevance recognition relies on a per-project mechanism           | Each project declares its mechanism in `spx/local/merging.md`; a project that declares none treats every change as non-production-relevant and merges on `MERGE_READINESS` alone                                               |

## Product invariants

- The PR-management skills expose exactly three gates — `REVIEW_READINESS`, `MERGE_READINESS`, `PRODUCTION_READINESS` — named with the single word "gate"; every condition a gate reads is a predicate, never a gate.
- `REVIEW_READINESS` holds from deterministic verification plus a converged local review; the PR opens `ready_for_review` the moment it holds, and draft state is not a gating mechanism.
- `MERGE_READINESS` and `PRODUCTION_READINESS` are decidable from observable PR state: an independent reader inspecting the same PR with the same overlay reaches the same verdict. `MERGE_READINESS` carries no time-based settle.
- The agent acts on a review finding by its validity and the current phase, never by its severity label; the reviewer never decides whether the change merges.
- Production-relevance is project-declared; the agent executes a production-relevant merge only after explicit operator approval, and carries no built-in rule that could silently authorize one.

## Compliance

### Recognized by

`plugins/spec-tree/skills/standardizing-merging/SKILL.md` declares the three gates, their predicates, the `terminal-green` definition, and the overlay-refinable production-relevance and merge-authority topics. `plugins/spec-tree/skills/opening-pr/SKILL.md` evaluates `REVIEW_READINESS` — running the local `reviewing-changes` gate to convergence over deterministic-green changes — and opens the PR ready. `plugins/spec-tree/skills/managing-pr/SKILL.md` evaluates `MERGE_READINESS` from the current-head CI review and terminal-green checks, evaluates `PRODUCTION_READINESS`, and merges only when both hold. The validity-and-phase handling of findings spans `/opening-pr` (the `REVIEW_READINESS` phase) and `/managing-pr` (the `MERGE_READINESS` phase).

### MUST

- The agent opens a PR `ready_for_review` once `REVIEW_READINESS` holds — every validation and testing check the project's full verification command runs reports success, and the local `reviewing-changes` review has converged so no finding is left unaddressed (each applied in-PR or recorded as out-of-PR scope in `ISSUES.md` / `PLAN.md`) — and uses no draft phase as a gating mechanism ([review])
- The agent merges a non-production-relevant PR without separate explicit human instruction once `MERGE_READINESS` holds: the current-head CI `spec-tree-review` reports no valid finding, and every other required check is terminal-green ([review])
- The agent treats a required check as terminal-green only when it has reached a terminal state (`status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}`) with a success conclusion (`conclusion == SUCCESS` or `state == SUCCESS`); a non-terminal, terminal-but-not-success, or absent required check blocks `MERGE_READINESS` and carries no time-based settle ([review])
- The agent executes the merge only when `PRODUCTION_READINESS` also holds: the change is not production-relevant per the project's recognition mechanism, or the operator has explicitly approved the merge ([review])
- The agent acts on each review finding by validity (its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions) and by phase (`REVIEW_READINESS` before open: apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong, capturing the split work in `ISSUES.md` / `PLAN.md`; `MERGE_READINESS` PR open: fix every valid finding the CI review surfaces and re-push, with no deferral), never by the finding's severity label ([review])
- When no current-head review exists because the CI `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main", the agent fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review once they land; this applies to that skip cause only, not path-filter, branch-filter, or manual skips ([review])

### NEVER

- Gate any of the three gates on a review finding's severity label: validity and phase decide whether the agent acts on a finding; the reviewer never decides whether the change merges ([review])
- Use a time-based settle window as a `MERGE_READINESS` predicate: the gate reads the review-landed and terminal-green events directly, not the age of the latest push ([review])
- Open a PR as draft as a gating mechanism, or add a separate gated draft-to-ready promotion: the PR opens ready once `REVIEW_READINESS` holds ([review])
- Execute a production-relevant merge from `MERGE_READINESS` alone; `PRODUCTION_READINESS` requires explicit operator approval ([review])
- Treat an agent-inferred "the work looks done" as a gate: a gate's predicates are observable or deterministically computed state, never large-language-model judgment ([review])
- Name a predicate a "gate", or introduce a fourth gate, without amending this PDR: the gate set is finite, ordered, and enumerated here ([review])
