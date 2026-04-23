# Skill Patterns

SKILL.md structure and examples for different skill types.

---

## Frontmatter Specification

### Complete Frontmatter Template

```yaml
---
name: skill-name # Required
description: >- # Required — directive with negative constraint
  ALWAYS invoke this skill when <triggers>.
  NEVER <alternative action> without this skill.
model: claude-sonnet-4-20250514 # Optional: model override
---
```

### Field Requirements

| Field         | Required | Constraints                                                            | Purpose                                         |
| ------------- | -------- | ---------------------------------------------------------------------- | ----------------------------------------------- |
| `name`        | Yes      | Lowercase, numbers, hyphens only; ≤64 chars; must match directory name | Skill identifier                                |
| `description` | Yes      | ≤1024 characters; directive with negative constraint                   | Claude Code uses this to decide when to trigger |
| `model`       | No       | Valid model ID                                                         | Override model for complex reasoning            |

### Name Constraints

```
✅ Valid: pdf-processor, data-viz, api-v2
❌ Invalid: PDF_Processor, dataViz, my skill
```

- Lowercase letters, numbers, hyphens only
- Maximum 64 characters
- Must match the directory name exactly

### Description Format

**Structure**: `ALWAYS invoke this skill when <triggers>. NEVER <alternative> without this skill.`

**Limit**: ≤1024 characters (truncated if exceeded)

**Purpose**: Claude Code reads this to decide when to activate the skill. Directive descriptions with negative constraints achieve ~100% activation (vs ~77% for passive style).

```yaml
# Good: Directive with negative constraint
description: >-
  ALWAYS invoke this skill when visualizing data, creating charts, or building dashboards.
  NEVER create data visualizations without this skill.

# Bad: Passive style (~77% activation)
description: |
  Create data visualizations with charts and graphs.
  Use when users ask to visualize data or create charts.

# Bad: Vague, no triggers
description: Helps with charts
```

**Negative constraint rules:**

- Use `NEVER` not "Do not"
- Drop the language from the negative — Claude knows which language is in play
- Frame as "without this skill" not "directly"

