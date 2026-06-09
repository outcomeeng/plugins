# Known issues — bump enabler

## FOLLOW-UP [correctness]: CHECK mode false positive for brand-new plugins

When a changed plugin has no manifest at `base_ref` (the plugin directory itself is new on this branch), `content_probe(base_ref, path)` returns `None`. The `working_tree_version != base_ref_version` branch is never entered, `plugin_already_bumped` stays `False`, and the plugin lands in `unbumped_plugins`. In CHECK mode this exits non-zero with `"still equals its origin/main version"` even after `just bump` has already written the bumped version on this branch — and the diagnostic is factually wrong because there is no `origin/main` version to equal.

The first PR that introduces a new plugin will trip this false positive once `just bump-check` is wired into CI (per the test plan in PR #46).

No test currently exercises this path. Caught by the marketplace code review of PR #46.

**Fix sketch:** when `base_ref_content is None`, treat the plugin as legitimately bumped (a new plugin's mere presence in the working tree IS the bump) — short-circuit the `unbumped_plugins.append(plugin)` path in this case. Add a scenario test with `ScriptedContentProbe(content={})` (empty mapping) and a manifest reader returning a record for the same plugin; assert CHECK mode exits 0 and the plugin is not named in the diagnostic.

## FOLLOW-UP [robustness]: `_version_from_manifest_text` surfaces tracebacks for malformed input

`outcomeeng/distribution/bump.py:_version_from_manifest_text` calls `json.loads(content)["version"]` without catching `json.JSONDecodeError` or `KeyError`. A manifest with malformed JSON or a missing `version` key surfaces as an unhandled exception with a traceback rather than the graceful `print-to-stderr-and-return-1` pattern every other error path in the module uses.

The ADR's read-then-write invariant still holds (the exception unwinds before any `manifest_writer` call), so the working tree is not mutated. But the failure mode is inconsistent with the rest of the module's error model. Caught by the marketplace code review of PR #46.

**Fix sketch:** wrap the parse in try/except for `json.JSONDecodeError`, `KeyError`, and `ValueError` (the last covers `Version.parse` failures). On any of those, print a stderr diagnostic naming the manifest path and the parse failure, then propagate as an exception that `bump()` catches and converts to `return 1` before any write phase. Add a scenario test with malformed JSON in a `ScriptedManifestReader` record; assert exit non-zero and no writes.

## FOLLOW-UP [correctness]: partial-bump CHECK false-pass for dual-manifest plugins

`plugin_already_bumped` is set to `True` if *any* record in a dual-manifest plugin is ahead of `base_ref`. If a previous `just bump` run was interrupted after writing `.claude-plugin/plugin.json` but before writing `.codex-plugin/plugin.json`, the codex manifest stays at the old version. On the next run:

- **CHECK mode exits 0** — the plugin is in `already_bumped_plugins`, so `unbumped_plugins` is empty and the check falsely passes.
- **WRITE mode exits 1** — the "already bumped" guard fires and refuses to bump the lagging manifest.

The lockstep invariant — both manifests carry the same version — is violated, and neither mode catches it. The ADR acknowledges the one-manifest-ahead-of-the-other failure mode as recoverable via `git checkout`, but does not note the CHECK false-pass. Caught by the marketplace code review of PR #46.

**Fix sketch:** classify per-record rather than per-plugin. Track `(plugin, record)` pairs whose `working_tree_version != base_ref_version`; a dual-manifest plugin with one record ahead and one record clean is in the partial-bump state, surfaceable as a distinct diagnostic (`Plugin <name>: manifests out of lockstep — <path> at <new>, <path> at <old>`). CHECK and WRITE both exit non-zero with that diagnostic; the operator runs `git checkout -- <lagging-path>` to recover.
