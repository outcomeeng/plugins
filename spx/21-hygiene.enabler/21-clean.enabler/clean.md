# Clean

PROVIDES on-demand removal of gitignored cache directories and artifacts from the working tree
SO THAT contributors invoking `just clean`
CAN reclaim disk space and reset cache state without remembering ad-hoc `find -delete` invocations

The `outcomeeng.hygiene.clean` module invokes `git clean -fdX` from the repository root when at least one top-level cleanup candidate remains after protected paths are removed. The protected set is `.git`, `.gitignore`, `.spx`, and the active Python environment. The flag combination is the base contract: `-f` (force, required by git), `-d` (recurse into untracked directories), `-X` (remove only gitignored paths). The module passes top-level pathspecs that omit the session store and, when the Python process running the cleanup lives inside the repository, that active environment. When every top-level path is protected, the module exits successfully without invoking Git.

This paragraph declares the base command and the protected set; the module complies with that declaration. Their agreement is audit evidence, because every oracle for it is a second declaration of the same value. Test evidence therefore covers the behavior around those values — the argv the builder composes, the paths it omits, the exit codes it returns — and never the values themselves. Removing a test that pinned one of these values re-routes its assertion's verification type in the same change, so the two layers cannot drift apart.

Evidence for an assertion of this node states the outcome the governed code decides. A predicate that holds whether or not that code runs is not evidence, in either layer: not a test whose expectation the arrangement alone satisfies, and not an assertion whose link no mutation of the governed code can falsify.

The module invokes the command in the repository root whose top-level entries produced the pathspecs. That root reaches the command boundary with the argv, so the declaration holds for every caller rather than only for one whose working directory already matches.

## Assertions

### Scenarios

- Given `clean` runs from an active Python environment inside the repository, when the runner records its call, then the recorded argv passes top-level pathspecs that omit that environment and the recorded call runs in the repository root those pathspecs were computed for ([test](tests/test_clean.scenario.l1.py))
- Given the generated argv is translated to a `git clean -ndX` dry run in a repository with an ignored `.spx/` directory, an ignored active environment, and another ignored cache, then Git lists only the other cache ([test](tests/test_clean.scenario.l1.py))
- Given the runner returns a non-zero exit code, when `clean` runs, then the exit code is propagated to the caller ([test](tests/test_clean.scenario.l1.py))
- Given every top-level path is protected, when `clean` runs, then the runner is not invoked and the exit code is 0 ([test](tests/test_clean.scenario.l1.py))

### Compliance

- ALWAYS: begin the generated argv with the declared base command when cleanup candidates exist ([test](tests/test_clean.compliance.l1.py))
- ALWAYS: the base command the module declares carries the flag combination this node declares above — force, recurse into untracked directories, and gitignored paths only — which gives the desired remove-only-gitignored semantics ([audit])
- ALWAYS: separate the base command from generated pathspecs with `--` ([test](tests/test_clean.compliance.l1.py))
- NEVER: include the active in-repository Python environment in the generated pathspecs ([test](tests/test_clean.compliance.l1.py))
- NEVER: include `.spx` in the generated pathspecs — the session store is operational state a live session reads ([test](tests/test_clean.compliance.l1.py))
- NEVER: include `.git` or `.gitignore` in the generated pathspecs — the repository's own metadata is never a cleanup candidate ([test](tests/test_clean.compliance.l1.py))
- NEVER: fall back to the bare base command when no cleanup candidates exist ([test](tests/test_clean.compliance.l1.py))
- ALWAYS: the root harness guides `CLAUDE.md` and `AGENTS.md` name `just clean` as the agent's own action when a gitignored artifact blocks a gate, with no operator question and no path-limited substitute ([audit])
