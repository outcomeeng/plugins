# Bump Orchestration Shape

## Purpose

This decision governs the module shape, dependency boundaries, and error model of `outcomeeng.distribution.bump`: how change detection, manifest reading, and manifest writing are factored into testable units; what semver representation the module owns; and how the "branch already carries a bump" condition is recognized.

## Context

**Business impact:** The bump module is the first plugin-distribution commit's mechanical actor — it sets the version that lands on `main` per `spx/local/committing-changes.md`. A bumper that re-bumps during PR review, that misses a manifest a plugin owns, or that writes when no plugin distribution path changed, silently corrupts the published version stream and forces operator intervention on every PR. The module's testability shape decides whether those failure modes are observable at `l1` or only at integration time.

**Technical constraints:**

- The marketplace's distribution package (`outcomeeng/distribution/sync.py`, `outcomeeng/distribution/push.py`) factors orchestration into Protocol-typed boundaries with a `main()` that wires real subprocess/filesystem adapters. Departing from that shape splits the package's mental model across two patterns.
- Per `spx/13-plugin-and-runtime-conventions.adr.md`, helpers under skills run on `python3` only and use stdlib. The marketplace's `outcomeeng/distribution/*` modules already follow stdlib-only for the same reason — they ship inside the marketplace and are invoked by `just` recipes that target `uv run` against `pyproject.toml`'s declared interpreter.
- Per `spx/local/committing-changes.md`, a plugin's "current version" exists in two places: the working-tree manifest and the manifest at `base_ref` (normally `origin/main`). The branch-already-bumped predicate compares those two values; the module needs read access to both via `git show <ref>:<path>` for the `base_ref` side.
- A plugin may own one or two manifests (`.claude-plugin/plugin.json` always; `.codex-plugin/plugin.json` when present). Per the same overlay, both must move in lockstep — a single-manifest bump produces Codex cache drift.
- The bump tool is invoked both by maintainers preparing a branch for PR and by CI workflows verifying that an in-flight branch already carries its bump. The two surfaces need different verdicts from the same predicates: a maintainer wants the new versions written, a CI gate wants exit-zero confirmation that writing would be redundant. A separate dry-run surface lets a maintainer preview what the write surface would do before mutating the working tree.
- Per `spx/local/committing-changes.md`, a `minor` bump is warranted when a plugin gains, loses, copies, or renames a skill, command, agent, or whole manifest surface; everything else is `patch`. This classification is observable from `git diff --name-status -M -C --find-copies-harder` output: file-status `A`/`C`/`D`/`R` on the structural paths (`skills/{slug}/SKILL.md`, `commands/{slug}.md`, `agents/{slug}.md`, `{.claude,.codex}-plugin/plugin.json`) means `minor`; everything else means `patch`. Major bumps are not auto-detectable — they capture human judgment about stability commitments — and are required to remain explicit per the same overlay.

## Decision

`outcomeeng.distribution.bump` factors its work into four injected Protocols — `ChangeProbe`, `ContentProbe`, `ManifestReader`, `ManifestWriter` — orchestrated by a pure `bump()` function whose `mode` parameter selects one of three behaviours over the same read phase: `WRITE` mutates the manifests, `DRY_RUN` reports the would-be new versions without mutating, and `CHECK` exits non-zero if any changed plugin's working-tree version still equals its `base_ref` version; `ChangeProbe` returns a `Mapping[str, tuple[ChangedPath, ...]]` from plugin name to the file-status-tagged paths that changed under that plugin so the orchestrator can resolve a per-plugin segment via the pure `auto_segment(changes)` function; an `Optional[Segment]` `segment` parameter overrides the per-plugin auto-detection when supplied and emits a stderr warning naming any plugin whose detected segment differs from the explicit value; `main()` wires `git diff --name-status -M -C --find-copies-harder` / `git show` / `Path.read_text` / `Path.write_text` adapters and exposes `--dry-run` and `--check` as mutually-exclusive CLI flags plus an optional `--segment {patch,minor,major}` flag; the module owns a stdlib-only `Version` representation (`MAJOR.MINOR.PATCH` tuple of `int`) with explicit `patch`, `minor`, and `major` increment operations; and the branch-already-bumped predicate is `working_tree_version != base_ref_version`, evaluated per plugin from the injected readers' output before any write happens.

## Rationale

