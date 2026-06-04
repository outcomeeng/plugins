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
