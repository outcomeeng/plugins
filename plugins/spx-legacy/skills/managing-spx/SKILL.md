---
name: managing-spx
description: >-
  ALWAYS invoke this skill when creating or organizing specs, capabilities, features, stories, or ADRs.
  NEVER create, read, or modify any files in the spx/ directory without this skill.
---

<objective>
Single source of truth for spx/ directory structure and all document templates. Enables creation of requirements (PRD), decisions (ADR for architecture, PDR for product), and work items (capability/feature/story) with consistent structure across all products using the SPX framework.
</objective>

<prerequisite>
**Foundational understanding required:**

- `/understanding-durable-map` - Specs are permanent product documentation, not work items
- `/understanding-outcome-decomposition` - What belongs at each level (capability/feature/story)

If you find yourself wanting to "close" items or thinking in tasks, read these first.
</prerequisite>

<quick_start>
Different use cases read different sections:

- **Structure definition** → Read `<structure_definition>` for spx/ directory hierarchy, BSP numbering, test co-location
- **ADR templates** → Read `<adr_templates>` for Architectural Decision Record patterns
- **PDR templates** → Read `<pdr_templates>` for Product Decision Record patterns
- **PRD templates** → Read `<requirement_templates>` for Product Requirements
- **Work item templates** → Read `<work_item_templates>` for capability, feature, and story patterns

Use progressive disclosure - read only what you need.
</quick_start>

<structure_definition>

<overview>
The spx/ directory follows the Outcome Engineering framework structure.
</overview>

<three_phase_transformation>

1. **Requirements (PRD)** - Capture product vision without implementation constraints
2. **Decisions (ADR/PDR)** - Constrain architecture (ADR) or product behavior (PDR) with explicit trade-offs
3. **Work Items (Capability/Feature/Story)** - Sized, testable implementation containers

</three_phase_transformation>

<directory_structure>

```
spx/
├── {product-name}.prd.md             # Product requirements
├── NN-{slug}.adr.md                  # Product-wide ADRs (interleaved)
├── NN-{slug}.pdr.md                  # Product-wide PDRs (interleaved)
└── NN-{slug}.capability/
    ├── {slug}.capability.md
    ├── tests/
    ├── NN-{slug}.adr.md              # Capability-scoped ADRs (interleaved)
    ├── NN-{slug}.pdr.md              # Capability-scoped PDRs (interleaved)
    └── NN-{slug}.feature/
        ├── {slug}.feature.md
        ├── tests/
        ├── NN-{slug}.adr.md          # Feature-scoped ADRs (interleaved)
        ├── NN-{slug}.pdr.md          # Feature-scoped PDRs (interleaved)
        └── NN-{slug}.story/
            ├── {slug}.story.md
            └── tests/
```

</directory_structure>

<work_item_hierarchy>

- **Capability**: Product-wide impact, contains features
  - Tests co-located in `spx/NN-{slug}.capability/tests/`
  - May have optional PRD as catalyst/enrichment

- **Feature**: Specific functionality, contains stories
  - Tests co-located in `spx/.../NN-{slug}.feature/tests/`
  - Technical details documented in feature.md (no separate TRD)

- **Story**: Atomic implementation unit, no children
  - Tests co-located in `spx/.../NN-{slug}.story/tests/`

Test level (unit, integration, e2e) is determined per-component by the evidence needed, not by hierarchy level. See `/testing` for the methodology.

</work_item_hierarchy>

<key_principles>

- **Requirements immutable** - code adapts to requirements, not vice versa
- **BSP numbering**: Binary Space Partitioning encodes dependency order—lower BSP items are dependencies that higher-BSP items may rely on; same BSP means independent
- **Full paths required**: BSP numbers repeat at different levels (see `<bsp_full_paths>` below)
- **Test co-location**: Tests stay in `spx/.../tests/` permanently (no graduation)

</key_principles>

<bsp_full_paths>

**🚨 CRITICAL: BSP numbers repeat at different levels—always use full paths.**

```text
21-foo.capability/21-bar.feature/54-baz.story/  ← One story-54
21-foo.capability/37-qux.feature/54-baz.story/  ← DIFFERENT story-54
37-other.capability/21-bar.feature/54-baz.story/  ← DIFFERENT story-54
```

**ALWAYS use the FULL PATH when referencing work items:**

| ❌ WRONG (Ambiguous)     | ✅ CORRECT (Unambiguous)                                  |
| ------------------------ | --------------------------------------------------------- |
| "story-54"               | "21-foo.capability/21-bar.feature/54-baz.story/"          |
| "implement feature-21"   | "implement 21-foo.capability/21-bar.feature/"             |
| "Continue with story-54" | "Continue 21-foo.capability/21-bar.feature/54-baz.story/" |

