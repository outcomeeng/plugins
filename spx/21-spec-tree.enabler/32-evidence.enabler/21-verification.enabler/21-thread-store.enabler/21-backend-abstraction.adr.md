# Backend Abstraction

## Purpose

This decision governs how thread-store persists branch-scoped verification records across multiple operating modes — the developer's worktree, CI runners, hosted services — without coupling the consuming skill or its wrapper agent to the chosen storage surface.

## Context

**Business impact:** Verification skills produce records (machine-readable JSON, human-readable markdown) that outlive the agent invocation. The developer running a verification skill locally wants those records under their worktree, gitignored. The same verification skill, run from CI, wants the records under a runner-cacheable path that survives across job invocations. A hosted-service deployment wants them in a remote object store. A persistence layer that fixes one storage surface forces N parallel verification skill implementations or N copies of every verification skill's I/O logic.

**Technical constraints:**

- The marketplace ships every persistence-touching script under a plugin skill's `scripts/` directory and runs them against `python3` stdlib only, per `spx/13-plugin-and-runtime-conventions.adr.md`. Test harnesses for these scripts live at `outcomeeng_testing/harnesses/` per `spx/15-test-infrastructure.pdr.md` — marketplace-internal infrastructure for in-repo test execution, distinct from the portable production scripts the harnesses exercise.
- Branch-slug derivation lives in `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` and is importable. Duplicating the rule lets it drift across audit and review surfaces.
- A branch slug must be safe to use as a single filesystem path segment under any backend: no `/`, no `.` or `..` whole-segment values, and a bounded length so long branch names cannot exhaust filesystem path-length limits (the POSIX minimum `NAME_MAX` is 255 bytes).
- The canonical slug function takes a branch name and an optional state-directory path; the state-directory argument participates in collision disambiguation when an existing state file records a different branch under the same base slug. Verification skill code that does not maintain audit-state files passes the argument as `None` and gets the same length-bounded, path-safe slug as the audit-state code path.
- Verification skills are language-agnostic at the prose level; the wrapper agents invoke CLIs and never branch on backend identity.
- The default concrete backend is the developer's filesystem under `.spx/reviews/<branch-slug>/` (the `.spx/` root is gitignored).
- Backend switching is a runtime concern (different invocation environments), not an authoring concern (the spec tree records one persistence model, not three).

## Decision

Thread-store exposes a single abstract `Backend` protocol that every concrete backend implements. Concrete backends live as separate modules under `plugins/spec-tree/skills/thread-store/scripts/`; the `thread_store` facade selects which backend to use at runtime via the `SPX_VERIFY_BACKEND` environment variable (default `local`, which selects the filesystem backend rooted at `.spx/reviews/<branch-slug>/`). The canonical branch-slug function lives in `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py`, takes `(branch_name, state_dir=None)`, replaces every `/` in the input with `__`, replaces a whole-segment `.` with the literal token `__dot__` and a whole-segment `..` with the literal token `__dotdot__`, bounds the resulting slug at `BRANCH_SLUG_MAX_LENGTH = 64` characters by truncating and appending `--<sha8>` where `sha8` is the first eight hex digits of `SHA-256(branch_name)`, and applies the same `--<sha8>` suffix when a state file at `state_dir/<base_slug>.md` records a different branch in its frontmatter. The thread-store helper at `plugins/spec-tree/skills/thread-store/scripts/branch_slug.py` re-exports this symbol via `importlib` so audit and review surfaces share one slug rule. CRUD CLIs (write, read, delete, list) consume the facade and are the only entry points wrapper agents invoke.

## Rationale

The abstract-protocol-plus-env-selection shape costs almost nothing when one backend is registered and accommodates additional backends through one dispatch point. The audit pipeline carries the same marketplace pattern: `audit_orchestrator.py` exposes one helper module, multiple CLI subcommands, and dispatch by skill argument rather than by hardcoded path. Thread-store applies the same factoring to a different concern.