**Four Protocols, not one.** Sibling distribution modules expose `StepRunner`, `ToolProbe`, `ChangeProbe`, and `UpstreamProbe` because each boundary has a different signature and a different test substitution. Bump's boundaries are likewise distinct: change detection asks "what plugin directories have any path changed under `src/plugins/{name}/**`", content reading asks "what is the version field of this manifest at this ref", manifest reading asks "what manifests does this plugin own in the working tree", and manifest writing performs the mutation. Collapsing them into one boundary forces tests to satisfy unrelated protocol surface to assert one behavior.

**Pure `bump()` plus thin `main()`.** Each sibling distribution module's `bump()`-equivalent is a single function that takes its Protocols by keyword and returns the process exit code. Tests construct controlled Protocol implementations, call the function, and assert against the implementations' recorded calls and the function's return value. `main()` parses argv and substitutes real adapters. The same shape keeps bump testable at `l1` against in-memory Protocol implementations for change detection and manifest I/O.

**Module-owned `Version` type.** Semver parsing and segment incrementing are small, deterministic, and stdlib-trivial: a frozen dataclass with `major`/`minor`/`patch` fields plus `bump_patch`/`bump_minor`/`bump_major` methods. Owning the type keeps the segment-increment behavior testable as pure logic and out of the orchestration code. The `packaging` library would add a third-party dependency for value the stdlib `str.split('.')` covers — and `packaging.version.Version` does not even expose "increment the patch segment" as an operation, so the wrapper would carry its own bump logic anyway.

**Branch-already-bumped from values, not from git history.** Comparing working-tree version to base-ref version makes "did this branch already bump?" a pure equality check on two `Version` values, both produced by the injected `ContentProbe`. Tests substitute the probe with a recorded mapping; production substitutes `git show <base_ref>:<path>`. Walking git history for previous bump commits would couple the predicate to commit-message conventions and lose the property that a manual edit to the manifest is also a bump.

**Read-then-write, not write-as-you-go.** `bump()` collects every plugin's old and new manifest content into a plan, surfaces the plan, then performs writes. The read phase can fail (missing manifest, malformed version) before any write happens, leaving the working tree untouched. The write phase is sequential rather than transactional: stdlib has no cross-file atomic write, and the failure mode the user can recover from is "one manifest updated, other not" — `git status` shows it and `git checkout -- <path>` restores it. Adding a temp-rename two-phase write would not produce cross-file atomicity either (rename is atomic per file, not across files) and would obscure the simpler model.

Alternatives rejected:

- **Single `Runner` Protocol covering all I/O.** Forces every test to construct or stub the union of change detection, manifest read, and manifest write even when asserting one of those.
- **`subprocess`-shelled bump command.** Sibling modules expose Protocols precisely so tests do not shell out; bump has no reason to deviate.
- **`packaging.version` for semver.** Third-party dependency for stdlib-trivial parsing, and does not expose the operations the module needs (segment-specific increment with lower-segment reset).
- **Git-history-based "already bumped" detection.** Couples the predicate to commit-message conventions; cannot detect manual manifest edits that already shifted the version.

## Trade-offs accepted

| Trade-off                                                                     | Mitigation / reasoning                                                                                                                                                                                                                                                     |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Four Protocols are more surface than one                                      | Each Protocol has one method; the total surface is smaller than a single Protocol with four methods and matches the sibling-module pattern                                                                                                                                 |
| Module-owned `Version` type duplicates a slice of `packaging.version.Version` | The slice is six lines of stdlib code, and the alternative requires a wrapper anyway because `packaging` lacks segment-specific increment with lower-segment reset                                                                                                         |
| Cross-file writes are sequential, not atomic                                  | Stdlib has no cross-file atomic primitive; the failure mode is observable via `git status` and recoverable via `git checkout`; manifest writes are local working-tree mutations the developer is about to commit anyway                                                    |
| `ContentProbe` adds a boundary that could be absorbed into `ManifestReader`   | The reader returns paths and parsed JSON from the working tree; the content probe returns raw content of a path at an arbitrary ref via `git show`. The signatures are not interchangeable and combining them produces a Protocol whose two methods have nothing in common |

## Compliance

### Recognized by

