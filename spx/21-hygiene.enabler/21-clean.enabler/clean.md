# Clean

PROVIDES on-demand removal of gitignored cache directories and artifacts from the working tree
SO THAT contributors invoking `just clean`
CAN reclaim disk space and reset cache state without remembering ad-hoc `find -delete` invocations

The `outcomeeng.hygiene.clean` module invokes `git clean -fdX` from the repository root. The flag combination is the contract: `-f` (force, required by git), `-d` (recurse into untracked directories), `-X` (remove only gitignored paths). The behavior of `git clean -fdX` itself — what it removes, what it preserves, when it exits zero — is owned by git and tested by the git project; this module's testable surface is the argv it constructs.

## Assertions

### Scenarios

- Given `clean` runs, when the runner records its call, then the recorded argv is `("git", "clean", "-fdX")` ([test](tests/test_clean.scenario.l1.py))
- Given the runner returns a non-zero exit code, when `clean` runs, then the exit code is propagated to the caller ([test](tests/test_clean.scenario.l1.py))

### Compliance

- ALWAYS: invoke `git clean -fdX` — the flag combination is the contract that gives the desired remove-only-gitignored semantics ([test](tests/test_clean.compliance.l1.py))
- NEVER: pass any additional argument to `git clean` — extra flags would broaden the remove set beyond gitignored paths ([test](tests/test_clean.compliance.l1.py))
