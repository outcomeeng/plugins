# Bump

PROVIDES the manifest version-bumping orchestration that detects which plugins changed against a base reference and updates each changed plugin's manifest version once per branch
SO THAT marketplace maintainers and CI workflows
CAN bump every modified plugin's version field consistently across all manifests for that plugin in a single command, preview the bump without writing, and verify in CI that every changed plugin already carries a bump

The `outcomeeng.distribution.bump` module enumerates plugin directories under the authored source and generated runtime roots (`src/plugins/{name}/**`, `dist/claude/{name}/**`, and `dist/codex/{name}/**`), asks an injected change probe which plugins have any distribution-surface path changed since `base_ref` along with the git file-status of each change, attributes a change under the shared authored root (`src/_shared/**`) to every plugin whose authored source includes the changed fragment, reads the working-tree and `base_ref` versions of every manifest each changed plugin owns (`.claude-plugin/plugin.json` and, when present, `.codex-plugin/plugin.json`), and either writes the next version — incremented on the resolved semantic segment — back to every owned manifest (default mode), reports what it would write without touching the filesystem (`--dry-run`), or verifies that every changed plugin's owned manifest versions are in lockstep and ahead of the base reference (`--check`). Without an explicit `--segment` flag, the segment is auto-detected per plugin: a plugin whose changes add, delete, or rename a skill, thin agent, or whole plugin manifest in any recognized distribution-surface root gets a `minor` bump; any other change pattern gets a `patch` bump. Auto-detection never selects `major` — major bumps require explicit `--segment major`. An explicit `--segment` flag overrides the per-plugin auto-detection and emits a stderr warning naming any plugin whose detected segment differs from the explicit value. The base reference defaults to `origin/main`.

## Assertions

### Scenarios

- Given a working tree with changes under `src/plugins/foo/**` and no changes under `src/plugins/bar/**` since `base_ref`, when bump runs, then only `foo`'s manifests are written ([test](tests/test_bump.scenario.l1.py))
- Given the default invocation, when bump runs against a changed plugin at version `0.4.1`, then the manifest version is written as `0.4.2` ([test](tests/test_bump.scenario.l1.py))
- Given `--segment minor`, when bump runs against a changed plugin at version `0.4.1`, then the manifest version is written as `0.5.0` ([test](tests/test_bump.scenario.l1.py))
- Given `--segment major`, when bump runs against a changed plugin at version `0.4.1`, then the manifest version is written as `1.0.0` ([test](tests/test_bump.scenario.l1.py))
- Given no plugin under an authored source or generated runtime root has any change since `base_ref`, when bump runs, then it exits 0 and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given `--dry-run` and a clean changed plugin at version `0.4.1`, when bump runs, then the would-be new version `0.4.2` is reported on stdout and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given `--check` and every changed plugin's working-tree version is already ahead of its `base_ref` version, when bump runs, then it exits 0 with no diagnostic and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given `--check` and a changed plugin has no manifest at `base_ref`, when the working tree owns a manifest for that plugin, then it exits 0 with no diagnostic and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given `--check` and a changed plugin whose working-tree version equals its `base_ref` version, when bump runs, then it exits non-zero with a diagnostic naming the unbumped plugin and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given `--check` and a changed plugin's owned manifest versions are out of lockstep, when bump runs, then it exits non-zero with a diagnostic naming the plugin and the lockstep failure and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given a changed plugin manifest contains malformed JSON or no parseable string version, when bump runs, then it exits non-zero with a diagnostic naming the manifest and no manifest is written ([test](tests/test_bump.scenario.l1.py))
- Given a changed plugin whose working-tree version is below its `base_ref` version after base advancement, when bump runs, then it writes the next version from the base version rather than preserving a downgrade ([test](tests/test_bump.scenario.l1.py))
- Given no explicit `--segment` and a changed plugin whose changes add a new `skills/{slug}/SKILL.md`, when bump runs, then that plugin's version is incremented at the `minor` segment ([test](tests/test_bump.scenario.l1.py))
- Given a working tree with an untracked, non-ignored new skill under a recognized distribution-surface root alongside a tracked modification, when change detection runs, then the untracked file is reported `Added` and the modification `Modified` — an uncommitted distribution-surface addition is detected, not missed ([test](tests/test_bump.scenario.l1.py))

