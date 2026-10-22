"""Resource lifecycle and observations for generated-output formatting evidence."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng.distribution.build import (
    FormatterProbe,
    build,
)
from outcomeeng.distribution.contracts import DIST_DIR_NAME
from outcomeeng_testing.harnesses.distribution import FileSnapshot, snapshot_files
from outcomeeng_testing.harnesses.plugin_build import _formatter_probe
from outcomeeng_testing.harnesses.src_tree import src_tree

GENERATED_FORMATTING_PLUGIN: Final = "formatting-plugin"
GENERATED_FORMATTING_SKILL: Final = "formatting-skill"
GITIGNORE_FILENAME: Final = ".gitignore"
IGNORE_EVERYTHING_PATTERN: Final = "*\n"
FORMAT_SUBCOMMAND: Final = "fmt"
HOST_DIRECTORY_NAME: Final = "host"
UNFORMATTED_SKILL_BODY: Final = "* first\n* second\n"


class Enclosure(StrEnum):
    """Where the output directory sits relative to repository ignore rules."""

    NONE = "none"
    REPOSITORY_IGNORES_OUTPUT_DIRECTORY = "repository-ignores-output-directory"
    OUTPUT_DIRECTORY_IGNORES_ITSELF = "output-directory-ignores-itself"


VIOLATING_ENCLOSURES: Final = tuple(
    enclosure for enclosure in Enclosure if enclosure is not Enclosure.NONE
)


@dataclass(frozen=True)
class FormattingObservation:
    """Generated output before and after the build's formatting step."""

    before_formatting: FileSnapshot
    after_formatting: FileSnapshot


def build_inside_enclosure(enclosure: Enclosure) -> FormattingObservation:
    """Build one plugin into an output directory placed inside ``enclosure``."""
    with src_tree() as builder:
        builder.add_plugin(
            GENERATED_FORMATTING_PLUGIN,
            skills={GENERATED_FORMATTING_SKILL: UNFORMATTED_SKILL_BODY},
        )
        host_root = builder.root / HOST_DIRECTORY_NAME
        host_root.mkdir()
        dist_root = host_root / DIST_DIR_NAME
        _place_enclosure(enclosure, host_root, dist_root)
        before: list[FileSnapshot] = []

        def recording_runner(
            command: tuple[str, ...], cwd: Path
        ) -> subprocess.CompletedProcess[str]:
            if FORMAT_SUBCOMMAND in command:
                before.append(_output_snapshot(dist_root))
            return subprocess.run(
                command, cwd=cwd, check=False, capture_output=True, text=True
            )

        probe: FormatterProbe = _formatter_probe(builder.root)
        build(
            builder.src_root,
            dist_root,
            formatter_probe=probe,
            formatter_runner=recording_runner,
        )
        return FormattingObservation(
            before_formatting=before[0] if before else (),
            after_formatting=_output_snapshot(dist_root),
        )


def _place_enclosure(enclosure: Enclosure, host_root: Path, dist_root: Path) -> None:
    if enclosure is Enclosure.REPOSITORY_IGNORES_OUTPUT_DIRECTORY:
        subprocess.run(
            ["git", "init", "--quiet", str(host_root)], check=True, capture_output=True
        )
        (host_root / GITIGNORE_FILENAME).write_text(f"{DIST_DIR_NAME}/\n")
    elif enclosure is Enclosure.OUTPUT_DIRECTORY_IGNORES_ITSELF:
        subprocess.run(
            ["git", "init", "--quiet", str(host_root)], check=True, capture_output=True
        )
        dist_root.mkdir()
        (dist_root / GITIGNORE_FILENAME).write_text(IGNORE_EVERYTHING_PATTERN)


def _output_snapshot(dist_root: Path) -> FileSnapshot:
    return tuple(
        entry
        for entry in snapshot_files(dist_root)
        if Path(entry[0]).name != GITIGNORE_FILENAME
    )
