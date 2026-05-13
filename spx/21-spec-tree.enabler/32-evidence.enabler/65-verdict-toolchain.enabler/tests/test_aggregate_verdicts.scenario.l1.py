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

from _helpers import AGGREGATE_SCRIPT, run_script


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
    return run_script(AGGREGATE_SCRIPT, *args)


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


class TestWrapperRows:
    """Coverage for the ``--row name=STATUS`` flag.

    The orchestrator owns three wrapper rows (``automated-gates``,
    ``test-execution``, ``determinism-contract``) that the dispatched
    audit skills do not produce. The wrapper rolls those statuses up
    alongside the children's overalls, so a FAIL wrapper row (e.g., a
    failing automated gate) flips the wrapper to REJECTED even when
    every child verdict is PASS.
    """

    def test_repeated_row_flag_populates_wrapper_rows(
        self, tmp_path: pathlib.Path
    ) -> None:
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(
            str(a),
            "--row",
            "automated-gates=PASS",
            "--row",
            "test-execution=PASS",
            "--row",
            "determinism-contract=PASS",
        )
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        names = [row["name"] for row in wrapper["rows"]]
        assert names == ["automated-gates", "test-execution", "determinism-contract"]
        assert all(row["status"] == "PASS" for row in wrapper["rows"])
        assert all(row["findings"] == [] for row in wrapper["rows"])
        assert wrapper["overall"] == "APPROVED"

    def test_fail_wrapper_row_rolls_up_to_rejected(
        self, tmp_path: pathlib.Path
    ) -> None:
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        _write_child(b, _child(skill="auditing-python", overall="PASS"))
        result = _run(
            str(a),
            str(b),
            "--row",
            "automated-gates=FAIL",
            "--row",
            "test-execution=PASS",
            "--row",
            "determinism-contract=PASS",
        )
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        # Wrapper-row FAIL propagates despite all-PASS children.
        assert wrapper["overall"] == "REJECTED"
        statuses = {row["name"]: row["status"] for row in wrapper["rows"]}
        assert statuses["automated-gates"] == "FAIL"

    def test_no_row_flag_means_empty_rows(self, tmp_path: pathlib.Path) -> None:
        """Backward compatibility: callers that pass no --row get the
        original children-only rollup with empty wrapper rows."""
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(str(a))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["rows"] == []
        assert wrapper["overall"] == "APPROVED"

    def test_unknown_row_status_is_rejected(self, tmp_path: pathlib.Path) -> None:
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(str(a), "--row", "automated-gates=APPROVED")
        # APPROVED is a root-level status, not a skill-level status; row
        # statuses must be PASS / FAIL / UNKNOWN.
        assert result.returncode != 0
        assert "status must be" in result.stderr

    def test_malformed_row_entry_is_rejected(self, tmp_path: pathlib.Path) -> None:
        a = tmp_path / "a.json"
        _write_child(a, _child(skill="auditing-typescript", overall="PASS"))
        result = _run(str(a), "--row", "no-equals-sign")
        assert result.returncode != 0
        assert "expected name=STATUS" in result.stderr


class TestMixedVocabularyChildren:
    """Coverage for the dual ``overall`` vocabulary across children.

    ``verdict.from_json_dict`` accepts both ``ROOT_STATUSES``
    (``APPROVED`` / ``REJECTED``) and ``SKILL_STATUSES`` (``PASS`` /
    ``FAIL``) on the wrapper's ``children``, because a wrapper composed
    of leaf skill verdicts and a child orchestrator wrapper may receive
    both. ``roll_up`` over the mixed set must still produce a coherent
    wrapper overall — a single ``FAIL`` or ``REJECTED`` child flips the
    wrapper to ``REJECTED``; an ``APPROVED`` child alongside ``PASS``
    children keeps the wrapper ``APPROVED``.
    """

    def test_pass_and_approved_children_yield_approved_wrapper(
        self, tmp_path: pathlib.Path
    ) -> None:
        leaf = tmp_path / "leaf.json"
        nested = tmp_path / "nested.json"
        _write_child(leaf, _child(skill="auditing-typescript", overall="PASS"))
        _write_child(nested, _child(skill="auditing", overall="APPROVED"))
        result = _run(str(leaf), str(nested))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["overall"] == "APPROVED"

    def test_fail_skill_and_approved_wrapper_yield_rejected(
        self, tmp_path: pathlib.Path
    ) -> None:
        leaf = tmp_path / "leaf.json"
        nested = tmp_path / "nested.json"
        _write_child(leaf, _child(skill="auditing-typescript", overall="FAIL"))
        _write_child(nested, _child(skill="auditing", overall="APPROVED"))
        result = _run(str(leaf), str(nested))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        # Mixed vocabulary: skill-level FAIL alongside root-level
        # APPROVED still rolls up to REJECTED because any non-passing
        # status flips the wrapper.
        assert wrapper["overall"] == "REJECTED"

    def test_pass_skill_and_rejected_wrapper_yield_rejected(
        self, tmp_path: pathlib.Path
    ) -> None:
        leaf = tmp_path / "leaf.json"
        nested = tmp_path / "nested.json"
        _write_child(leaf, _child(skill="auditing-typescript", overall="PASS"))
        _write_child(nested, _child(skill="auditing", overall="REJECTED"))
        result = _run(str(leaf), str(nested))
        assert result.returncode == 0
        wrapper = json.loads(result.stdout)
        assert wrapper["overall"] == "REJECTED"
