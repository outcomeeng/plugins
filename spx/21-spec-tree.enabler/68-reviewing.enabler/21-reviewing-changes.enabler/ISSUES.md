# Issues: Reviewing Changes Enabler

## 1. Caller-narrowing prompt-content assertion is `[review]`, could be `[test]` (FOLLOW-UP)

The assertion added to `reviewing-changes.md` —

> ALWAYS: the review prompt instructs the reviewer to review the whole diff against the whole shared taxonomy using the repository's own instructions, and to treat any caller-supplied scope, severity pre-filter, or emphasis as non-authoritative — the local reviewer runs at parity with the CI reviewer per `spx/15-agent-pr-authority.pdr.md`

carries `[review]` evidence. Its subject is a static, observable property of `references/review-prompt.md`: the file contains a Scope section whose text rejects caller-supplied scope, severity pre-filter, and emphasis. That is the same class of prompt-content property the sibling assertion at `reviewing-changes.md` already verifies with `[test]` — "the swappable review prompt template lives at `…/review-prompt.md`" → `tests/test_reviewing_changes.compliance.l1.py`.

A compliance test in the style of the existing `test_reviewing_changes.compliance.l1.py` checks (a prompt-content presence assertion) would make this verifiable without human inspection on every PR, removing the `[review]`/`[test]` evidence-strength inconsistency between two assertions about the same file.

Required handling when a test-evidence sweep happens on this node:

- Add a compliance test asserting `review-prompt.md` contains the Scope section with the caller-narrowing rejection text (whole-diff/whole-taxonomy, no caller-supplied scope/severity-filter/emphasis).
- Retag the assertion from `[review]` to `[test](tests/test_reviewing_changes.compliance.l1.py)`.

Split out of the parity-contract change (PR `feat/local-review-parity`) because it adds a new test class beyond that change's blast-radius.

## 2. Local review may resolve its base from a stale local ref, not `origin/<base>`

