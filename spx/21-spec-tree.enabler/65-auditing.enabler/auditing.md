# Auditing

PROVIDES generic audit orchestration that dispatches to language-specific `auditing-{lang}*` skills via template substitution
SO THAT every caller running an audit on TypeScript, Python, Rust, or any future language plugin
CAN run a deterministic six-phase audit producing a structured verdict without each language plugin maintaining its own orchestrator

## Assertions

### Scenarios

- Given a scope containing files of one or more supported languages, when `/auditing` runs, then it partitions the scope by file extension and emits one structured verdict per language partition ([review])
- Given the `auditor` agent runs on a branch where state exists from a prior run, when the audit re-runs, then prior open findings are re-checked and findings previously flipped to `RESOLVED` reopen when their root cause returns ([review])
- Given a branch name and the per-language state directory, when `branch_slug` runs, then it returns a slug usable as the state-file name, appending an 8-character SHA-256 suffix when an existing state file under the bare slug names a different branch ([test](tests/test_auditing.scenario.l1.py))
- Given a target lock-file path, when `RunLock` enters its context, then the file is created atomically via `O_CREAT | O_EXCL`; a fresh lock raises `RunLockError` and a stale lock (older than the TTL) is silently overwritten; the lock is removed on every exit path ([test](tests/test_auditing.scenario.l1.py))
- Given an on-disk state file, when `load_state` runs, then an absent file returns `None`, a parseable file returns a populated `AuditState`, and an unparseable file raises `StateFileCorruptError`; `save_state` writes atomically via temp-and-replace so a crash mid-write leaves the prior state intact ([test](tests/test_auditing.scenario.l1.py))
- Given an `AuditState` with open and resolved findings, when a regression returns at the same `file:line` as a resolved finding, then `find_resolved_by_identity` locates the prior ID and `reopen_finding` moves it back to the open section without allocating a new ID ([test](tests/test_auditing.scenario.l1.py))

### Properties

- The scope hash is deterministic and collision-resistant: the same sorted file list always produces the same scope hash, and file lists with different `(path, content)` pairs produce different scope hashes even when their naive `path\0content` concatenations would be byte-equal — closed by length-prefixed framing ([test](tests/test_auditing.property.l1.py))
- Finding IDs are monotonic across re-runs: a finding ID assigned in any run is never reassigned to a different finding in any subsequent run on the same branch ([review])

### Compliance

- ALWAYS: emit one structured verdict per language partition — multi-language scopes produce multiple verdicts, not one merged verdict ([review])
- ALWAYS: dispatch to every concern's skill in the protocol-prescribed phase order before emitting a verdict — partial dispatch produces misleading verdicts ([review])
- NEVER: continue past a missing skill in the `auditing-{lang}*` trio — halt before any phase runs so callers see the gap immediately ([review])
