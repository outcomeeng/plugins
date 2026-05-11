"""Scenario tests for the ``pass_results.py`` CLI.

Covers the Compliance MUST clauses on ``pass_results.py`` in
``../verdict-toolchain.md``:

- ``mkdir`` creates a fresh ``audit-results-*`` directory and prints its path
- ``add`` writes verbatim content to ``<dir>/<sanitized-command>``
- spaces in the command are replaced with underscores; other characters
  preserved
- collisions append ``.1``, ``.2``, … instead of overwriting
"""

from __future__ import annotations

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
SCRIPT = SCRIPTS_DIR / "pass_results.py"


def _run(
    *args: str,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


class TestMkdir:
    def test_creates_directory_under_parent(self, tmp_path: pathlib.Path) -> None:
        result = _run("mkdir", "--parent", str(tmp_path))
        assert result.returncode == 0
        path = pathlib.Path(result.stdout.strip())
        assert path.is_dir()
        assert path.parent == tmp_path
        assert path.name.startswith("audit-results-")

    def test_multiple_invocations_produce_distinct_directories(
        self, tmp_path: pathlib.Path
    ) -> None:
        a = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        b = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        assert a != b
        assert a.is_dir()
        assert b.is_dir()


class TestAddSanitization:
    def test_replaces_spaces_with_underscores(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        result = _run("add", str(results), "ruff check --fix", stdin="output")
        assert result.returncode == 0
        assert (results / "ruff_check_--fix").exists()

    def test_preserves_non_space_characters(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        result = _run("add", str(results), "pnpm run validate --full", stdin="output")
        assert result.returncode == 0
        # Hyphens, double dashes, slashes (none here), equals all preserved.
        assert (results / "pnpm_run_validate_--full").exists()

    def test_writes_verbatim_content(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        content = "line one\nline two\n\nline four\n"
        _run("add", str(results), "tool one", stdin=content)
        written = (results / "tool_one").read_text()
        assert written == content


class TestAddCollision:
    def test_second_invocation_appends_suffix(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        _run("add", str(results), "ruff check", stdin="first run")
        _run("add", str(results), "ruff check", stdin="second run")
        assert (results / "ruff_check").read_text() == "first run"
        assert (results / "ruff_check.1").read_text() == "second run"

    def test_third_invocation_increments_suffix(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        _run("add", str(results), "tool", stdin="a")
        _run("add", str(results), "tool", stdin="b")
        _run("add", str(results), "tool", stdin="c")
        assert (results / "tool").read_text() == "a"
        assert (results / "tool.1").read_text() == "b"
        assert (results / "tool.2").read_text() == "c"


class TestAddInputSources:
    def test_reads_from_stdin_by_default(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        _run("add", str(results), "tool", stdin="from stdin")
        assert (results / "tool").read_text() == "from stdin"

    def test_reads_from_file_when_flag_given(self, tmp_path: pathlib.Path) -> None:
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        source = tmp_path / "source.txt"
        source.write_text("from file")
        _run("add", str(results), "tool", "--file", str(source))
        assert (results / "tool").read_text() == "from file"


class TestAddErrors:
    def test_missing_directory_fails(self, tmp_path: pathlib.Path) -> None:
        result = _run("add", str(tmp_path / "does-not-exist"), "tool", stdin="x")
        assert result.returncode != 0


class TestUsageErrors:
    def test_no_subcommand_fails(self) -> None:
        result = _run()
        assert result.returncode != 0
