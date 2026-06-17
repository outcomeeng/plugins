<xml_structure_examples>
**What to flag as XML structure violations:**

<example name="markdown_headings_in_body">
❌ Flag as critical:
```markdown
## Quick start

Extract text with pdfplumber...

## Advanced features

Form filling...

````
✅ Should be:
```xml
<quick_start>
Extract text with pdfplumber...
</quick_start>

<advanced_features>
Form filling...
</advanced_features>
````

**Why**: Markdown headings in body is a critical anti-pattern. Pure XML structure required.
</example>

<example name="missing_required_tags">
❌ Flag as critical:
```xml
<workflow>
1. Do step one
2. Do step two
</workflow>
```

Missing: `<objective>`, `<success_criteria>`

✅ Should have both required tags:

```xml
<objective>What the skill does and why it matters</objective>

<success_criteria>How to know it worked</success_criteria>
```

**Why**: Required tags are non-negotiable for all skills. `<quick_start>` is conditional — include for on-demand tool skills, omit for foundation/gate/validator/reference skills.
</example>

<example name="hybrid_xml_markdown">
❌ Flag as critical:
```markdown
<objective>
PDF processing capabilities
</objective>

## Quick start

Extract text...

## Advanced features

Form filling...

````
✅ Should be pure XML:
```xml
<objective>
PDF processing capabilities
</objective>

<quick_start>
Extract text...
</quick_start>

<advanced_features>
Form filling...
</advanced_features>
````

**Why**: Mixing XML with markdown headings creates inconsistent structure.
</example>

<example name="unclosed_xml_tags">
❌ Flag as critical:
```xml
<objective>
Process PDF files

<quick_start>
Use pdfplumber...
</quick_start>

````
Missing closing tag: `</objective>`

✅ Should properly close all tags:
```xml
<objective>
Process PDF files
</objective>

<quick_start>
Use pdfplumber...
</quick_start>
````

**Why**: Unclosed tags break parsing and create ambiguous boundaries.
</example>

<example name="inappropriate_conditional_tags">
Flag when conditional tags don't match complexity:

**Over-engineered simple skill** (flag as recommendation):

```xml
<objective>Convert CSV to JSON</objective>
<quick_start>Use pandas.to_json()</quick_start>
<context>CSV files are common...</context>
<workflow>Step 1... Step 2...</workflow>
<advanced_features>See [advanced.md]</advanced_features>
<security_checklist>Validate input...</security_checklist>
<testing>Test with all models...</testing>
```

**Why**: Simple single-domain skill only needs required tags. Too many conditional tags add unnecessary complexity.

**Under-specified complex skill** (flag as critical):

```xml
<objective>Manage payment processing with Stripe API</objective>
<quick_start>Create checkout session</quick_start>
<success_criteria>Payment completed</success_criteria>
```

**Why**: Payment processing needs security_checklist, validation, error handling patterns. Missing critical conditional tags.
</example>
</xml_structure_examples>
