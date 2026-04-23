# Workflow: Add a Workflow to Existing Skill

<required_reading>
Read these reference files NOW:

1. `references/use-xml-tags.md`

</required_reading>

<process>
## Step 1: Identify Target Skill

**If user provided path**: Use that skill

**If not specified**: Ask which skill to add workflow to

## Step 2: Verify Skill Structure

Check if skill uses router pattern:

```bash
ls ~/.claude/skills/{skill-name}/workflows/ 2>/dev/null
```

**If no workflows/ directory**:
→ Recommend running `workflows/upgrade-to-router.md` first
→ Or create workflows/ directory if user confirms

## Step 3: Gather Workflow Details

Ask using AskUserQuestion:

1. **Workflow name**: What should this workflow be called?
   - Use lowercase-with-hyphens
   - Be descriptive: `create-component.md`, `deploy-service.md`

2. **Workflow purpose**: What does this workflow do?

3. **Required references**: Which reference files should be loaded?

## Step 4: Create Workflow File

Use this structure:

```markdown
# Workflow: {Descriptive Title}

<required_reading>
Read these reference files NOW:

1. `references/{relevant-reference}.md`
   </required_reading>

<process>
## Step 1: {First Step}

{Step description}

## Step 2: {Second Step}

{Step description}

...
</process>

<success_criteria>
Workflow is complete when:

- [ ] {First criterion}
- [ ] {Second criterion}

</success_criteria>
```

Write to: `~/.claude/skills/{skill-name}/workflows/{workflow-name}.md`

## Step 5: Update SKILL.md Routing

Add new workflow to the routing table in SKILL.md:

```text
<routing>| Response | Workflow |
|----------|----------|
| existing entries... |
| {new trigger}, "{keywords}" | `workflows/{workflow-name}.md` |</routing>
```

Also update `<workflows_index>`:

```text
<workflows_index>| Workflow | Purpose |
|----------|---------|
| existing entries... |
| {workflow-name}.md | {Purpose} |</workflows_index>
```

## Step 6: Validate

- [ ] Workflow file exists at correct path
- [ ] Has required_reading section
- [ ] Has process section with numbered steps
- [ ] Has success_criteria section
- [ ] SKILL.md routing table updated
- [ ] SKILL.md workflows_index updated
- [ ] All referenced files exist

</process>

<success_criteria>
Workflow addition is complete when:

- [ ] Workflow file created with proper structure
- [ ] SKILL.md routing updated
- [ ] SKILL.md workflows_index updated
- [ ] All references exist
- [ ] User can invoke the new workflow

</success_criteria>
