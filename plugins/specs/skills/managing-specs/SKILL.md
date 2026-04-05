---
name: managing-specs
description: >-
  ALWAYS invoke this skill when creating or organizing specs, capabilities, features, stories, or ADRs.
  NEVER create, read, or modify any files in the specs/ directory without this skill.
---

<objective>
Single source of truth for specs/ directory structure and all document templates. Enables creation of requirements (PRD/TRD), decisions (ADR for architecture, PDR for product), and work items (capability/feature/story) with consistent structure across all products using the SPX framework.
</objective>

<quick_start>
Different use cases read different sections:

- **Structure definition** → Read `<structure_definition>` for specs/ directory hierarchy, BSP numbering, co-located tests
- **ADR templates** → Read `<adr_templates>` for Architectural Decision Record patterns
- **PDR templates** → Read `<pdr_templates>` for Product Decision Record patterns
- **PRD/TRD templates** → Read `<requirement_templates>` for Product and Technical Requirements
- **Work item templates** → Read `<work_item_templates>` for capability, feature, story, and DONE.md patterns

Use progressive disclosure - read only what you need.
</quick_start>

<structure_definition>

<overview>
The specs/ directory follows the SPX framework structure.
</overview>

<three_phase_transformation>

1. **Requirements (PRD/TRD)** - Capture vision without implementation constraints
2. **Decisions (ADR/PDR)** - Constrain architecture (ADR) or product behavior (PDR) with explicit trade-offs
3. **Work Items (Capability/Feature/Story)** - Sized, testable implementation containers

</three_phase_transformation>

<directory_structure>

```
specs/
├── [product-name].prd.md          # Product-wide PRD
├── decisions/                      # Product-wide ADRs (optional)
│   └── adr-NN_{slug}.md
└── work/
    ├── backlog/
    ├── doing/
    │   └── capability-NN_{slug}/
    │       ├── {slug}.capability.md
    │       ├── {slug}.prd.md       # Optional capability-scoped PRD from which the capability work item (`{slug}.capability.md`) is derived
    │       ├── {slug}.prd.md       # Optional capability-scoped TRD from which capability-scoped ADRs are derived
    │       ├── decisions/           # Capability-scoped ADRs
    │       ├── tests/
    │       └── feature-NN_{slug}/
    │           ├── {slug}.prd.md   # Optional capability-scoped PRD from which the feature spec in `{slug}.feature.md` is derived
    │           ├── {slug}.trd.md   # Optional capability-scoped TRD from which the feature-scoped ADRs are derived
    │           ├── {slug}.feature.md
    │           ├── decisions/       # Feature-scoped ADRs
    │           ├── tests/
    │           └── story-NN_{slug}/
    │               ├── {slug}.story.md
    │               └── tests/
    └── done/
```

</directory_structure>

<work_item_hierarchy>

- **Capability**: E2E scenario with product-wide impact
  - Tests co-located in `specs/.../capability-NN/tests/` (E2E level)
  - May have optional PRD as catalyst/enrichment
  - Contains features

- **Feature**: Integration scenario with specific functionality
  - Tests co-located in `specs/.../feature-NN/tests/` (Integration level)
  - May have optional TRD as catalyst/enrichment
  - Contains stories

- **Story**: Unit-tested atomic implementation
  - Tests co-located in `specs/.../story-NN/tests/` (Unit level)
  - No children
  - Atomic implementation unit

</work_item_hierarchy>

<key_principles>

- **PRD OR TRD** at same scope, never both
- **Requirements immutable** - code adapts to requirements, not vice versa
- **BSP numbering**: Two-digit (10-99), lower number = must complete first
- **BSP numbers are SIBLING-UNIQUE**: Numbers are only unique among siblings, not globally (see `<bsp_sibling_uniqueness>` below)
- **Tests co-located**: Tests stay in `specs/.../tests/` permanently (no graduation)

</key_principles>

<bsp_sibling_uniqueness>

**🚨 CRITICAL: BSP numbers are ONLY unique among siblings at the same level.**

