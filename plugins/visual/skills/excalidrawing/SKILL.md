---
name: excalidrawing
description: >-
  ALWAYS invoke this skill when creating Excalidraw diagrams, visualizing workflows, architectures, or concepts.
  NEVER generate Excalidraw JSON without this skill.
---

<objective>
Generate `.excalidraw` JSON files that **argue visually**, not just display information.

**Setup:** If the user asks you to set up this skill (renderer, dependencies, etc.), see `README.md` for instructions.
</objective>

<customization>
**All colors and brand-specific styles live in one file:** `references/color-palette.md`. Read it before generating any diagram and use it as the single source of truth for all color choices — shape fills, strokes, text colors, evidence artifact backgrounds, everything.

To make this skill produce diagrams in your own brand style, edit `color-palette.md`. Everything else in this file is universal design methodology and Excalidraw best practices.
</customization>

<quick_start>

1. **Assess depth** — Simple/conceptual or comprehensive/technical?
2. **Research** (technical only) — Look up actual specs, formats, event names
3. **Map concepts to visual patterns** — See `references/visual-patterns.md`
4. **Design before JSON** — Sketch the flow mentally, ensure variety
5. **Generate JSON** — Section-by-section for large diagrams (see `references/large-diagrams.md`)
6. **Render & validate** — Run the render-view-fix loop until it's right

Pull colors from `references/color-palette.md`, element templates from `references/element-templates.md`, and JSON schema from `references/json-schema.md`.

</quick_start>

<philosophy>
**Diagrams should ARGUE, not DISPLAY.**

A diagram isn't formatted text. It's a visual argument that shows relationships, causality, and flow that words alone can't express. The shape should BE the meaning.

**The Isomorphism Test**: If you removed all text, would the structure alone communicate the concept? If not, redesign.

**The Education Test**: Could someone learn something concrete from this diagram, or does it just label boxes? A good diagram teaches — it shows actual formats, real event names, concrete examples.
</philosophy>

<depth_assessment>
Before designing, determine what level of detail this diagram needs:

**Simple/Conceptual Diagrams** — Use abstract shapes when:

- Explaining a mental model or philosophy
- The audience doesn't need technical specifics
- The concept IS the abstraction (e.g., "separation of concerns")

**Comprehensive/Technical Diagrams** — Use concrete examples when:

- Diagramming a real system, protocol, or architecture
- The diagram will be used to teach or explain (e.g., YouTube video)
- The audience needs to understand what things actually look like
- You're showing how multiple technologies integrate

**For technical diagrams, you MUST include evidence artifacts and do research first.**
</depth_assessment>

<research_mandate>
**Before drawing anything technical, research the actual specifications.**

If you're diagramming a protocol, API, or framework:

1. Look up the actual JSON/data formats
2. Find the real event names, method names, or API endpoints
3. Understand how the pieces actually connect
4. Use real terminology, not generic placeholders

Bad: "Protocol" → "Frontend"
Good: "AG-UI streams events (RUN_STARTED, STATE_DELTA, A2UI_UPDATE)" → "CopilotKit renders via createA2UIMessageRenderer()"

**Research makes diagrams accurate AND educational.**
</research_mandate>

<evidence_artifacts>
Evidence artifacts are concrete examples that prove your diagram is accurate and help viewers learn. Include them in technical diagrams.

