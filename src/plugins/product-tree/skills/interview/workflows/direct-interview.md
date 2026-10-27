<required_reading>
The essential principles in SKILL.md are already loaded. No additional reading needed.
</required_reading>

<process>

<step number="0" name="check-resume">

Before classifying input, check whether the interview is resuming a prior session.

1. If the user's input is a file path, check for `.{name}.interview-state.json` in the same directory
2. If the user's input is free text containing "resume" or "continue", search the current directory and parents for any `.*.interview-state.json` files

**If state file found:**

1. Read the state file. Extract: Q&A pairs, coverage map state, timestamp, codebase analysis summary, output status
2. Re-validate against current codebase:
   - Has the input file changed since the timestamp? (compare mtime or git blob)
   - Have referenced source files changed?
   - Have product docs (README, {{! file('root_guide') !}}) changed?
3. Flag any stale answers: "This answer may no longer apply because [reason]. Re-ask?"
4. Display the current coverage map with `[done]` / `[current]` / `[pending]` markers
5. Use {{! tool('ask_user') !}} to confirm: "Resume from [area X], or start over?"
6. If resume → jump to **Step 4: Conduct Interview** with the loaded state
7. If start over → proceed to Step 1, delete the state file after the new interview completes

**If no state file:** proceed to Step 1.

</step>

<step number="1" name="classify-input">

Determine what the user provided in response to the intake question:

1. **File path** (contains `/`, `.md`, `.txt`, etc.) — read the file
2. **Free text** — treat as a verbal requirement
3. **Non-spec file** (source code, config, data) — confirm intent via {{! tool('ask_user') !}}: "This looks like [type]. Want me to interview you about [inferred intent]?"

</step>

<step number="2" name="pre-analysis">

Complete the Pre-Analysis Protocol, including a check of dependency manifests (package.json, pyproject.toml, etc.), and share the structured brief with its preliminary opinions before the first question.

</step>

<step number="3" name="build-initial-coverage-map">

From the input and pre-analysis, identify coverage areas:

- Start with the generic defaults: **Problem, Users, Technical Approach, Risks, Constraints**
- Add areas revealed by the input (e.g., input mentions an API — add "API Design")
- Remove areas already fully addressed in the input (mark [done])
- If modifying an existing document, derive areas from its current sections

Display the initial coverage map to the user.

</step>

<step number="4" name="conduct-interview">

Conduct the interview under the Questioning, Coverage, and Pushback Protocols, and record every pushback and resolution in a running decisions log.

</step>

<step number="5" name="propose-completion">

When all discovered areas are [done]:

1. Summarize what was covered and key decisions made
2. Ask via {{! tool('ask_user') !}}: "Ready to write, or explore further?"
3. If further — identify what areas to add or deepen
4. If ready — proceed to output

</step>

<step number="6" name="determine-output">

Ask the user via {{! tool('ask_user') !}}:

1. **Output format** — markdown spec, structured notes, or other
2. **Output location** — where to save the file

</step>

<step number="7" name="generate-output">

Generate dynamic sections based on what the interview revealed:

- Do NOT use a fixed template — let the interview content drive structure
- Each sufficiently explored coverage area becomes a section
- Include a **Decisions Log** with all pushback, disagreements, and resolutions
- Include **Implementation Order** if technical dependencies were discussed
- If auto-split was triggered, generate separate files with a master document linking them

</step>

<step number="8" name="post-output">

Ask via {{! tool('ask_user') !}} what task format the user wants:

- Claude Code tasks (trackable in current session)
- GitHub Issues via `gh` CLI
- Markdown checklist appended to the document
- No tasks — just the document

Generate the task breakdown from the document's dependency graph and implementation order.

</step>

</process>

<success_criteria>
The direct interview is complete when:

- [ ] Pre-analysis brief shared with user before first question
- [ ] All coverage areas explored and marked [done]
- [ ] Pushback applied where warranted, decisions logged
- [ ] Output document generated
- [ ] Task breakdown generated (if requested)
- [ ] Interview state persisted to `.interview-state.json`

</success_criteria>
