# Guide Update Harness

PROVIDES reusable root-guide topology fixtures and assertions for guide updater tests
SO THAT `spx/21-spec-tree.enabler/43-update-spx.enabler`
CAN verify root `CLAUDE.md` and `AGENTS.md` migration behavior across existing consumer repository shapes

## Assertions

### Scenarios

- Given a root guide topology where one harness guide is a symlink to the other, when the harness materializes harness guides, then both guide paths are regular files preserving the source guide body for each harness-specific test path ([test](tests/test_guide_update_harness.scenario.l1.py))

### Mappings

- Root guide topology maps to harness seed bodies: only `CLAUDE.md` present seeds both harness paths from `CLAUDE.md`; only `AGENTS.md` present seeds both harness paths from `AGENTS.md`; separate regular files seed each agent harness from its matching file; a symlinked harness path seeds both paths from the shared target body ([test](tests/test_guide_update_harness.mapping.l1.py))
