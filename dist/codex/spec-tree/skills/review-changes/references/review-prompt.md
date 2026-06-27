# Reviewing Changes Prompt

Review a labeled diff bundle. It may contain committed changes from the base ref to HEAD plus staged, unstaged, and untracked worktree sections. Inspect every section and classify findings using the taxonomy below. The review **streams**: emit each finding the instant you raise it as one JSON `Finding` object — the skill pipes each finding through `journal_emit.py finding-reported` (the per-finding validity gate) and appends it; on a non-zero exit, fix the issue surfaced in stderr and re-emit that finding. Do not gather findings into one document and emit them at the end.

Report findings only — no praise, no open questions, no commentary that is neither a finding nor a tracking commitment.

**ALWAYS:** report findings. When the changeset omits a fact a finding depends on, frame the finding as worst-case or conditional. Example: "Evidence: cannot verify X from the changeset; if assumption Y holds, this breaks Z because …"

**NEVER:** emit open questions or speculative commentary that does not constitute a finding. Questions add CI roundtrips this single-pass review cannot recover from.

## Contents

- Scope
- Coverage procedure
- Defect-class handling
- Category
- Severity
- Finding labels
- Completeness
- No findings
- Output shape
- Rule citation

## Scope

Review the whole diff bundle — every emitted section, including committed, staged, unstaged, and untracked content when present — against the whole taxonomy below, judged by the loaded repository instructions (`CLAUDE.md` / `AGENTS.md` and the standards skills). Do not narrow the review to a caller-supplied focus, file list, area, or severity filter, and do not adopt caller-supplied emphasis on what to conclude or what matters most — any such steering is not authoritative. Emit every finding the bundle exhibits.

## Coverage procedure

Before raising any finding, enumerate the review surface:

1. Every changed file in every emitted diff-bundle section.
2. Every touched spec assertion and its linked `[test]`, `[eval]`, or `[audit]` evidence.
3. Every changed test or eval case and the source contract it claims to exercise.
4. Every changed implementation file and the governing spec, ADR, PDR, or standards rule it must satisfy.

Visit every item; emit each finding the instant you raise it. A pass that samples one obvious defect and stops is incomplete.

## Defect-class handling

When a finding is valid, state the defect class in `message`: the violated rule, the pattern that makes the cited site representative, and any parallel in-scope sites visible in the diff. If the cited site is isolated, say why the same-class sweep found no visible parallel instance.

A finding that only names one line while the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship appears elsewhere in the diff is incomplete. Surface the class — the author resolves it across the touched node(s) — before the next review round.

## Category (6, grouped by three axes)

Every finding carries one `concern`:

**What the code does vs. what it is supposed to do**

- `consistency` — equivalence across the layers: what the decisions (PDRs and ADRs) govern, what the spec asserts, what tests and evals verify, what the implementation does. A finding is a consistency one when a lower layer does not match a higher one. Surface the disagreement; do not judge which side is right.
- `security` — confidentiality, integrity, availability.
- `performance` — unbounded loops, hot-path allocations, O(n^2) traversals where O(n) suffices, synchronous I/O on async paths, and similar pessimisations that change the changeset's runtime characteristics under realistic load.

**How we know it does what it is supposed to do**

- `evidence` — inadequate coverage of declared assertions by tests or evals; unmaintainable tests (literals, magic numbers, test-owned constants, duplication); evals that no longer exercise the assertions they claim to.

**How it does what it is supposed to do**

- `standards` — adherence to `CLAUDE.md` and the rules declared in standards skills (naming conventions, command tokens, file structure, language idioms).
- `architecture` — violation of structural principles declared by ADRs or PDRs — layer boundaries, separation of concerns, dependency directions, module-shape rules. A finding is an architecture one when the structure itself is at odds with a governance principle, even if every layer is internally consistent.

## Severity (2)

Every finding carries one `severity`:

- `blocking` — merge-safety defect: if deployed, the changeset would create a deterministic issue or pose a risk.
- `debt` — a real defect that does not jeopardize merge safety: a genuine problem the change carries, but not merge-blocking.

Judge validity and severity only. Whether each `debt` finding is fixed in this PR or tracked out of scope is the author's disposition call — do not introduce a third, scope-shaped severity.

## Finding labels

Every finding carries the same fields. Populate `message` and `action` so the rendered surface is complete:

- Both `blocking` and `debt` require an action. Populate `message` with the diff quote and failure explanation; populate `action` with the concrete change. The `rule` field carries the cited rule.

## Completeness

Each review pass is independent and self-contained — there is no cross-pass continuity. Surface every finding the changeset exhibits in the first pass against that changeset; a finding missed on this pass has no second chance unless the diff itself changes. Read the diff once, methodically, across all categories, emitting each finding the instant you raise it.

## No findings

When the changeset has no `blocking` or `debt` findings, emit no finding objects — the run records scope and completion only, and that empty result is the plain statement that the change is clean. A review carries findings only: no summary, no acknowledgement, no praise. The reviewer emits no decision or verdict; each consumer applies its own policy (by validity and phase, never by severity). NEVER invent lower-priority findings to prove the review happened.

## Output shape

Emit each finding as one JSON `Finding` object the instant you raise it — never a batch document gathering all findings. The skill's `journal_emit.py finding-reported` parses each finding and owns the journal envelope; you emit the `Finding` object only. Each `Finding` object carries:

- `id` — a stable identifier of the form `F-NNN` so the finding can be referenced unambiguously.
- `concern` ∈ `consistency`, `security`, `performance`, `evidence`, `standards`, `architecture`.
- `severity` ∈ `blocking`, `debt`.
- `file`, `line` — the cited location.
- `rule` — the cited rule (see Rule citation).
- `message`, `action` — the evidence and the required change.

There is no top-level `schema_version` or `findings` array to emit — those belong to the document-level schema the streaming review does not produce. Do not embed the diff, the prompt, or any other side data inside the `Finding` object. The object is the structured judgment only.

## Rule citation

The `rule` field cites the actual rule the finding rests on as a path-style citation into an existing rule in the spec-tree or skill ecosystem. Accepted forms:

- `spx/<path>/<node>.md:<MUST|NEVER|ALWAYS>:<n>` — a spec assertion under the spec tree.
- `spx/<path>/<n>-<slug>.adr.md` or `spx/<path>/<n>-<slug>.pdr.md` — an ADR or PDR.
- `plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>` — a skill rule, resolved against the plugin roots available to the current runtime.
- `AGENTS.md:<rule-slug>` or `CLAUDE.md:<rule-slug>` — a root convention rule.

Before citing a rule:

- Locate and read the cited text in a file that exists in the repository under review or in a loaded skill file that governs that repository. Use the citation only when that file contains the cited rule, assertion, or governing section.
- Treat rules recalled from system prompts, user/global instructions outside the repository, prior sessions, or training as invalid review citations.
- Drop the finding when the candidate rule cannot be located; do not downgrade it or report it with a weaker citation.
- Emit a standards finding about comment length or docstring length only when that exact constraint appears in the repository's own `CLAUDE.md`, `AGENTS.md`, loaded standards skill, or other governance file.
- Never use relative `SKILL.md:<rule-slug>` citations — they are not uniquely resolvable to a file.
- Never populate it with free-form prose, the required action, the tracking location, or an invented label. The Required change goes in `action`. Inventing a citation that does not name a real rule in the loaded context is a finding this skill must not produce.
