# PR-Thread State Surface

PROVIDES the pull-request comment thread as the durable cross-CI-run state surface for audit verdicts — the most recent comment carrying the `<!-- AUDIT_VERDICT_JSON_BEGIN --> ... <!-- AUDIT_VERDICT_JSON_END -->` delimiters is the prior verdict, recovered by `read_verdict.py` and consumed by `audit_orchestrator.py verdict-diff` to compute resolved and reopened by content identity
SO THAT the CI-side `pr-review-orchestrator` agent and any future CI-side caller of `/spec-tree:audit` can iterate auditably across pushes — surfacing what got fixed and what regressed across iterations
CAN ship without writing audit state to disk: PR-thread mode never writes to `.spx/audits/` (that surface belongs to the local `audit-orchestrator` agent), so a CI runner that exits between iterations preserves no state outside the PR thread itself

## Assertions

### Compliance

- ALWAYS: the prior audit verdict for a PR is the most recent comment whose body contains the `<!-- AUDIT_VERDICT_JSON_BEGIN -->` delimiter — `read_verdict.py` extracts the JSON payload between the begin/end delimiters; comments without the begin delimiter are ignored ([review])
- ALWAYS: `compute_verdict_diff` keys finding identity on the tuple `(file, line, rule, message)` — `id` and `severity` are excluded so a regenerated finding with a fresh producer-assigned ID, or one whose severity is upgraded or downgraded across runs, matches its prior counterpart by content rather than by accident-of-numbering ([test](../tests/test_auditing.scenario.l1.py))
- ALWAYS: `compute_verdict_diff` emits the `resolved` and `reopened` arrays in a content-identity-sorted order so the JSON output is byte-equal across Python processes regardless of `PYTHONHASHSEED` — a re-run of the same audit against the same prior produces a verdict comment that matches the previous one byte-for-byte, otherwise PR-thread comparison would treat trivially-reordered output as drift and surface false resolutions or reopens ([test](tests/test_audit_orchestrator_cli.scenario.l1.py))
- ALWAYS: the PR-thread mode preserves `<!-- AUDIT_VERDICT_JSON_BEGIN --> ... <!-- AUDIT_VERDICT_JSON_END -->` delimiters intact in every posted comment so the next iteration's `read_verdict.py` can recover this verdict as the prior — wrapping the JSON in a markdown fence or stripping the delimiters breaks the ingest ([review])
- ALWAYS: a PR-thread audit comment contains at most one `<!-- AUDIT_VERDICT_JSON_BEGIN -->` block per comment — the orchestrator posts the review prose plus the audit verdict's `markdown+json` carrier as one combined comment, never as two delimiter-bearing comments side-by-side ([review])
- NEVER: PR-thread mode writes to `.spx/audits/` or any other on-disk audit state surface — the durable surface is the PR comment thread; on-disk persistence belongs to the local `audit-orchestrator` agent, not the CI-side `pr-review-orchestrator` ([review])
- NEVER: a PR-thread audit comment lingers alongside the new one after a re-run — the orchestrator supersedes the prior comment by `gh pr comment --edit-last` (when the prior is the orchestrator's last comment) or by post + delete (otherwise), so the PR thread carries exactly one delimiter-bearing audit comment per agent at any time ([review])
- NEVER: the absence of a prior verdict on a fresh PR halts the audit — the first run on a new PR is the empty-prior case, where `compute_verdict_diff` returns the current verdict with empty `resolved` and `reopened` arrays ([test](../tests/test_auditing.scenario.l1.py))
