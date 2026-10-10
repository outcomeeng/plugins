# Issues: Prowl environment

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The Prowl generator raises AssertionError for a generated value of the wrong shape

`outcomeeng_testing/generators/prowl_environment.py` raises `AssertionError` when a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the generator owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the generator becomes a dependency or execution error type the generator owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.

## The handback command passes its request through a pipe and an inline quoted argument

`_handback_command` in `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py` builds the command text `printf '%s\n' <json> | python3 prowl_environment.py run`, which an agent then runs. The payload reaches the command through a pipe and an inline quoted argument, a form the payload rule in [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) forbids and the dangerous-command guard refuses when the JSON carries code spans, quotes or shell text.

**Evidence.** The function builds the command text at line 1193 of `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py`.

**Settlement condition.** A spec assertion on this node states that the handback command passes its request through a scratch file and an input redirect, an implementation round changes `_handback_command` and its callers, and tests on this node exercise the new form.
