# Clean

PROVIDES on-demand removal of gitignored cache directories and artifacts from the working tree
SO THAT contributors invoking `just clean`
CAN reclaim disk space and reset cache state without remembering ad-hoc `find -delete` invocations

The `outcomeeng.hygiene.clean` module invokes `git clean -fdX` from the repository root when at least one top-level cleanup candidate remains after protected paths are removed. The flag combination is the base contract: `-f` (force, required by git), `-d` (recurse into untracked directories), `-X` (remove only gitignored paths). When the Python process running the cleanup lives inside the repository, the module passes top-level pathspecs that omit that active environment so `just clean` does not delete the interpreter it is running under. When every top-level path is protected, the module exits successfully without invoking Git.

## Assertions

### Scenarios

- Given `clean` runs from an active Python environment inside the repository, when the runner records its call, then the recorded argv passes top-level pathspecs that omit that environment ([test](tests/test_clean.scenario.l1.py))
- Given the generated argv is translated to a `git clean -ndX` dry run in a repository with an ignored active environment and another ignored cache, then Git lists the other cache and does not list the active environment ([test](tests/test_clean.scenario.l1.py))
- Given the runner returns a non-zero exit code, when `clean` runs, then the exit code is propagated to the caller ([test](tests/test_clean.scenario.l1.py))
- Given every top-level path is protected, when `clean` runs, then the runner is not invoked and the exit code is 0 ([test](tests/test_clean.scenario.l1.py))

### Compliance

- ALWAYS: invoke `git clean -fdX` as the base command when cleanup candidates exist — the flag combination gives the desired remove-only-gitignored semantics ([test](tests/test_clean.compliance.l1.py))
- ALWAYS: separate `git clean -fdX` from generated pathspecs with `--` ([test](tests/test_clean.compliance.l1.py))
- NEVER: include the active in-repository Python environment in the generated pathspecs ([test](tests/test_clean.compliance.l1.py))
- NEVER: fall back to bare `git clean -fdX` when no cleanup candidates exist ([test](tests/test_clean.compliance.l1.py))
