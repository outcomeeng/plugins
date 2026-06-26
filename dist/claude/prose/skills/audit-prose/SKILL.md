---
name: audit-prose
description: >-
  ALWAYS invoke this skill when auditing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers.
  NEVER invoke for chat responses to the user (no matter how long), operational prose like code comments, commit messages, or agent-facing instructions like SKILL.md.
allowed-tools: Read, Glob, Grep, Bash, Skill
---

Invoke the `prose:prose-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

A list of formulaic, machine-generated, or lazy-writing patterns found in reader-facing prose, each flagged with a concrete rewrite.

</objective>

<essential_principles>

Six categories of patterns to detect. Each is detailed with examples in the reference file.

**Word choice** -- Significance adverbs ("quietly", "deeply"), authenticity adverbs ("genuinely", "truly", "actually"), overused vocabulary ("delve", "leverage", "robust", "genuine"), ornate nouns ("tapestry", "landscape", "paradigm"), pompous verbs ("serves as", "stands as").

**Sentence structure** -- Negative parallelism ("It's not X -- it's Y"), stacked negations ("Not X. Not Y. Just Z."), rhetorical self-answers ("The result? Devastating."), anaphora abuse, tricolon stacking, filler transitions ("It's worth noting"), tacked-on significance ("highlighting its importance"), false ranges, gerund fragment litanies, tautological definitions ("An irreversible change does not revert"), redundant paired examples.

**Paragraph structure** -- Strings of punchy fragments as standalone paragraphs, listicles disguised as prose ("The first... The second... The third...").

**Tone** -- False-suspense transitions ("Here's the kicker"), unnecessary metaphors ("Think of it as..."), hypothetical openers ("Imagine a world where..."), performed vulnerability, asserting clarity ("The truth is simple"), grandiose stakes inflation, teacher-student condescension ("Let's break this down"), vague attributions ("Experts argue"), invented concept labels ("the supervision paradox").

**Formatting** -- Em-dash overuse, bold-first bullets, unicode decoration.

**Composition** -- Fractal summaries, dead metaphors, historical analogy stacking, one-point dilution, content duplication, signposted conclusions, dismissive optimism ("Despite its challenges...").

</essential_principles>

<workflow>

1. Read `/prose-standards` for the anti-pattern catalog
2. Read the text to review
3. Flag each violation with the specific pattern name and category
4. Suggest concrete rewrites -- don't just say "avoid X", show the fix
5. Summarize: total violations found, most frequent category, overall assessment

</workflow>

<success_criteria>

Review is complete when:

- Every flagged violation names the specific pattern and category
- Every flag includes a concrete rewrite, not just a label
- The summary gives a count, identifies the most frequent category, and assesses overall quality
- Zero tolerance -- every pattern match is flagged as a violation, never excused as "single use" or "it works here"
- Co-occurring patterns in a single sentence are the highest-priority flags

</success_criteria>

<reference_index>

| Skill              | When to Read              |
| ------------------ | ------------------------- |
| `/prose-standards` | Always -- before auditing |

</reference_index>