```text
capability-21/feature-01/story-54  ← One story-54
capability-22/feature-01/story-54  ← DIFFERENT story-54
capability-21/feature-02/story-54  ← DIFFERENT story-54
```

**ALWAYS use the FULL PATH when referencing work items:**

| ❌ WRONG (Ambiguous)     | ✅ CORRECT (Unambiguous)                     |
| ------------------------ | -------------------------------------------- |
| "story-54"               | "capability-21/feature-54/story-54"          |
| "implement feature-01"   | "implement capability-21/feature-01"         |
| "Continue with story-54" | "Continue capability-21/feature-54/story-54" |

**Why this matters:**

- Different capabilities can have identically-numbered features
- Different features can have identically-numbered stories
- "story-54" could refer to dozens of different stories across the codebase
- Without the full path, agents will access the WRONG work item

**When communicating about work items:**

1. Always include the full hierarchy path
2. Never use bare numbers like "story-54" without context
3. When in doubt, use the absolute path from `specs/work/`

</bsp_sibling_uniqueness>

</structure_definition>

<workflow>

<reading_status>

<understanding_work_items>

<three_states>
Status values:

| State           | Meaning          |
| --------------- | ---------------- |
| **OPEN**        | Work not started |
| **IN_PROGRESS** | Work underway    |
| **DONE**        | Complete         |

</three_states>

<bsp_dependency_order>

> **Lower BSP number = must complete FIRST.**
>
> You CANNOT work on item N until ALL items with numbers < N are DONE.

This applies at every level:

| If you see...                                   | It means...                                      |
| ----------------------------------------------- | ------------------------------------------------ |
| `feature-48` before `feature-87`                | feature-48 MUST be DONE before feature-87 starts |
| `story-21` before `story-32`                    | story-21 MUST be DONE before story-32 starts     |
| `feature-48 [OPEN]`, `feature-87 [IN_PROGRESS]` | **BUG**: Dependency violation                    |

</bsp_dependency_order>

<finding_next_work_item>

```
1. List all work items in BSP order (capability → feature → story)
2. Return the FIRST item where status ≠ DONE
3. That item blocks everything after it
```

**Example**:

```text
feature-48_test-harness [OPEN]        ← Was added after feature-87 but blocks it
feature-87_e2e-workflow [IN_PROGRESS] ← Was already started, then dependency discovered
```

**Next work item**: `feature-48_test-harness` → its first OPEN story.

</finding_next_work_item>

</understanding_work_items>

</reading_status>

<managing_items>

<managing_work_items>

<numbering_work_items>

<bsp_numbering>
Two-digit prefixes in range **[10, 99]** encode dependency order.
</bsp_numbering>

<creating_new_items>

<case_1_first_item>

Use position **21** (leaves room for ~10 items before/after):

```
# First feature in a new capability
capability-21_foo/
└── feature-21_first-feature/
```

</case_1_first_item>

<case_2_insert_between>

Use midpoint: `new = floor((left + right) / 2)`

```
# Insert between feature-21 and feature-54
new = floor((21 + 54) / 2) = 37

feature-21_first/
feature-37_inserted/    ← NEW
feature-54_second/
```

</case_2_insert_between>

<case_3_append_after>

Use midpoint to upper bound: `new = floor((last + 99) / 2)`

```
# Append after feature-54
new = floor((54 + 99) / 2) = 76

feature-21_first/
feature-54_second/
feature-76_appended/    ← NEW
```

</case_3_append_after>

</creating_new_items>

</numbering_work_items>

<creating_work_items>
Every work item needs:

1. **Directory**: `NN_{slug}/`
2. **Definition file**: `{slug}.{capability|feature|story}.md`
3. **Tests directory**: `tests/` (create when starting work)

Optional:

- **Requirements document**: `{topic}.prd.md` or `{topic}.trd.md`
- **Decision Records**: `decisions/adr-NNN_{slug}.md`

</creating_work_items>

</managing_work_items>

</managing_items>

</workflow>

<adr_templates>

<overview>
ADRs document technical choices with trade-offs and consequences.
</overview>

<template_location>

