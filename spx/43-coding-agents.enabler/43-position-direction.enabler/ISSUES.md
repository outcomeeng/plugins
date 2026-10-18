# ISSUES — position-direction

## The operator-prompt guard and the context-fill flag read pane-item fields no environment adapter produces

The operator-prompt guard reads `last_prompt_origin` and the context-fill flag reads `context_percent` from the pane items of the herdr and Prowl environment adapters. The evidence contracts of both adapters, `spx/43-coding-agents.enabler/18-herdr-environment.enabler/herdr-environment.md` and `spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`, name neither field and produce neither. Against the real adapters a pane item carries no prompt origin and no context fill, so the guard cannot fire and the flag cannot be raised.

The guard complies with its assertion as written, which binds when the adapter shows the prompt's origin. This node changes neither adapter and does not change its own spec for the gap.

**Settlement condition.** The evidence contracts of the herdr and Prowl environment nodes name `last_prompt_origin` and `context_percent` as pane-item fields and their adapters produce them, delivered by a separate Change to those two nodes.

**Evidence.** `grep -c -E "last_prompt_origin|context_percent"` over each of the two evidence contracts reports 0.

## The Proposed-Change ranking assertion has no subject in the director skill

The assertion that the Director ranks a Change the Product's Maintainer confirmed at Proposed for its Frame ahead of the Product's other Proposed Changes (ALWAYS, `[audit]`, line 29 of `spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md`) names behavior the director skill and its scripts do not carry. Neither the director skill `SKILL.md` nor its scripts name a Proposed-Change ranking, so an audit of the assertion finds no subject to judge. The finding is rule `subject-unlocated`, severity debt, filed by run 2026-10-18_05-07-31-681-a6aa1f7ee3a9 on the assertion at ordinal 9.

**Settlement condition.** The director skill or its scripts state the ranking of a Maintainer-confirmed Proposed Change for its Frame ahead of other Proposed Changes, so the assertion has a located subject; or the assertion is removed from the spec through a Change that amends the node.

**Evidence.** Base ref 3b24e1c7f19b9c2898a400e148f3e096714253d8. `git diff --unified=0 3b24e1c7f19b9c2898a400e148f3e096714253d8 -- spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md` leaves the assertion at line 29 untouched in the audited tree, and the director skill's diff does not touch such text.

## The refining-position question assertion has no subject in the director skill

The assertion that the Director answers each question a refining position sends and takes it to the operator only when the answer adds intent or settles an open product question (ALWAYS, `[audit]`, line 30 of `spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md`) names behavior the director skill does not carry. The director skill names no handling of refining-position questions, so an audit of the assertion finds no subject to judge. The finding is rule `subject-unlocated`, severity debt, filed by run 2026-10-18_05-07-31-681-a6aa1f7ee3a9 on the assertion at ordinal 10.

**Settlement condition.** The director skill states how the Director answers a refining position's question and when it takes the question to the operator, so the assertion has a located subject; or the assertion is removed from the spec through a Change that amends the node.

**Evidence.** Base ref 3b24e1c7f19b9c2898a400e148f3e096714253d8. `git diff --unified=0 3b24e1c7f19b9c2898a400e148f3e096714253d8 -- spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md` leaves the assertion at line 30 untouched in the audited tree, and the director skill names no handling of refining-position questions.
