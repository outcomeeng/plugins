# Script Decomposition for Reviewing Changes

## Purpose

This decision governs how the reviewing-changes lens decomposes into Python scripts under the skill's `scripts/` directory, where the consistency invariant is enforced, how the swappable prompt is loaded, and how the wrapper agent drives the chain end-to-end without holding any policy of its own.

## Context

**Business impact:** A judgment-style review lens produces a structured `review-result.json` document plus a rendered `review.md` surface. The lens has three distinct concerns that drift if they share a module: (1) the canonical schema and consistency invariant; (2) the deterministic validation arbiter the wrapper agent invokes against every result it emits; (3) the I/O orchestration that resolves the current thread, reads the optional `changes.json` override, computes a diff, and persists outputs through thread-store. Conflating them puts the schema source-of-truth next to argparse plumbing and lets the consistency invariant drift between the parser and the validator.

**Technical constraints:**

- The scripts run under `python3` stdlib only, no `outcomeeng_*` imports, per `spx/13-plugin-and-runtime-conventions.adr.md` and the Plugin Portability Constraints in `AGENTS.md`.
- Every filesystem effect routes through the `thread_store` facade, per the cross-lens contract in `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/vetting.md` and the backend-abstraction decision in `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/21-thread-store.enabler/21-backend-abstraction.adr.md`.
- The wrapper agent at `plugins/spec-tree/agents/changes-reviewer.md` holds `model: sonnet`, `tools: Bash, Read, Skill`. Agent prompt bodies do NOT receive `${CLAUDE_SKILL_DIR}` substitution per `spx/21-spec-tree.enabler/17-auditing.adr.md`; only skill prose does. The agent therefore reaches script paths only by invoking the lens skill.
- The wrapper agent must NOT hand-validate the JSON it just emitted — duplicate validation policy in agent prose drifts from the policy module, per vetting.md.
- The swappable judgment-style review prompt is a standalone markdown file at `${CLAUDE_SKILL_DIR}/references/review-prompt.md` so swapping the prompt does not require touching scripts.
- A review against a `base_ref` requires a real git diff, which the orchestrator computes once per run; the model never derives diffs from text descriptions.

## Decision

The reviewing-changes lens decomposes into one policy module plus four single-purpose CLI scripts under `plugins/spec-tree/skills/reviewing-changes/scripts/`. The policy module — `review_result.py` — declares the canonical schema (`SCHEMA_VERSION`, the `Decision`/`Severity`/`Concern` enums, the frozen `Finding` and `ReviewResult` dataclasses), the consistency invariant (`decision == "approve"` AND any `finding.severity == "must_fix"` raises `ReviewResultValidationError`), and the parser entry points (`parse_json(text)`, `to_json_dict(r)`, `from_json_dict(d)`). The CLI scripts each delegate to the policy module or to the `thread_store` facade for every effect and never re-implement schema knowledge:

- `validate_review_result.py` — the arbiter. Reads JSON on stdin or via `--file`, calls `review_result.parse_json`, exits 0 on success, non-zero with a structured stderr message on every violation surfaced by the parser (missing key, unknown enum value, consistency invariant).
- `compute_diff.py` — orchestration helper. Resolves the current thread (via `thread_store.current_slug()`, which honors the `SPX_VET_BRANCH` env override and falls back to `git symbolic-ref --short HEAD`), reads the optional `changes.json` override from the thread (via the facade), resolves `base_ref` from `SPX_VET_BASE_REF` env → `changes.json` `base_ref` field → `git symbolic-ref refs/remotes/origin/HEAD` (stripped), runs `git diff <base_ref>..HEAD` via `subprocess.run`, writes the diff to stdout. Exits non-zero with a stderr message naming every source when no `base_ref` can be resolved.
- `render_review.py` — orchestration helper. Reads `review-result.json` from the thread store, parses through `review_result.parse_json` so rendering cannot be driven by an invalid result, emits `review.md` content to stdout.
- `__init__.py` — package marker, no exports.

