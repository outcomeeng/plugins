# ISSUES — position-direction

## The operator-prompt guard and the context-fill flag read pane-item fields no environment adapter produces

The operator-prompt guard reads `last_prompt_origin` and the context-fill flag reads `context_percent` from the pane items of the herdr and Prowl environment adapters. The evidence contracts of both adapters, `spx/43-coding-agents.enabler/18-herdr-environment.enabler/herdr-environment.md` and `spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`, name neither field and produce neither. Against the real adapters a pane item carries no prompt origin and no context fill, so the guard cannot fire and the flag cannot be raised.

The guard complies with its assertion as written, which binds when the adapter shows the prompt's origin. This node changes neither adapter and does not change its own spec for the gap.

**Settlement condition.** The evidence contracts of the herdr and Prowl environment nodes name `last_prompt_origin` and `context_percent` as pane-item fields and their adapters produce them, delivered by a separate Change to those two nodes.

**Evidence.** `grep -c -E "last_prompt_origin|context_percent"` over each of the two evidence contracts reports 0.

## assertion:ordinal-8:spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md:director-behavior-unstated

Rule `director-behavior-unstated`, severity `debt`, run `2026-10-25_06-58-42-164-64cd6dcac8f7`.

The eighth assertion of `spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md` binds the Director to rank a Change the Product's Maintainer confirmed at Proposed for its Frame ahead of the Product's other Proposed Changes. `/direct-positions`, in its `SKILL.md` and its scripts, states no ranking behavior, and no other skill or spec states it for the Director.

**Impact.** The assertion declares a Director behavior that no instruction the Director loads carries, so a Director following `/direct-positions` has no source for the ranking and the assertion's audit has no stated behavior to judge.

**Settlement condition.** A skill or spec the Director loads states the ranking of a Maintainer-confirmed Proposed Change ahead of the Product's other Proposed Changes, or the assertion no longer declares it.

**Evidence.** `git diff --unified=0 7ec19d3fa3507eed2984643366938176b0535c12 -- spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md` adds only the relaunch-write-paths assertion and leaves this assertion's lines untouched in the audited tree, so the finding lies outside the change (`baseRefEvidence` 7ec19d3fa3507eed2984643366938176b0535c12). A search of `src/plugins/coding-agents/skills/direct-positions/SKILL.md` and its `scripts/` for the terms `confirmed`, `Proposed`, and `Maintainer` finds no ranking statement; its matches concern pane guards and controller forwarding.

## assertion:ordinal-9:spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md:director-behavior-unstated

Rule `director-behavior-unstated`, severity `debt`, run `2026-10-25_06-58-42-164-64cd6dcac8f7`.

The ninth assertion of `spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md` binds the Director to answer each question a refining position sends because no assumption can defend an answer, and to take it to the operator only when the answer adds intent or settles an open product question. `/direct-positions`, in its `SKILL.md` and its scripts, states no routing of a refining position's question, and no other skill or spec states it for the Director. The controller's forwarding of a stalled position's question to the advisor concerns a stalled pane, not a refining position's question.

**Impact.** The assertion declares a Director behavior that no instruction the Director loads carries, so a Director following `/direct-positions` has no source for the answer-or-escalate rule and the assertion's audit has no stated behavior to judge.

**Settlement condition.** A skill or spec the Director loads states the Director's answering of a refining position's question and the condition for taking it to the operator, or the assertion no longer declares it.

**Evidence.** `git diff --unified=0 7ec19d3fa3507eed2984643366938176b0535c12 -- spx/43-coding-agents.enabler/43-position-direction.enabler/position-direction.md` leaves this assertion's lines untouched in the audited tree, so the finding lies outside the change (`baseRefEvidence` 7ec19d3fa3507eed2984643366938176b0535c12). A search of `src/plugins/coding-agents/skills/direct-positions/SKILL.md` and its `scripts/` for the terms `refining` and `question` finds only pane question-screen guards and the controller's advisor forwarding.
