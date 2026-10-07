# Issues: Prowl environment

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The Prowl generator raises AssertionError for a generated value of the wrong shape

`outcomeeng_testing/generators/prowl_environment.py` raises `AssertionError` when a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the generator owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the generator becomes a dependency or execution error type the generator owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.

## `/operate-prowl` claims a return command the script does not build, and states its outputs and validation errors loosely

**Evidence.** `instructions:skill-auditor` run `2026-10-07_07-54-09-817-7aae52d28339` on `src/plugins/coding-agents/skills/operate-prowl` raised two `blocking` and three `debt` findings; the `caller-independence` finding at `SKILL.md:126` is repaired in the changeset and four remain open:

- `internal-consistency` at `SKILL.md:161-163` (`<environment_traps>`): the text says the return address carries the command form that resolves when `PATH` does not resolve Prowl, while the script builds every argument vector from the bare `prowl` name and maps a missing executable to `prowl-unavailable`.
- `objective-shape` at `SKILL.md:10`: the objective names an operation result or a terminal handback and omits the `resolve-target` result and the `plan-handback` block.
- `script-testing-rule` at `SKILL.md:183-191`: the recorded exercised inputs hold no error case.
- `validation-rule` at `scripts/prowl_environment.py:644-651`, `1224-1231`, `1346-1353` and `1451-1458`: validation errors compute the unexpected and missing fields and discard them, or reject a shape without naming the valid shapes.

**Standing.** The findings lie on text the changeset leaves untouched: the diff of the skill against `origin/main` holds the hunks at `SKILL.md:126` and the closing failure-mode paragraph at `SKILL.md:211`, and no hunk in `scripts/prowl_environment.py`.

**Impact.** A session loading the skill reads a return-address guarantee the script does not honor, and a rejected request names no field to fix.

**Settlement condition.** `<environment_traps>` states the behavior the script has, the objective covers every output the skill returns, the testing record holds an invalid-input, a missing-Prowl and a mutation-unauthorized result, the validation errors name the unexpected and missing fields, and a typed skill audit raises none of the four findings.