The wrapper agent invokes `validate_review_result.py` against every JSON document it emits before any persistence call and treats a non-zero exit as a re-emit signal. The swappable prompt template lives at `references/review-prompt.md`; the skill prose loads it via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` and inlines it into the model context. No script embeds the prompt text. The skill chains scripts via stdin/stdout pipes (per `spx/13-plugin-and-runtime-conventions.adr.md`) so the run is observable, deterministic at each step, and free of intermediate files the chain has to clean up.

## Rationale

**Why a separate policy module from CLI scripts.** The consistency invariant — `approve` + `must_fix` is invalid — is the single most important rule the lens exists to enforce. The wrapper agent cannot self-approve into an inconsistent state because `parse_json` raises before the validator exits 0. A rule that lived in the CLI rather than the parser would let any caller that bypasses the CLI (a downstream skill, a Python consumer) accept the inconsistent shape silently. Placing the invariant in the parser makes the rule total over every entry path; placing the CLI on top of the parser makes the rule visible to the wrapper agent as exit code.

**Why dataclasses + enums over a JSON Schema document.** The marketplace has a working precedent at `plugins/spec-tree/skills/auditing/scripts/verdict.py` — stdlib `dataclasses` + `enum.StrEnum` + a `parse_json` entry point. It validates against the same constraints (required keys, enum membership, consistency invariants) without depending on `jsonschema` or any third-party package. The lens reuses the pattern. JSON Schema is not authored here because the dataclass module is the canonical schema; a second representation invites drift.

**Why frozen dataclasses.** The `ReviewResult` and `Finding` instances cross the boundary between the parser (which produces them) and the validator (which only re-runs the consistency invariant). Frozen dataclasses guarantee that any mutation between parse and validate is a programming error caught at instantiation rather than a silent state-change. The same applies to `to_json_dict` / `from_json_dict` round-trip property tests: instances are values, not records.

**Why `compute_diff` auto-derives `base_ref` rather than taking a `--base-ref` flag.** A flag passed by the wrapper agent would be an extra piece of state the agent has to compute, hand to the chain, and remember — and three values would drift across runs (the value the agent computed, the value the test harness fixtures, the value the operator put in `changes.json`). One precedence chain governed by the script keeps the lens identical across surfaces: local iteration with no setup, CI with environment overrides, a tracked review with an explicit `changes.json` override file. The chain is `SPX_VET_BASE_REF` env → optional `changes.json` `base_ref` field → strict `git symbolic-ref refs/remotes/origin/HEAD` (no fallback to a literal "main") → abort with all three sources named.

**Why the agent never names the thread slug.** Slug is the filesystem backend's addressing scheme; on a future `gh_pr` backend the addressing is the PR number. An agent that names slugs in its prose can't be backend-agnostic. `thread_store.current_slug()` derives the slug internally on the local backend (from `SPX_VET_BRANCH` env or `git symbolic-ref --short HEAD`); every CRUD CLI makes `--slug` optional and falls back to that derivation. The agent invokes the chain with no addressing input.

**Why `changes.json` is platform-neutral naming.** "PR" is GitHub slang; GitLab calls the same concept a merge request, Gerrit a change-list. The override file holds the configuration the lens consumes (`base_ref`, optionally more in future); naming it after one platform's term would lock the file to that platform's vocabulary. `changes.json` parallels the skill name `reviewing-changes` and stays valid across surfaces. The field is `base_ref` (git-native, the spec already declares it) rather than `baseRefName` (the GitHub API's literal field name).

**Why `render_review` parses before rendering.** A `review.md` produced from a `review-result.json` that did not pass the arbiter is by definition surfacing an inconsistent verdict. Re-parsing through `review_result.parse_json` makes the renderer total over only the documents the arbiter accepts; an invalid input causes a non-zero exit before any markdown is emitted.

**Why piping over intermediate files.** The plugin runtime ADR mandates stdin/stdout pipes over intermediate files when fanout does not require a directory. A four-script chain has one producer and one consumer per stage; intermediate files would add scratch-cleanup surface and four paths to disagree on. The lens follows the precedent set by `verdict.py` → `emit_verdict.py` and the rest of the verdict toolchain.

**Why the prompt is a separate file.** The cross-lens contract names the swappable prompt as the variable the lens user adjusts. Embedding the prompt in `SKILL.md` couples prompt revision to skill revision; embedding it in a script makes every prompt edit a code change. A standalone `references/review-prompt.md` makes the prompt the data the skill loads.

**Alternatives rejected:**

- **One monolithic script that does everything.** The wrapper agent would have no way to validate the JSON it emits without also re-running the diff/render path; the consistency invariant would conflate with I/O and become opaque to a reader.
- **Validator and parser as separate code paths.** Tests would have to assert the two paths reject the same documents in lockstep; the invariant would inevitably drift.
- **Embed the review prompt in SKILL.md.** Every prompt iteration would touch the skill; the spec explicitly forbids it (`NEVER: the review prompt is embedded inside SKILL.md or any script`).
- **Generate `review.md` inside the wrapper agent prose.** The agent has no path-substitution surface, so it could not reach scripts; it would also re-implement the rendering rules and drift from the canonical schema.

## Trade-offs accepted

| Trade-off                                                                                                                 | Mitigation / reasoning                                                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| One policy module governs schema, enums, parser, and consistency invariant — a single file holds several responsibilities | The responsibilities are co-variant: any change to the enum set or the invariant must update the parser. Splitting them into separate modules guarantees drift between artifacts that always change together.                                                     |
| Four CLI scripts instead of one composite                                                                                 | Each script has one entry point and one exit code, which the wrapper agent can reason about without parsing prose. The pipe chain composes the four into one orchestration without inventing an intermediate file.                                                |
| The wrapper agent invokes the arbiter as an external process for every emit                                               | The exit-code surface is the contract the agent reads; invoking the arbiter as a process is the only way `disable-model-invocation`-free agent prose can rely on deterministic validation.                                                                        |
| `compute_diff.py` shells out to `git`                                                                                     | `git` is part of the consumer's standard development environment; the marketplace already relies on `subprocess.run(["git", ...])` in `audit_orchestrator.py`. The dependency is the same.                                                                        |
| Schema versioning lives in a module-level constant rather than in the JSON document                                       | The `SCHEMA_VERSION` constant carries the schema generation; a generation bump adds a `schema_version` field to the wire format and a migration path in the parser. The constant marks the generation without committing the wire shape until a bump requires it. |

## Compliance

### Recognized by

A conformant reviewing-changes lens ships `review_result.py`, `validate_review_result.py`, `compute_diff.py`, `render_review.py`, and `__init__.py` under `plugins/spec-tree/skills/reviewing-changes/scripts/`. The policy module declares `SCHEMA_VERSION`, the `Decision`/`Severity`/`Concern` enums, the frozen `Finding` and `ReviewResult` dataclasses, the `ReviewResultValidationError` exception, and the `parse_json` / `to_json_dict` / `from_json_dict` entry points. The arbiter CLI invokes `review_result.parse_json` and surfaces its exceptions as non-zero exits. Every filesystem effect in any script routes through the `thread_store` facade. The skill prose loads the swappable prompt via `${CLAUDE_SKILL_DIR}/references/review-prompt.md`. The wrapper agent reaches the scripts only by invoking the lens skill.

### MUST

- The policy module `plugins/spec-tree/skills/reviewing-changes/scripts/review_result.py` declares `SCHEMA_VERSION`, frozen `Finding` and `ReviewResult` dataclasses, the `Decision`/`Severity`/`Concern` enums, the `ReviewResultValidationError` exception, and the `parse_json` / `to_json_dict` / `from_json_dict` entry points — the canonical schema lives in one Python module ([test](tests/test_review_result.scenario.l1.py))
- The consistency invariant (`decision == "approve"` AND any `finding.severity == "must_fix"`) is enforced inside `review_result.parse_json` — every entry path through the parser raises `ReviewResultValidationError` on violation, including direct Python callers that bypass the arbiter CLI ([test](tests/test_review_result.property.l1.py))
- `validate_review_result.py` invokes `review_result.parse_json` for validation — the arbiter does not re-implement schema knowledge ([test](tests/test_validate_review_result.scenario.l1.py))
- `compute_diff.py` resolves the current thread via `thread_store.current_slug()`, reads the optional `changes.json` override through the `thread_store` facade (treating `NotFound` as "no override"), resolves `base_ref` from the precedence chain (`SPX_VET_BASE_REF` env → `changes.json` `base_ref` field → `git symbolic-ref refs/remotes/origin/HEAD` stripped), and runs `git diff <base_ref>..HEAD` — every filesystem effect routes through `thread_store`, the only `subprocess` invocations are the documented git commands, and no `base_ref` source means a non-zero exit with all three sources named in stderr ([test](tests/test_skill_orchestration.scenario.l2.py))
- `render_review.py` parses `review-result.json` through `review_result.parse_json` before emitting markdown — an invalid `review-result.json` causes a non-zero exit before any rendered surface is produced ([test](tests/test_skill_orchestration.scenario.l2.py))
- The swappable judgment-style review prompt template at `plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md` is loaded by skill prose via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` — the prompt is data the skill loads, never code ([test](tests/test_reviewing_changes.compliance.l1.py))
- The wrapper agent at `plugins/spec-tree/agents/changes-reviewer.md` reaches the scripts only by invoking the lens skill — agent prose contains no `${CLAUDE_SKILL_DIR}`, no `${CLAUDE_PLUGIN_ROOT}`, and no hard-coded path into `scripts/`, per `spx/21-spec-tree.enabler/17-auditing.adr.md` ([test](tests/test_reviewing_changes.compliance.l1.py))
- Frozen dataclasses are used for `Finding` and `ReviewResult` — instances are values that cannot be mutated between parse and validate ([test](tests/test_review_result.scenario.l1.py))