### Mappings

- Auto-detection maps each `(file-status, path-pattern)` pair to a segment within any recognized distribution-surface root: an `A`/`C`/`D`/`R` change to `skills/{slug}/SKILL.md`, `agents/{slug}.md`, or `{.claude,.codex}-plugin/plugin.json` yields `minor`; every other path or any `M` change yields `patch` ([test](tests/test_bump.mapping.l1.py))
- Each file status maps to the plugins one change attributes to: an `R` change attributes both its destination and its source plugin, and every other status attributes its destination plugin alone — a `C` change leaves its source untouched at `base_ref` ([test](tests/test_bump.mapping.l1.py))

### Conformance

- The include index the change-detection adapter derives conforms to the include directives present in authored plugin sources — a directive's target names the plugin whose source carries it, and a plugin naming no directive appears under no target ([test](tests/test_bump.conformance.l1.py))

### Properties

- For every semantic `Version` triple, `--segment patch` increments the third component; `--segment minor` increments the second and resets the third to 0; `--segment major` increments the first and resets the second and third to 0 ([test](tests/test_bump.property.l1.py))
- ALWAYS: a change attributes to plugin `{name}` when its path falls under `src/plugins/{name}/**`, `dist/claude/{name}/**`, or `dist/codex/{name}/**`, or when its path falls under the shared authored root and that plugin's authored source includes the changed fragment; a path matching neither triggers no bump ([test](tests/test_bump.property.l1.py))

### Compliance

- ALWAYS: every manifest a changed plugin owns is written in the same bump pass — when both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` exist, both receive the same new version in one bump invocation ([test](tests/test_bump.compliance.l1.py))
- ALWAYS: check availability of `git` before any orchestration step — missing tools fail fast with a diagnostic rather than partway through the sequence ([test](tests/test_bump.compliance.l1.py))
- NEVER: bump a plugin whose working-tree version is already ahead of its `base_ref` version — the branch already carries a valid bump for that plugin (re-bumping during PR review is the failure `spx/local/commit-changes.md` prohibits); outside CHECK mode, that plugin is skipped with a diagnostic while every other changed-but-unbumped plugin is still bumped — or, under `--dry-run`, reported — in the same pass ([test](tests/test_bump.compliance.l1.py))
- NEVER: write a manifest for a plugin with no changes under an authored source or generated runtime root since `base_ref` — change detection is the sole trigger for writing ([test](tests/test_bump.compliance.l1.py))
- NEVER: a shared fragment reaches a plugin's shipped surface without that plugin's version advancing in the same bump pass — a version that does not move when the surface moves misreports what the plugin ships ([test](tests/test_bump.compliance.l1.py))
- NEVER: reformat manifest content beyond the version field — every byte outside the `"version": "{old}"` substring is preserved character-for-character, so version bumps produce minimal diffs and do not churn manifest authors' formatting choices ([test](tests/test_bump.compliance.l1.py))
- NEVER: write any manifest when `--dry-run` or `--check` is selected — both modes are read-only regardless of plugin state ([test](tests/test_bump.compliance.l1.py))
- NEVER: combine `--dry-run` with `--check` — the modes are mutually exclusive and the CLI parser rejects their combined use ([test](tests/test_bump.compliance.l1.py))
- ALWAYS: when `--segment` is unspecified, the resolved segment is the auto-detected per-plugin segment from the file-status pattern of changes under recognized distribution-surface roots ([test](tests/test_bump.compliance.l1.py))
- ALWAYS: when `--segment` is specified and a plugin's detected segment differs from the explicit value, the explicit value is used and a stderr warning names the plugin and its detected segment ([test](tests/test_bump.compliance.l1.py))
- NEVER: auto-detection chooses `major` — major bumps require explicit `--segment major` ([test](tests/test_bump.compliance.l1.py))
