# Instruction Block Harness

PROVIDES reusable root-instruction-file topology materialization backed by inert whole-document payload fixtures
SO THAT `spx/21-spec-tree.enabler/43-instruction-block.enabler`
CAN verify root `CLAUDE.md` and `AGENTS.md` migration behavior across existing consumer repository shapes

## Assertions

### Scenarios

- Given a root instruction-file topology where one harness instruction file is a symlink to the other, when the harness materializes harness instruction files, then both instruction-file paths are regular files preserving the source body for each harness-specific test path ([test](tests/test_instruction_block_harness.scenario.l1.py))

### Mappings

- Root instruction-file topology maps to harness seed bodies: only `CLAUDE.md` present seeds both harness paths from `CLAUDE.md`; only `AGENTS.md` present seeds both harness paths from `AGENTS.md`; separate regular files seed each agent harness from its matching file; a symlinked harness path seeds both paths from the shared target body ([test](tests/test_instruction_block_harness.mapping.l1.py))

### Compliance

- ALWAYS: root instruction bodies, shared-region examples, and line-boundary examples come from inert whole-document fixture files accessed through the harness; the harness owns materialization and access while source modules own generator and automation vocabulary ([audit])
