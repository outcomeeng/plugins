# Spike — audit-orchestrator benefit

Throwaway experiment. Asks one question before any design work: **does folding
a scope's prior audit runs into open / resolved / reopened surface information
a stateless per-run audit structurally cannot?** If no, a stateful audit
orchestrator (and the cross-run primitive it would need) is not worth building.

## Run

```bash
python3 spike.py
```

Requires `spx` on PATH and a repo with `.spx/`. The script records three
per-commit audit runs on the real `spx journal` local backend, reads them back,
folds them, and contrasts the orchestrator view against the stateless view at
the final commit.

## Scope

Local backend only. The `local` and `github-pr` journal backends are disjoint
sources of truth, so cross-run folding is always *within one backend*; this
spike is purely the local audit-orchestrator's case (a developer iterating
across local commits), not anything on a PR.

See `FINDINGS.md` for the result and its limits.
