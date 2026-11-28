# Issues: Prowl environment

Known defects, contradictions and gaps in this node.

## The Prowl generator raises AssertionError for a generated value of the wrong shape

`outcomeeng_testing/generators/prowl_environment.py` raises `AssertionError` when a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the generator owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the generator becomes a dependency or execution error type the generator owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.

## The handback command passes its request through a pipe and an inline quoted argument

`_handback_command` in `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py` builds the command text `printf '%s\n' <json> | python3 prowl_environment.py run`, which an agent then runs. The payload reaches the command through a pipe and an inline quoted argument, a form the payload rule in [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) forbids and the dangerous-command guard refuses when the JSON carries code spans, quotes or shell text.

**Evidence.** The function builds the command text at line 1193 of `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py`.

**Settlement condition.** A spec assertion on this node states that the handback command passes its request through a scratch file and an input redirect, an implementation round changes `_handback_command` and its callers, and tests on this node exercise the new form.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_prowl_subprocess_input.property.l1.py`: write a file, start a process

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
