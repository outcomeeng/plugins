"""Scenario tests for the ``aggregate_verdicts.py`` CLI.

Covers the Compliance MUST clauses on ``aggregate_verdicts.py`` in
``../verdict-toolchain.md``:

- reads N child verdict JSON files (positional or via ``--directory``)
- emits one wrapper verdict whose ``children`` array holds the parsed
  children
- the wrapper's ``overall`` is derived via ``verdict.roll_up``
- accepts ``--skill``, ``--target``, and repeatable ``--metadata``
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[5]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)
AGGREGATE_SCRIPT = SCRIPTS_DIR / "aggregate_verdicts.py"


def _child(
    *,
    skill: str,
    overall: str,
    rows: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "skill": skill,
        "target": "spx/path/" + skill,
        "overall": overall,
        "rows": rows or [],
        "children": [],
        "metadata": {},
    }


def _write_child(path: pathlib.Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _run(
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AGGREGATE_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestPositionalChildren:
    def test_combines_two_children(self, tmp_path: pathlib.Path) -> None:
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        _write_child(b, _child(skill="auditing-python", overall="PASS"))
        result = _run(str(a), str(b))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["overall"] == "APPROVED"
        assert len(wrapper["children"]) == 2
        assert wrapper["children"][0]["skill"] == "auditing-typescript"

    def test_any_fail_child_makes_wrapper_rejected(
        self, tmp_path: pathlib.Path
    ) -> None:
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        _write_child(a, _child(skill="auditing-typescript", overall="FAIL"))
        _write_child(b, _child(skill="auditing-python", overall="PASS"))
        result = _run(str(a), str(b))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["overall"] == "REJECTED"

    def test_unknown_without_fail_yields_unknown_wrapper(
        self, tmp_path: pathlib.Path
    ) -> None:
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        _write_child(b, _child(skill="auditing-python", overall="UNKNOWN"))
        result = _run(str(a), str(b))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["overall"] == "UNKNOWN"


class TestDirectoryEnumeration:
    def test_reads_all_json_files_from_directory(self, tmp_path: pathlib.Path) -> None:
        children_dir = tmp_path / "children"
        children_dir.mkdir()
        _write_child(
            children_dir / "a.json",
            _child(skill="auditing-typescript", overall="PASS"),
        )
        _write_child(
            children_dir / "b.json",
            _child(skill="auditing-python", overall="PASS"),
        )
        # A non-JSON file is ignored.
        (children_dir / "notes.txt").write_text("ignored")
        result = _run("--directory", str(children_dir))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert len(wrapper["children"]) == 2

    def test_empty_directory_fails(self, tmp_path: pathlib.Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        result = _run("--directory", str(empty))
        assert result.returncode != 0


class TestWrapperMetadata:
    def test_skill_flag_sets_wrapper_skill(self, tmp_path: pathlib.Path) -> None:
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(str(a), "--skill", "auditing", "--target", "spx/root")
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["skill"] == "auditing"
        assert wrapper["target"] == "spx/root"

    def test_metadata_flag_repeats(self, tmp_path: pathlib.Path) -> None:
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(
            str(a),
            "--metadata",
            "branch=feature/x",
            "--metadata",
            "commit=abc123",
        )
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["metadata"]["branch"] == "feature/x"
        assert wrapper["metadata"]["commit"] == "abc123"

    def test_metadata_value_may_contain_equals(self, tmp_path: pathlib.Path) -> None:
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(str(a), "--metadata", "url=https://example.com?a=b")
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["metadata"]["url"] == "https://example.com?a=b"


class TestInvalidChildren:
    def test_invalid_child_fails(self, tmp_path: pathlib.Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        result = _run(str(bad))
        assert result.returncode != 0


class TestNoInputs:
    def test_no_positional_no_directory_fails(self) -> None:
        result = _run()
        assert result.returncode != 0
