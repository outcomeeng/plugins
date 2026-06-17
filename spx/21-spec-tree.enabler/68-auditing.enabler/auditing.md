# Auditing

PROVIDES generic audit orchestration that dispatches to language-specific `audit-{lang}*` skills via template substitution, plus one-off agent wrappers that render and combine its verdict
SO THAT every caller running an audit on TypeScript, Python, Rust, or any future language plugin — locally or in CI
CAN run a deterministic six-phase audit producing a structured JSON verdict, rendered in the surface form the caller asks for, without each language plugin maintaining its own orchestrator

## Assertions

### Scenarios

- Given a scope containing files of one or more supported languages, when `/audit` runs, then it partitions the scope by file extension, dispatches one `audit-{lang}*` skill per partition, collects each dispatched verdict, and emits one wrapper verdict whose `children` array holds the dispatched verdicts and whose `overall` is derived via `aggregate_verdicts.py` ([review])
- Given a repo with `refs/remotes/origin/HEAD` configured, when `detect_base_ref` runs, then it returns the bare base-branch name with the `refs/remotes/origin/` prefix stripped; when the symbolic ref is absent, it returns `main` ([test](tests/test_auditing.scenario.l1.py))
- Given a feature branch with commits ahead of `origin/<base>`, when `branch_scope` runs, then it returns the files the branch added — three-dot semantics, so commits that landed on the base branch after the branch was cut are excluded — filtered by the supplied pathspec patterns ([test](tests/test_auditing.scenario.l1.py))
- Given a git diff range and optional pathspec patterns, when `expand_diff_range` runs, then it returns the matching file paths in git's order, with an empty list for no matches rather than an error ([test](tests/test_auditing.scenario.l1.py))

### Properties

- The scope hash is deterministic and collision-resistant: the same sorted file list always produces the same scope hash, and file lists with different `(path, content)` pairs produce different scope hashes even when their naive `path\0content` concatenations would be byte-equal — closed by length-prefixed framing ([test](tests/test_auditing.property.l1.py))

### Compliance

- ALWAYS: emit exactly one wrapper verdict per orchestrator run — children of the wrapper carry per-partition (per-language) verdicts; the wrapper's overall is derived via `aggregate_verdicts.py` per the canonical rollup rule in `verdict.py` ([review])
- ALWAYS: dispatch to every concern's skill in the protocol-prescribed phase order before emitting a verdict — partial dispatch produces misleading verdicts ([review])
- ALWAYS: emit every audit verdict through `emit_verdict.py` with the format axis forwarded from the calling workflow — orchestrator and dispatched skills produce JSON, never hand-formatted markdown ([review])
- ALWAYS: enumerate the audit scope and compute the scope hash through `audit_orchestrator.py`'s git/scope helpers — `/audit` never embeds git plumbing or scope hashing inline in skill prose ([review])
- ALWAYS: the `auditor` agent invokes the `/audit` skill on a scope and forwards the requested format (`--json`, `--markdown`, or `--markdown+json`) to `emit_verdict.py` — it owns no audit policy of its own and invokes nothing the `/audit` skill does not already resolve ([review])
- ALWAYS: `/audit` recognises `MODE: prior-verdict-read` and `MODE: with-prior-verdict` invocation lines and selects the matching PR-thread sub-protocol; an invocation containing neither a recognised `MODE:` line nor a standard six-phase audit context, OR containing both `MODE:` lines, halts with an error rather than defaulting silently — drift in calling-agent wording surfaces on the next CI run rather than as quiet behavioural divergence ([review])
- ALWAYS: in `MODE: with-prior-verdict`, `/audit` drives `audit_orchestrator.py verdict-diff` to compute `resolved` and `reopened` by content identity `(file, line, rule, message)` — `id` and `severity` are excluded so a regenerated finding with a fresh ID or upgraded severity matches its prior counterpart ([test](tests/test_auditing.scenario.l1.py))
- NEVER: continue past a missing skill in the `audit-{lang}*` trio — halt before any phase runs so callers see the gap immediately ([review])
- NEVER: re-implement verdict shape or rollup logic in the orchestrator — the canonical schema lives in `verdict.py` and the rollup lives in `verdict.roll_up` ([review])
- NEVER: write to `.spx/audits/` in either PR-thread mode — the durable cross-CI-run state surface for these modes is the PR comment thread, not the worktree-local state file used by stateful-orchestration mode ([review])
