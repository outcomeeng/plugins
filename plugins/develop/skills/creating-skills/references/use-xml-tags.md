<overview>
Skills use pure XML structure for consistent parsing, efficient token usage, and improved Claude performance. This reference defines required and conditional XML tags.
</overview>

<critical_rule>
**Remove ALL markdown headings (#, ##, ###) from skill body content.** Replace with semantic XML tags. Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).
</critical_rule>

<required_tags>
Every skill MUST have these two tags:

**`<objective>`**
What the skill does and why it matters. Sets context and scope.

```text
<objective>Extract text and tables from PDF files, fill forms, and merge documents.</objective>
```

**`<success_criteria>`**
How to know the task worked. Defines completion criteria.

```text
<success_criteria>
A well-structured skill has:
- Valid YAML frontmatter
- Pure XML structure
- Required tags present

</success_criteria>
```

</required_tags>

<router_tags>
For skills using the router pattern:

**`<essential_principles>`**
Principles that ALWAYS apply, regardless of which workflow runs. Must be inline in SKILL.md (not in separate file).

**`<intake>`**
Question to ask user to determine which workflow to run.

**`<routing>`**
Table mapping user responses to workflow files.

**`<reference_index>`**
List of available reference files.

**`<workflows_index>`**
List of available workflow files.
</router_tags>

<workflow_tags>
For workflow files:

**`<required_reading>`**
Which reference files to load before following this workflow.

**`<process>`**
Step-by-step procedure to follow.

**`<success_criteria>`**
When this workflow is considered complete.
</workflow_tags>

<conditional_tags>
Add these based on skill complexity and purpose:

**`<quick_start>`** - Immediate actionable guidance for on-demand tool skills. Include when the skill has a meaningful fast path (builders, utilities). Omit for foundation, gate, validator, and reference skills where completeness is the point — a quick_start signals "you can abbreviate" which undermines skills that must execute fully.

**`<context>`** - Background or situational information needed before starting.

**`<workflow>`** or **`<process>`** - Step-by-step procedures, sequential operations.

**`<advanced_features>`** - Deep-dive topics for progressive disclosure.

**`<validation>`** - Verification steps, quality checks.

**`<examples>`** - Multi-shot learning, input/output pairs.

**`<anti_patterns>`** - Common mistakes to avoid.

**`<security_checklist>`** - For skills with security implications.

**`<testing>`** - Testing workflows, validation steps.

**`<common_patterns>`** - Code examples, recipes, reusable patterns.

**`<reference_guides>`** - Links to detailed reference files.
</conditional_tags>

<intelligence_rules>
**Simple skills** (single domain, straightforward):

- Required tags only: objective, success_criteria
- Add quick_start if the skill is an on-demand tool with a clear fast path

**Medium skills** (multiple patterns, some complexity):

- Required tags + workflow/examples as needed
- Add quick_start if there's a meaningful abbreviated invocation

**Complex skills** (multiple domains, security, APIs):

- Required tags + router pattern + conditional tags as appropriate

**Foundation/gate/validator skills** (must execute fully):

- Required tags + workflow + success_criteria
- Omit quick_start — completeness is the point, no abbreviated path exists

**Don't over-engineer simple skills. Don't under-specify complex skills.**
</intelligence_rules>

<nesting_guidelines>
XML tags can nest for hierarchical content:

```text
<examples>
  <example number="1">
    <input>User input here</input>
    <output>Expected output here</output>
  </example>
</examples>
```

**Always close tags properly**:

```text
<!-- Good -->
<objective>Content here</objective>

<!-- Bad - missing closing tag -->
<objective>Content here
```

**Use descriptive, semantic names**:

- `<workflow>` not `<steps>`
- `<success_criteria>` not `<done>`
- `<anti_patterns>` not `<dont_do>`

</nesting_guidelines>

<anti_pattern>
**DO NOT use markdown headings in skill body content.**

Bad (hybrid approach):

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber...
```

Good (pure XML):

```text
<objective>PDF processing with text extraction, form filling, and merging.</objective>

<quick_start>Extract text with pdfplumber...</quick_start>
```

</anti_pattern>

<tag_reference_pattern>
When referencing content in tags, use the tag name:

"Using the schema in `<schema>` tags..."
"Follow the workflow in `<workflow>`..."
"See examples in `<examples>`..."

This makes the structure self-documenting.
</tag_reference_pattern>
