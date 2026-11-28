# ISSUES — position-direction

## The operator-prompt guard and the context-fill flag read pane-item fields no environment adapter produces

The operator-prompt guard reads `last_prompt_origin` and the context-fill flag reads `context_percent` from the pane items of the herdr and Prowl environment adapters. The evidence contracts of both adapters, `spx/43-coding-agents.enabler/18-herdr-environment.enabler/herdr-environment.md` and `spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`, name neither field and produce neither. Against the real adapters a pane item carries no prompt origin and no context fill, so the guard cannot fire and the flag cannot be raised.

The guard complies with its assertion as written, which binds when the adapter shows the prompt's origin. This node changes neither adapter and does not change its own spec for the gap.

**Settlement condition.** The evidence contracts of the herdr and Prowl environment nodes name `last_prompt_origin` and `context_percent` as pane-item fields and their adapters produce them, delivered by a separate Change to those two nodes.

**Evidence.** `grep -c -E "last_prompt_origin|context_percent"` over each of the two evidence contracts reports 0.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_direction.mapping.l1.py`: write a file, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
