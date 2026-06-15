"""Compliance evidence: the runtime-token validator's enforcement contract.

Spec: spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md

The validator never passes a raw runtime-divergent name in a non-ignored file, derives
its forbidden-name set from the build's runtime-token registry, and enforces every file
under src/plugins/ by default — a file not on the ignore-list is checked without opt-in.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY
from outcomeeng.validation.runtime_tokens import (
    RUNTIME_TOKEN_IGNORE,
    find_raw_tokens,
    is_ignored,
    scan_file,
)

_REGISTRY_NAMES = frozenset(
    name for entry in RUNTIME_TOKEN_REGISTRY.values() for name in entry.values()
)
_REPO_ROOT = Path(__file__).resolve().parents[4]


def test_never_passes_a_raw_registry_name_in_a_non_ignored_file(tmp_path: Path) -> None:
    # A non-ignored file (tmp_path resolves outside the repo, so never ignored)
    # carrying any registry name is reported.
    for name in _REGISTRY_NAMES:
        probe = tmp_path / "probe.md"
        probe.write_text(f"Use {name} here.\n", encoding="utf-8")
        violations = scan_file(probe)
        assert [v.token for v in violations] == [name]


def test_forbidden_set_derives_from_the_registry() -> None:
    # Every name the registry owns is detected; a name not in the registry is not.
    for name in _REGISTRY_NAMES:
        assert find_raw_tokens(f"text {name} text") == [(1, name)]
    assert find_raw_tokens("text NotARegisteredTool text") == []


def test_enforced_by_default_only_ignored_files_exempt() -> None:
    # A file under src/plugins/ not named on the ignore-list is enforced; the
    # ignore-list is the only exemption.
    ignored_relative = next(iter(RUNTIME_TOKEN_IGNORE))
    assert is_ignored(_REPO_ROOT / ignored_relative)
    assert not is_ignored(
        _REPO_ROOT
        / "src"
        / "plugins"
        / "develop"
        / "skills"
        / "creating-skills"
        / "SKILL.md"
    )
