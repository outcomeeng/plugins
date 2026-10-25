---
name: refocus
description: >-
  ALWAYS invoke this skill when running ad hoc commands or writing code without a spec inside a repository whose root contains `spx/`.
allowed-tools: Read, Glob, Grep
---

<objective>
Ad hoc work re-focused onto the strict product-tree methodology.
</objective>

<diagnosis>
**What went wrong:**

Claude left the path of the product-tree `/apply` flow. One or more of these happened:

- Claude ran ad hoc commands or tool calls instead of writing tests that provide the debuggability now needed.
- Claude executed throwaway commands to "see what the API returns" instead of writing a proper contract test that will help again 6 months from now when the API has changed.
- Claude made changes or ran operations without loading the product-tree node with `/contextualize` first.

**Why it matters:**

Ad hoc commands cost as much as a proper test, require user permission (this is how the user noticed the ad hoc work), and block progress toward the goal.

Evidence established through `/verify` serves Claude and other agents again in the future; when `/verify` selects test, it delegates generic test decisions through `/test` before language-specific expression. The debugging or exploration done without following `/apply` is reworked from scratch when the spec changes.

</diagnosis>

<process>

**Step 1 — Stop the ad hoc work**

Run no further ad hoc commands.

**Step 2 — Assess the damage**

Review what has been produced so far:

- Ad hoc commands or tool calls run: note any useful information but do not continue in this mode.
- Ad hoc scripts or debug code written: leave them uncommitted and report their paths to the operator.
- Implementation written without tests: keep the code but do not commit it.
- Tests written without loading context: the tests may be wrong — verify after Step 3 of `/apply`.

**Step 3 — Resume the flow**

Use skill `product-tree:apply`.

</process>

<success_criteria>

- Ad hoc commands stopped.
- The `/apply` skill is invoked and proper flow started from Step 1.
- No throwaway scripts or debug code written, and any already written are left uncommitted and reported.

</success_criteria>
