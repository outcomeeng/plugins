---
name: agent-prompt-standards
user-invocable: false
description: >-
  Agent prompt writing conventions enforced across all creator and auditor skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The agent-prompt writing conventions and their rule catalog — voice, objective shape, description wording, constraint language, anti-patterns, conciseness, and failure-mode writing — for the text within SKILL.md files and subagent system prompts.
</objective>

<reference_note>
This is a reference skill governing prompt *craft* — how to write the text. Prompt *structure* — which XML tags, file organization, and frontmatter — belongs to `/skill-standards` for a skill and to `/subagent-standards` for a subagent definition. It carries no standalone workflow.
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

**YAML frontmatter exception:** The `name` and `description` fields cannot contain the word "claude" per validation rules. Omit any subject in descriptions and word them per `<description_style>`.

</voice>

<objective_shape>

**An `<objective>` states the skill's output, not an activity or an actor.** It describes the observable artifact or state the skill produces, in a definite shape — what is true when the skill has been applied correctly, such that "every rule followed exactly" is the visible proof. It never opens with an actor ("The skill produces…", "Claude produces…") or a bare activity verb ("Audit…", "Generate…", "Evaluate…"). It names the output and its required shape.

**One sentence — it is the output target, not a summary of the skill.** Write one sentence; reach for a second only when the output has two distinct parts. A paragraph-length objective is the smell that activation, workflow, or constraints have leaked in. The litmus: every clause must name a property of the *output*. A clause that says *when* the skill runs belongs in `description`; *how* it runs (steps, gates, orchestration) belongs in `<workflow>`; *what it must not do* belongs in `<constraints>`. Delete such clauses from the objective — they are not new truth to relocate, they already live in those sections. `/manage-github-pr`'s output is "the changeset merged into the default branch on origin through a pull request," not the paragraph that narrates how it gets there.

**Common shapes by skill family** — name the output, never the activity:

- **Auditor** → "A verdict on X — &lt;the finding categories&gt;" (the canonical auditor shape; see `/skill-standards` `references/auditor-skeleton.md`).
- **Coder / builder** → "The &lt;artifact&gt; that &lt;holds the property&gt;" — e.g. "Python implementation code that makes its node's tests pass."
- **Reference / standards** → "The &lt;standards or vocabulary&gt; &lt;scope&gt;" — e.g. "The Python-specific test standards every Python skill enforces."
- **Router** → "A &lt;request&gt; routed to its matching workflow" — the routing outcome, not the menu.
- **Orchestrator** → the end-state its lifecycle produces — e.g. "the changeset merged to the default branch on origin," not the step sequence.

**An objective is not a behavioral claim.** `<voice>` governs behavioral claims — what Claude does, tends to do, or fails to do. An objective is an output statement, a different category, so the imperative-vs-"Claude" subject choice never applies to it. Naming an actor as the subject of an objective is the error the output framing removes.

This mirrors the methodology's output / outcome / impact distinction — assertions specify the **output**, and an objective names the skill's output the same way. `<success_criteria>` proves it: the objective names the output and its shape, `<success_criteria>` states the properties that make it sound, and the two never duplicate.

</objective_shape>

<description_style>

**The owning structure standard selects the style; this section governs the wording.** `/skill-standards` `<descriptions>` selects directive or passive wording for a skill, and `/subagent-standards` owns a subagent definition's frontmatter, its description among it. The wording below applies to every description written in the directive style.

**Directive descriptions for reliable activation.**

Research (Seleznov, 650 automated trials, Feb 2026) shows description wording has a 20x impact on activation odds:

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

- The skill is the only one with that negative (e.g., `NEVER work on the spec tree without loading context` — only contextualizing says this)
- Claude has a strong built-in alternative the negative prevents (e.g., `NEVER run git commit without this skill` — Claude would otherwise run `git commit` directly)

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
- Natural terms: "test-python" not "python-unit-test-framework"
- Plain language: "read all specs" not "hierarchical context ingestion protocol"

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

| Pattern             | Problem                  | Fix                                                        |
| ------------------- | ------------------------ | ---------------------------------------------------------- |
| "helpful assistant" | Generic, zero signal     | State the specific domain and expertise                    |
| "helps with"        | Vague                    | Name the concrete action                                   |
| "processes data"    | Could mean anything      | Name the specific data and operation                       |
| "please"            | Wastes tokens, no effect | Direct instruction                                         |
| "if possible"       | Hedges the instruction   | State the instruction; add a fallback if the hedge is real |

`<voice>` governs the banned subjects, and `<constraint_language>` governs the weak modals.

**Structural anti-patterns:**

- **Explaining Claude to Claude** — "As an AI language model..." wastes context. Claude knows what it is.
- **Motivational prose** — "This is a critical task that requires careful attention" adds nothing. State the constraints.
- **Repeating the skill name** — "The create-skill skill is designed to..." — Claude has the name from frontmatter.
- **Empty disclaimers** — "Results may vary" — if there are real failure modes, document them concretely; if not, cut the disclaimer.

</anti_patterns>

<conciseness>