```
${CLAUDE_SKILL_DIR}/templates/decisions/architectural-decision.adr.md
```

</template_location>

<usage>

Read the template and adapt:

```bash
# Read ADR template
Read: ${CLAUDE_SKILL_DIR}/templates/decisions/architectural-decision.adr.md

# Adapt for your decision
- State the architectural concern this decision governs (atemporal voice — no history)
- Document the chosen option and rationale
- Specify consequences and trade-offs
- Define compliance criteria
```

</usage>

<scope_levels>

ADRs can exist at three levels:

- **Project**: `specs/decisions/adr-NN_{slug}.md`
- **Capability**: `specs/work/doing/capability-NN/decisions/adr-NN_{slug}.md`
- **Feature**: `specs/work/doing/.../feature-NN/decisions/adr-NN_{slug}.md`

Stories inherit decisions from parent feature/capability.

</scope_levels>

<naming_convention>

Format: `adr-{NN}_{slug}.md`

- NN: BSP number in range [10, 99]
- slug: Kebab-case description (e.g., `use-postgresql-for-persistence`)

</naming_convention>

<bsp_numbering_for_adrs>

**Lower BSP number = must decide first (within scope).**

ADRs follow the same BSP numbering as work items:

<creating_first_adr>

Use position **21** (leaves room for ~10 items before/after):

```
decisions/adr-21_first-decision.md
```

</creating_first_adr>

<inserting_between_adrs>

Use midpoint: `new = floor((left + right) / 2)`

```
# Insert between adr-21 and adr-54
new = floor((21 + 54) / 2) = 37

decisions/adr-21_type-safety.md
decisions/adr-37_inserted-decision.md    ← NEW
decisions/adr-54_cli-framework.md
```

</inserting_between_adrs>

<appending_after_last>

Use midpoint to upper bound: `new = floor((last + 99) / 2)`

```
# Append after adr-54
new = floor((54 + 99) / 2) = 76

decisions/adr-21_type-safety.md
decisions/adr-54_cli-framework.md
decisions/adr-76_appended-decision.md    ← NEW
```

</appending_after_last>

</bsp_numbering_for_adrs>

<dependency_order_within_scope>

**Scope boundaries**: ADRs are scoped to product/capability/feature.

**Within scope**: Lower BSP = must decide first.

| If you see...             | It means...                              |
| ------------------------- | ---------------------------------------- |
| `adr-21_type-safety.md`   | Foundational decision, must decide first |
| `adr-37_validation.md`    | Depends on adr-21, must come after       |
| `adr-54_cli-framework.md` | May depend on both adr-21 and adr-37     |

**Cross-scope dependencies**: Must be documented explicitly in the ADR content.

| Dependency                            | How to Express                           |
| ------------------------------------- | ---------------------------------------- |
| Feature ADR depends on capability ADR | Reference in "Context" section with link |
| Capability ADR depends on product ADR | Reference in "Context" section with link |

</dependency_order_within_scope>

<why_bsp_numbering>

**Problem**: Sequential numbering (01, 02, 03) cannot accommodate discovered dependencies.

**Example**: You have decisions adr-01, adr-02, adr-03. You discover adr-02 needs a prior decision about type safety. With sequential numbering, you must renumber all subsequent ADRs.

**Solution**: BSP numbering allows insertion at any point using midpoint calculation.

</why_bsp_numbering>

<why_no_numbers_in_content>

**Problem**: If ADR file is renumbered (e.g., adr-23 → adr-37), content with embedded numbers becomes stale.

**Examples**:

- Header `# ADR 23: Foo` - wrong after renumbering
- Reference "See ADR-23" - wrong after renumbering

**Solution**:

- Header: `# ADR: Foo` (document type prefix, no number)
- References: `[Foo](decisions/adr-37_foo.md)` (markdown link with path)
- Filenames can be renamed, slugs stay stable, markdown links update automatically

</why_no_numbers_in_content>

<why_markdown_links_only>

**Problem**: Plain text references like "ADR-23" or even `` `adr-23_foo.md` `` break when files are renumbered.

