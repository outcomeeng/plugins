# Bounded Consumption Runtime

Consumption control ships a standard-library Python command and sibling modules for incremental transcript storage, accounting, evidence reports, and managed scheduling. SQLite owns durable collection progress, reconciled requests, bounded behavior excerpts, and signal identities; the command accepts validated configuration and explicit operation timestamps.

## Rationale

Persistent offsets avoid repeatedly parsing accumulated transcripts. Transactional updates keep request accounting and file progress consistent across interruption, while bounded discovery and collection let large histories resume over successive finite invocations. Pure accounting and signal functions expose independently testable behavior without starting a model or scheduler.

The runtime lives under `src/plugins/coding-agents/skills/control-token-spend/scripts/`. `usage_control.py` owns command parsing and orchestration, `usage_accounting.py` owns validated configuration, source-owned vocabulary, transcript storage and measurement, `usage_reports.py` owns bounded behavioral evidence and report rendering, and `usage_schedule.py` owns versioned installation and launchd operations. Installed assets contain this complete module set; accounting has no dependency on optional investigation commands.

## Invariants

- Original transcript files are read-only inputs. Stable native request identities reconcile streaming records within the same native session and parent relationship.
- An invocation has finite directory-entry, file, byte, row, excerpt, query, and elapsed-time limits. Exhaustion is visible and resumes through durable progress.
- A transaction advances a file offset together with the usage and behavior rows parsed before that offset. A partial final line remains pending until complete.
- One frozen measurement supplies every output format. Estimated pricing identifies its source, effective date, model and cache-duration assumptions; missing pricing remains visible.
- Installed assets are versioned independently of state. One nonblocking lock excludes overlapping collector, detector and report workers; a busy worker exits with an inspectable result.

## Verification

### Testing

- ALWAYS: configuration crosses an explicitly validated standard-library dataclass boundary; timestamps, positive monetary values, paths and optional investigation settings are checked before use ([compliance]).
- ALWAYS: SQLite collection transactions persist offsets, pending fragments and reconciled usage together, while report and status files use atomic replacement ([compliance]).
- NEVER: scheduled workers invoke a model, rebuild an optional index, mutate an original transcript, install a dependency, or wait indefinitely for an overlapping worker ([compliance]).

### Audit

- ALWAYS: external commands cross an injected Protocol-typed runner; the default runner uses argument arrays, a finite timeout, bounded captured output and checked exit status ([audit]).
- ALWAYS: filesystem collection, time and external command boundaries remain observable to independently owned harnesses, with semantic vocabulary owned by the production module that consumes it ([audit]).
- ALWAYS: test harnesses, generators and inert transcript fixtures live in the repository's declared `outcomeeng_testing/` infrastructure home; linked node tests contain typed assertions only ([audit]).
- NEVER: framework mocks replace runtime behavior or its external-command boundary; controlled runner implementations require an explicit failure-simulation or interaction-protocol exception selected through the test workflow ([audit]).