### NEVER

- The consistency invariant is enforced only in `validate_review_result.py` and not in `review_result.parse_json` — a Python caller that bypasses the CLI would accept an inconsistent result silently ([test](tests/test_review_result.property.l1.py))
- A CLI script under `plugins/spec-tree/skills/reviewing-changes/scripts/` calls `open()`, `pathlib.Path.write_*`, `os.remove`, or any direct filesystem primitive against the thread-store backend's storage paths — every read and write routes through `thread_store` ([test](tests/test_reviewing_changes.compliance.l1.py))
- A second representation of the schema is authored (JSON Schema document, OpenAPI fragment, second dataclass set) — the `review_result.py` module is the canonical schema; alternate representations invite drift ([test](tests/test_reviewing_changes.compliance.l1.py))
- The judgment-style review prompt is embedded inside `SKILL.md` or any `*.py` file — the prompt is one standalone markdown file at the declared reference path ([test](tests/test_reviewing_changes.compliance.l1.py))
- A script under `plugins/spec-tree/skills/reviewing-changes/scripts/` imports a third-party package, depends on `uv` at runtime, or imports any `outcomeeng_*` module — stdlib only ([test](tests/test_reviewing_changes.compliance.l1.py))
- The wrapper agent hand-validates JSON it just emitted by re-checking enum membership, required keys, or the consistency invariant in agent prose — the arbiter CLI is the single source of validity, per the cross-lens contract ([review])
- An intermediate file is used between two scripts in the chain when stdin/stdout suffices — per `spx/13-plugin-and-runtime-conventions.adr.md`, pipes over files when fanout does not demand a directory ([review])