Slug-rule re-export over duplication matters because slug collisions and slug shape are observable in the user's working directory: if review state and audit state for the same branch ever resolved to different slugs, the developer would see two unrelated directories where one branch's record lives in each. Sharing one function makes that misalignment impossible.

The bounded-length rule (`BRANCH_SLUG_MAX_LENGTH = 64`) protects every backend from filesystem path-length limits. POSIX guarantees `NAME_MAX` of 255 bytes for a single path component, but real-world filesystems impose tighter limits in deep trees (Windows `MAX_PATH = 260` bytes for an entire path, ecryptfs `NAME_MAX = 143` bytes) and the slug nests inside `.spx/reviews/<slug>/<record-name>` already. A 64-character bound leaves abundant headroom for the path prefix, the record filename, and any backend-specific naming overhead. The truncation-plus-digest construction preserves injectivity for any pair of branch names whose 64-character prefixes differ or whose `SHA-256` digests differ — the latter is the disambiguator for branch names that share a long common prefix.

Sharing the same `--<sha8>` mechanism for length-truncation and state-collision keeps the slug grammar uniform — every disambiguation suffix is the same shape, and any path the developer sees has at most one trailing `--<sha8>` regardless of which condition triggered it. The wrapper character substitution for `.` / `..` whole-segment values keeps the canonical function total: the upstream `audit_orchestrator` callers always pass branch names that Git accepts (which already forbid `.` / `..` segments), so the substitution is dormant for them; the thread-store callers may pass arbitrary strings (the verification skill may invoke against a non-branch context such as a synthetic identifier), so the substitution is the safety net.

The filesystem backend serves as the default and the harness reference implementation because it requires no auth, no network, and no state-machine coordination; the full CRUD contract is exercisable from a `tmp_path` pytest fixture, and other backends validate their conformance against it.

Env-var-driven selection over skill-argument-driven keeps the verification skill unaware of the backend. A verification skill that knows it's running against filesystem-vs-cache would either branch in prose (drifts across verification skills) or thread a `--backend` flag through every CLI call (every verification skill reimplements the plumbing). Env var resolved once inside `thread_store.get_backend()` keeps the verification skill definition single-shape.

Alternatives rejected:

- **Hardcode filesystem with no abstraction.** Adding a second backend then requires re-authoring every verification skill's persistence calls or introducing a parallel surface. The cost of one Protocol class plus one env-var lookup stays much smaller than the cost of that re-authoring across every verification skill.
- **Each verification skill owns its persistence.** Backend swap becomes N-place change. Slug-rule drift becomes inevitable. The shared verification contract in `spx/21-spec-tree.enabler/32-evidence.enabler/21-verification.enabler/verification.md` exists specifically to prevent this.
- **Slug derivation re-implemented inside thread-store.** Two implementations of one rule guarantee drift. Re-exporting the canonical function from `audit_orchestrator.py` is the only way to keep audit and review surfaces in sync without a marketplace-wide refactor.
- **Skill-argument backend selection.** Forces every wrapper agent to know which backend is configured. Env var lookup is a single point that the agent never references.

## Trade-offs accepted

| Trade-off                                                                                          | Mitigation / reasoning                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| One indirection layer between every verification skill I/O call and storage                        | The interface is small (write, read, delete, list, thread_path); the facade is a single function call; performance cost is negligible relative to the LLM-emit step every verification skill already performs |
| Verification skills cannot observe which backend is in play                                        | Verification skills have no legitimate reason to know; any genuinely backend-specific operation lives behind a CRUD method whose semantics every backend honors uniformly                                     |
| Adding a backend requires both an implementation module and a registration entry in the facade     | The registration is a small dispatch dict; adding a backend is one PR that touches one file, far below the cost of N-place changes the absence of abstraction would imply                                     |
| Env-var selection is invisible to a verification skill reader inspecting just the skill prose      | The wrapper agent's prose names the env var and the default; the verification skill itself doesn't reference backend selection at all, which is the desired separation of concerns                            |
| The 64-character slug bound truncates long branch names                                            | The `--<sha8>` digest suffix preserves injectivity; readability cost is mitigated by the disambiguator appearing only when truncation or state-file collision actually triggers it                            |
| The canonical slug function carries an optional `state_dir` argument that some callers leave unset | Callers that pass an explicit state directory participate in state-collision disambiguation; callers that pass `None` get the same length-bounded, path-safe slug without consulting any filesystem state     |

