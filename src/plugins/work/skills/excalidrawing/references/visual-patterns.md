<patterns>

**Fan-Out (One-to-Many)**

Central element with arrows radiating to multiple targets. Use for: sources, PRDs, root causes, central hubs.

```
      ○
     ↗
□ → ○
     ↘
      ○
```

**Convergence (Many-to-One)**

Multiple inputs merging through arrows to single output. Use for: aggregation, funnels, synthesis.

```
○ ↘
○ → □
○ ↗
```

**Tree (Hierarchy)**

Parent-child branching with connecting lines and free-floating text (no boxes needed). Use for: file systems, org charts, taxonomies.

```
label
├── label
│   ├── label
│   └── label
└── label
```

Use `line` elements for the trunk and branches, free-floating text for labels.

**Spiral/Cycle (Continuous Loop)**

Elements in sequence with arrow returning to start. Use for: feedback loops, iterative processes, evolution.

```
□ → □
↑     ↓
□ ← □
```

**Cloud (Abstract State)**

Overlapping ellipses with varied sizes. Use for: context, memory, conversations, mental states.

**Assembly Line (Transformation)**

Input → Process Box → Output with clear before/after. Use for: transformations, processing, conversion.

```
○○○ → [PROCESS] → □□□
chaos              order
```

**Side-by-Side (Comparison)**

Two parallel structures with visual contrast. Use for: before/after, options, trade-offs.

**Gap/Break (Separation)**

Visual whitespace or barrier between sections. Use for: phase changes, context resets, boundaries.

**Lines as Structure**

Use lines (type: `line`, not arrows) as primary structural elements instead of boxes:

- **Timelines**: Vertical or horizontal line with small dots (10-20px ellipses) at intervals, free-floating labels beside each dot
- **Tree structures**: Vertical trunk line + horizontal branch lines, with free-floating text labels (no boxes needed)
- **Dividers**: Thin dashed lines to separate sections
- **Flow spines**: A central line that elements relate to, rather than connecting boxes

```
Timeline:           Tree:
  ●─── Label 1        │
  │                   ├── item
  ●─── Label 2        │   ├── sub
  │                   │   └── sub
  ●─── Label 3        └── item
```

Lines + free-floating text often creates a cleaner result than boxes + contained text.

</patterns>

<shape_meaning>

Choose shape based on what it represents — or use no shape at all:

| Concept Type                  | Shape                         | Why                          |
| ----------------------------- | ----------------------------- | ---------------------------- |
| Labels, descriptions, details | **none** (free-floating text) | Typography creates hierarchy |
| Section titles, annotations   | **none** (free-floating text) | Font size/weight is enough   |
| Markers on a timeline         | small `ellipse` (10-20px)     | Visual anchor, not container |
| Start, trigger, input         | `ellipse`                     | Soft, origin-like            |
| End, output, result           | `ellipse`                     | Completion, destination      |
| Decision, condition           | `diamond`                     | Classic decision symbol      |
| Process, action, step         | `rectangle`                   | Contained action             |
| Abstract state, context       | overlapping `ellipse`         | Fuzzy, cloud-like            |
| Hierarchy node                | lines + text (no boxes)       | Structure through lines      |

**Rule**: Default to no container. Add shapes only when they carry meaning. Aim for <30% of text elements to be inside containers.

</shape_meaning>

<concept_to_pattern>

When mapping concepts to visual patterns during design (Step 2):

| If the concept...               | Use this pattern                                   |
| ------------------------------- | -------------------------------------------------- |
| Spawns multiple outputs         | **Fan-out** (radial arrows from center)            |
| Combines inputs into one        | **Convergence** (funnel, arrows merging)           |
| Has hierarchy/nesting           | **Tree** (lines + free-floating text)              |
| Is a sequence of steps          | **Timeline** (line + dots + free-floating labels)  |
| Loops or improves continuously  | **Spiral/Cycle** (arrow returning to start)        |
| Is an abstract state or context | **Cloud** (overlapping ellipses)                   |
| Transforms input to output      | **Assembly line** (before → process → after)       |
| Compares two things             | **Side-by-side** (parallel with contrast)          |
| Separates into phases           | **Gap/Break** (visual separation between sections) |

</concept_to_pattern>
