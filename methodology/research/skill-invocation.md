# Reliable Skill Activation in Claude Code

Claude Code skills are prompt templates that inject domain-specific instructions into conversation context on demand. Anthropic documents them as "model-invoked" — Claude autonomously decides when to load a skill based on its `description` field in `SKILL.md` frontmatter.

In practice, default activation rates hover around 50%. This document surveys the community's fixes, ranked by evidence quality.

## Root cause

Skills appear in Claude's tool schema as entries in an `<available_skills>` list. Claude sees the `name` and `description` from frontmatter and decides per-turn whether to invoke the `Skill` tool. The decision is probabilistic: Claude may skip a skill if it judges it can handle the task directly with base tools (`Read`, `Write`, `Bash`). Simple, one-step queries are particularly unlikely to trigger skills regardless of description quality.

Hooks, by contrast, are deterministic shell commands (or HTTP endpoints, or LLM prompts) that fire at defined lifecycle events. They execute unconditionally when their event and matcher criteria are met.

This distinction — **skills are probabilistic, hooks are deterministic** — drives every fix below.

## Fix 1: Directive descriptions (no hooks)

**Evidence: 650 automated trials across 3 skills, 3 description variants, with and without hooks/CLAUDE.md. Logistic regression with interaction terms. Source: Seleznov, Feb 2026.**

Three `description` variants were tested:

| Variant       | Style                            | Example                                         | Activation (no hooks) |
| ------------- | -------------------------------- | ----------------------------------------------- | --------------------- |
| A — Passive   | Default Anthropic style          | `Docker expert for containerization. Use when…` | ~77%                  |
| B — Expanded  | More trigger keywords            | `…or any Docker-related task`                   | ~93%                  |
| C — Directive | Imperative + negative constraint | `ALWAYS invoke… Do not X directly`              | ~100%                 |

Description wording had a **20× impact on activation odds**. The recommended template:

```yaml
description: >-
  ALWAYS invoke this skill when the user asks about <triggers>.
  Do not <alternative action> directly — use this skill first.
```

### Key findings

- Directive descriptions (Variant C) achieved 100% activation without any hooks.
- Hooks as a main effect **reduced** activation (coefficient −2.35, p < 0.0001). This is counterintuitive and contradicts the prevailing community narrative.
- CLAUDE.md context mitigated hook-induced degradation (interaction coefficient +7.16, p = 0.026).
- Skills where Claude has a strong built-in alternative (e.g., `git-workflow` vs. direct `git` commands via Bash) showed the widest activation variance and benefit most from directive descriptions with negative constraints.

### Practical guidance

1. List explicit trigger conditions comprehensively.
2. Include a negative constraint naming the action Claude would take instead.
3. If using hooks alongside directive descriptions, always pair with a CLAUDE.md that references the skills.
4. Avoid overlapping triggers across multiple skills.

## Fix 2: Forced-eval hook (`UserPromptSubmit`)

**Evidence: 200+ automated trials across 5 prompt types on Haiku 4.5. Source: Spence, Nov 2025.**

A `UserPromptSubmit` hook injects a mandatory evaluation protocol into every prompt before Claude responds. The hook's stdout is prepended to the user's message.

| Approach            | Activation rate |
| ------------------- | --------------- |
| No hook (baseline)  | ~50%            |
| Simple keyword hook | ~20%            |
| Forced-eval hook    | ~84%            |

The forced-eval hook enforces a three-step commitment:

```
MANDATORY SKILL EVALUATION:
Step 1 — EVALUATE: For each skill in <available_skills>, state YES/NO with reason.
Step 2 — ACTIVATE: Use Skill(skill-name) NOW for each YES.
Step 3 — IMPLEMENT: Only proceed after activation.
CRITICAL: The evaluation is WORTHLESS unless you ACTIVATE the skills.
```

### Implementation

Hook configuration in `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/skill-activation-prompt.sh"
          }
        ]
      }
    ]
  }
}
```

The shell script reads JSON from stdin (Claude Code passes `{"prompt": "..."}`) and echoes the evaluation protocol to stdout.

### Trade-offs

- Verbose: Claude lists every skill with YES/NO reasoning on every turn, consuming tokens.
- The 84% rate, while much better than baseline, is still below what directive descriptions alone achieve in Seleznov's study.
- The aggressive phrasing ("MANDATORY", "WORTHLESS", "CRITICAL") is load-bearing — softer language degrades to baseline rates.

