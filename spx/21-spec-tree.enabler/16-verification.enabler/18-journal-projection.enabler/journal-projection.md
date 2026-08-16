# Journal Projection

PROVIDES the consumer-side run-journal projection — per-event builders a streaming verification run appends as it advances (scope-entered, scope-advanced, finding-reported, run-completed), and computing the rollup and rendering the human-readable surface from any event prefix, including a partial in-flight prefix
SO THAT the agentic verification skills — audit and review-changes
CAN stream runs and produce surfaces through one shared, type-agnostic projection rather than each re-implementing event construction, rollup, and rendering, and never batch-dumping a finished result

## Assertions

### Scenarios

- Given the data for one domain event the run has reached, when the projection builds that event, then it yields one valid channel event input carrying non-empty `id`, `source`, `type`, and `time` strings and an integer `attempt`: a scope-entered event carrying the run's branch/head/base identity, a scope-advanced event naming the unit of scope just examined, a finding-reported event carrying the raised finding, or a terminal `com.outcomeeng.spx.journal.run.completed` event whose data is the core journal run-state record — branch name, branch slug, target kind, head SHA, base ref, optional base SHA, config digest, participants, path-filter scope, timestamps, output paths, and terminal status — so the consuming skill appends each as the run advances rather than building a sequence from a finished result ([test](tests/test_journal_projection.scenario.l1.py))
- Given any event prefix — partial and in-flight, or sealed — when the projection renders the human-readable surface, then it produces a heading line from the scope-entered event, a progress line per scope-advanced event, one severity-prefixed location line per finding-reported event, and an overall footer only once a run-completed event is present, so a reader resuming from a cursor sees the run as it has advanced so far ([test](tests/test_journal_projection.scenario.l1.py))
- Given a sealed review run token, when `/inspect-review-run` renders it through its skill-local entrypoint, then it reads the review journal prefix through `spx journal render --type review --run <token>`, resolves a not-found current-scope miss through `spx journal list --type review --sealed sealed --limit 200` and re-renders with the listed branch slug when exactly one sealed run matches the token, and prints the run token, terminal status, full head/base identity, scope coverage, finding counts, and any findings from the shared projection, so the manager can inspect the raw `changes-reviewer` token without hand-reading JSON ([test](tests/test_render_review_run.scenario.l1.py))

### Mappings

- The rollup projection maps an event prefix's finding severities to the run's overall: any `REJECT` finding maps to a rejected overall; otherwise any `UNKNOWN` finding maps to an unknown overall; otherwise the overall is approved ([test](tests/test_journal_projection.mapping.l1.py))
- A finding's optional `concern` and `action` map into the finding-reported event data and the rendered line when present (the review kind sets them) and are omitted from both when absent (the audit kind leaves them unset), so the audit shape is unchanged ([test](tests/test_journal_projection.mapping.l1.py))

### Compliance

- ALWAYS: the projection is a pure function of its inputs — it builds each domain event from that event's data and renders the rollup and human-readable surface from an event prefix supplied as data, touching no journal backend, filesystem, or network — so it is verified at `l1` without a real journal and without mocking ([audit])
- NEVER: the projection exposes a builder that emits a whole run's events from a finished result — it offers one builder per domain event so the consuming skill appends each as the run advances, never a batch dump, per `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` ([audit])
- NEVER: the projection reads or writes the journal channel, a filesystem path, or a network resource directly — the consuming skill drives the channel and passes event data to and from the pure projection ([audit])
- ALWAYS: the projection helper lives in one dedicated shared scripts home imported by every agentic verification consumer, not duplicated or co-located per consumer ([audit])
