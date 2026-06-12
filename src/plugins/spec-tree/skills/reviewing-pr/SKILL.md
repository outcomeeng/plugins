---
name: reviewing-pr
description: Use when asked by the user to invoke the PR review skill
allowed-tools: Read, Bash, Glob, Grep, Skill
---

<objective>

Review a pull request and return constructive, repository-grounded feedback labeled with the two-severity / six-category taxonomy from `/standardizing-merging` `<review_classification>` (canonical specification: `REVIEW.template.md` at the repository root). This skill produces review *prose* — observations and suggestions a maintainer reads — not a structured audit verdict and not code changes. When a caller needs the deterministic audit verdict alongside the review, it runs the `/auditing` skill separately and combines the two; this skill stays focused on the human-facing review.

Repository-read-only — never edits code, tests, or any repository file. `Bash` is used for two purposes: read operations against GitHub (`gh pr diff`, `gh pr view`) and — in standalone mode only — the single mutating call that posts the review (`gh pr comment --body-file -`). The skill never pushes, merges, or runs `gh pr merge` / `gh pr close` / any write-side `gh` subcommand beyond `gh pr comment`.

</objective>

<reference_loading>

Before reading the diff, invoke `/standardizing-merging` via the Skill tool. The two-severity (`BLOCKING` / `DEBT`) × six-category (`consistency` / `security` / `performance` / `evidence` / `standards` / `architecture`) taxonomy, the severity-rank ban, the prohibition on open questions and bare commentary, and the comment-format examples live there. They are shared with `/managing-pr` (author-side triage) so reviewer output and author triage use the same vocabulary — nothing needs to be translated between the two sides.

</reference_loading>

<scope>

The caller supplies the target PR (`REPO`, `PR NUMBER`). Read the diff with `gh pr diff <number>` and the PR description with `gh pr view <number>`; read the repository's `CLAUDE.md` / `AGENTS.md` for the conventions the review is held against. Do not widen the review beyond the PR's diff — comment on what changed, plus the immediate context needed to judge it.

</scope>

<process>

1. **Load shared standards.** Invoke `/standardizing-merging` via the Skill tool to load the two-severity / six-category taxonomy and comment format used to label every finding.
2. **Read the change.** `gh pr view <number>` for the title, description, and linked issues; `gh pr diff <number>` for the diff. Read the repository's `CLAUDE.md` / `AGENTS.md` and any `REVIEW.md` override at the repository root so the review is grounded in the project's own style and conventions, not generic preferences.
3. **Review across the six categories from `/standardizing-merging` `<review_classification>`:**
   - **`consistency`** — disagreement across layers (decisions / PDR / ADR ↔ spec ↔ tests ↔ implementation). Surface the disagreement; do not judge which side is right.
   - **`security`** — confidentiality, integrity, availability. Injection surfaces, leaked secrets, missing authorization checks.
   - **`performance`** — unbounded loops, hot-path allocations, accidental quadratics, synchronous I/O on async paths — flagged only when it matters for this code path.
   - **`evidence`** — inadequate test or eval coverage of declared assertions; unmaintainable tests; tautology over real coupling.
   - **`standards`** — adherence to `CLAUDE.md` and `standardizing-*` skill rules (naming, command tokens, file structure, language idioms).
   - **`architecture`** — violation of structural principles declared by ADRs or PDRs (layer boundaries, separation of concerns, dependency directions).
4. **Label every finding with one severity × one category from `/standardizing-merging` `<review_classification>`.** Severity is `BLOCKING` or `DEBT` — never `FOLLOW-UP`, never `P0` / `P1` / `critical` / `high` / `medium` / `low` / `minor` / `nit`, never the legacy classes `NEEDS-ANSWER` or `NOTE`. The bracketed dimension after the severity names the category. Cite `file:line` and explain *why* something is a concern, not just *that* it is. Reframe open questions as findings rather than asking; never emit bare commentary or praise that does not constitute a finding.
5. **If the review has no `BLOCKING` or `DEBT` items, say so directly.** Do not manufacture lower-priority findings to prove that review happened.
6. **Deliver the review.** Two invocation modes:
   - **Standalone** (a developer asking for a review, or a workflow invoking only this skill): post the feedback with `gh pr comment <number> --body-file - <<'EOF' ... EOF` (via the `Bash` tool), piping the body on stdin so kilobyte-sized reviews are not truncated by shell-argument limits. One comment per run.
   - **Composed** (the `pr-reviewer` agent invokes this skill alongside `/auditing` and posts one combined comment): return the review prose as the skill's output. Do not post separately — the caller posts the single combined comment.

   **Mode selection is explicit.** The caller passes a `MODE:` line in the invocation prompt — `MODE: composed` for composed mode, `MODE: standalone` for standalone mode. The skill keys on that line; a free-text description of the desired behaviour may accompany it for human readability but is not what the skill matches on. Exactly one `MODE:` line must appear: if the invocation prompt contains no recognisable `MODE: composed` or `MODE: standalone` line, OR contains both `MODE: composed` AND `MODE: standalone` (a template copy-paste accident), STOP and return an error naming which condition was hit — never default silently and never pick one of the conflicting modes. Silent defaulting produces a spurious extra PR comment when a caller's wording drifts, and the failure surfaces months later as duplicate comments; loud failure surfaces the drift on the next CI run.

</process>

<constraints>

- Read-only over the repository — never edit code or tests, never push.
- Ground the review in the repository's `CLAUDE.md` / `AGENTS.md`. Do not invent style rules the project does not hold.
- Stay within the PR's diff plus the immediate context needed to judge it; do not turn a review into a whole-codebase audit.
- Produce review prose, not a structured verdict. The deterministic audit verdict is the `/auditing` skill's job; this skill does not emit one and does not re-implement one.
- Contain zero language-specific tokens — the review concerns are language-agnostic; language-specific evaluation belongs in the language audit skills the `/auditing` skill dispatches to.
- Use the two-severity / six-category taxonomy from `/standardizing-merging` `<review_classification>` — the same vocabulary the author skill `/managing-pr` consumes, so triage requires no translation.

</constraints>

<success_criteria>

- `/standardizing-merging` is loaded before any finding is labeled.
- The invocation prompt carried a recognised `MODE: composed` or `MODE: standalone` line; ambiguous invocations were rejected with an error, not silently defaulted.
- The PR diff and description were read, and the review is grounded in the repository's `CLAUDE.md` / `AGENTS.md` conventions.
- Feedback covers the six categories (`consistency`, `security`, `performance`, `evidence`, `standards`, `architecture`), with `file:line` citations and rationale.
- Every finding is labeled with one severity × one category per `/standardizing-merging` `<review_classification>` — `BLOCKING` / `DEBT`, never `FOLLOW-UP`, never a severity rank, never a legacy class label.
- A review with no `BLOCKING` or `DEBT` items says so directly rather than padding with lower-priority findings.
- **Standalone mode**: the feedback was posted as one `gh pr comment --body-file -` on the target PR.
- **Composed mode**: the review prose was returned to the caller; no `gh pr comment` was issued by this skill.
- No code, tests, or commits were produced; no structured audit verdict was emitted.

</success_criteria>