During the `fix/sessions-test-hermeticity` work, the `changes-reviewer` agent (driving the `reviewing-changes` skill) twice surfaced findings about code **already merged to `main`** — verification-taxonomy (#103) and merging-review (#104) changes that were not part of the changeset under review. The reviewer was invoked with base `origin/main`, yet its diff included those merged commits.

The symptom correlated with the local `main` ref being stale: `main` pointed at `e880a61` while `origin/main` had advanced past #103/#104. Force-updating `git branch -f main origin/main` before each review made the false findings disappear. This points at a candidate defect: the diff base appears to resolve from the local `main` branch ref (or a merge-base computed against it) rather than from `origin/<base>` or the explicitly-passed base ref. In a multi-worktree checkout — where `main` is intentionally kept unattached and can lag `origin/main` — that reviews a superset diff and yields false findings against already-merged work.

Required handling (investigate before fixing):

- Invoke `/understanding` then `/contextualizing spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`.
- Inspect how `reviewing-changes` computes its diff base (the `git diff <base>...<head>` resolution and any merge-base step).
- Confirm whether it dereferences a local branch ref (e.g., `main`) or uses `origin/<base>` (fetched) and the explicit base the caller passes.
- If it keys off a local ref, resolve the base against `origin/<base>` (fetch first) or honor the caller-passed base verbatim, so a stale local ref cannot widen the reviewed diff. Add evidence that a stale local `main` does not change the reviewed diff.

Until then, agents running the local review in this multi-worktree repo keep `main` synced (`git branch -f main origin/main`) before invoking the reviewer.

Surfaced during the `fix/sessions-test-hermeticity` change review (PR #105).

## 3. Local census markers diverge from the GH CI clean-review message (FOLLOW-UP)

The local `reviewing-changes` render emits a per-severity census for the no-findings state — `BLOCKING: none` / `DEBT: none` / `FOLLOW-UP: none` — while the GH-hosted `spec-tree-review` workflow (in `outcomeeng/gh-actions`) emits a single composite clean-review line, `No BLOCKING or DEBT findings.`. The `21-script-decomposition.adr.md` "one source of truth" rationale assumes the two surfaces share the rendered shape; for the no-findings state they now differ.

This does not block its originating PR: the divergence is in the GH workflow (another repository), outside this repo's blast-radius, and no `MERGE_READINESS` predicate reads the local render — the gate reads the CI review surface.

Required handling (cross-repo, when pursued):

- Decide the canonical clean-review representation (per-severity census vs composite line) and align both surfaces — the local `render_review.py` templates here and the `spec-tree-review` workflow in `outcomeeng/gh-actions`.
- Any clean-review detection that reads both surfaces recognizes both forms until they converge.

Surfaced during the `fix/reviewing-no-findings-convention` change review (PR #108).

## 4. Reviewer cites phantom rules it recalls instead of reading from the repo

The review prompt lets the reviewer emit `standards` findings against rules
that do not exist in the repository under review. On `outcomeeng/spx` PR #109
the reviewer posted a `debt` / `standards` finding whose `Reference:` quoted
`CLAUDE.md` as saying *"Never write multi-paragraph docstrings or multi-line
comment blocks — one short line max."* No such rule exists in that repository's
`CLAUDE.md`. The rule leaked from the underlying coding agent's own system
prompt / global instructions (or is an outright hallucination), and the
reviewer attributed it to the repository's `CLAUDE.md`.

The current guard does not catch this. `references/review-prompt.md` defines
the `standards` concern as "adherence to `CLAUDE.md` and the rules declared in
standardizing-\* skills" (Category section), and the `## Rule citation` section
already forbids "Inventing a citation that does not name a real rule in the
loaded context." But an agent that *recalls* a comment-length rule from its own
system prompt believes the rule is real and present in `CLAUDE.md` — from its
vantage it is not inventing a citation, so the existing prohibition does not
fire. The gap: the prompt never requires the reviewer to confirm the cited rule
by reading it back out of a file that actually exists in the repository under
review.

Required handling (fix in the canonical prompt, then propagate to the built
plugins and any restating workflow):

- Edit `src/plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md`
  `## Rule citation` section to add a strongly worded rule: a finding may cite a
  rule ONLY when the reviewer has located and read that exact text in a file
  that exists in the repository under review (`CLAUDE.md`, `AGENTS.md`, a loaded
  standardizing-\* skill, or a governance doc on disk). The reviewer MUST NOT
  cite any rule it recalls from its own system prompt, the user/global
  `CLAUDE.md`, prior sessions, or training, and MUST discard rather than report
  such a rule.
- Name comment-length and docstring-length rules as the known failure mode:
  never emit a finding about comment or docstring length unless that constraint
  is present verbatim in the repository's own `CLAUDE.md` or a loaded skill.
- When a candidate standard cannot be located in a repository file, the finding
  is dropped, not downgraded.
- Add evidence: a compliance test asserting `review-prompt.md` carries the
  read-it-from-the-repo citation rule, in the style of the existing
  `tests/test_reviewing_changes.compliance.l1.py` prompt-content checks.

The `outcomeeng/gh-actions` `spec-tree-review.yml` workflow carries a baked-in
restatement of this prompt; that copy needs the same hardening once the
canonical prompt is fixed, per the cross-reference recorded in that repo's
`spx/54-verification-gates.enabler`.

Surfaced from the Spec Tree reviewer run on `outcomeeng/spx` PR #109.

**Recurrence (raises priority).** The same phantom rule fired again on
`outcomeeng/plugins` PR #148 (2026-06-09): the CI `spec-tree-review` reviewer
posted two `debt`/`standards` findings against
`outcomeeng/validation/reference_portability.py` — the module docstring and the
lookbehind comment — each citing the identical non-existent rule *"Never write
multi-paragraph docstrings or multi-line comment blocks — one short line max."* A
repo-wide grep finds that phrase only in this `ISSUES.md`. The author refuted both
as unbacked at the `MERGE_READINESS` gate (the citation resolves to nothing in the
repo, and the approved sibling `outcomeeng/validation/skill_injection_safety.py`
on `main` carries the same multi-paragraph module docstring), then merged — but
the gate spent author effort the prompt-side fix above would prevent at the
source. Second confirmed instance across two repositories: the `## Rule citation`
read-it-from-the-repo hardening is load-bearing, not speculative.

## 5. Live runs do not meet the per-pass exhaustiveness assertion

`reviewing-changes.md` declares (Compliance, `[review]`): *"each pass against a given
changeset surfaces every finding the changeset exhibits in that single pass —
there is no cross-pass continuity, and a finding missed on this pass has no second
chance unless the diff itself changes."* Live runs do not meet this.

On `outcomeeng/plugins` PR #148 (2026-06-09), five `changes-reviewer` passes over
the reference-portability node each surfaced roughly one finding and missed latent
ones present in the *same* diff. Two real defects existed in the first committed
diff — the implementation regex `spx/\d` looser than the spec's `spx/\d+-`
discriminator, and the spec's "caught even inside an absolute checkout path" claim
left unexercised by any test sample — yet were not surfaced until the third and
second passes respectively. The cost was extra rounds, not shipped defects, but the
rounds are the symptom: each pass sampled a non-deterministic subset of the
findings the diff already exhibited instead of enumerating all of them.

Because the design is intentionally stateless (line 53: "no cross-pass
continuity"), the remedy is to make a single pass actually exhaustive — never to
add cross-pass memory.

Required handling:

- Give `references/review-prompt.md` a completeness procedure: enumerate the
  changeset's `(spec assertion → [test]/[eval] evidence link → implementation)`
  triples and every changed file, and require the reviewer to visit each before
  emitting, rather than free-form issue-spotting.
- Consider emitting a coverage manifest in `review-result.json` (files and
  assertions visited) so the consumer can see what a pass actually covered. A new
  top-level wire field requires a `SCHEMA_VERSION` bump in the `review_result.py`
  policy module plus coordinated updates to `validate_review_result.py`,
  `render_review.py`, and every consumer that round-trips the document.
- This is finding COVERAGE (did the pass find everything), orthogonal to PLAN
  items 3 and 7, which check finding VALIDITY (real diff coordinate / real rule
  citation).
- Consider whether line 53's `[review]` evidence should gain an `[eval]` probing
  per-pass completeness on a diff carrying several independent defects.

Surfaced by the `changes-reviewer` runs on `outcomeeng/plugins` PR #148.

## 6. Proposed: collapse the reviewer severity set to `blocking`/`debt` and move disposition to the author

The shared taxonomy declares three severities — `blocking`, `debt`, `follow_up`
(`reviewing.md`, `reviewing-changes.md`'s severity rubric `[eval]`,
`REVIEW.template.md`, the `Severity` enum and render templates). `follow_up` is
defined as *"out-of-scope items that would extend the blast-radius of the PR"* — a
**scope** judgment, not a severity one.

**Proposal.** The reviewer emits only `blocking` (merge-safety defect) and `debt`
(real defect) — the **validity/severity** axis it judges from the code and the
rules — and the **author** maps each `debt` to `{fix-in-PR |
track-out-of-scope-in-ISSUES/PLAN-with-justification}` along the **disposition**
axis, which only the author — holding the changeset's intended scope and its
`PLAN.md` — is positioned to judge.

**Rationale (this session).** On PR #148 the reviewer labeled a CLI-scenario
assertion gap `follow_up`; the author tracked it in `ISSUES.md` rather than fixing
it, deferring to the reviewer's scope call — and the operator then asked why a
small, in-scope fix had been merely tracked. The `follow_up` label outsourced a
scope decision the reviewer is not positioned to make. The skill already declares
the reviewer "carries findings only … never decides" (`reviewing.md`) and that the
consumer "acts by validity and phase, never by severity"
(`spx/15-agent-pr-authority.pdr.md`); `follow_up` is the one place the reviewer
still makes a disposition call, in tension with that stance.

**Blast-radius (cross-cutting — author a decision record first; this amends the
agent-pr-authority taxonomy, not just this skill):**

- `reviewing.md` three-severity Compliance assertions (the
  `blocking`/`debt`/`follow_up` set and the severity-rank NEVER).
- `reviewing-changes.md`: the `Severity` enum wire-value Mapping, the
  `Severity → render-class` Mapping, the render census/label-asymmetry Compliance,
  and the severity-rubric `[eval]` (`evals/severity-classification/`).
- `Severity` enum and `from_json_dict` in the `review_result.py` policy module;
  render templates `references/render/finding-followup.md` and `none-followup.md`.
- `evals/severity-classification/` cases — this node's `PLAN.md` already records
  them as calibration-fragile at the `follow_up` boundary (cases 3–4 flip
  `debt`/`follow_up` across trials); a two-severity rubric would likely *improve*
  eval stability.
- `REVIEW.template.md` (the consumer-override taxonomy surface at repo root).
- `spx/15-agent-pr-authority.pdr.md` — `MERGE_READINESS` reads the taxonomy; its
  "`FOLLOW-UP` tracked, not blocking" clause becomes "a `debt` the author tracked
  out-of-scope, with a recorded reason, is not blocking." Same gate strength,
  ownership corrected.

**Open.** Whether to keep a render bucket for author-tracked-out-of-scope `debt`
(so the rendered surface still distinguishes fixed-here from tracked-elsewhere),
or leave that distinction entirely to the author's `ISSUES.md`/`PLAN.md` record.
Decide in the decision record.

Surfaced from the operator review of `changes-reviewer` behavior on
`outcomeeng/plugins` PR #148 (2026-06-09).
