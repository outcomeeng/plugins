"""Unit tests for sync_exclude.

Tests the sync script against the assertions in
spx/21-spec-tree.enabler/32-evidence.enabler/21-sync-exclude.enabler/sync-exclude.md.
"""

from __future__ import annotations

from pathlib import Path

import tomlkit

from outcomeeng.scripts.sync_exclude import (
    is_excluded_entry,
    main,
    read_excluded_nodes,
    sync,
    to_mypy_regex,
    to_pyright_path,
    to_pytest_ignore,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_PYPROJECT = """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers"

[tool.mypy]
exclude = []

[tool.pyright]
exclude = []
"""

PYPROJECT_WITHOUT_MYPY_OR_PYRIGHT = """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers"
"""


def _write_exclude(tmp_path: Path, content: str) -> Path:
    spx = tmp_path / "spx"
    spx.mkdir(exist_ok=True)
    p = spx / "EXCLUDE"
    p.write_text(content)
    return p


def _write_pyproject(tmp_path: Path, content: str = MINIMAL_PYPROJECT) -> Path:
    p = tmp_path / "pyproject.toml"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Scenario: flat node path produces all three tool entries
# ---------------------------------------------------------------------------


def test_flat_node_sync(tmp_path: Path) -> None:
    _write_exclude(tmp_path, "76-risc-v.outcome\n")
    pyproject = _write_pyproject(tmp_path)

    changed = sync(pyproject, ["76-risc-v.outcome"])

    assert changed is True
    content = pyproject.read_text()
    doc = tomlkit.parse(content)
    addopts: str = doc["tool"]["pytest"]["ini_options"]["addopts"]  # type: ignore[index]
    assert "--ignore=spx/76-risc-v.outcome/" in addopts
    mypy_exclude: list[str] = list(doc["tool"]["mypy"]["exclude"])  # type: ignore[index]
    assert any("76\\-risc\\-v\\.outcome" in e for e in mypy_exclude)
    pyright_exclude: list[str] = list(doc["tool"]["pyright"]["exclude"])  # type: ignore[index]
    assert "spx/76-risc-v.outcome/" in pyright_exclude


# ---------------------------------------------------------------------------
# Scenario: comments and blank lines are stripped
# ---------------------------------------------------------------------------


def test_comments_and_blanks_stripped(tmp_path: Path) -> None:
    exclude = _write_exclude(
        tmp_path,
        "# This is a comment\n"
        "\n"
        "76-risc-v.outcome\n"
        "  \n"
        "# Another comment\n"
        "43-parser.enabler\n",
    )

    nodes = read_excluded_nodes(exclude)

    assert nodes == ["76-risc-v.outcome", "43-parser.enabler"]


# ---------------------------------------------------------------------------
# Scenario: nested path with correct escaping
# ---------------------------------------------------------------------------


def test_nested_path_sync(tmp_path: Path) -> None:
    node = "57-subsystems.outcome/32-risc-v.outcome"
    pyproject = _write_pyproject(tmp_path)

    changed = sync(pyproject, [node])

    assert changed is True
    content = pyproject.read_text()
    doc = tomlkit.parse(content)
    addopts: str = doc["tool"]["pytest"]["ini_options"]["addopts"]  # type: ignore[index]
    assert f"--ignore=spx/{node}/" in addopts
    mypy_exclude: list[str] = list(doc["tool"]["mypy"]["exclude"])  # type: ignore[index]
    # Dots and hyphens must be escaped in the mypy regex
    assert any(
        "57\\-subsystems\\.outcome/32\\-risc\\-v\\.outcome" in e for e in mypy_exclude
    )
    pyright_exclude: list[str] = list(doc["tool"]["pyright"]["exclude"])  # type: ignore[index]
    assert f"spx/{node}/" in pyright_exclude


# ---------------------------------------------------------------------------
# Scenario: previously-synced entries are replaced
# ---------------------------------------------------------------------------


def test_replacement_of_old_entries(tmp_path: Path) -> None:
    pyproject = _write_pyproject(tmp_path)

    # First sync with node A
    sync(pyproject, ["76-risc-v.outcome"])
    # Second sync with node B (replaces A)
    changed = sync(pyproject, ["43-parser.enabler"])

    assert changed is True
    content = pyproject.read_text()
    assert "76-risc-v.outcome" not in content
    assert "43-parser.enabler" in content


# ---------------------------------------------------------------------------
# Scenario: already in sync produces no changes
# ---------------------------------------------------------------------------


def test_idempotent_no_change(tmp_path: Path) -> None:
    pyproject = _write_pyproject(tmp_path)
    nodes = ["76-risc-v.outcome"]

    sync(pyproject, nodes)
    content_after_first = pyproject.read_text()

    changed = sync(pyproject, nodes)

    assert changed is False
    assert pyproject.read_text() == content_after_first


# ---------------------------------------------------------------------------
# Scenario: pyproject.toml without [tool.mypy] or [tool.pyright] sections
# ---------------------------------------------------------------------------


def test_creates_missing_mypy_and_pyright_sections(tmp_path: Path) -> None:
    pyproject = _write_pyproject(tmp_path, PYPROJECT_WITHOUT_MYPY_OR_PYRIGHT)
    node = "76-risc-v.outcome"

    changed = sync(pyproject, [node])

    assert changed is True
    doc = tomlkit.parse(pyproject.read_text())

    # Missing [tool.mypy] section was created with exclude entry
    mypy_exclude: list[str] = list(doc["tool"]["mypy"]["exclude"])  # type: ignore[index]
    assert any("76\\-risc\\-v\\.outcome" in e for e in mypy_exclude)

    # Missing [tool.pyright] section was created with exclude entry
    pyright_exclude: list[str] = list(doc["tool"]["pyright"]["exclude"])  # type: ignore[index]
    assert f"spx/{node}/" in pyright_exclude


# ---------------------------------------------------------------------------
# Scenario: missing EXCLUDE file exits with error code 1
# ---------------------------------------------------------------------------


def test_missing_exclude_exits_1(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    missing_exclude = tmp_path / "spx" / "EXCLUDE"
    # Do not create the EXCLUDE file

    exit_code = main(
        exclude_path=missing_exclude, pyproject_path=tmp_path / "pyproject.toml"
    )

    assert exit_code == 1


# ---------------------------------------------------------------------------
# Mapping: node path → three tool formats
# ---------------------------------------------------------------------------


def test_to_pytest_ignore() -> None:
    assert to_pytest_ignore("76-risc-v.outcome") == "--ignore=spx/76-risc-v.outcome/"


def test_to_mypy_regex_flat() -> None:
    result = to_mypy_regex("76-risc-v.outcome")
    assert result == r"^spx/76\-risc\-v\.outcome/"


def test_to_mypy_regex_nested() -> None:
    result = to_mypy_regex("57-subsystems.outcome/32-risc-v.outcome")
    assert result == r"^spx/57\-subsystems\.outcome/32\-risc\-v\.outcome/"


def test_to_pyright_path() -> None:
    assert to_pyright_path("76-risc-v.outcome") == "spx/76-risc-v.outcome/"


# ---------------------------------------------------------------------------
# Property: idempotency — two runs produce identical content
# ---------------------------------------------------------------------------


def test_idempotency_property(tmp_path: Path) -> None:
    pyproject = _write_pyproject(tmp_path)
    nodes = ["57-subsystems.outcome/32-risc-v.outcome", "76-risc-v.outcome"]

    sync(pyproject, nodes)
    content_first = pyproject.read_text()

    sync(pyproject, nodes)
    content_second = pyproject.read_text()

    assert content_first == content_second


# ---------------------------------------------------------------------------
# is_excluded_entry detects synced entries
# ---------------------------------------------------------------------------


def test_is_excluded_entry_outcome() -> None:
    assert is_excluded_entry("spx/76-risc-v.outcome/") is True


def test_is_excluded_entry_enabler() -> None:
    assert is_excluded_entry("spx/43-parser.enabler/") is True


def test_is_excluded_entry_nested() -> None:
    assert is_excluded_entry("spx/57-subsystems.outcome/32-risc-v.outcome/") is True


def test_is_excluded_entry_mypy_regex() -> None:
    assert is_excluded_entry(r"^spx/76\-risc\-v\.outcome/") is True


def test_is_excluded_entry_unrelated() -> None:
    assert is_excluded_entry("src/utils/") is False


def test_is_excluded_entry_pytest_ignore() -> None:
    assert is_excluded_entry("--ignore=spx/76-risc-v.outcome/") is True
