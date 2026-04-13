<required_reading>
The essential principles in SKILL.md are already loaded. No additional reading needed.
</required_reading>

<process>

## Step 0: Check for resume

Before classifying input, check whether the interview is resuming a prior session.

1. If the user's input is a file path, check for `.{name}.interview-state.json` in the same directory
2. If the user's input is free text containing "resume" or "continue", search the current directory and parents for any `.*.interview-state.json` files

**If state file found:**

1. Read the state file. Extract: Q&A pairs, coverage map state, timestamp, codebase analysis summary, preview status
2. Re-validate against current codebase:
   - Has the input file changed since the timestamp? (compare mtime or git blob)
   - Have referenced source files changed?
   - Have project docs (README, CLAUDE.md) changed?
3. Flag any stale answers: "This answer may no longer apply because [reason]. Re-ask?"
4. Display the current coverage map with `[done]` / `[current]` / `[pending]` markers
5. Use AskUserQuestion to confirm: "Resume from [area X], or start over?"
6. If resume → jump to **Step 4: Conduct Interview** with the loaded state
7. If start over → proceed to Step 1, delete the state file after the new interview completes

**If no state file:** proceed to Step 1.

## Step 1: Classify Input

Determine what the user provided in response to the intake question:

1. **File path** (contains `/`, `.md`, `.txt`, etc.) — read the file
2. **Free text** — treat as a verbal requirement
3. **Non-spec file** (source code, config, data) — confirm intent via AskUserQuestion: "This looks like [type]. Want me to interview you about [inferred intent]?"

## Step 2: Pre-Analysis

Launch an Explore agent to:

1. Analyze the input — what's defined, ambiguous, missing
2. Scan the codebase for existing patterns, architecture, tech stack
3. Check dependencies (package.json, pyproject.toml, etc.)
4. Read project docs (README, CLAUDE.md, existing specs)

Share the structured brief with the user before asking the first question. Include your preliminary opinions — they set the tone for a collaborative interview, not a passive one.

## Step 3: Build Initial Coverage Map

From the input and pre-analysis, identify coverage areas:

- Start with the generic defaults: **Problem, Users, Technical Approach, Risks, Constraints**
- Add areas revealed by the input (e.g., input mentions an API — add "API Design")
- Remove areas already fully addressed in the input (mark [done])
- If modifying an existing document, derive areas from its current sections

Display the initial coverage map to the user.

## Step 4: Conduct Interview

Follow the essential principles strictly:

1. Display coverage map before each question
2. Ask one question at a time via AskUserQuestion (2-4 options, no obvious choices)
3. Push back on contradictions, over-engineering, missing edge cases
4. Refine coverage map as new areas emerge — split, add, mark [done]
5. Record every pushback and resolution in a running decisions log

## Step 5: Propose Completion

When all discovered areas are [done]:

1. Summarize what was covered and key decisions made
2. Ask via AskUserQuestion: "Ready to write, or explore further?"
3. If further — identify what areas to add or deepen
4. If ready — proceed to output

## Step 6: Determine Output

Ask the user via AskUserQuestion:

1. **Output format** — markdown spec, structured notes, or other
2. **Output location** — where to save the file

Then ask whether to generate an interactive HTML preview or go straight to the document. If preview, follow the Preview Protocol from essential principles.

## Step 7: Generate Output

Generate dynamic sections based on what the interview revealed:

- Do NOT use a fixed template — let the interview content drive structure
- Each sufficiently explored coverage area becomes a section
- Include a **Decisions Log** with all pushback, disagreements, and resolutions
- Include **Implementation Order** if technical dependencies were discussed
- If auto-split was triggered, generate separate files with a master document linking them

## Step 8: Post-Output

Ask via AskUserQuestion what task format the user wants:

- Claude Code tasks (trackable in current session)
- GitHub Issues via `gh` CLI
- Markdown checklist appended to the document
- No tasks — just the document

Generate the task breakdown from the document's dependency graph and implementation order.

</process>

<success_criteria>
The direct interview is complete when:

- [ ] Pre-analysis brief shared with user before first question
- [ ] All coverage areas explored and marked [done]
- [ ] Pushback applied where warranted, decisions logged
- [ ] Output document generated (with preview revision loop if opted in)
- [ ] Task breakdown generated (if requested)
- [ ] Interview state persisted to `.interview-state.json`

</success_criteria>
