# Known issues — bump enabler

## FOLLOW-UP [robustness]: `_version_from_manifest_text` surfaces tracebacks for malformed input

`outcomeeng/distribution/bump.py:_version_from_manifest_text` calls `json.loads(content)["version"]` without catching `json.JSONDecodeError` or `KeyError`. A manifest with malformed JSON or a missing `version` key surfaces as an unhandled exception with a traceback rather than the graceful `print-to-stderr-and-return-1` pattern every other error path in the module uses.

The ADR's read-then-write invariant still holds (the exception unwinds before any `manifest_writer` call), so the working tree is not mutated. But the failure mode is inconsistent with the rest of the module's error model. Caught by the marketplace code review of PR #46.

**Fix sketch:** wrap the parse in try/except for `json.JSONDecodeError`, `KeyError`, and `ValueError` (the last covers `Version.parse` failures). On any of those, print a stderr diagnostic naming the manifest path and the parse failure, then propagate as an exception that `bump()` catches and converts to `return 1` before any write phase. Add a scenario test with malformed JSON in a `ScriptedManifestReader` record; assert exit non-zero and no writes.