## Fix 3: Keyword detection hook

A `UserPromptSubmit` hook that greps the prompt for trigger words and injects `INSTRUCTION: Use Skill(skill-name)` when matched.

```bash
#!/bin/bash
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

if echo "$PROMPT" | grep -qiE '(docker|container|dockerfile)'; then
  echo "INSTRUCTION: Use Skill(dockerfile-generator) for this request."
fi
```

### Limitations

- **False positives**: "research the database schema" triggers a research skill when the user wants database work.
- **Tested poorly**: Spence measured ~20% activation for the simple keyword variant, worse than no hook at all.
- **Does not scale**: each new skill requires manual keyword lists and conditional logic.

Not recommended as a primary strategy. Mentioned for completeness.

## Fix 4: CLAUDE.md / custom instructions

Add to project-level or global CLAUDE.md:

```markdown
MANDATORY: Before responding to ANY prompt, you MUST:

1. Check ALL available skills in <available_skills>
2. Identify which skills apply to this prompt
3. Use Skill(skill-name) for EACH applicable skill
4. ONLY THEN start your response

Do NOT skip skill activation. This is NON-NEGOTIABLE.
```

This is the lowest-effort fix. It works sometimes but is the least reliable because custom instructions sit in background context and Claude can deprioritize them under cognitive load or long context windows. Seleznov's data shows CLAUDE.md alone adds roughly +15 percentage points over bare baseline — meaningful but insufficient.

## Fix 5: Plugin router with dynamic loading

A `UserPromptSubmit` hook that:

1. Spawns a lightweight Claude call (`--model haiku`) to classify which plugins/skills the prompt needs.
2. Synchronously installs only those plugins (`claude plugin install` blocks until done).
3. Forwards the prompt with the relevant skills loaded.

This makes activation deterministic but at the cost of an extra LLM call per prompt, added latency, and significant implementation complexity. Suitable for teams with many skills where context budget is a real concern.

## Silent failure: Prettier reformatting

If Prettier is configured in the project, it may reformat the YAML frontmatter `description` field to multi-line, which causes Claude Code to silently fail to recognize the skill. The fix:

```yaml
---
name: my-skill
# prettier-ignore
description: ALWAYS invoke this skill when <triggers>. Do not <alternative> directly.
---
```

Keep descriptions on a single line and add `# prettier-ignore` above the field.

## Recommended approach

For most teams, the evidence suggests a layered strategy:

1. **Write directive descriptions with negative constraints.** This is the single highest-leverage change and requires zero infrastructure. Apply the `ALWAYS invoke… Do not X directly` template to every skill.
2. **Add the forced-eval hook** only for skills that still underperform after description optimization — particularly skills where Claude has strong built-in alternatives (git operations, basic file manipulation).
3. **Use `disable-model-invocation: true`** in frontmatter for skills with side effects (deploy, publish, send) where you need explicit `/skill-name` invocation.
4. **Validate with Prettier** and other formatters that the YAML frontmatter remains single-line.
5. **Test activation empirically.** Anthropic's own `skill-creator` skill includes an eval framework. Use it or build a lightweight equivalent — subjective impressions of activation rates are unreliable.

### Open question

Seleznov's finding that hooks reduce activation as a main effect has not been independently replicated across diverse skill types and models. The interaction with CLAUDE.md suggests the degradation may be an artifact of context budget pressure. Teams adopting hooks should measure before/after activation rates rather than assuming hooks help.

## Sources

- Seleznov, I. "Why Claude Code Skills Don't Activate — And How to Fix It." Medium, Feb 2026.
- Spence, S. "Claude Code Skills Don't Auto-Activate." scottspence.com, Nov 2025.
- Spence, S. "How to Make Claude Code Skills Activate Reliably." scottspence.com, Nov 2025.
- Abyzov, A. "Claude Code Hook Limitations: No Skill Invocation & Lazy Plugin Loading." DEV Community, Jan 2026.
- Anthropic. "Extend Claude with skills." code.claude.com/docs/en/skills.
- Anthropic. "Hooks reference." code.claude.com/docs/en/hooks.
- Shilkov, M. "Inside Claude Code Skills: Structure, prompts, invocation." mikhail.io, Oct 2025.
- Jesse. "Hooks, Rules, and Skills: Feedback Loops in Claude Code." Medium, Mar 2026.
