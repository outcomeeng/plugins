---
description: Stop ad hoc work and follow the spec-tree methodology
---

<objective>
You are doing ad hoc work — writing code without specs, debugging without tests, or skipping the methodology. Stop. This command exists because what you are doing right now will be thrown away.
</objective>

<diagnosis>
**What you did wrong:**

You skipped the spec-tree TDD flow. One or more of these happened:

- You wrote implementation code before writing tests
- You wrote a throwaway script to "see what's happening" instead of a test
- You started debugging without checking the spec for the expected behavior
- You made changes without loading the work item context first
- You produced an ADR or tests without going through the review gate

**Why it matters:**

The ad hoc code you just wrote takes the same effort as a proper test, but the test stays and the script gets deleted. The debug session you just ran answered one question; a test answers that question every time CI runs. The implementation you wrote without specs will be reworked when the actual requirements surface.
</diagnosis>

<process>

## Step 1: Stop what you are doing

Do not finish the current ad hoc work. Do not "just quickly" wrap it up. Stop.

## Step 2: Assess the damage

Look at what you have produced so far:

- If you wrote ad hoc scripts or debug code: delete them
- If you wrote implementation without tests: keep the code but do not commit it
- If you wrote tests without loading context: the tests may be wrong — verify after Step 3

## Step 3: Start the proper flow

Invoke the applying skill NOW:

```text
Skill tool → { "skill": "spec-tree:applying" }
```

This runs the full 8-step TDD flow: methodology → context → architect → audit → test → audit → implement → audit. Follow it from Step 1.

</process>

<success_criteria>

- Ad hoc work stopped
- Applying skill invoked and proper flow started from Step 1
- No throwaway scripts or debug code committed

</success_criteria>
