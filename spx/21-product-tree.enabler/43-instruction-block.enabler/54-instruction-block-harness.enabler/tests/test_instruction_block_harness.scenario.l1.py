"""Scenario evidence for root instruction-file topology materialization."""

from pathlib import Path

from outcomeeng_testing.harnesses import instruction_block as harness


def test_symlinked_harness_instruction_files_materialize_as_regular_files() -> None:
    def preserves_bodies(
        paths: tuple[Path, ...], materialized: dict[str, str], body: str
    ) -> None:
        for path in paths:
            assert path.is_file()
            assert not path.is_symlink()
            assert path.read_text(encoding="utf-8") == body
            assert materialized[path.name] == body

    harness.observe_symlinked_instruction_topology(preserves_bodies)
