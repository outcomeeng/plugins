"""Harness for inspecting build output trees in tests.

DistTreeReader provides query methods over a dist/{claude,codex}/ tree
emitted by the build. Tests use it to assert what's present, what's
absent, and what content was emitted, without manually constructing
runtime path strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from outcomeeng.scripts.build_plugins import (
    DIST_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    SKILL_FILENAME,
    Target,
)


@dataclass(frozen=True)
class DistTreeReader:
    """Query an emitted dist/ tree.

    All methods are pure reads over the filesystem; nothing is written.
    """

    root: Path

    @property
    def dist_root(self) -> Path:
        return self.root / DIST_DIR_NAME

    def runtime_root(self, target: Target) -> Path:
        return self.dist_root / target.value

    def is_skill_present(
        self,
        plugin: str,
        skill: str,
        *,
        target: Target,
    ) -> bool:
        return self._skill_path(plugin, skill, target=target).is_file()

    def read_skill_body(
        self,
        plugin: str,
        skill: str,
        *,
        target: Target,
    ) -> str:
        return self._skill_path(plugin, skill, target=target).read_text()

    def list_plugins(self, target: Target) -> tuple[str, ...]:
        runtime_root = self.runtime_root(target)
        if not runtime_root.is_dir():
            return ()
        return tuple(sorted(p.name for p in runtime_root.iterdir() if p.is_dir()))

    def list_skills(self, plugin: str, *, target: Target) -> tuple[str, ...]:
        skills_root = self.runtime_root(target) / plugin / SKILLS_SUBDIR_NAME
        if not skills_root.is_dir():
            return ()
        return tuple(sorted(s.name for s in skills_root.iterdir() if s.is_dir()))

    def list_all_files(self, target: Target) -> tuple[Path, ...]:
        """Return every file under runtime_root(target), as paths relative to it."""
        runtime_root = self.runtime_root(target)
        if not runtime_root.is_dir():
            return ()
        return tuple(
            sorted(
                f.relative_to(runtime_root)
                for f in runtime_root.rglob("*")
                if f.is_file()
            )
        )

    def _skill_path(
        self,
        plugin: str,
        skill: str,
        *,
        target: Target,
    ) -> Path:
        return (
            self.runtime_root(target)
            / plugin
            / SKILLS_SUBDIR_NAME
            / skill
            / SKILL_FILENAME
        )
