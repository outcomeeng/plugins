---
name: open-parent-issue
description: >-
  ALWAYS invoke this skill when filing an issue in a repository the operator does not control — a fork's parent, or any base whose permission is READ or NONE.
  NEVER open an issue against such a repository without this skill.
argument-hint: "[what was observed]"
allowed-tools: Read, Glob, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_target.py":*), Bash(gh issue create:*), Bash(gh search issues:*), Bash(git log:*), Bash(printf:*)
---

<objective>
One issue open in a repository the operator does not control, carrying an observation its maintainer can reproduce without access to the operator's machine.
</objective>

<workflow>

**Step 1 — Load the standards and read the invocation input.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS`, when non-empty, is the observation this report is built around: it supplies Step 3's distinguishing search terms, Step 4's claim to gather evidence for, and Step 5's one-sentence summary. When it is empty, ask the operator what was observed before Step 3, because a report has no subject without it.

**Step 2 — GATE: Resolve the target.** Run the resolver named in `/contribution-standards` `<resolution>`. Report `base` and `permission` verbatim.

An issue needs no head repository, so both `parent-contribution` and `fork-absent` continue here — the absent fork blocks a pull request, never a report. `controlled` stops: an issue in a repository the operator controls belongs to that repository's own workflow. `blocked` stops with the resolver's `detail` verbatim.

**Step 3 — Search before filing.** Search the base repository for an existing issue describing the same observation:

```bash
gh search issues --repo "<base>" --state all "<distinguishing terms>"
```

An existing issue takes a comment through `/manage-parent-issue`, not a duplicate. Report what the search returned.

**Step 4 — Assemble the evidence.** Per `/contribution-standards` `<invariants>` "Carry reproducible evidence", collect: the versions of every tool involved, the base repository commit the observation was made against, the exact command or interaction that produced it, and a negative control showing the same method reporting the opposite result.

A claim without a negative control cannot distinguish a defect from a broken measurement, and a maintainer has no way to tell which they received. When the condition cannot be reproduced in the real surface, say so and say why; never substitute a lookalike and report it as observed.

**Step 5 — GATE: Obtain authorization.** Present, through the runtime's structured-question tool, the resolved `base`, the issue title, the observation in one sentence, and the choice to file it against that base or to stop and inspect. Create nothing until the operator authorizes it in this turn.

**Step 6 — GATE: Review the outward text.** Draft the title and body per `<report_shape>`, then review them — the prose plugin's `prose-auditor` agent where installed, `/contribution-standards` `<outward_text>` unassisted where not, stated as such in the report.

**Step 7 — File it.** Interactive sessions pipe the body through a quoted heredoc:

```bash
gh issue create --repo "<base>" --title "<title>" --body-file - <<'EOF'
<what was observed>

## Reproduction

<versions, base commit, exact command>

## Negative control

<the same method reporting the opposite result>
EOF
```

Programmatic runners use one `printf` argument per output line piped into the same command. Never assemble the body through a temporary file, command substitution, or post-hoc repair.

**Step 8 — Hand off.** Surface the issue URL. `/manage-parent-issue` owns every later pass on the thread.

</workflow>

<report_shape>

The title names the observed behavior, not the suspected cause.

The body opens with what was observed, in the surface a maintainer recognizes. Then:

- **Reproduction** — tool versions, the base repository commit observed against, and the exact command or interaction. Quote output rather than describing it.
- **Negative control** — the same method reporting the opposite result, which is what separates a defect from a broken measurement.
- What was inferred rather than observed, marked as inference. An unreproduced condition is stated as unverified.

Leave the fix to the maintainer unless they asked for one. A report that prescribes an implementation constrains a decision that is theirs.

</report_shape>

<constraints>

- MUST resolve the target through the bundled resolver before the first write.
- MUST search the base repository for an existing issue before filing a new one.
- MUST obtain authorization naming the resolved base in the same turn.
- MUST name the base repository with `--repo` on `gh issue create`.
- MUST carry a negative control with every defect claim.
- NEVER file against a base whose classification is `controlled` or `blocked`.
- NEVER present a synthesized approximation of the condition as an observation.

</constraints>

<success_criteria>

- The resolver returned `parent-contribution` or `fork-absent`, and `base` and `permission` appear verbatim.
- A search for an existing issue ran and its result is reported.
- The operator authorized this issue against the resolved base in the turn it was filed.
- The body carries tool versions, the base commit observed against, the exact command, and a negative control.
- Every inference is marked as inference and every unreproduced condition as unverified.
- The title and body passed a prose review, reported as unassisted where the prose plugin is absent.
- `gh issue create` named the base with `--repo` and the body arrived on stdin.
- The issue URL is surfaced.

</success_criteria>
