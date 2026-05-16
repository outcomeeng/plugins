# Push

PROVIDES the publish-and-sync orchestration that pushes the current branch and then refreshes the local marketplace install when the pushed range changed plugin distribution paths
SO THAT marketplace maintainers and CI workflows
CAN publish work to origin and observe the immediate impact on the locally installed marketplace in a single command without re-running marketplace mutations manually

The `outcomeeng.distribution.push` module captures the upstream commit reference before invoking `git push`, runs the push with the caller's arguments, and delegates to `outcomeeng.distribution.sync` with the captured reference so sync's change detection decides whether to refresh marketplace caches.

## Assertions

### Scenarios

- Given a branch tracking an upstream ref, when push runs and `git push` succeeds, then the upstream ref is captured before `git push` and sync is invoked with that ref as `base_ref` ([test](tests/test_push.scenario.l1.py))
- Given a branch with no upstream, when push runs and `git push` succeeds, then sync is invoked without a `base_ref` argument ([test](tests/test_push.scenario.l1.py))
- Given `git push` returns a non-zero exit code, when push runs, then push exits with the same code and sync is not invoked ([test](tests/test_push.scenario.l1.py))

### Compliance

- ALWAYS: check availability of `git`, `claude`, `codex`, and `uv` before any orchestration step — missing tools fail fast with a diagnostic ([test](tests/test_push.compliance.l1.py))
- ALWAYS: capture the upstream ref before invoking `git push` — the captured ref reflects the pre-push state, never the post-push state ([test](tests/test_push.compliance.l1.py))
- NEVER: invoke sync when `git push` failed — a failed push has no published range for sync to act on ([test](tests/test_push.compliance.l1.py))
