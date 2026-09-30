# Clean

PROVIDES on-demand removal of gitignored cache directories and artifacts from the working tree
SO THAT contributors invoking `just clean`
CAN reclaim disk space and reset cache state without remembering ad-hoc `find -delete` invocations

The `outcomeeng.hygiene.clean` module invokes `git clean -fdX` from the repository root when at least one top-level cleanup candidate remains after protected paths are removed. The protected set is `.git`, `.gitignore`, `.spx`, and the active Python environment. The flag combination is the base contract: `-f` (force, required by git), `-d` (recurse into untracked directories), `-X` (remove only gitignored paths). The module passes top-level pathspecs that omit the session store and, when the Python process running the cleanup lives inside the repository, that active environment. When every top-level path is protected, the module exits successfully without invoking Git.

This paragraph declares the base command and the protected set; the module complies with that declaration. Their agreement is audit evidence, because every oracle for it is a second declaration of the same value. Test evidence therefore covers the behavior around those values — the argv the builder composes, the paths it omits, the exit codes it returns — and never the values themselves. Removing a test that pinned one of these values re-routes its assertion's verification type in the same change, so the two layers cannot drift apart.

Evidence for an assertion of this node states the outcome the governed code decides. A predicate that holds whether or not that code runs is not evidence, in either layer: not a test whose expectation the arrangement alone satisfies, and not an assertion whose link no mutation of the governed code can falsify.

Every value the cleanup command uses that this node spells out is listed here with its owner and the evidence it takes; a value the command uses and this list omits is not spelled by the node. The names of surfaces the node refers to — the recipe, the module, the harness guides — are not values the command uses and fall outside the list.

| Value                           | Owner                              | Evidence                                            |
| ------------------------------- | ---------------------------------- | --------------------------------------------------- |
| The base command                | this node                          | audit, against the module's own base argv           |
| Its flag combination            | this node                          | audit, against the same argv                        |
| The protected name `.git`       | this node                          | audit, against the module's metadata-directory name |
| The protected name `.gitignore` | this node                          | audit, against the module's ignore-file name        |
| The protected name `.spx`       | this node                          | audit, against the module's session-store name      |
| The pathspec separator `--`     | Git's end-of-options convention    | test, against that convention's name                |
| The success exit code `0`       | the process exit-status convention | test, against the standard library's name for it    |
| The active Python environment   | the running interpreter            | test — a path resolved at runtime, not a literal    |

A value this node owns admits no test of its agreement with the module, because every oracle for it would be a second declaration of the same choice; audit judges that agreement. A value an outside convention owns does admit one, because its oracle is the convention's own name rather than a copy of the module's. A test may import any of these values to arrange or read a case. The behavior around each value — which paths the builder omits, which it keeps, what it returns when nothing is left — is test evidence and restates no value the node owns.

The module invokes the command in the repository root whose top-level entries produced the pathspecs. A caller that names no root gets the nearest directory at or above its working directory that holds the repository's metadata. That root reaches the command boundary with the argv, so the declaration holds for every caller rather than only for one whose working directory already matches.

## Assertions

### Scenarios

- Given `clean` runs from a directory nested inside a repository that holds the running interpreter's environment, and its caller hands it neither the root nor the environment, when the runner records its call, then the recorded argv passes top-level pathspecs that omit that environment and the recorded call runs in the repository root those pathspecs were computed for ([test](tests/test_clean.scenario.l1.py))
- Given the generated argv run as a Git dry run in a repository with an ignored session store, an ignored active environment, and another ignored cache, then Git lists only the other cache ([test](tests/test_clean.scenario.l1.py))
- Given the runner returns a non-zero exit code, when `clean` runs, then the exit code is propagated to the caller ([test](tests/test_clean.scenario.l1.py))
- Given every top-level path is protected, when `clean` runs, then the runner is not invoked and the call reports success ([test](tests/test_clean.scenario.l1.py))

### Compliance

- ALWAYS: begin the generated argv with the declared base command when cleanup candidates exist ([test](tests/test_clean.compliance.l1.py))
- ALWAYS: every value the table above assigns to this node — the base command, its flag combination, and the three protected names — equals the value the module declares ([audit])
- ALWAYS: separate the base command from generated pathspecs with the pathspec separator ([test](tests/test_clean.compliance.l1.py))
- NEVER: include the active in-repository Python environment in the generated pathspecs ([test](tests/test_clean.compliance.l1.py))
- NEVER: include the session store in the generated pathspecs while another ignored cache remains one — the store is operational state a live session reads ([test](tests/test_clean.compliance.l1.py))
- NEVER: include the repository's own metadata in the generated pathspecs — neither its directory nor its ignore file is ever a cleanup candidate ([test](tests/test_clean.compliance.l1.py))
- NEVER: fall back to the bare base command when no cleanup candidates exist ([test](tests/test_clean.compliance.l1.py))
- ALWAYS: the root harness guides `CLAUDE.md` and `AGENTS.md` name `just clean` as the agent's own action when a gitignored artifact blocks a gate, with no operator question and no path-limited substitute ([audit])
