---
name: standardizing-agent-prompts
user-invocable: false
description: >-
  Agent prompt writing conventions enforced across all creator and auditor skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical reference for writing agent prompts — the text content within SKILL.md files, slash command bodies, and subagent system prompts. Covers voice, description style, constraint language, and anti-patterns. Creator skills reference these conventions when authoring; auditor skills check compliance against them.

This skill governs prompt *craft* (how to write text). Prompt *structure* (which XML tags to use, file organization) is governed by the creator skills themselves.
</objective>

<reference_note>
This is a reference skill. Creator and auditor skills load these conventions automatically. Invoke `/creating-skills`, `/creating-commands`, or `/creating-subagents` to author; invoke `/auditing-skills`, `/auditing-commands`, or `/auditing-subagents` to review.
</reference_note>

<voice>

**How to refer to the executing Claude instance in prompt bodies.**

Two-tier hierarchy:

1. **Imperative mood (default)** — drop the subject when giving instructions:
   - "Reflect deeply on what was learned before persisting anything"
   - "Read the spec file before proposing changes"

2. **"Claude" (for failure modes, tendencies, and behavioral claims)** — use when naming what Claude does, tends to do, or fails to do:
   - "Without reflection, Claude will dump a narrative instead of making durable decisions"
   - "Claude loses track of coverage state after 30+ turns"

**Banned subjects:**

| Subject     | Problem                                                                                                          |
| ----------- | ---------------------------------------------------------------------------------------------------------------- |
| "the agent" | Anthropic's own skills use "Claude" exclusively; "the agent" appears zero times across 18 shipped SKILL.md files |
| "the model" | Too generic, distances Claude from its own identity                                                              |
| "you"       | Ambiguous — could address Claude or the user                                                                     |

**YAML frontmatter exception:** The `name` and `description` fields cannot contain the word "claude" per validation rules. Omit any subject in descriptions — use the directive pattern directly ("ALWAYS invoke this skill when...").

**Evidence:** Anthropic-authored skills use "Claude" as the named subject ~70 times. "The agent" appears zero times. Imperative mood is the most common voice for direct instructions.

</voice>

<description_style>

**Directive descriptions for reliable activation.**

Research (650 automated trials) shows description wording has a 20x impact on activation odds:

| Style         | Activation | Example                                         |
| ------------- | ---------- | ----------------------------------------------- |
| Passive       | ~77%       | `Docker expert for containerization. Use when…` |
| Expanded      | ~93%       | `…or any Docker-related task`                   |
| **Directive** | **~100%**  | `ALWAYS invoke… NEVER X without this skill`     |

**Base template:**

```yaml
description: >-
  ALWAYS invoke this skill when <triggers>.
```

**NEVER constraint — add only when it disambiguates.** A NEVER line helps when:

- The skill is the only one with that negative
- Claude has a strong built-in alternative the negative prevents

Omit NEVER when:

- Multiple skills share the same negative
- The ALWAYS trigger is already specific enough

**Language-after-artifact** (matches user speech):

```yaml
# ✅ "audit ADRs for Python" — matches what users say
ALWAYS invoke this skill when auditing ADRs for Python.

# ❌ "audit Python ADRs" — unnatural phrasing
ALWAYS invoke this skill when auditing Python ADRs.
```

**Match actual user speech:**

- Abbreviations: "ADRs" not "Architecture Decision Records"
- Natural terms: "testing-python" not "python-unit-test-framework"
- Plain language: "read all specs" not "hierarchical context ingestion protocol"

**Reference skills** use `disable-model-invocation: true` with a passive description:

```yaml
disable-model-invocation: true
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
```

</description_style>

<constraint_language>

**Strong modal verbs for constraints:**

- `MUST` — required behavior, no exceptions
- `NEVER` — prohibited behavior, no exceptions
- `ALWAYS` — required in every case

**Weak modals to avoid in constraint blocks:**