**Solution**: Markdown links `[Decision Title](relative/path/to/adr-NN_slug.md)`:

- Modern editors update links automatically on file rename
- Links are clickable for navigation
- Slug provides stability even if number changes
- Can search by slug if link breaks

</why_markdown_links_only>

</adr_templates>

<pdr_templates>

<overview>
PDRs document product behavior decisions with trade-offs and user impact. Unlike ADRs (which govern code architecture), PDRs govern observable product behavior.
</overview>

<template_location>

```
${CLAUDE_SKILL_DIR}/templates/decisions/product-decision.pdr.md
```

</template_location>

<usage>

Read the template and adapt:

```bash
# Read PDR template
Read: ${CLAUDE_SKILL_DIR}/templates/decisions/product-decision.pdr.md

# Adapt for your decision
- State the product behavior this decision governs (atemporal voice — no history)
- Describe the chosen product behavior
- List product invariants users can rely on
- Specify compliance criteria for product behavior
```

</usage>

<scope_levels>

PDRs can exist at three levels:

- **Project**: `specs/decisions/pdr-NN_{slug}.md`
- **Capability**: `specs/work/doing/capability-NN/decisions/pdr-NN_{slug}.md`
- **Feature**: `specs/work/doing/.../feature-NN/decisions/pdr-NN_{slug}.md`

Stories inherit product decisions from parent feature/capability.

</scope_levels>

<naming_convention>

Format: `pdr-{NN}_{slug}.md`

- NN: BSP number in range [10, 99]
- slug: Kebab-case description (e.g., `simulation-lifecycle-phases`)

</naming_convention>

<adr_vs_pdr>

| Aspect     | ADR                              | PDR                           |
| ---------- | -------------------------------- | ----------------------------- |
| Governs    | Code architecture                | Product behavior              |
| Invariants | Algebraic code properties        | Observable user guarantees    |
| Compliance | Code review criteria             | Product behavior validation   |
| Example    | "Use PostgreSQL for persistence" | "Simulation has three phases" |

**When to use which:**

- Technical implementation choice → ADR
- User-facing behavior choice → PDR
- If unsure, ask: "Is this about HOW we build it (ADR) or WHAT users experience (PDR)?"

</adr_vs_pdr>

</pdr_templates>

<referencing_decisions>

<overview>
**Always use markdown links with descriptive titles for both ADRs and PDRs.**
</overview>

<in_markdown_documents>

<within_same_directory>

```markdown
See [Type Safety](adr-21_type-safety.md) for validation approach.
```

</within_same_directory>

<from_child_to_parent_scope>

```markdown
<!-- Feature ADR referencing capability ADR -->

This decision builds on [Config Loading](../../decisions/adr-21_config-loading.md).

<!-- Story referencing feature ADR -->

Implementation follows [CLI Structure](../../decisions/adr-21_cli-structure.md).
```

</from_child_to_parent_scope>

<from_work_item_to_adr>

```markdown
<!-- From story to capability ADR -->

Architectural constraints: [Commander Pattern](../../decisions/adr-21_commander-pattern.md)

<!-- From feature to product ADR -->

Type system: [Type Safety](../../../../decisions/adr-21_type-safety.md)
```

</from_work_item_to_adr>

</in_markdown_documents>

<never_use_these_formats>

❌ Plain text reference: "See ADR-21"
❌ Code-only reference: `` `adr-21_type-safety.md` ``
❌ Number-only reference: "ADR 21 specifies..."

</never_use_these_formats>

<why_markdown_links>

- **Clickable**: Navigate directly in editors/viewers
- **Stable**: Slug provides stability even if number changes
- **Updatable**: Modern editors can update links on file rename
- **Descriptive**: Title provides context without opening file

</why_markdown_links>

</referencing_decisions>

<requirement_templates>

<overview>
Templates for Product Requirements (PRD) and Technical Requirements (TRD).
</overview>

<prd_template>

**Location**: `${CLAUDE_SKILL_DIR}/templates/requirements/product-change.prd.md`

**Purpose**: Product requirements - user value, customer journey, measurable outcomes

