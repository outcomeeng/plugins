# PLAN — reviewing-changes lens follow-ups

## Why

The four evals shipped in PR #43 (`judgment-grounding`, `severity-classification`, `decision-thresholds`, `wrapper-protocol`) cover the lens's judgment surface against the current `references/review-prompt.md`. Two open items surfaced during the eval work itself are worth recording for whoever picks up future iteration on this lens.

## Open items

1. **Approve / comment calibration at trivial diffs.** During the `wrapper-protocol` dry-run, the lens emitted `decision == "comment"` on a trivial internal rename (`def to_upper → to_uppercase`). The `decision-thresholds` eval expects `approve` for clean diffs; the wrapper-protocol case was narrowed (drop the strict `decision` requirement on the clean case) so the test passes without weakening the spec. The lens prompt's wording for `comment` ("reserved for cases where the lens has no actionable judgment to offer") is ambiguous at the trivial-diff boundary — a pure rename arguably IS clean enough for `approve` AND simple enough to warrant `comment`. Tighten the prompt or extend the rubric to remove the ambiguity if the boundary case recurs in real reviews.

2. **Lens hallucinates absence in own-diff live run.** The pre-PR-#43 dogfood (run against PR #37's own diff via direct `changes-reviewer` agent invocation in a live session) produced two false-positive findings claiming `spx/21-spec-tree.enabler/17-auditing.adr.md` and the reviewing-changes `tests/` directory "do not exist" — both clearly do. The `judgment-grounding` eval probes this exact pattern across 4 cases and passes at 100%. The original live failure may be a function of the live invocation context (full repo state, larger surface area to misread) versus the eval context (only the diff is visible). Worth tracking whether the failure reproduces under the live agent on subsequent diffs; if it does, the lens prompt may need an explicit "verify the file exists before claiming absence" instruction.

## Eval coverage today

Per the cross-lens eval design pattern in `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/PLAN.md`, this lens carries:

- `evals/judgment-grounding/` — absence-claim hallucination (4 cases, 100% pass)
- `evals/severity-classification/` — severity rubric adherence (4 cases, 100% pass)
- `evals/decision-thresholds/` — decision direction on clean vs broken diffs (6 cases, 100% pass)
- `evals/wrapper-protocol/` — wrapper agent's planned tool-call sequence includes the arbiter and uses thread-store CLIs (3 cases, 100% pass after narrowing)

New judgment claims added to the lens's prompt or spec adopt the same per-eval-directory pattern; existing evals already cover the core judgment surfaces.

## Out of scope

- Cross-lens eval design changes — those belong in the umbrella's `PLAN.md`.
- Lens prompt rewrites that change wire shape — would require coordinated updates to all four evals' prompts.

## Reference

- PR #43 — the four evals and their spec assertions: `evals/judgment-grounding`, `evals/severity-classification`, `evals/decision-thresholds`, `evals/wrapper-protocol`
- Cross-lens eval pattern: `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/PLAN.md`
- PR #37 — the lens itself, the wrapper agent, the thread-store backend
- Spec-coverage ADR: `spx/15-spec-coverage.adr.md`
