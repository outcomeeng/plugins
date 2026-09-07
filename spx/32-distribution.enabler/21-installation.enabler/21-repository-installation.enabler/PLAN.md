# PLAN — repository installation

Coordination note; not spec truth. Governing decision: `spx/12-marketplace-state.adr.md`.

## Retire the activation-selection restore in favor of a settings-unchanged invariant

Persistent installation snapshots the checkout's committed `.claude/settings.json` plugin selection before the run and restores it afterward — `_declared_plugin_selection`, `_restore_plugin_selection`, and the `finally` restore in `execute_persistent_installation` in `outcomeeng/distribution/installation.py`. A correct persistent run installs and enables exactly the committed selection, and the agent CLI's writes for that selection are idempotent upserts, so the file ends unchanged by construction. A post-run difference is therefore unexpected and requires investigation — a run that installed or enabled a plugin outside the committed selection, or a change in the CLI's write semantics — and the restore erases the only signal of it. The decision's "restores the scope's pre-run activation selection" sentence, its rationale sentence, and this node's two restore-shaped compliance assertions encode that masking as product truth.

Steps, in one changeset:

1. `/author`: amend `spx/12-marketplace-state.adr.md` — remove the restore mandate and its rationale sentence, and declare the invariant: a persistent run leaves `.claude/settings.json` byte-identical to its committed content, and any post-run change is unexpected and requires investigation, never compensation.
2. `/author` with `/verify`: in `repository-installation.md`, replace the activation-selection-preserved clause of the real-agent mapping and the two committed-selection compliance assertions with settings-unchanged evidence — real-CLI `l3` evidence that post-run settings bytes equal the committed content for the refresh and fresh-machine cases, and `l1` compliance evidence with a violating runner that writes an entry outside the committed selection and fails the invariant.
3. `python:code-python`: delete the restore machinery; install and enable command emission stays unchanged.
4. `spec-tree:test` with `python:test-python`: retire the restore observations in `outcomeeng_testing/harnesses/installation.py` and the restore lane in `tests/test_repository_installation.compliance.l1.py`; the source-reconciliation half of that lane survives as marketplace-source-versus-settings evidence.
5. Gates per the router, then `/merge`.

Ordering: this changeset precedes the structural relocation recorded in `spx/PLAN.md`, so the split carries the corrected decision.
