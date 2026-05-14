---
name: reviewing-pr
disable-model-invocation: true
description: Use when asked by the user to invoke the PR review skill
allowed-tools: Read, Bash, Glob, Grep
---

<objective>

Review a pull request and return constructive, repository-grounded feedback. This skill produces review *prose* — observations and suggestions a maintainer reads — not a structured audit verdict and not code changes. When a caller needs the deterministic audit verdict alongside the review, it runs the `/auditing` skill separately and combines the two; this skill stays focused on the human-facing review.

Repository-read-only — never edits code, tests, or any repository file. `Bash` is used for two purposes: read operations against GitHub (`gh pr diff`, `gh pr view`) and — in standalone mode only — the single mutating call that posts the review (`gh pr comment --body-file -`). The skill never pushes, merges, or runs `gh pr merge` / `gh pr close` / any write-side `gh` subcommand beyond `gh pr comment`.

</objective>

<scope>

The caller supplies the target PR (`REPO`, `PR NUMBER`). Read the diff with `gh pr diff <number>` and the PR description with `gh pr view <number>`; read the repository's `CLAUDE.md` / `AGENTS.md` for the conventions the review is held against. Do not widen the review beyond the PR's diff — comment on what changed, plus the immediate context needed to judge it.

</scope>

<process>

1. **Read the change.** `gh pr view <number>` for the title, description, and linked issues; `gh pr diff <number>` for the diff. Read the repository's `CLAUDE.md` / `AGENTS.md` so the review is grounded in the project's own style and conventions, not generic preferences.
2. **Review against five concerns:**
   - **Code quality and conventions** — does the change follow the repository's conventions (the ones in `CLAUDE.md` / `AGENTS.md`), and is it clear and maintainable?
   - **Bugs and correctness** — logic errors, unhandled edge cases, broken invariants, off-by-ones, resource leaks.
   - **Performance** — needless work, accidental quadratics, unbounded growth — flagged only when it matters for this code path.
   - **Security** — injection surfaces, unsanitised input flowing to a shell or query, leaked secrets, missing authorization checks.
   - **Test coverage** — does the change carry tests for the behaviour it adds or alters, and do those tests exercise real coupling rather than tautology?
3. **Write the feedback.** Group it by concern. Be specific: cite `file:line` and explain *why* something is a concern, not just *that* it is. Distinguish must-fix items from suggestions. Acknowledge what the change does well — a review that is only criticism is harder to act on.
4. **Deliver the review.** Two invocation modes:
   - **Standalone** (a developer asking for a review, or a workflow invoking only this skill): post the feedback with `gh pr comment <number> --body-file - <<'EOF' ... EOF` (via the `Bash` tool), piping the body on stdin so kilobyte-sized reviews are not truncated by shell-argument limits. One comment per run.
   - **Composed** (the `pr-reviewer` agent invokes this skill alongside `/auditing` and posts one combined comment): return the review prose as the skill's output. Do not post separately — the calling agent posts the single combined comment.

   **Mode selection is explicit.** The caller passes a `MODE:` line in the invocation prompt — `MODE: composed` for composed mode, `MODE: standalone` for standalone mode. The skill keys on that line; a free-text description of the desired behaviour may accompany it for human readability but is not what the skill matches on. Exactly one `MODE:` line must appear: if the invocation prompt contains no recognisable `MODE: composed` or `MODE: standalone` line, OR contains both `MODE: composed` AND `MODE: standalone` (a template copy-paste accident), STOP and return an error naming which condition was hit — never default silently and never pick one of the conflicting modes. Silent defaulting produces a spurious extra PR comment when a calling agent's wording drifts, and the failure surfaces months later as duplicate comments; loud failure surfaces the drift on the next CI run.

</process>

<constraints>

- Read-only over the repository — never edit code or tests, never push.
- Ground the review in the repository's `CLAUDE.md` / `AGENTS.md`. Do not invent style rules the project does not hold.
- Stay within the PR's diff plus the immediate context needed to judge it; do not turn a review into a whole-codebase audit.
- Produce review prose, not a structured verdict. The deterministic audit verdict is the `/auditing` skill's job; this skill does not emit one and does not re-implement one.
- Contain zero language-specific tokens — the review concerns are language-agnostic; language-specific evaluation belongs in the language audit skills the `/auditing` skill dispatches to.

</constraints>

<success_criteria>

- The invocation prompt carried a recognised `MODE: composed` or `MODE: standalone` line; ambiguous invocations were rejected with an error, not silently defaulted.
- The PR diff and description were read, and the review is grounded in the repository's `CLAUDE.md` / `AGENTS.md` conventions.
- Feedback covers the five concerns (quality, bugs, performance, security, test coverage), grouped, with `file:line` citations and rationale, distinguishing must-fix from suggestions.
- **Standalone mode**: the feedback was posted as one `gh pr comment --body-file -` on the target PR.
- **Composed mode**: the review prose was returned to the calling agent; no `gh pr comment` was issued by this skill.
- No code, tests, or commits were produced; no structured audit verdict was emitted.

</success_criteria>
