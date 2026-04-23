# Workflow: Create a New Skill

<required_reading>
Read these reference files NOW:

1. `references/core-principles.md`
2. `references/use-xml-tags.md`
3. `references/skill-patterns.md`

</required_reading>

<process>
## Step 1: Adaptive Requirements Gathering

**If user provided context** (e.g., "create a skill for X"):
→ Analyze what's stated, what can be inferred, what's unclear
→ Skip to asking about genuine gaps only

**If user just invoked skill without context:**
→ Ask what they want to build

### Using AskUserQuestion

Ask 2-4 domain-specific questions based on actual gaps:

1. **Skill type**: Builder, Guide, Automation, Analyzer, or Validator?
2. **Domain**: What domain or technology?
3. **Use case**: What's YOUR specific need? (after domain discovery)
4. **Constraints**: Any specific requirements?

**Decision gate**: Ask "Ready to proceed, or want me to ask more questions?"

## Step 2: Domain Discovery (Automatic)

Research the domain BEFORE asking user requirements:

| Discover       | How                                   | Example: "Kafka integration"  |
| -------------- | ------------------------------------- | ----------------------------- |
| Core concepts  | Official docs                         | Topics, partitions, consumers |
| Best practices | Search "[domain] best practices 2025" | Partition strategies          |
| Anti-patterns  | Search "[domain] common mistakes"     | Over-partitioning             |
| Security       | Search "[domain] security"            | SASL, SSL, ACLs               |
| Ecosystem      | Search "[domain] tools"               | Schema Registry, Connect      |

**Sources priority**: Official docs → Library docs → GitHub → Community → WebSearch

### Knowledge Sufficiency Check

Before proceeding, verify internally:

- [ ] Core concepts: Can I explain the fundamentals?
- [ ] Best practices: Do I know the recommended approaches?
- [ ] Anti-patterns: Do I know what to avoid?
- [ ] Security: Do I know the security considerations?

If ANY is incomplete → Research more. Only ask user for proprietary/internal info.

## Step 3: Decide Structure

**Simple skill** (single workflow, <200 lines):
→ Single SKILL.md file with all content
→ Use `templates/simple-skill.md`

**Complex skill** (multiple workflows OR domain knowledge):
→ Router pattern with workflows/ and references/
→ Use `templates/router-skill.md`

Factors favoring router pattern:

- Multiple distinct user intents
- Shared domain knowledge across workflows
- Essential principles that must not be skipped
- Skill likely to grow over time

## Step 4: Create Directory

```bash
mkdir -p ~/.claude/skills/{skill-name}
# If complex:
mkdir -p ~/.claude/skills/{skill-name}/workflows
mkdir -p ~/.claude/skills/{skill-name}/references
# If needed:
mkdir -p ~/.claude/skills/{skill-name}/templates
mkdir -p ~/.claude/skills/{skill-name}/scripts
```

## Step 5: Write SKILL.md

**Simple skill**: Use `templates/simple-skill.md` as base. Include:

- YAML frontmatter (name, description)
- `<objective>`
- `<quick_start>`
- `<workflow>` or `<process>`
- `<success_criteria>`

**Complex skill**: Use `templates/router-skill.md` as base. Include:

- YAML frontmatter
- `<essential_principles>` (inline, unavoidable)
- `<intake>` (question to ask user)
- `<routing>` (maps answers to workflows)
- `<reference_index>` and `<workflows_index>`

## Step 6: Write Type-Specific Content

Based on skill type from Step 1:

| Type       | Key Sections                           | Template                        |
| ---------- | -------------------------------------- | ------------------------------- |
| Builder    | Clarifications, Output spec, Standards | `templates/builder-skill.md`    |
| Guide      | Workflow, Examples, Official docs      | `templates/guide-skill.md`      |
| Automation | Scripts, Dependencies, Error handling  | `templates/automation-skill.md` |
| Analyzer   | Scope, Criteria, Output format         | `templates/analyzer-skill.md`   |
| Validator  | Criteria, Scoring, Thresholds          | `templates/validator-skill.md`  |

## Step 7: Embed Domain Knowledge

Put gathered domain expertise into `references/`:

| Gathered Knowledge | Purpose in Skill              |
| ------------------ | ----------------------------- |
| Library/API docs   | Enable correct implementation |
| Best practices     | Guide quality decisions       |
| Code examples      | Provide reference patterns    |
| Anti-patterns      | Prevent common mistakes       |

## Step 8: Add "Before Implementation" Section

Every skill should gather context at runtime:

```markdown
## Before Implementation

| Source               | Gather                                    |
| -------------------- | ----------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions |
| **Conversation**     | User's specific requirements, constraints |
| **Skill References** | Domain patterns from `references/`        |
| **User Guidelines**  | Project-specific conventions              |
```

## Step 9: Validate Structure

Check:

- [ ] YAML frontmatter valid (name matches directory, description has What + When)
- [ ] Pure XML structure (no markdown headings in body)
- [ ] Required tags present: objective, quick_start, success_criteria
- [ ] All referenced files exist
- [ ] SKILL.md under 500 lines
- [ ] XML tags properly closed

Run: `python scripts/quick_validate.py {skill-path}`

## Step 10: Test

Invoke the skill and observe:

- Does it ask the right intake question?
- Does it load the right workflow?
- Does the workflow load the right references?
- Does output match expectations?

Iterate based on real usage, not assumptions.
</process>

<success_criteria>
Skill is complete when:

- [ ] Requirements gathered with appropriate questions
- [ ] Domain discovery done (user NOT asked for domain knowledge)
- [ ] Directory structure correct
- [ ] SKILL.md has valid frontmatter
- [ ] Pure XML structure (no markdown headings)
- [ ] Type-specific sections included
- [ ] "Before Implementation" section included
- [ ] All workflows have required_reading + process + success_criteria
- [ ] References contain reusable domain knowledge
- [ ] Tested with real invocation

</success_criteria>
