---
name: open-upstream-issue
description: >-
  ALWAYS invoke this skill when filing an issue in a repository the operator does not control — a fork's upstream, or any base whose permission is READ, TRIAGE, or NONE.
  NEVER open an issue against such a repository without this skill.
argument-hint: "[what was observed]"
allowed-tools: Read, Skill, multi_agent_v1.spawn_agent, multi_agent_v1.wait_agent, multi_agent_v1.close_agent, request_user_input, Bash(gh issue create:*), Bash(gh search issues:*), Bash(printf:*)
---

<objective>
One issue open in a repository the operator does not control, carrying an observation its maintainer can reproduce without access to the operator's machine — or the existing issue that already reports it, named instead of duplicated.
</objective>

<workflow>

**Step 1 — Load the standards and read the invocation input.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS`, when non-empty, is the observation this report is built around: it supplies Step 3's distinguishing search terms, Step 4's claim to gather evidence for, and Step 5's one-sentence summary. When it is empty, present, through the runtime's structured-question tool, the request for what was observed, before Step 3, because a report has no subject without it.

**Step 2 — GATE: Establish the target.** Read the live `<UPSTREAM_TARGET>` marker; invoke `/upstream` when none is live. Report `base` and `permission` verbatim.

An issue needs no head repository, so `upstream-contribution`, `head-ambiguous`, and `fork-absent` all continue here — an absent or ambiguous head blocks a pull request, never a report. `controlled` stops: an issue in a repository the operator controls belongs to that repository's own workflow. `blocked` stops with the resolver's `detail` verbatim.

**Step 3 — Search before filing.** Search the base repository for an existing issue describing the same observation:

```bash
gh search issues --repo "<base>" --state open "<distinguishing terms>"
gh search issues --repo "<base>" --state closed "<distinguishing terms>"
```

Both states are searched because `gh search issues --state` accepts only `open` or `closed`; passing `all` fails the command and would stop the flow before duplicate detection runs. A closed issue matters as much as an open one — it may record that the maintainer already rejected this report.

Report what both searches returned.

**STOP when either search matched this observation.** Surface that issue's URL and return; Steps 4 through 8 do not run. An existing issue takes a comment through `/manage-upstream-issue`, never a duplicate, and a duplicate filed into a repository the operator does not control cannot be taken back by deciding afterwards that the search had already answered.

**Step 4 — Assemble the evidence.** Per `/contribution-standards` `<invariants>` "Carry reproducible evidence", collect: the versions of every tool involved, the base repository commit the observation was made against, the exact command or interaction that produced it, and a negative control showing the same method reporting the opposite result. Those probes belong to the subject tool rather than to this skill, so they run per `/contribution-standards` `<capability_scope>`.

A claim without a negative control cannot distinguish a defect from a broken measurement, and a maintainer has no way to tell which they received. When the condition cannot be reproduced in the real surface, say so and say why; never substitute a lookalike and report it as observed.

**Step 5 — GATE: Obtain authorization.** Present, through the runtime's structured-question tool, the resolved `base`, the issue title, the observation in one sentence, and the choice to file it against that base or to stop and inspect. Create nothing until the operator authorizes it in this turn.

**Step 6 — GATE: Review the outward text.** Draft the title and body per `<report_shape>`, then review them — the prose plugin's `prose-auditor` thin agent where installed, `/contribution-standards` `<outward_text>` unassisted where not, stated as such in the report.

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

Programmatic runners that require one physical command line use one `printf` argument per output line piped into the same command:

```bash
printf '%s\n' '<what was observed>' '' '## Reproduction' '' '<versions, base commit, exact command>' '' '## Negative control' '' '<the same method reporting the opposite result>' | gh issue create --repo "<base>" --title "<title>" --body-file -
```

Never assemble the body through a temporary file, command substitution, or post-hoc repair.

**Step 8 — Hand off.** Surface the URL of the issue this pass filed. `/manage-upstream-issue` owns every later pass on the thread, including the first one on an issue Step 3 found rather than filed.

</workflow>

<report_shape>

The title names the observed behavior, not the suspected cause.

The body opens with what was observed, in the surface a maintainer recognizes. Then:

- **Reproduction** — tool versions, the base repository commit observed against, and the exact command or interaction. Quote output rather than describing it.
- **Negative control** — the same method reporting the opposite result, which is what separates a defect from a broken measurement.
- What was inferred rather than observed, marked as inference. An unreproduced condition is stated as unverified.

Leave the fix to the maintainer unless they asked for one. A report that prescribes an implementation constrains a decision that is theirs.

</report_shape>

<worked_example>

One report against a fictional base `acme/parser`, to compare a draft against.

Title: `--strict is ignored when the config file sets strict: false`

Body:

```text
`parser --strict` exits 0 on input that `strict: true` in the config file
rejects. The flag is accepted and changes nothing.

## Reproduction

parser 4.2.0, Python 3.13.2, macOS 15.3
acme/parser at 4f9c2a1

$ printf 'strict: false\n' > parser.yml
$ printf 'a = = 1\n' > sample.txt
$ parser --strict sample.txt; echo "exit $?"
exit 0

## Negative control

The same input with the flag's effect present:

$ printf 'strict: true\n' > parser.yml
$ parser sample.txt; echo "exit $?"
sample.txt:1:5: unexpected '='
exit 1

The parse error exists and the config file surfaces it, so the exit 0 above is
the flag failing rather than the input parsing cleanly.
```

The title names what the run observed rather than the precedence bug it suspects. The negative control is the same command and the same input with one value changed, so it separates a defect from a broken measurement. The report proposes no fix and names no line of source, because where the flag and the file merge is the maintainer's to decide.

</worked_example>

<constraints>

- MUST read the resolved target from a live `<UPSTREAM_TARGET>` marker before the first write, invoking `/upstream` when none is live.
- MUST search the base repository for an existing issue before filing a new one.
- MUST obtain authorization naming the resolved base in the same turn.
- MUST name the base repository with `--repo` on `gh issue create`.
- MUST carry a negative control with every defect claim.
- NEVER file against a base whose classification is `controlled` or `blocked`.
- NEVER present a synthesized approximation of the condition as an observation.

</constraints>

<success_criteria>

- The `<UPSTREAM_TARGET>` marker read for this pass carries `upstream-contribution`, `head-ambiguous`, or `fork-absent`, and `base` and `permission` appear verbatim.
- A search for an existing issue ran and its result is reported.
- A search that matched surfaced that issue's URL and filed nothing; every criterion below covers a pass that filed.
- The operator authorized this issue against the resolved base in the turn it was filed.
- The body carries tool versions, the base commit observed against, the exact command, and a negative control.
- Every inference is marked as inference and every unreproduced condition as unverified.
- The title and body passed a prose review, reported as unassisted where the prose plugin is absent.
- `gh issue create` named the base with `--repo` and the body arrived on stdin.
- The issue URL is surfaced.

</success_criteria>