The context window is shared: a prompt competes for tokens with the system prompt, conversation history, other skills' metadata, and the user's request.

**The test for every sentence in a prompt:**

"Does removing this reduce Claude's effectiveness at the task?"

If no — cut it.

**What Claude already knows (never include):**

- General programming knowledge
- Language syntax and standard library APIs
- Common design patterns
- How to use its own tools

**What Claude needs (include):**

- Product-specific conventions that contradict common patterns
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

**When to elaborate:** the concept is domain-specific (not general programming), the pattern is non-obvious or counterintuitive, or context affects behavior in subtle ways.

</conciseness>

<failure_mode_writing>

Write failure modes from actual experience, not speculation.

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

<rule_catalog>

Every rule the sections above state carries exactly one row below, giving it one stable identifier and one severity and naming the section that states it. The stating section is authoritative for what the rule requires. Recommendations and patterns those sections offer without requiring them carry no row. The identifier, severity, finding-key, and closed-vocabulary rules for this catalog are the catalog contract `/skill-standards` states for both rule catalogs.

| Identifier                       | Severity | Rule                                                                                                                               | Stated in                |
| -------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `instruction_not_imperative`     | debt     | An instruction drops its subject and uses imperative mood.                                                                         | `<voice>`                |
| `behavioral_claim_subject`       | debt     | A behavioral claim, tendency, or failure mode names Claude as its subject.                                                         | `<voice>`                |
| `banned_subject`                 | debt     | Prompt text never uses "the agent", "the model", or "you" as a subject.                                                            | `<voice>`                |
| `description_subject`            | debt     | A frontmatter description names no subject.                                                                                        | `<voice>`                |
| `claude_in_frontmatter`          | blocking | The `name` and `description` fields never contain the word "claude".                                                               | `<voice>`                |
| `actor_or_activity_objective`    | blocking | An `<objective>` names the output and its required shape, never opening with an actor or a bare activity verb.                     | `<objective_shape>`      |
| `objective_non_output_clause`    | debt     | An `<objective>` is one sentence, two only for an output with two distinct parts, and every clause names a property of the output. | `<objective_shape>`      |
| `objective_criteria_duplication` | debt     | `<objective>` and `<success_criteria>` never restate each other.                                                                   | `<objective_shape>`      |
| `directive_description_form`     | debt     | A directive description states `ALWAYS invoke` with the triggers that select it.                                                   | `<description_style>`    |
| `redundant_never_clause`         | debt     | A description carries a NEVER clause only where it disambiguates.                                                                  | `<description_style>`    |
| `artifact_language_order`        | debt     | A description names the artifact before the language.                                                                              | `<description_style>`    |
| `description_jargon`             | debt     | A description uses the abbreviations, natural terms, and plain language users say.                                                 | `<description_style>`    |
| `weak_modal_in_rule`             | debt     | A constraint block uses MUST, NEVER, or ALWAYS, and none of the weak modals.                                                       | `<constraint_language>`  |
| `banned_phrase`                  | debt     | Prompt text carries none of the phrases the banned-phrase table lists.                                                             | `<anti_patterns>`        |
| `explaining_claude_to_claude`    | debt     | Prompt text never explains to Claude what Claude is.                                                                               | `<anti_patterns>`        |
| `motivational_prose`             | debt     | Prompt text states constraints rather than urging care.                                                                            | `<anti_patterns>`        |
| `skill_name_repetition`          | debt     | Prompt text never restates the name its frontmatter carries.                                                                       | `<anti_patterns>`        |
| `empty_disclaimer`               | debt     | Prompt text carries no disclaimer that names no concrete failure.                                                                  | `<anti_patterns>`        |
| `removable_sentence`             | debt     | A prompt carries no sentence whose removal leaves Claude's effectiveness at the task unchanged.                                    | `<conciseness>`          |
| `known_content`                  | debt     | A prompt omits knowledge Claude already has.                                                                                       | `<conciseness>`          |
| `abstract_guidance`              | debt     | Guidance states concrete commands and thresholds rather than abstractions.                                                         | `<conciseness>`          |
| `failure_mode_structure`         | debt     | A failure mode states what happened, why it failed, and how to avoid it.                                                           | `<failure_mode_writing>` |
| `invented_failure_mode`          | debt     | A failure mode records an occurrence from actual usage, never a speculative scenario.                                              | `<failure_mode_writing>` |

</rule_catalog>

<success_criteria>

A prompt that follows these conventions:

- Uses imperative mood for instructions, "Claude" for failure modes and tendencies
- Never uses "the agent", "the model", or "you" as a subject
- States its `<objective>` as one output-shaped sentence per `<objective_shape>`, with no actor, activity, or clause about when or how it runs
- Uses the description style its owning structure standard selects, worded per `<description_style>`
- Uses strong modal verbs (MUST/NEVER/ALWAYS) in constraint blocks
- Contains no banned phrases or structural anti-patterns
- Includes only information Claude doesn't already have
- Documents failure modes from actual usage with concrete specifics
- Violates no rule in `<rule_catalog>`, and every finding against it names one catalog identifier

</success_criteria>
