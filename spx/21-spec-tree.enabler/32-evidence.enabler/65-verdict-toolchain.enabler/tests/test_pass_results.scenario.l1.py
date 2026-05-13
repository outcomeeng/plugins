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

    def test_replaces_posix_path_separator(self, tmp_path: pathlib.Path) -> None:
        """A command containing ``/`` must not produce a nested subdirectory.

        ``filename_for_command``'s narrow contract — return a single filename
        component — is the safety property that prevents ``directory / name``
        from creating a path that escapes the results directory. Without the
        ``/`` replacement, ``python3 /path/to/check.py`` would write to
        ``<results>/python3 /path/to/check.py`` (or fail with ENOENT), not to
        a single file under the results directory.
        """
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        result = _run(
            "add",
            str(results),
            "python3 /path/to/check.py",
            stdin="output",
        )
        assert result.returncode == 0
        # All four path-resolving characters (space, /, \, :) become _.
        target = results / "python3__path_to_check.py"
        assert target.is_file()
        # The written path is one filename component directly under the
        # results directory — no nested subdirectories were created.
        assert target.parent == results

    def test_replaces_windows_path_separator(self, tmp_path: pathlib.Path) -> None:
        """The Windows ``\\`` separator is replaced even on POSIX runtimes.

        ``filename_for_command`` is portable: the same input produces the
        same filename component regardless of the host. A command pulled
        verbatim from a Windows tool wrapper (e.g., a PowerShell script
        path) does not accidentally become a path with backslashes that
        some POSIX filesystems would still interpret as a literal
        component.
        """
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        result = _run(
            "add",
            str(results),
            "wrapper.cmd C:\\Tools\\check.exe",
            stdin="output",
        )
        assert result.returncode == 0
        assert (results / "wrapper.cmd_C__Tools_check.exe").is_file()

    def test_replaces_colon(self, tmp_path: pathlib.Path) -> None:
        """The ``:`` byte is replaced (NTFS ADS / macOS HFS separator).

        Commands like ``rg --type=py 'pattern:with_colon'`` or NTFS
        alternate-data-stream paths (``file.txt:stream``) would otherwise
        produce filenames that Windows or older macOS filesystems treat
        as path metadata rather than file content.
        """
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        result = _run(
            "add",
            str(results),
            "rg --type=py pattern:with_colon",
            stdin="output",
        )
        assert result.returncode == 0
        assert (results / "rg_--type=py_pattern_with_colon").is_file()


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

    def test_max_collision_suffix_is_reachable(self, tmp_path: pathlib.Path) -> None:
        """Pin the boundary: the docstring promises ``up to MAX_COLLISION_SUFFIX``
        appended suffixes. With ``MAX_COLLISION_SUFFIX = 999`` and the base name
        pre-occupied, the script must accept up to 999 collision suffixes
        (``.1`` through ``.999``) before raising. Tests pre-create every slot
        through ``.999`` to force the script onto the final reachable slot —
        a regression that drops the last candidate (off-by-one in the suffix
        range) makes the slot unreachable and the script raises.
        """
        results = pathlib.Path(_run("mkdir", "--parent", str(tmp_path)).stdout.strip())
        # Pre-occupy ``tool`` and ``tool.1`` … ``tool.998`` so the next
        # ``add`` MUST land on ``tool.999`` (the boundary slot).
        (results / "tool").write_text("base")
        for suffix in range(1, 999):
            (results / f"tool.{suffix}").write_text(f"slot {suffix}")
        result = _run("add", str(results), "tool", stdin="final")
        assert result.returncode == 0
        assert (results / "tool.999").read_text() == "final"


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