**Why this matters:**

- BSP numbers encode dependency order within each level, not global uniqueness
- Different capabilities can have identically-numbered features
- Different features can have identically-numbered stories
- Without the full path, agents will access the WRONG work item

**When communicating about work items:**

1. Always include the full hierarchy path
2. Never use bare numbers like "story-54" without context
3. When in doubt, use the absolute path from `spx/`

</bsp_full_paths>

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

> **Lower BSP = dependency.** Higher-BSP items may rely on lower-BSP items.
>
> Check dependencies before working on an item—lower-numbered items in the same scope may need to be done first.

This applies at every level:

| If you see...                              | It means...                              |
| ------------------------------------------ | ---------------------------------------- |
| `48-foo.feature/` before `87-bar.feature/` | 48-foo MUST be DONE before 87-bar starts |
| `21-foo.story/` before `32-bar.story/`     | 21-foo MUST be DONE before 32-bar starts |
| `48-foo [OPEN]`, `87-bar [IN_PROGRESS]`    | **BUG**: Dependency violation            |

</bsp_dependency_order>

<finding_next_work_item>

```
1. List all work items in BSP order (capability → feature → story)
2. Return the FIRST item where status ≠ DONE
3. That item blocks everything after it
```

**Example**:

```text
48-test-harness.feature/ [OPEN]        ← Was added after 87 but blocks it
87-e2e-workflow.feature/ [IN_PROGRESS] ← Was already started, then dependency discovered
```

**Next work item**: `48-test-harness.feature/` → its first OPEN story.

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
21-foo.capability/
└── 21-first-feature.feature/
```

</case_1_first_item>

<case_2_insert_between>

Use midpoint: `new = floor((left + right) / 2)`

```
# Insert between 21 and 54
new = floor((21 + 54) / 2) = 37

21-first.feature/
37-inserted.feature/    ← NEW
54-second.feature/
```

</case_2_insert_between>

<case_3_append_after>

Use midpoint to upper bound: `new = floor((last + 99) / 2)`

```
# Append after 54
new = floor((54 + 99) / 2) = 76

21-first.feature/
54-second.feature/
76-appended.feature/    ← NEW
```

</case_3_append_after>

</creating_new_items>

</numbering_work_items>

<creating_work_items>
Every work item needs:

1. **Directory**: `NN-{slug}.{type}/` (e.g., `21-auth.capability/`)
2. **Spec file**: `{slug}.{type}.md` (e.g., `auth.capability.md`)
3. **Tests directory**: `tests/` (create when starting work)

Optional:

- **Decision Records**: `NN-{slug}.adr.md` or `NN-{slug}.pdr.md` (interleaved with work items)

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

ADRs are interleaved with work items at any level:

- **Product**: `spx/NN-{slug}.adr.md`
- **Capability**: `spx/NN-{slug}.capability/NN-{slug}.adr.md`
- **Feature**: `spx/.../NN-{slug}.feature/NN-{slug}.adr.md`

Stories inherit decisions from parent feature/capability.

</scope_levels>

<naming_convention>

Format: `NN-{slug}.adr.md`

- NN: BSP number in range [10, 99]
- slug: Kebab-case description (e.g., `use-postgresql-for-persistence`)

</naming_convention>

<bsp_numbering_for_adrs>

**Lower BSP = dependency.** Higher-BSP ADRs may rely on lower-BSP decisions.

ADRs follow the same BSP numbering as work items:

<creating_first_adr>

Use position **21** (leaves room for ~10 items before/after):

```
21-first-decision.adr.md
```

</creating_first_adr>

<inserting_between_adrs>

Use midpoint: `new = floor((left + right) / 2)`

```
# Insert between 21 and 54
new = floor((21 + 54) / 2) = 37

21-type-safety.adr.md
37-inserted-decision.adr.md    ← NEW
54-cli-framework.adr.md
```

</inserting_between_adrs>

<appending_after_last>

Use midpoint to upper bound: `new = floor((last + 99) / 2)`

```
# Append after 54
new = floor((54 + 99) / 2) = 76

