---
name: refocus
description: >-
  ALWAYS invoke this skill when running ad hoc commands, writing debug scripts, or writing code without a spec.
  NEVER run ad hoc commands or write throwaway scripts without invoking this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

<objective>
Re-focus on pursuing the goal following the strict spec-tree methodology.
</objective>

<diagnosis>
**What went wrong:**

Claude left the path of the spec-tree `/apply` flow. One or more of these happened:

- Claude ran ad hoc commands or tool calls instead of writing tests that provide the debuggability now needed.
- Claude executed throwaway commands to "see what the API returns" instead of writing a proper contract test that will help again 6 months from now when the API has changed.
- Claude made changes or ran operations without loading the spec-tree node with `/contextualize` first.

**Why it matters:**

Those ad hoc commands take the same effort as writing a proper test. But they require user permission (this is how the user noticed the ad hoc work) and block progress toward the goal.

A proper test written with the `/test-{language}` skill would serve Claude and other agents again in the future. The debugging or exploration just done without following `/apply` will need to be reworked from scratch when the spec changes — a monumental waste of effort.

</diagnosis>

<process>

**Step 1 — Stop the ad hoc work**

Do not run any more ad hoc commands. Do not "just quickly" execute one more step. Stop.

**Step 2 — Assess the damage**

Review what has been produced so far:

- Ad hoc commands or tool calls run: note any useful information but do not continue in this mode.
- Ad hoc scripts or debug code written: delete them.
- Implementation written without tests: keep the code but do not commit it.
- Tests written without loading context: the tests may be wrong — verify after Step 3 of `/apply`.

</process>

<success_criteria>

- Ad hoc commands stopped.
- The `/apply` skill is invoked and proper flow started from Step 1.
- No further ad hoc commands executed, whether they require permission or not is immaterial.
- No throwaway scripts or debug code written.

</success_criteria>