A single `outcomeeng/distribution/bump.py` module exporting `bump(...)` taking `change_probe`, `content_probe`, `manifest_reader`, `manifest_writer`, `tool_probe` Protocol parameters by keyword plus a `Mode` enum parameter and an `Optional[Segment]` `segment` parameter; a `Version` frozen dataclass with `bump_patch`, `bump_minor`, `bump_major` methods; a `FileStatus` StrEnum and a frozen `ChangedPath` dataclass; a pure `auto_segment(changes)` function alongside `changed_plugins_from_diff`; a `main(argv)` that constructs real adapters around `git diff --name-status -M -C --find-copies-harder`, `git show`, `Path.read_text`, `Path.write_text` and exposes `--dry-run` and `--check` as mutually-exclusive CLI flags plus an optional `--segment` flag; and an `if __name__ == "__main__": sys.exit(main())` entrypoint matching `outcomeeng/distribution/sync.py` and `outcomeeng/distribution/push.py`.

### MUST

- All git invocations (`git diff --name-status -M -C --find-copies-harder`, `git show <ref>:<path>`) and all filesystem reads/writes pass through injected `ChangeProbe`, `ContentProbe`, `ManifestReader`, `ManifestWriter` Protocols — enables `l1` testing without subprocess fixtures or temp filesystems ([review])
- `ChangeProbe` returns a `Mapping[str, tuple[ChangedPath, ...]]` from plugin name to file-status-tagged changed paths under that plugin — both the changed-plugin set and the per-plugin classification input flow from one call ([review])
- The pure `auto_segment(changes)` function maps a file-status pattern to a segment — `[test]`-verifiable as a finite mapping, lives outside the orchestration so it can be exercised independently of `bump()` ([review])
- `bump()` returns the process exit code; `main()` parses argv and calls `bump()` with real adapters — the same shape as `outcomeeng/distribution/sync.py` and `outcomeeng/distribution/push.py` ([review])
- The module's `Version` representation owns segment-specific increment with lower-segment reset semantics (`bump_patch`, `bump_minor`, `bump_major`) — keeps the increment behavior testable as pure logic and out of the orchestration path ([review])
- `bump()` reads every changed plugin's working-tree and `base_ref` versions before performing any write — read failures (missing manifest, malformed JSON, malformed version) surface before the working tree is mutated ([review])
- The branch-already-bumped predicate compares `working_tree_version` against `base_ref_version` per plugin — manual edits that already shifted the version are recognized as a prior bump ([review])
- Tool availability for `git` is checked once at the start of `bump()` via the injected `ToolProbe`, before any other orchestration step — missing tools fail fast with a diagnostic ([review])
- The `Mode` parameter selects exactly one of `WRITE`, `DRY_RUN`, `CHECK` — all three share the read phase; `WRITE` writes; `DRY_RUN` reports without writing; `CHECK` verifies every changed plugin is already bumped and exits non-zero when any is not ([review])
- `--dry-run` and `--check` CLI flags are declared in argparse's mutually-exclusive group — the parser rejects their combination at the boundary, not inside `bump()` ([review])
- The `segment` parameter to `bump()` is `Optional[Segment]`; `None` selects per-plugin auto-detection via `auto_segment(changes)`, a concrete value overrides detection for every plugin in the run ([review])
- When an explicit `segment` overrides a plugin's auto-detected value, the orchestrator emits a stderr warning naming the plugin and the detected segment — the override is honored but the discrepancy is surfaced ([review])

### NEVER

- Direct `subprocess.run`, `Path.read_text`, or `Path.write_text` calls inside `bump()` — every I/O effect crosses an injected Protocol boundary ([review])
- A single `Runner` Protocol carrying all I/O method signatures — each boundary has a distinct contract and tests should substitute only what the assertion requires ([review])
- Third-party dependencies (`packaging`, `pydantic`, `gitpython`) — the module ships inside the marketplace's stdlib-only distribution package per `spx/13-plugin-and-runtime-conventions.adr.md` ([review])
- Walking commit history to recognize a prior bump — the predicate is a value comparison on the parsed `Version` of two manifest snapshots ([review])
- Writing any manifest before every changed plugin's read phase completes — partial-read-then-partial-write produces working-tree states whose recovery is not obvious from `git status` ([review])
- Calling the injected `ManifestWriter` inside the `DRY_RUN` or `CHECK` branch — the read-only modes are observable as zero writer invocations regardless of plugin state ([review])
- Auto-detection returning `Segment.MAJOR` — major bumps require explicit human opt-in per `spx/local/committing-changes.md`; `auto_segment` chooses only between `PATCH` and `MINOR` ([review])
- Silently dropping an explicit-vs-detected segment disagreement — the stderr warning is the audit trail that the user-chosen segment overrode the file-status-derived one ([review])
