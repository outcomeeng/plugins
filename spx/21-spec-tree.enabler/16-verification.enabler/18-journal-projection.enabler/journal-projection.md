# Journal Projection

PROVIDES the consumer-side run-journal projection — building `spx journal` channel event inputs from a verification run's results, and computing the rollup and rendering the human-readable surface from an event prefix
SO THAT the agentic verification skills — audit and review-changes
CAN record runs and produce surfaces through one shared, type-agnostic projection rather than each re-implementing event construction, rollup, and rendering

## Assertions

### Scenarios

- Given a verification run's results carrying branch/head/base identity, when the projection builds the channel event-input sequence, then it yields a scope-entered event, one finding-reported event per finding, and a terminal `com.outcomeeng.spx.journal.run.completed` event whose data is the core journal run-state record — branch name, branch slug, target kind, head SHA, base ref, optional base SHA, config digest, participants, path-filter scope, timestamps, output paths, and terminal status — with every event a valid channel event input carrying non-empty `id`, `source`, `type`, and `time` strings and an integer `attempt` ([test](tests/test_journal_projection.scenario.l1.py))
- Given a sealed event prefix, when the projection renders the human-readable surface, then it produces a heading line from the scope-entered event, one severity-prefixed location line per finding-reported event, and an overall footer from the run-completed event ([test](tests/test_journal_projection.scenario.l1.py))

### Mappings

- The rollup projection maps an event prefix's finding severities to the run's overall: any `REJECT` finding maps to a rejected overall; otherwise any `UNKNOWN` finding maps to an unknown overall; otherwise the overall is approved ([test](tests/test_journal_projection.mapping.l1.py))

### Compliance

- ALWAYS: the projection is a pure function of its inputs — it builds channel event inputs from a run's results and renders the rollup and human-readable surface from an event prefix supplied as data, touching no journal backend, filesystem, or network — so it is verified at `l1` without a real journal and without mocking ([audit])
- NEVER: the projection reads or writes the journal channel, a filesystem path, or a network resource directly — the consuming skill drives the channel and passes event data to and from the pure projection ([audit])
- ALWAYS: the projection helper lives in one dedicated shared scripts home imported by every agentic verification consumer, not duplicated or co-located per consumer ([audit])