21-type-safety.adr.md
54-cli-framework.adr.md
76-appended-decision.adr.md    ← NEW
```

</appending_after_last>

</bsp_numbering_for_adrs>

<dependency_order_within_scope>

**Scope boundaries**: ADRs are scoped to product/capability/feature.

**Within scope**: Lower BSP = dependency that higher-BSP items may rely on.

| If you see...             | It means...                              |
| ------------------------- | ---------------------------------------- |
| `21-type-safety.adr.md`   | Foundational decision, others may depend |
| `37-validation.adr.md`    | May depend on 21                         |
| `54-cli-framework.adr.md` | May depend on both 21 and 37             |

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
- References: `[Foo](37-foo.adr.md)` (markdown link with path)
- Filenames can be renamed, slugs stay stable, markdown links update automatically

</why_no_numbers_in_content>

<why_markdown_links_only>

**Problem**: Plain text references like "ADR-23" or even `` `23-foo.adr.md` `` break when files are renumbered.

**Solution**: Markdown links `[Decision Title](NN-slug.adr.md)`:

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

PDRs are interleaved with work items at any level:

- **Product**: `spx/NN-{slug}.pdr.md`
- **Capability**: `spx/NN-{slug}.capability/NN-{slug}.pdr.md`
- **Feature**: `spx/.../NN-{slug}.feature/NN-{slug}.pdr.md`

Stories inherit product decisions from parent feature/capability.

</scope_levels>

<naming_convention>

Format: `NN-{slug}.pdr.md`

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
See [Type Safety](21-type-safety.adr.md) for validation approach.
```

</within_same_directory>

<from_child_to_parent_scope>

```markdown
<!-- Feature ADR referencing capability ADR -->

This decision builds on [Config Loading](../21-config-loading.adr.md).

<!-- Story referencing feature ADR -->

Implementation follows [CLI Structure](../21-cli-structure.adr.md).
```

</from_child_to_parent_scope>

<from_work_item_to_adr>

```markdown
<!-- From story to capability ADR -->

Architectural constraints: [Commander Pattern](../../21-commander-pattern.adr.md)

<!-- From feature to product ADR -->

Type system: [Type Safety](../../../21-type-safety.adr.md)
```

</from_work_item_to_adr>

</in_markdown_documents>

<never_use_these_formats>

❌ Plain text reference: "See ADR-21" or "See PDR-21"
❌ Code-only reference: `` `21-type-safety.adr.md` `` or `` `21-lifecycle.pdr.md` ``
❌ Number-only reference: "ADR 21 specifies..." or "PDR 21 specifies..."

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
Templates for Product Requirements (PRD).
</overview>

<prd_template>

**Location**: `${CLAUDE_SKILL_DIR}/templates/product/product.prd.md`

**Purpose**: Product requirements - user value, customer journey, measurable outcomes

**Usage**:

```bash
# Read PRD template
Read: ${CLAUDE_SKILL_DIR}/templates/product/product.prd.md

# Adapt for product change
- Define user value proposition
- Document measurable outcomes with targets
- Specify acceptance criteria
- Avoid implementation details
```

**Placement**:

- Product-wide: `spx/{product-name}.prd.md`
- Capability catalyst: `spx/NN-{slug}.capability/{topic}.prd.md`

</prd_template>

<requirements_rules>

- **Immutable**: Code adapts to requirements, not vice versa
- **Optional catalyst**: PRD may exist as enrichment; spec file is always required
- **No TRDs**: Technical details belong in feature.md, not separate documents

</requirements_rules>

</requirement_templates>

<work_item_templates>

<overview>
Templates for capabilities, features, and stories.
</overview>

<template_locations>

```
${CLAUDE_SKILL_DIR}/templates/outcomes/capability-name.capability.md
${CLAUDE_SKILL_DIR}/templates/outcomes/feature-name.feature.md
${CLAUDE_SKILL_DIR}/templates/outcomes/story-name.story.md
```

</template_locations>

<usage_pattern>

```bash
# For capability
Read: ${CLAUDE_SKILL_DIR}/templates/outcomes/capability-name.capability.md
Adapt: Replace {slug} with kebab-case name
       Fill functional requirements
       Add user value context

# For feature
Read: ${CLAUDE_SKILL_DIR}/templates/outcomes/feature-name.feature.md
Adapt: Replace {slug} with kebab-case name
       Specify integration scope
       Define component interactions

# For story
Read: ${CLAUDE_SKILL_DIR}/templates/outcomes/story-name.story.md
Adapt: Replace {slug} with kebab-case name
       Detail atomic implementation
       List specific functions/classes
```

</usage_pattern>

<file_placement>

Work items follow this pattern:

```
spx/{BSP}-{slug}.{type}/{slug}.{type}.md
```

Examples:

- `spx/21-core-cli.capability/core-cli.capability.md`
- `spx/21-core-cli.capability/10-init.feature/init.feature.md`
- `spx/21-core-cli.capability/15-init.feature/87-parse-flags.story/parse-flags.story.md`

</file_placement>

<test_verification>

Tests stay co-located with their specs permanently. Test level is indicated by filename suffix (`.unit.test.*`, `.integration.test.*`, `.e2e.test.*`) but is not tied to hierarchy level — any test level can appear at any node. See `/testing` for how to determine the right level.

</test_verification>

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
