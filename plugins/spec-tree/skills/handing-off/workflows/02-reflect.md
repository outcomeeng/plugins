<objective>
Work through all five perspectives internally before presenting anything to the user. This is the most important workflow — it produces the input for everything that follows. Do not rush. Do not skip perspectives.

For each perspective, think about what was learned, what changed, and what the next agent needs. Check existing escape hatches (PLAN.md, ISSUES.md) against current reality — stale escape hatches are worse than none.

</objective>

<perspective_lessons>
What did you learn during this session that changes how future agents should work on this codebase?

- **User corrections** — things the user had to repeat or correct. What rule would have prevented the mistake?
- **Methodology gaps** — skills that were inadequate or missing. What should change?
- **Coding patterns** — patterns that worked or failed. What should be codified?

For each lesson, classify by nature to determine the correct persistence target:

| Lesson nature         | Signal                                                       | Destination                                                                         |
| --------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| **Library / API**     | API change, library behavior, version gotcha                 | Language plugin `coding-*` skill references (e.g., `coding-typescript/references/`) |
| **Methodology**       | Skill invocation order, audit interpretation, process error  | Spec-tree plugin skill (amend skill instructions)                                   |
| **Project rule**      | Convention specific to this codebase, forbidden pattern      | Project `CLAUDE.md`                                                                 |
| **Interaction style** | Response format, verbosity, tone — NOT coding patterns       | Memory (`feedback` type)                                                            |
| **Domain knowledge**  | Who's doing what, external system locations, project context | Memory (`project`/`reference` type)                                                 |
| **Spec correction**   | Assertion was wrong or incomplete                            | Amend the spec file directly                                                        |
| **Task-specific**     | Only relevant to this session's work                         | Session file only                                                                   |

**The nature determines the target — not the other way around.** A library API change belongs in a coding skill reference even if you discovered it in this project. A coding pattern the auditor would reject belongs in `standardizing-*`, not `coding-*`.

</perspective_lessons>

<perspective_issues>
What is broken, missing, or wrong?

- **Spec issues** — assertions that are wrong, missing, or untestable
- **Implementation gaps** — known bugs, missing edge cases, incomplete features
- **Test gaps** — assertions without test coverage, tests that don't test what they claim
- **Stale references** — old paths, renamed nodes, broken links anywhere in the tree

**Fix it now or defer it — never propose fixing something you can fix right now.**

For each issue:

1. **Can you fix it right now?** Stale references, broken links, wrong paths, simple corrections — fix them immediately using Edit/Grep. Do not propose them in workflow 03. Do not ask the user. Just fix them and note what you fixed.
2. **Is the fix too large for this session?** Write or update ISSUES.md in the node directory.
3. **Is a spec assertion wrong?** Fix the spec directly — this is a durable fix.

**Critical**: Read any existing ISSUES.md for each anchored node. Check every item — are items listed as open now fixed? Are there new issues not yet listed? A stale ISSUES.md will mislead the next agent.

</perspective_issues>

<perspective_path_forward>
What do you now understand about how the remaining work should proceed?

- **Approach decisions** — what approach was chosen and why alternatives were rejected
- **Remaining steps** — what concrete steps remain, in what order
- **Dependencies** — what must happen before what

For each insight, determine persistence target:

- Amend a spec (if the insight changes what the spec says)
- Write or update PLAN.md in the node directory (if it's a concrete plan for remaining work)
- Remove PLAN.md (if all planned steps are now complete — a done plan is a stale plan)
- Session file only (if it's coordination context)

**Critical**: Read any existing PLAN.md for each anchored node. Are steps listed as remaining now complete? Is the plan still the right approach? Update or remove — never leave a stale plan.

</perspective_path_forward>

<perspective_skills>
Which skills did you invoke, which should you have invoked, and which does the next agent need?

- **Critical skills** — always include `/understanding` and `/contextualizing {node}` for each anchored node, plus language-specific skills that were used
- **Missed skills** — skills that SHOULD have been invoked but were not. What problems did skipping them cause?
- **Next skill** — what specific skill should the receiving agent invoke first, and why

</perspective_skills>

<perspective_starting_point>
Where exactly should the next agent begin?

- **Node path** — full path to the node (e.g., `spx/21-foo.enabler/32-bar.outcome`)
- **TDD flow position** — which step (1-8) per the `/applying` skill
- **First action** — the specific skill invocation that resumes work

</perspective_starting_point>

<success_criteria>

All five perspectives completed internally before proceeding to workflow 03.

</success_criteria>
