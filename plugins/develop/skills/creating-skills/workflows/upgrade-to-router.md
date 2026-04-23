# Workflow: Upgrade Simple Skill to Router Pattern

<required_reading>
Read these reference files NOW:

1. `references/core-principles.md`
2. `references/use-xml-tags.md`

</required_reading>

<process>
## Step 1: Analyze Current Skill

Read the existing SKILL.md:

```bash
cat ~/.claude/skills/{skill-name}/SKILL.md
wc -l ~/.claude/skills/{skill-name}/SKILL.md
```

Identify:

- [ ] Current line count (if >300 lines, router pattern recommended)
- [ ] Distinct user intents (multiple = router pattern)
- [ ] Domain knowledge that could be extracted
- [ ] Essential principles that must not be skipped

## Step 2: Confirm Upgrade

Present analysis to user:

```
Current skill analysis:
- Line count: {X} lines
- User intents identified: {list}
- Extractable content: {list}

Router pattern is recommended because: {reason}

Proceed with upgrade?
```

## Step 3: Create Directory Structure

```bash
mkdir -p ~/.claude/skills/{skill-name}/workflows
mkdir -p ~/.claude/skills/{skill-name}/references
```

## Step 4: Extract Essential Principles

Identify content that:

- Must ALWAYS be loaded
- Applies regardless of which workflow runs
- Should not be skippable

Move this into `<essential_principles>` tag in SKILL.md.

## Step 5: Create Workflows

For each distinct user intent, create a workflow file:

```bash
# Example: create, edit, delete intents
touch ~/.claude/skills/{skill-name}/workflows/create-{thing}.md
touch ~/.claude/skills/{skill-name}/workflows/edit-{thing}.md
touch ~/.claude/skills/{skill-name}/workflows/delete-{thing}.md
```

Each workflow should have:

- `<required_reading>` - Which references to load
- `<process>` - Step-by-step procedure
- `<success_criteria>` - When it's done

## Step 6: Extract References

Move domain knowledge to reference files:

- Patterns and examples → `references/patterns.md`
- API documentation → `references/api-reference.md`
- Best practices → `references/best-practices.md`

## Step 7: Rewrite SKILL.md

Replace original SKILL.md with router structure:

```yaml
---
name: { skill-name }
description: |
  {What it does}.
  Use when {trigger conditions}.
---
```

**IMPORTANT:** ALWAYS use the AskUserQuestion tool to ask the user for guidance and decisions. Present concise, highly structured options. Think hardest when determinng, which options to present and whether the user must choose one or multiple options might make sense.

```text
<essential_principles>
{Extracted essential principles that always apply}
</essential_principles>

<intake>What would you like to do?
1. {First option}
2. {Second option}
3. {Third option}

**Wait for response before proceeding.**
</intake>

<routing>| Response | Workflow |
|----------|----------|
| 1, "{keywords}" | `workflows/{first-workflow}.md` |
| 2, "{keywords}" | `workflows/{second-workflow}.md` |
| 3, "{keywords}" | `workflows/{third-workflow}.md` |

**After reading the workflow, follow it exactly.**</routing>

<reference_index>All in `references/`:

| File | Purpose |
|------|---------|
| {reference-1}.md | {Purpose} |
| {reference-2}.md | {Purpose} |
</reference_index>

<workflows_index>All in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| {workflow-1}.md | {Purpose} |
| {workflow-2}.md | {Purpose} |
</workflows_index>

<success_criteria>{Overall success criteria for the skill}</success_criteria>
```

## Step 8: Validate Upgrade

- [ ] SKILL.md under 200 lines (was possibly 500+)
- [ ] Essential principles inline in SKILL.md
- [ ] All workflows exist and have proper structure
- [ ] All references exist
- [ ] Routing table maps to correct workflows
- [ ] No broken links
- [ ] Test each workflow path

</process>

<success_criteria>
Upgrade is complete when:

- [ ] Directory structure created (workflows/, references/)
- [ ] Essential principles extracted and inline
- [ ] Workflows created for each user intent
- [ ] References created for domain knowledge
- [ ] SKILL.md rewritten with router pattern
- [ ] All paths tested and working
- [ ] SKILL.md significantly shorter than before

</success_criteria>