**Types of evidence artifacts** (choose what's relevant to your diagram):

| Artifact Type            | When to Use                                | How to Render                                                                         |
| ------------------------ | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| **Code snippets**        | APIs, integrations, implementation details | Dark rectangle + syntax-colored text (see color palette for evidence artifact colors) |
| **Data/JSON examples**   | Data formats, schemas, payloads            | Dark rectangle + colored text (see color palette)                                     |
| **Event/step sequences** | Protocols, workflows, lifecycles           | Timeline pattern (line + dots + labels)                                               |
| **UI mockups**           | Showing actual output/results              | Nested rectangles mimicking real UI                                                   |
| **Real input content**   | Showing what goes IN to a system           | Rectangle with sample content visible                                                 |
| **API/method names**     | Real function calls, endpoints             | Use actual names from docs, not placeholders                                          |

The key principle: **show what things actually look like**, not just what they're called.
</evidence_artifacts>

<multi_zoom>
Comprehensive diagrams operate at multiple zoom levels simultaneously:

**Level 1: Summary Flow** — A simplified overview showing the full pipeline at a glance. Often placed at the top or bottom.

**Level 2: Section Boundaries** — Labeled regions that group related components. These create visual "rooms" that help viewers understand what belongs together.

**Level 3: Detail Inside Sections** — Evidence artifacts, code snippets, and concrete examples within each section. This is where the educational value lives.

**For comprehensive diagrams, aim to include all three levels.** The summary gives context, the sections organize, and the details teach.

| Bad (Displaying)              | Good (Arguing)                                     |
| ----------------------------- | -------------------------------------------------- |
| 5 equal boxes with labels     | Each concept has a shape that mirrors its behavior |
| Card grid layout              | Visual structure matches conceptual structure      |
| Icons decorating text         | Shapes that ARE the meaning                        |
| Same container for everything | Distinct visual vocabulary per concept             |
| Everything in a box           | Free-floating text with selective containers       |

</multi_zoom>

<container_discipline>
**Not every piece of text needs a shape around it.** Default to free-floating text. Add containers only when they serve a purpose.

| Use a Container When...                                   | Use Free-Floating Text When...                |
| --------------------------------------------------------- | --------------------------------------------- |
| It's the focal point of a section                         | It's a label or description                   |
| It needs visual grouping with other elements              | It's supporting detail or metadata            |
| Arrows need to connect to it                              | It describes something nearby                 |
| The shape itself carries meaning (decision diamond, etc.) | Typography alone creates sufficient hierarchy |
| It represents a distinct "thing" in the system            | It's a section title, subtitle, or annotation |

**Typography as hierarchy**: Use font size, weight, and color to create visual hierarchy without boxes. A 28px title doesn't need a rectangle around it.

**The container test**: For each boxed element, ask "Would this work as free-floating text?" If yes, remove the container.
</container_discipline>

<design_process>
Do this BEFORE generating JSON:

**Step 0: Assess Depth** — Simple/conceptual or comprehensive/technical? If comprehensive, do research first.

**Step 1: Understand Deeply** — For each concept, ask:

- What does this concept **DO**? (not what IS it)
- What relationships exist between concepts?
- What's the core transformation or flow?
- **What would someone need to SEE to understand this?**

**Step 2: Map Concepts to Patterns** — See `references/visual-patterns.md` for the full pattern library and concept-to-pattern mapping table.

**Step 3: Ensure Variety** — Each major concept must use a different visual pattern. No uniform cards or grids.

**Step 4: Sketch the Flow** — Mentally trace how the eye moves through the diagram. There should be a clear visual story.

**Step 5: Generate JSON** — For large/comprehensive diagrams, build section-by-section (see `references/large-diagrams.md`). Use descriptive string IDs and namespace seeds by section.

**Step 6: Render & Validate (MANDATORY)** — Run the render-view-fix loop until the diagram looks right. See `<render_validate>` below.
</design_process>

<color_usage>
Colors encode information, not decoration. Every color choice should come from `references/color-palette.md`.

**Key principles:**

- Each semantic purpose (start, end, decision, AI, error, etc.) has a specific fill/stroke pair
- Free-floating text uses color for hierarchy (titles, subtitles, details — each at a different level)
- Evidence artifacts (code snippets, JSON examples) use their own dark background + colored text scheme
- Always pair a darker stroke with a lighter fill for contrast

**Do not invent new colors.** If a concept doesn't fit an existing semantic category, use Primary/Neutral or Secondary.
</color_usage>

<aesthetics>
**Roughness:**

- `roughness: 0` — Clean, crisp edges. **Default** for modern/technical diagrams.
- `roughness: 1` — Hand-drawn, organic feel. Use for brainstorming/informal diagrams.

**Stroke Width:**

- `strokeWidth: 1` — Thin, elegant. Good for lines, dividers, subtle connections.
- `strokeWidth: 2` — Standard. Good for shapes and primary arrows.
- `strokeWidth: 3` — Bold. Use sparingly for emphasis.

**Opacity:** Always `opacity: 100`. Use color, size, and stroke width for hierarchy instead of transparency.

**Small markers:** Use small dots (10-20px ellipses) instead of full shapes for timeline markers, bullet points, connection nodes, and visual anchors.
</aesthetics>

<layout>
**Hierarchy Through Scale:**

- **Hero**: 300×150 — visual anchor, most important
- **Primary**: 180×90
- **Secondary**: 120×60
- **Small**: 60×40

**Whitespace = Importance:** The most important element has the most empty space around it (200px+).

**Flow Direction:** Left→right or top→bottom for sequences, radial for hub-and-spoke.

**Connections Required:** Position alone doesn't show relationships. If A relates to B, there must be an arrow.
</layout>

<text_rules>
**CRITICAL**: The JSON `text` property contains ONLY readable words.

```json
{
  "id": "myElement1",
  "text": "Start",
  "originalText": "Start"
}
```

Settings: `fontSize: 16`, `fontFamily: 3`, `textAlign: "center"`, `verticalAlign: "middle"`
</text_rules>

<json_structure>

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

See `references/element-templates.md` for copy-paste JSON templates for each element type (text, line, dot, rectangle, arrow). See `references/json-schema.md` for the complete element schema. Pull colors from `references/color-palette.md` based on each element's semantic purpose.
</json_structure>

<render_validate>
You cannot judge a diagram from JSON alone. After generating or editing the Excalidraw JSON, you MUST render it to PNG, view the image, and fix what you see — in a loop until it's right.

**GATE: Before first render**, verify the `.excalidraw` file is valid JSON:

```bash
python3 -m json.tool < path-to-file.excalidraw > /dev/null
```

If invalid, fix JSON syntax before wasting a render cycle.

**How to render:**

```bash
cd ${CLAUDE_SKILL_DIR}/references && uv run python render_excalidraw.py <path-to-file.excalidraw>
```

This outputs a PNG next to the `.excalidraw` file. Then use the **Read tool** on the PNG to view it.

**The loop:**

1. **Render & View** — Run the render script, then Read the PNG.
2. **Audit against your original vision** — Does the visual structure match the conceptual structure you planned? Does each section use the intended pattern? Is the visual hierarchy correct?
3. **Check for visual defects:**
   - Text clipped by or overflowing its container
   - Text or shapes overlapping other elements
   - Arrows crossing through elements instead of routing around them
   - Arrows landing on the wrong element or pointing into empty space
   - Labels floating ambiguously
   - Uneven spacing, text too small, lopsided composition
4. **Fix** — Edit the JSON. Common fixes: widen containers, adjust `x`/`y` coordinates, add waypoints to arrow `points` arrays, reposition labels, resize elements.
5. **Re-render & re-view** — Repeat until the diagram passes both the vision check and the defect check. Typically 2-4 iterations.

**When to stop:** No text clipped or overlapping, arrows route cleanly, spacing is consistent, composition is balanced, you'd show it without caveats.

**First-time setup:**

```bash
cd ${CLAUDE_SKILL_DIR}/references
uv sync
uv run playwright install chromium
```

</render_validate>

<failure_modes>
Failures from actual usage:

**Failure 1: JSON truncated mid-generation**

- What happened: Entire diagram generated in one response, hit output token limit, produced invalid JSON
- Why it failed: Comprehensive diagrams exceed ~32,000 token output limit
- How to avoid: ALWAYS build section-by-section for large diagrams. See `references/large-diagrams.md`

**Failure 2: Text clipped by container**

- What happened: Text overflowed rectangle bounds but looked fine in JSON
- Why it failed: Container `width`/`height` not updated after changing text content
- How to avoid: After changing any `text` property, recalculate and update the container dimensions. Always verify with a render cycle.

**Failure 3: Arrow bound to wrong element**

- What happened: Arrow visually pointed at element B but was bound to element A
- Why it failed: IDs were reused or copy-pasted without updating `startBinding`/`endBinding`
- How to avoid: Use descriptive unique IDs (e.g., `"auth_flow_arrow"`, not `"arrow1"`). After every arrow edit, verify both `startBinding.elementId` and `endBinding.elementId` reference the correct targets.

**Failure 4: All boxes same size — "card grid" anti-pattern**

- What happened: Diagram looked like a PowerPoint slide with equal rectangles
- Why it failed: Skipped Step 2 (map concepts to patterns) and defaulted to uniform containers
- How to avoid: Each major concept MUST use a different visual pattern. Run the Isomorphism Test before generating JSON.

</failure_modes>

<success_criteria>

**Depth & Evidence** (technical diagrams):

- [ ] Research done — actual specs, formats, event names looked up
- [ ] Evidence artifacts included — code snippets, JSON examples, or real data
- [ ] Multi-zoom — summary flow + section boundaries + detail
- [ ] Concrete over abstract — real content shown, not just labeled boxes

**Conceptual:**

- [ ] Isomorphism — each visual structure mirrors its concept's behavior
- [ ] Argument — diagram SHOWS something text alone couldn't
- [ ] Variety — each major concept uses a different visual pattern
- [ ] No card grids or uniform containers

**Container Discipline:**

- [ ] <30% of text elements inside containers
- [ ] Lines as structure for tree/timeline patterns
- [ ] Typography hierarchy via font size and color

**Technical:**

- [ ] `text` contains only readable words
- [ ] `fontFamily: 3`, `roughness: 0`, `opacity: 100`
- [ ] Valid JSON (verify: `python3 -m json.tool < file.excalidraw > /dev/null`)

**Visual Validation (render required):**

- [ ] Rendered to PNG and visually inspected
- [ ] No text overflow, no overlapping elements
- [ ] Arrows land correctly, even spacing, balanced composition

</success_criteria>

<reference_guides>

| File                              | When to Read                                       |
| --------------------------------- | -------------------------------------------------- |
| `references/color-palette.md`     | Before generating any diagram (colors and styles)  |
| `references/element-templates.md` | When writing JSON (copy-paste element templates)   |
| `references/json-schema.md`       | When you need the complete element schema          |
| `references/visual-patterns.md`   | During Step 2 (concept-to-pattern mapping)         |
| `references/large-diagrams.md`    | When building comprehensive/multi-section diagrams |

</reference_guides>
