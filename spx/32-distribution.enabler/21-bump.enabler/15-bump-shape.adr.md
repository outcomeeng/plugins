# Bump Orchestration Shape

`outcomeeng.distribution.bump` factors version bumping into four injected Protocols — `ChangeProbe`, `ContentProbe`, `ManifestReader`, and `ManifestWriter` — orchestrated by a pure `bump()` function whose `Mode` parameter selects one behavior over a shared read phase: `WRITE` mutates the manifests, `DRY_RUN` reports the would-be versions without mutating, and `CHECK` exits non-zero when any changed plugin's owned manifest versions are not in lockstep or not ahead of their `base_ref` versions. `main()` wires the real adapters: change detection unions `git diff --name-status -M -C --find-copies-harder` against `base_ref` (tracked changes) with `git ls-files --others --exclude-standard` under the authored source and generated runtime roots (`src/plugins/`, `dist/claude/`, and `dist/codex/`) for untracked, non-ignored additions tagged Added, alongside `git show`, `Path.read_text`, and `Path.write_text`; it exposes `--dry-run` and `--check` as mutually exclusive flags plus an optional `--segment {patch,minor,major}`. The module owns a stdlib-only `Version` (`MAJOR.MINOR.PATCH` of `int`) with segment-specific increment, resolves a per-plugin segment from git file-status through the pure `auto_segment(changes)` function, and recognizes a prior bump by comparing each plugin's working-tree manifest versions against its `base_ref` versions while requiring those owned manifests to agree with one another.

## Rationale

Four Protocols rather than one: change detection, content reading at a ref, working-tree manifest reading, and manifest writing each have a distinct signature and a distinct test substitution, matching the boundary-per-concern shape of the sibling distribution modules (`outcomeeng/distribution/sync.py`, `outcomeeng/distribution/push.py`). A single `Runner` Protocol would force every test to satisfy unrelated method surface to assert one behavior.

A pure `bump()` that takes its Protocols by keyword and returns the exit code keeps every behavior verifiable against in-memory Protocol implementations, while `main()` parses argv and binds the real adapters. The module owns a stdlib `Version` because semver parsing and segment increment are stdlib-trivial and `packaging.version` exposes no segment-specific increment with lower-segment reset — a third-party dependency would carry its own bump logic anyway, and the distribution package is stdlib-only.

Recognizing a prior bump by comparing working-tree to `base_ref` version makes the predicate a value comparison, so a manual manifest edit that leaves the branch ahead of base also counts as a bump; walking commit history would couple the predicate to commit-message conventions and miss manual edits. The comparison is ordered, not merely unequal: a branch version below an advanced base is not a valid prior bump, and the next write increments from the base version rather than preserving a downgrade. Dual-manifest plugins add the lockstep predicate: one manifest ahead and one manifest unchanged is not a prior bump, and the next write aligns every owned manifest to the current maximum version rather than skipping the plugin. `bump()` collects every plugin's read result into a plan before any write, so a missing manifest or a malformed version surfaces before the working tree is mutated. Cross-file writes are sequential because the stdlib has no cross-file atomic primitive and the one-updated-one-not state is observable through `git status` and recoverable through `git checkout`.

## Verification

### Testing

- ALWAYS: the pure `auto_segment(changes)` function maps each `(file-status, path-pattern)` pair to a segment — an `A`/`C`/`D`/`R` change to a structural path yields `minor`, every other change yields `patch` ([mapping])
- ALWAYS: the real change-detection adapter unions the tracked `git diff` against `base_ref` with the untracked, non-ignored working-tree files under `src/plugins/`, `dist/claude/`, and `dist/codex/` (`git ls-files --others --exclude-standard`), tagging each untracked path Added, so an uncommitted new structural file is detected rather than missed ([compliance])
- ALWAYS: the pure `plugins_from_change(change)` function attributes a renamed path to both its destination and source plugin and every other status to its destination alone, so copy detection over near-identical generated files never counts an untouched plugin as changed ([mapping])
- ALWAYS: the `Version` representation owns segment-specific increment with lower-segment reset (`bump_patch`, `bump_minor`, `bump_major`) ([mapping])
- ALWAYS: the branch-already-bumped predicate requires each plugin's owned manifest versions to agree with one another and be ahead of their `base_ref_version`, so a manual edit that leaves the branch ahead counts as a prior bump while a stale lower version after base advancement or a one-manifest-ahead state is bumped into lockstep from the current maximum version ([compliance])
- ALWAYS: `git` availability is checked once before any other orchestration step, failing fast with a diagnostic ([compliance])
- ALWAYS: the `Mode` parameter selects exactly one of `WRITE`, `DRY_RUN`, `CHECK`, all three sharing the read phase ([compliance])
- ALWAYS: `--dry-run` and `--check` are declared in argparse's mutually-exclusive group, so the parser rejects their combination at the boundary ([compliance])
- ALWAYS: the `segment` parameter is optional — absent selects per-plugin auto-detection, a concrete value overrides detection for every plugin in the run ([compliance])
- ALWAYS: an explicit `segment` that differs from a plugin's auto-detected value is honored and emits a stderr warning naming the plugin and its detected segment ([compliance])
- NEVER: a manifest is written when `DRY_RUN` or `CHECK` is selected — both modes are read-only regardless of plugin state ([compliance])
- NEVER: `auto_segment` returns `major` — major bumps require an explicit `--segment major` ([compliance])
- NEVER: an explicit-versus-detected segment disagreement is dropped silently — the stderr warning is the audit trail ([compliance])

### Audit

- ALWAYS: every git invocation and filesystem read/write passes through the injected `ChangeProbe`, `ContentProbe`, `ManifestReader`, `ManifestWriter`, and `ToolProbe` Protocols ([audit])
- ALWAYS: `ChangeProbe` returns a `Mapping` from plugin name to file-status-tagged changed paths, so the changed-plugin set and the per-plugin classification input flow from one call ([audit])
- ALWAYS: `bump()` returns the process exit code and `main()` parses argv and binds the real adapters, matching the shape of `outcomeeng/distribution/sync.py` and `outcomeeng/distribution/push.py` ([audit])
- ALWAYS: `bump()` reads every changed plugin's working-tree and `base_ref` versions before performing any write, so read failures surface before the working tree is mutated ([audit])
- NEVER: `bump()` calls `subprocess.run`, `Path.read_text`, or `Path.write_text` directly — every effect crosses an injected Protocol boundary ([audit])
- NEVER: a single `Runner` Protocol carries all I/O — each boundary has a distinct contract and a test substitutes only what the assertion requires ([audit])
- NEVER: the module depends on a third-party package (`packaging`, `pydantic`, `gitpython`) — the distribution package is stdlib-only ([audit])
- NEVER: a prior bump is recognized by walking commit history — the predicate is a value comparison on two manifest snapshots ([audit])
- NEVER: a manifest is written before every changed plugin's read phase completes — a partial-read-then-partial-write leaves a working-tree state whose recovery is not obvious from `git status` ([audit])