**Reference skills** (loaded by other skills, not user-triggered) use `disable-model-invocation: true` and a passive description instead. See the [Reference Skills](#reference-skills-for-shared-knowledge) section below for the full pattern.

### allowed-tools Usage

Restrict tool access for security or scope:

```yaml
# Read-only skill (no file modifications)
allowed-tools: Read, Grep, Glob

# Analysis skill with web access
allowed-tools: Read, Grep, WebFetch, WebSearch

# Full access (default if omitted)
# allowed-tools: (omit field)
```

### model Override

Specify when skill needs different model capabilities:

```yaml
# For complex reasoning tasks
model: claude-sonnet-4-20250514

# For simple, fast operations
model: claude-haiku-3-20250514
```

---

## SKILL.md Structure

### Complete Template

```markdown
---
name: skill-name
description: >-
  ALWAYS invoke this skill when <specific triggers>.
  NEVER <alternative action> without this skill.
---

# Skill Name

Brief one-line description.

## What This Skill Does

- Capability 1
- Capability 2
- Capability 3

## What This Skill Does NOT Do

- Exclusion 1
- Exclusion 2

---

## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                                      |
| -------------------- | --------------------------------------------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions to integrate with                 |
| **Conversation**     | User's specific requirements, constraints, preferences                      |
| **Skill References** | Domain patterns from `references/` (library docs, best practices, examples) |
| **User Guidelines**  | Project-specific conventions, team standards                                |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Required Clarifications

Ask about USER'S context (not domain knowledge):

1. **Use case**: "What's YOUR specific need?"
2. **Constraints**: "Any specific requirements?"

---

## Workflow

1. Step one
2. Step two
3. Step three

---

## [Domain-Specific Section]

Content specific to what the skill does.

---

## Output Checklist

Before delivering, verify:

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

---

## Reference Files

| File                  | When to Read |
| --------------------- | ------------ |
| `references/file1.md` | When X       |
| `references/file2.md` | When Y       |
```

---

## Skill Types Taxonomy

### Overview

| Type           | Purpose               | Key Output                        |
| -------------- | --------------------- | --------------------------------- |
| **Builder**    | Creates new artifacts | Code, documents, widgets, configs |
| **Guide**      | Provides instructions | Step-by-step workflows, tutorials |
| **Automation** | Executes workflows    | Processed files, transformed data |
| **Analyzer**   | Extracts insights     | Reports, summaries, reviews       |
| **Validator**  | Enforces quality      | Pass/fail assessments, scores     |
| **Reference**  | Shares knowledge      | Standards loaded by other skills  |

### Type Selection Guide

```
What does the skill primarily do?

Creates NEW artifacts (code, docs, widgets)?
  → Builder

Teaches HOW to do something?
  → Guide

Executes multi-step PROCESSES automatically?
  → Automation

EXTRACTS information or provides ANALYSIS?
  → Analyzer

CHECKS quality or ENFORCES standards?
  → Validator

SHARES knowledge that multiple skills need?
  → Reference (disable-model-invocation: true)
```

---

## Builder Skills (Create Artifacts)

**Purpose**: Generate new code, documents, widgets, configurations

**Key elements**:

- Required Clarifications (MUST ask before building)
- Output specification
- Domain standards enforcement
- Templates in assets/

**Example frontmatter**:

```yaml
---
name: widget-creator
description: |
  Create production widgets for ChatGPT Apps.
  Use when users ask to build UI components, visual interfaces,
  or interactive elements.
---
```

**Required sections**:

```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                      |
| -------------------- | ----------------------------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions to integrate with |
| **Conversation**     | User's specific requirements, constraints, preferences      |
| **Skill References** | Domain patterns from `references/`                          |
| **User Guidelines**  | Project-specific conventions, team standards                |

## Required Clarifications

1. **Data shape**: "What structure will input have?"
2. **Output type**: "What artifact to create?"
3. **Constraints**: "Any specific requirements?"

## Output Specification

[Define what the artifact looks like]

## Domain Standards

### Must Follow

- [ ] Standard 1

### Must Avoid

- Anti-pattern 1

## Output Checklist

- [ ] Artifact meets requirements
```

---

## Guide Skills (Provide Instructions)

**Purpose**: Teach procedures, provide tutorials, explain how-to

**Key elements**:

- Step-by-step workflow
- Input → Output examples (not just good/bad)
- Copyable workflow checklists
- Official documentation links
- Decision trees for branching

### Input → Output Examples Pattern

For skills where output quality matters, show explicit pairs:

````markdown
**Example 1:**
Input: Added user authentication with JWT tokens
Output:

```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:

```
fix(reports): correct date formatting in timezone conversion
```
````

This is MORE effective than describing the format in prose.

### Copyable Workflow Checklist Pattern

For complex multi-step workflows, provide copyable progress tracker:

````markdown
Copy this checklist and track progress:

```
- [ ] Step 1: Analyze input
- [ ] Step 2: Validate data
- [ ] Step 3: Process changes
- [ ] Step 4: Verify output
```
````

Claude can copy this into responses and check items as completed.

**Example frontmatter**:

```yaml
---
name: api-integration-guide
description: |
  Guide for integrating external APIs.
  Use when users need to connect to third-party services,
  handle authentication, or manage API responses.
---
```

**Required sections**:

```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                      |
| -------------------- | ----------------------------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions to integrate with |
| **Conversation**     | User's specific requirements, constraints, preferences      |
| **Skill References** | Domain patterns from `references/`                          |
| **User Guidelines**  | Project-specific conventions, team standards                |

## Workflow

1. **Step 1** - Action
2. **Step 2** - Action
3. **Step 3** - Action

## Examples

### Good Example

[Correct pattern with explanation]

### Bad Example (Avoid)

[Incorrect pattern with explanation]

## Official Documentation

| Resource | URL         | Use For   |
| -------- | ----------- | --------- |
| Docs     | https://... | Reference |
```

---

## Automation Skills (Execute Workflows)

**Purpose**: Process files, deploy systems, execute multi-step operations

**Key elements**:

- Tested scripts in scripts/
- Error handling guidance
- Dependencies documented
- Input/output contracts

**Example frontmatter**:

```yaml
---
name: pdf-processor
description: |
  Process PDF files with extraction, rotation, and form filling.
  Use when users need to manipulate PDF documents programmatically.
---
```

**Required sections**:

```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                      |
| -------------------- | ----------------------------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions to integrate with |
| **Conversation**     | User's specific requirements, constraints, preferences      |
| **Skill References** | Domain patterns from `references/`                          |
| **User Guidelines**  | Project-specific conventions, team standards                |

## Available Scripts

| Script               | Purpose         | Usage                            |
| -------------------- | --------------- | -------------------------------- |
| `scripts/process.py` | Main processing | `python process.py input output` |

## Dependencies

- Python 3.10+
- Required packages: [list]

## Error Handling

| Error         | Recovery |
| ------------- | -------- |
| Invalid input | [Action] |

## Input/Output

- **Input**: [Format, constraints]
- **Output**: [Format, location]
```

---

## Analyzer Skills (Extract Insights)

**Purpose**: Review documents, analyze data, extract information, summarize

**Key elements**:

- Analysis scope and criteria
- Extraction patterns
- Output format specification
- Synthesis guidance

**Example frontmatter**:

```yaml
---
name: outcome-engineering-analyzer
description: |
  Analyze codebases for patterns, issues, and improvements.
  Use when users ask to review code, find patterns,
  assess quality, or understand architecture.
---
```

**Required sections**:

```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                      |
| -------------------- | ----------------------------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions to integrate with |
| **Conversation**     | User's specific requirements, constraints, preferences      |
| **Skill References** | Domain patterns from `references/`                          |
| **User Guidelines**  | Project-specific conventions, team standards                |

## Analysis Scope

- What to analyze
- What to ignore

## Evaluation Criteria

| Criterion   | Weight | How to Assess |
| ----------- | ------ | ------------- |
| Criterion 1 | X%     | [Method]      |

## Output Format

[Specify report structure]

## Synthesis

- Combine findings into actionable insights
- Prioritize by impact
```

---

## Validator Skills (Enforce Quality)

**Purpose**: Check compliance, score quality, enforce standards

**Key elements**:

- Quality criteria with scoring
- Pass/fail thresholds
- Remediation guidance
- Evidence collection

**Example frontmatter**:

```yaml
---
name: accessibility-validator
description: |
  Validate web content for WCAG accessibility compliance.
  Use when users ask to check accessibility, audit for
  compliance, or verify standards adherence.
---
```

**Required sections**:

```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                      |
| -------------------- | ----------------------------------------------------------- |
| **Codebase**         | Existing structure, patterns, conventions to integrate with |
| **Conversation**     | User's specific requirements, constraints, preferences      |
| **Skill References** | Domain patterns from `references/`                          |
| **User Guidelines**  | Project-specific conventions, team standards                |

## Quality Criteria

| Criterion   | Weight | Pass Threshold |
| ----------- | ------ | -------------- |
| Criterion 1 | X%     | [Threshold]    |

## Scoring Rubric

- **3 (Excellent)**: [Definition]
- **2 (Good)**: [Definition]
- **1 (Needs Work)**: [Definition]
- **0 (Fail)**: [Definition]

## Thresholds

- **Pass**: Score ≥ X
- **Conditional**: Score X-Y
- **Fail**: Score < Y

## Remediation

| Issue   | Fix          |
| ------- | ------------ |
| Issue 1 | [How to fix] |
```

---

## Reference Skills for Shared Knowledge

**Purpose**: Hold shared domain knowledge that multiple skills need. Not invoked directly by users or Claude — loaded by other skills via `/skill-name` references.

**When to use**: When two or more skills in the same plugin need the same domain knowledge (standards, patterns, anti-patterns, conventions). Without a reference skill, you either duplicate the content (maintenance burden) or put it in one skill's `references/` directory where the other skill can't reach it (each skill's `${CLAUDE_SKILL_DIR}` is isolated).

**Key elements**:

- `disable-model-invocation: true` in frontmatter (prevents false activations)
- Passive description (NOT directive — no `ALWAYS`/`NEVER`)
- `allowed-tools: Read` (read-only, no side effects)
- Content is the shared knowledge itself, not a workflow

**Example frontmatter**:

```yaml
---
name: standardizing-python
disable-model-invocation: true
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---
```

**How consuming skills reference it**:

```markdown
# In writing-prose/SKILL.md:

Zero tolerance for patterns in `/standardizing-prose` -- never use any of them.

# In reviewing-prose/SKILL.md:

**Before reviewing**, read `/standardizing-prose` for the complete catalog of anti-patterns.
```

When Claude encounters `/standardizing-prose` in a loaded skill's text, it reads the reference skill to load the shared knowledge into context.

**Naming convention**: Use `standardizing-{domain}` for standards/anti-patterns. Examples:

- `standardizing-python` — Python code standards
- `standardizing-python-testing` — Python testing standards
- `standardizing-prose` — Prose anti-patterns

**What NOT to do**:

- Do NOT use directive descriptions (`ALWAYS`/`NEVER`) — causes false activations when users aren't invoking it
- Do NOT put shared content in one skill's `references/` directory and hope the other skill can find it — `${CLAUDE_SKILL_DIR}` is isolated per skill
- Do NOT duplicate the same content across multiple skills' `references/` directories — creates maintenance drift

---

## Assets Directory Patterns

### When to Use assets/

| Use Case          | Example                               |
| ----------------- | ------------------------------------- |
| Output templates  | HTML boilerplate, component scaffolds |
| Exact boilerplate | Config files that must be precise     |
| Visual assets     | Images, icons, fonts                  |
| Data templates    | JSON schemas, sample data             |

### When NOT to Use assets/

| Avoid                    | Instead                      |
| ------------------------ | ---------------------------- |
| Code that varies per use | Describe pattern in SKILL.md |
| Large files (>50KB)      | Reference external URLs      |
| Generated content        | Create dynamically           |

### Asset Types

```
assets/
├── templates/           # Output scaffolds
│   ├── component.tsx    # React component template
│   ├── page.html        # HTML page template
│   └── config.json      # Configuration template
├── schemas/             # Data structures
│   ├── input.schema.json
│   └── output.schema.json
└── examples/            # Reference implementations
    ├── simple.tsx
    └── advanced.tsx
```

### Referencing Assets in SKILL.md

**Template with placeholders**:

```markdown
Use `assets/templates/component.tsx` as base template.

Replace placeholders:

- `{{COMPONENT_NAME}}` → PascalCase component name
- `{{PROPS_INTERFACE}}` → TypeScript props interface
- `{{RENDER_CONTENT}}` → JSX content
```

**Exact copy**:

```markdown
Copy `assets/config.json` to project root.
Do not modify structure; only update values.
```

**Reference example**:

```markdown
Follow pattern in `assets/examples/simple.tsx` for basic usage.
For advanced features, see `assets/examples/advanced.tsx`.
```

### Template Design Principles

1. **Self-documenting placeholders**: `{{DESCRIPTIVE_NAME}}`
2. **Minimal structure**: Only essential boilerplate
3. **Clear boundaries**: Mark customizable sections
4. **Valid syntax**: Template should be syntactically valid

**Good template**:

```typescript
// assets/templates/component.tsx
import React from 'react';

interface {{COMPONENT_NAME}}Props {
  {{PROPS}}
}

export function {{COMPONENT_NAME}}({ {{DESTRUCTURED_PROPS}} }: {{COMPONENT_NAME}}Props) {
  {{HOOKS}}

  return (
    {{JSX_CONTENT}}
  );
}
```

---

## Frontmatter Best Practices

### Good Description (triggers reliably)

```yaml
description: >-
  ALWAYS invoke this skill when building UI components, visual interfaces,
  progress trackers, quiz interfaces, or interactive elements.
  NEVER build UI components without this skill.
```

**Why it works**:

- `ALWAYS` with specific trigger phrases
- `NEVER` with negative constraint
- ≤1024 characters
- Claude Code can match user intent and knows not to bypass

### Bad Description (won't trigger)

```yaml
# Passive style — ~77% activation
description: |
  Create production widgets for ChatGPT Apps.
  Use when users ask to build UI components or visual interfaces.

# Vague — near 0% activation
description: Widget stuff
```

**Why these fail**:

- Passive "Use when" gives Claude room to skip activation
- No negative constraint — Claude may build UI directly
- Vague description has no trigger phrases at all

---

## Scope Clarity Examples

### Good Scope

```markdown
## What This Skill Does

- Creates ChatGPT widgets with window.openai integration
- Supports all display modes (inline, fullscreen, pip)
- Implements theme support (light/dark)
- Follows OpenAI UX/UI guidelines

## What This Skill Does NOT Do

- Create native mobile apps
- Handle backend server logic
- Manage user authentication
- Deploy widgets to production
```

### Bad Scope (missing exclusions)

```markdown
## What This Skill Does

- Creates widgets
```

---

## Reference Organization

### By Domain (for multi-domain skills)

```
references/
├── aws.md        # AWS-specific patterns
├── gcp.md        # GCP-specific patterns
└── azure.md      # Azure-specific patterns
```

### By Complexity (for single-domain skills)

```
references/
├── quick-start.md     # Basic usage
├── advanced.md        # Complex scenarios
└── troubleshooting.md # Common issues
```

### By Feature (for feature-rich skills)

```
references/
├── authentication.md  # Auth patterns
├── state-management.md # State handling
└── error-handling.md   # Error patterns
```