- "should" — implies optional
- "try to" — invites half-measures
- "consider" — without a specific condition, this is noise
- "might want to" — means nothing actionable

Weak modals are fine in non-constraint contexts — recommendations, trade-off discussions, conditional guidance. The rule applies to constraint blocks (`<constraints>`, hardened rules in workflows).

**Pattern — constraint with rationale:**

```text
NEVER modify files during audit — audits are read-only by design.
MUST read reference documentation before evaluating — prevents memory-based assessment.
```

The rationale after the dash prevents blind rule-following and helps Claude judge edge cases.

</constraint_language>

<anti_patterns>

**Banned phrases in prompt text:**

| Pattern             | Problem                    | Fix                                                        |
| ------------------- | -------------------------- | ---------------------------------------------------------- |
| "helpful assistant" | Generic, zero signal       | State the specific domain and expertise                    |
| "helps with"        | Vague                      | Name the concrete action                                   |
| "processes data"    | Could mean anything        | Name the specific data and operation                       |
| "the agent"         | Not Anthropic convention   | Use imperative or "Claude" (see `<voice>`)                 |
| "you should"        | Ambiguous addressee        | Use imperative                                             |
| "please"            | Wastes tokens, no effect   | Direct instruction                                         |
| "if possible"       | Hedges the instruction     | State the instruction; add a fallback if the hedge is real |
| "try to"            | Invites partial compliance | State the requirement                                      |

**Structural anti-patterns:**

- **Explaining Claude to Claude** — "As an AI language model..." wastes context. Claude knows what it is.
- **Motivational prose** — "This is a critical task that requires careful attention" adds nothing. State the constraints.
- **Repeating the skill name** — "The creating-skills skill is designed to..." — Claude has the name from frontmatter.
- **Empty disclaimers** — "Results may vary" — if there are real failure modes, document them concretely; if not, cut the disclaimer.

</anti_patterns>

<conciseness>

**The test for every sentence in a prompt:**

"Does removing this reduce Claude's effectiveness at the task?"

If no — cut it.

**What Claude already knows (never include):**

- General programming knowledge
- Language syntax and standard library APIs
- Common design patterns
- How to use its own tools

**What Claude needs (include):**

- Project-specific conventions that contradict common patterns
- Domain knowledge not in training data
- Failure modes from actual usage (not hypotheticals)
- Verification commands and thresholds

**Concrete over abstract:**

```text
# ❌ Abstract
"Ensure coverage is maintained"

# ✅ Concrete
"Coverage delta must be ≤0.5%. Run: pnpm test --coverage | grep target.ts"
```

</conciseness>

<failure_mode_writing>

Failure modes are among the most valuable content in a skill. Write them from actual experience, not speculation.

**Structure each failure mode:**

1. **What happened** — concrete scenario with specifics
2. **Why it failed** — root cause, not symptom
3. **How to avoid** — actionable prevention

**Use "Claude" as the subject** (failure modes are the primary case for named-subject voice):

```text
✅ Claude compared coverage per-story instead of per-file. Multiple stories share one
   legacy file; per-story coverage is meaningless.

❌ "Compare coverage per-file, not per-story."
   (States the rule but loses the WHY — the failure mode teaches the reason.)
```

Never invent failure modes. If a skill is new and hasn't failed yet, omit the section rather than fabricating scenarios. Add failure modes as they occur in real usage.

</failure_mode_writing>

<success_criteria>

A prompt that follows these conventions:

- Uses imperative mood for instructions, "Claude" for failure modes and tendencies
- Never uses "the agent", "the model", or "you"
- Has a directive description (ALWAYS + optional NEVER) unless it is a reference skill
- Uses strong modal verbs (MUST/NEVER/ALWAYS) in constraint blocks
- Contains no banned phrases or structural anti-patterns
- Includes only information Claude doesn't already have
- Documents failure modes from actual usage with concrete specifics

</success_criteria>
