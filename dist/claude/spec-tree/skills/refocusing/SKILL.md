---
name: refocusing
description: >-
  ALWAYS invoke this skill when running ad hoc commands, writing debug scripts, or writing code without a spec.
  NEVER run ad hoc commands or write throwaway scripts without invoking this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

<objective>
You are re-focused on pursuing your goal following the strict spec-tree methodology.
</objective>

<diagnosis>
**What you did wrong:**

You left the path of the spec-tree `/applying` flow. One or more of these happened:

- You ran ad hoc commands or tool calls instead of writing tests that provide the debuggability you now know you need.
- You executed throwaway commands to "see what the API returns" instead of writing a proper contract test that will help you again 6 months from now when the API has changed.
- You made changes or ran operations without loading the spec-tree node with `/contextualizing` first.

**Why it matters:**

The ad hoc commands you just ran take the same effort as writing a proper test. But they require user permission (this is how the uer noticed what you are doing) and keep you from reaching your goal.

If you had written a proper test using `/testing-{language}` skill, the test would serve you and other agents again in the future. The debugging or exploration you just did without following `/applying` will need to be reworked from scratch when the spec changes. What a monumental waste of your time!

</diagnosis>

<process>

## Step 1: Stop what you are doing

Do not run any more ad hoc commands. Do not "just quickly" execute one more step. Stop.

## Step 2: Assess the damage

Look at what you have produced so far:

- If you ran ad hoc commands or tool calls: note any useful information but do not continue in this mode.
- If you wrote ad hoc scripts or debug code: delete them.
- If you wrote implementation without tests: keep the code but do not commit it.
- If you wrote tests without loading context: the tests may be wrong — verify after Step 3 of `/applying`.

</process>

<success_criteria>

- Ad hoc commands stopped.
- The `/applying` skill is invoked and proper flow started from Step 1.
- No further ad hoc commands executed, whether they require permission or not is immaterial.
- No throwaway scripts or debug code written.

</success_criteria>
