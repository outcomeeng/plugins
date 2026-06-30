# Guide Update Harness

PROVIDES reusable root-guide topology fixtures and assertions for guide updater tests
SO THAT `spx/21-spec-tree.enabler/43-update-spx.enabler`
CAN verify root `CLAUDE.md` and `AGENTS.md` migration behavior across existing consumer repository shapes

## Assertions

### Scenarios

- Given a root guide topology where one runtime guide is a symlink to the other, when the harness materializes runtime guides, then both guide paths are regular files preserving the source guide body for each runtime-specific test path ([test](tests/test_guide_update_harness.scenario.l1.py))

### Mappings

- Root guide topology maps to runtime seed bodies: only `CLAUDE.md` present seeds both runtime paths from `CLAUDE.md`; only `AGENTS.md` present seeds both runtime paths from `AGENTS.md`; separate regular files seed each runtime from its matching file; a symlinked runtime path seeds both paths from the shared target body ([test](tests/test_guide_update_harness.mapping.l1.py))