## Compliance

### Recognized by

A conformant backend module implements every method declared by the `Backend` protocol in `plugins/spec-tree/skills/thread-store/scripts/backend.py`. The `thread_store` facade selects backends via `SPX_VERIFY_BACKEND` and defaults to `local`. Every CRUD CLI under `plugins/spec-tree/skills/thread-store/scripts/` invokes the facade and never touches the filesystem directly. The slug helper at `plugins/spec-tree/skills/thread-store/scripts/branch_slug.py` re-exports the function from `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` via `importlib` without redefinition.

### MUST

- A backend module implements every method of the `Backend` protocol (`thread_path`, `write`, `read`, `delete`, `list`) — partial implementations are detected at facade-registration time and refused ([test](tests/test_backend_protocol.compliance.l1.py))
- Backend selection runs through `SPX_VERIFY_BACKEND` resolved inside `thread_store.get_backend()` — neither a verification skill, a wrapper agent, nor any CLI argument selects the backend ([review])
- The branch-slug function used by every backend is the symbol re-exported by `plugins/spec-tree/skills/thread-store/scripts/branch_slug.py` from `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` — slug derivation has one canonical implementation ([test](tests/test_thread_store.compliance.l1.py))
- The canonical `branch_slug` function accepts `(branch_name, state_dir=None)`, returns a string of at most `BRANCH_SLUG_MAX_LENGTH = 64` characters, contains no `/` and no `.` or `..` whole-segment values, and is deterministic for a given `(branch_name, state_dir)` pair — every caller relies on this contract regardless of whether it maintains audit-state files ([test](tests/test_slug.property.l1.py))
- Every script under `plugins/spec-tree/skills/thread-store/scripts/` runs against `python3` only, depends only on the standard library, and imports no `outcomeeng_*` module — per the Plugin Portability Constraints in `AGENTS.md` ([test](tests/test_plugin_portability.compliance.l1.py))
- The facade's `write` operation is atomic — a crash mid-write leaves the prior content of the target intact ([test](tests/test_thread_store.compliance.l1.py))
- The filesystem backend confines all writes to its configured root (`.spx/reviews/<branch-slug>/` by default) — leaking outside that root breaks the gitignore contract and surprises the developer ([test](tests/test_thread_store.compliance.l1.py))

### NEVER

- A verification skill or wrapper agent imports a backend module directly (`fs_backend` or any other concrete backend module) — every read and write routes through the `thread_store` facade ([test](tests/test_plugin_portability.compliance.l1.py))
- A CLI under `plugins/spec-tree/skills/thread-store/scripts/` calls `open()`, `pathlib.Path.write_*`, `os.remove`, or any other direct filesystem primitive — every CLI invokes the facade, which dispatches to the backend ([test](tests/test_cli.compliance.l1.py))
- A backend module redefines the branch-slug rule — the rule lives in one function and is re-exported, never re-implemented ([test](tests/test_plugin_portability.compliance.l1.py))
- The canonical `branch_slug` function returns a string longer than `BRANCH_SLUG_MAX_LENGTH = 64` characters, a string containing `/`, or a string whose segments resolve to `.` or `..` — these forms break filesystem-path safety on at least one supported backend ([test](tests/test_slug.property.l1.py))
- A backend write succeeds without atomic semantics — partial writes that survive a crash are forbidden, because every consumer expects the post-write read to return either the prior content or the new content, never a torn record ([test](tests/test_thread_store.compliance.l1.py))
