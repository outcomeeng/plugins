# Workflow: Add a Reference to Existing Skill

<required_reading>
Read these reference files NOW:

1. `references/core-principles.md` (for progressive disclosure guidance)

</required_reading>

<process>
## Step 1: Identify Target Skill

**If user provided path**: Use that skill

**If not specified**: Ask which skill to add reference to

## Step 2: Verify References Directory

```bash
ls ~/.claude/skills/{skill-name}/references/ 2>/dev/null
```

**If no references/ directory**:

```bash
mkdir -p ~/.claude/skills/{skill-name}/references
```

## Step 3: Gather Reference Details

Ask using AskUserQuestion:

1. **Reference name**: What should this reference be called?
   - Use lowercase-with-hyphens
   - Be descriptive: `api-patterns.md`, `security-checklist.md`

2. **Reference purpose**: What domain knowledge does this contain?

3. **When to load**: Which workflows should reference this file?

## Step 4: Determine Content Source

Ask how to populate the reference:

1. **Research domain** - I'll gather information from official docs and best practices
2. **User provides content** - You'll give me the content to include
3. **Extract from existing** - Pull domain knowledge from current SKILL.md

## Step 5: Create Reference File

Structure varies by content type:

**For domain knowledge**:

```markdown
<overview>
Brief description of what this reference covers.
</overview>

<section_name>
Content organized by topic...
</section_name>

<patterns>
Code examples, recipes, or reusable patterns...
</patterns>
```

**For checklists**:

```markdown
<checklist>
## {Checklist Name}

- [ ] Item 1
- [ ] Item 2

</checklist>
```

**For API/library docs**:

```markdown
<api_reference>

| Method           | Purpose | Example     |
| ---------------- | ------- | ----------- |
| method1          | Does X  | `example()` |
| </api_reference> |         |             |
```

Write to: `~/.claude/skills/{skill-name}/references/{reference-name}.md`

## Step 6: Update SKILL.md

Add to `<reference_index>`:

```text
<reference_index>| File | Purpose |
|------|---------|
| existing entries... |
| {reference-name}.md | {Purpose} |</reference_index>
```

## Step 7: Update Relevant Workflows

For each workflow that should use this reference, add to `<required_reading>`:

```text
<required_reading>Read these reference files NOW:

1. existing references...
2. `references/{reference-name}.md`</required_reading>
```

## Step 8: Validate

- [ ] Reference file exists at correct path
- [ ] Content is well-organized with XML tags
- [ ] SKILL.md reference_index updated
- [ ] Relevant workflows updated with required_reading
- [ ] No broken links

</process>

<success_criteria>
Reference addition is complete when:

- [ ] Reference file created with proper structure
- [ ] SKILL.md reference_index updated
- [ ] Relevant workflows reference the new file
- [ ] Content is useful and well-organized

</success_criteria>