**Usage**:

```bash
# Read PRD template
Read: ${CLAUDE_SKILL_DIR}/templates/requirements/product-change.prd.md

# Adapt for product change
- Define user value proposition
- Document measurable outcomes with targets
- Specify acceptance criteria
- Avoid implementation details
```

**Placement**:

- Product-wide: `specs/{product-name}.prd.md`
- Capability catalyst: `specs/work/doing/capability-NN/{topic}.prd.md`

</prd_template>

<trd_template>

**Location**: `${CLAUDE_SKILL_DIR}/templates/requirements/technical-change.trd.md`

**Purpose**: Technical requirements - system architecture, validation strategy, test infrastructure

**Usage**:

```bash
# Read TRD template
Read: ${CLAUDE_SKILL_DIR}/templates/requirements/technical-change.trd.md

# Adapt for technical change
- Specify technical architecture
- Define testing strategy (Level 1/2/3)
- Document validation approach
- Identify infrastructure needs
```

**Placement**:

- Feature catalyst: `specs/work/doing/.../feature-NN/{topic}.trd.md`

</trd_template>

<requirements_rules>

- **PRD OR TRD** at same scope, never both
- **Immutable**: Code adapts to requirements, not vice versa
- **Optional catalyst**: PRD/TRD may exist as enrichment; spec file is always required

</requirements_rules>

</requirement_templates>

<work_item_templates>

<overview>
Templates for capabilities, features, stories, and completion evidence.
</overview>

<template_locations>

```
${CLAUDE_SKILL_DIR}/templates/work-items/capability-name.capability.md
${CLAUDE_SKILL_DIR}/templates/work-items/feature-name.feature.md
${CLAUDE_SKILL_DIR}/templates/work-items/story-name.story.md
${CLAUDE_SKILL_DIR}/templates/work-items/DONE.md
```

</template_locations>

<usage_pattern>

```bash
# For capability
Read: ${CLAUDE_SKILL_DIR}/templates/work-items/capability-name.capability.md
Adapt: Replace {slug} with kebab-case name
       Fill functional requirements
       Add user value context

# For feature
Read: ${CLAUDE_SKILL_DIR}/templates/work-items/feature-name.feature.md
Adapt: Replace {slug} with kebab-case name
       Specify integration scope
       Define component interactions

# For story
Read: ${CLAUDE_SKILL_DIR}/templates/work-items/story-name.story.md
Adapt: Replace {slug} with kebab-case name
       Detail atomic implementation
       List specific functions/classes

# For completion
Read: ${CLAUDE_SKILL_DIR}/templates/work-items/DONE.md
Adapt: List co-located tests by level
       Document verification steps
       Include evidence of completion
```

</usage_pattern>

<file_placement>

Work items follow this pattern:

```
specs/work/{backlog|doing|done}/{level}-{bsp}_{slug}/{slug}.{level}.md
```

Examples:

- `specs/work/doing/capability-21_core-cli/core-cli.capability.md`
- `specs/work/doing/capability-21_core-cli/feature-10_init/init.feature.md`
- `specs/work/doing/capability-21_core-cli/feature-15_init/story-87_parse-flags/parse-flags.story.md`

</file_placement>

<test_co_location>

Tests stay co-located with their work item permanently:

- Capability tests: `specs/.../capability-NN/tests/*.e2e.test.ts`
- Feature tests: `specs/.../feature-NN/tests/*.integration.test.ts`
- Story tests: `specs/.../story-NN/tests/*.unit.test.ts`

DONE.md documents test verification and provides completion evidence.

</test_co_location>

</work_item_templates>

<success_criteria>
Skill is working correctly when:

- [ ] Templates exist and are readable in `templates/` subdirectories
- [ ] Other skills can successfully read templates from appropriate sections
- [ ] Progressive disclosure guides readers to relevant sections
- [ ] ADR, PDR, requirement, and work item patterns are clearly documented
- [ ] Test co-location paths are correctly specified for each level
- [ ] BSP numbering uses consistent two-digit format (10-99)

</success_criteria>
