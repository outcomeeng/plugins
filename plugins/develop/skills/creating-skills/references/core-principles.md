<overview>
Core principles guide skill authoring decisions. These principles ensure skills are efficient, effective, and maintainable.
</overview>

<xml_structure_principle>
Skills use pure XML structure for consistent parsing, efficient token usage, and improved Claude performance.

**Why XML over markdown headings**:

1. **Consistency**: XML enforces consistent structure. All skills use the same tag names for the same purposes (`<objective>`, `<quick_start>`, `<success_criteria>`).

2. **Parseability**: XML provides unambiguous boundaries. Claude can reliably identify section boundaries, understand content purpose, and skip irrelevant sections.

3. **Token efficiency**: XML tags use fewer tokens than markdown headings while providing semantic meaning.

4. **Claude performance**: Claude performs better with pure XML because of unambiguous section boundaries and semantic tags.

**Critical rule**: Remove ALL markdown headings (#, ##, ###) from skill body content. Replace with semantic XML tags. Keep markdown formatting WITHIN content (bold, lists, code blocks).

**Required tags**:

- `<objective>` - What the skill does
- `<quick_start>` - Immediate actionable guidance
- `<success_criteria>` - How to know it worked

</xml_structure_principle>

<conciseness_principle>
The context window is shared. Your skill shares it with the system prompt, conversation history, other skills' metadata, and the actual request.

**Guidance**: Only add context Claude doesn't already have. Challenge each piece:

- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Example**:

Concise (~50 tokens):

````text
<quick_start>
Extract PDF text with pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
````

</quick_start>

````
Verbose (~150 tokens):
```text
<quick_start>
PDF files are a common file format used for documents. To extract text from them, we'll use a Python library called pdfplumber...
</quick_start>
````

The concise version assumes Claude knows what PDFs are, understands Python imports, and can read code.

**When to elaborate**:

- Concept is domain-specific (not general programming knowledge)
- Pattern is non-obvious or counterintuitive
- Context affects behavior in subtle ways

</conciseness_principle>

<degrees_of_freedom_principle>
Match the level of specificity to the task's fragility and variability.

**High freedom** (text-based instructions):

- Multiple approaches are valid
- Decisions depend on context
- Creative solutions welcome

Example: Code review, content generation, analysis

**Medium freedom** (pseudocode or scripts with parameters):

- A preferred pattern exists
- Some variation is acceptable
- Configuration affects behavior

Example: API calls, file processing, data transformation

**Low freedom** (specific scripts, few parameters):

- Operations are fragile and error-prone
- Consistency is critical
- A specific sequence must be followed

Example: Database migrations, payment processing, security operations

**Analogy**: Think of Claude as a robot exploring a path:

- **Narrow bridge**: Only one safe way forward. Provide exact instructions.
- **Open field**: Many paths lead to success. Give general direction.

</degrees_of_freedom_principle>

<progressive_disclosure_principle>
SKILL.md serves as an overview. Reference files contain details. Claude loads reference files only when needed.

**Token efficiency**:

- Simple task: Load SKILL.md only (~500 tokens)
- Medium task: Load SKILL.md + one reference (~1000 tokens)
- Complex task: Load SKILL.md + multiple references (~2000 tokens)

**Implementation**:

- Keep SKILL.md under 500 lines
- Split detailed content into reference files
- Keep references one level deep from SKILL.md
- Use descriptive reference file names

</progressive_disclosure_principle>

<domain_discovery_principle>
Users want domain expertise IN the skill. They may not BE domain experts.

**Research the domain BEFORE asking user questions**:

| Discover       | How                                   |
| -------------- | ------------------------------------- |
| Core concepts  | Official docs                         |
| Best practices | Search "[domain] best practices 2025" |
| Anti-patterns  | Search "[domain] common mistakes"     |
| Security       | Search "[domain] security"            |
| Ecosystem      | Search "[domain] tools"               |

**Sources priority**: Official docs → Library docs → GitHub → Community → WebSearch

**Knowledge sufficiency check** before asking user:

- Core concepts: Can I explain the fundamentals?
- Best practices: Do I know the recommended approaches?
- Anti-patterns: Do I know what to avoid?

If incomplete → Research more. Only ask user for proprietary/internal info.
</domain_discovery_principle>

<validation_principle>
Validation scripts are force multipliers. They catch errors that Claude might miss.

**Good validation scripts**:

- Provide verbose, specific error messages
- Show available valid options when something is invalid
- Pinpoint exact location of problems
- Suggest actionable fixes
- Are deterministic and reliable

</validation_principle>

<principle_summary>

| Principle              | Key Point                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------- |
| XML Structure          | Pure XML, no markdown headings. Required: objective, quick_start, success_criteria |
| Conciseness            | Only add context Claude doesn't have. Assume Claude is smart.                      |
| Degrees of Freedom     | Match specificity to fragility. High for creative, low for fragile.                |
| Progressive Disclosure | SKILL.md under 500 lines. Details in reference files.                              |
| Domain Discovery       | Research domain BEFORE asking users. Embed expertise in skill.                     |
| Validation             | Make validation scripts verbose and specific.                                      |
| </principle_summary>   |                                                                                    |
