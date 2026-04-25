---
name: reviewing-prose
description: >-
  ALWAYS invoke this skill when reviewing, editing, or improving prose for quality.
  NEVER review prose without this skill.
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-prose/SKILL.md"`

<objective>

Detect and fix formulaic patterns that signal machine-generated or lazy writing. Flag specific violations and suggest concrete rewrites.

</objective>

<quick_start>

**Core rule**: Zero tolerance. Every pattern in the reference catalog is a violation. Do not excuse any instance as "single use" or "it lands here." If a sentence triggers a pattern, flag it. If a sentence triggers two patterns simultaneously, it is the highest priority flag.

**Before reviewing**, read `/standardizing-prose` for the complete catalog of 30+ anti-patterns across 6 categories.

</quick_start>

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

1. Read `/standardizing-prose` for the anti-pattern catalog
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

| Skill                  | When to Read               |
| ---------------------- | -------------------------- |
| `/standardizing-prose` | Always -- before reviewing |

</reference_index>
