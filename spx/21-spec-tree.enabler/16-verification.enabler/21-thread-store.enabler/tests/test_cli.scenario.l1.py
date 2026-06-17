"""Scenario tests for the CRUD CLIs.

Covers the Scenario clauses on the CLI surface in
``../manage-thread-store.md``:

- ``write_record.py``, ``read_record.py``, ``delete_record.py``, and
  ``list_records.py`` accept slug + name + payload via stdin or
  ``--file`` and exit 0 on success.
- ``thread_store.current_slug()`` derives the slug from
  ``SPX_VERIFY_BRANCH`` env or ``git symbolic-ref --short HEAD``; every CRUD
  CLI invoked without ``--slug`` falls back to that derivation. Detached
  HEAD or missing git aborts with a structured error.

The compliance clauses on the CLI surface (every CLI invokes the
facade; no CLI calls direct filesystem primitives; ``--slug`` is
optional on every CRUD CLI) live in ``test_cli.compliance.l1.py`` —
one evidence type per file.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

from outcomeeng_testing.harnesses.thread_store import (
    DELETE_RECORD_SCRIPT,
    LIST_RECORDS_SCRIPT,
    READ_RECORD_SCRIPT,
    WRITE_RECORD_SCRIPT,
    load_branch_slug_module,
    run_script,
    with_temp_local_store,
)


SLUG = "feature__x"
NAME = "result.json"
PAYLOAD = '{"verdict":"APPROVED"}'


def _env_for(tmp_path: pathlib.Path) -> dict[str, str]:
    return {
        **os.environ,
        "SPX_VERIFY_BACKEND": "local",
        "SPX_VERIFY_LOCAL_ROOT": str(tmp_path),
    }


def _init_git_repo(repo: pathlib.Path, branch: str = "feature/x") -> None:
    """Initialise a tiny git repo at ``repo`` switched to ``branch``."""
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(  # noqa: S603 — args derived from the test
        ["git", "init", "-q", "-b", "main", str(repo)],
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(  # noqa: S603
        ["git", "config", "commit.gpgsign", "false"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
    )
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    subprocess.run(  # noqa: S603
        ["git", "add", "seed.txt"], cwd=repo, env=env, check=True, capture_output=True
    )
    subprocess.run(  # noqa: S603
        ["git", "commit", "-q", "-m", "init"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(  # noqa: S603
        ["git", "switch", "-c", branch],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
    )


class TestWriteRecordCli:
    def test_writes_from_stdin_and_exits_zero(self, tmp_path: pathlib.Path) -> None:
        result = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            stdin=PAYLOAD,
            env=_env_for(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / SLUG / NAME).read_text() == PAYLOAD

    def test_writes_from_file_flag_and_exits_zero(self, tmp_path: pathlib.Path) -> None:
        payload_path = tmp_path / "input.json"
        payload_path.write_text(PAYLOAD)
        result = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            "--file",
            str(payload_path),
            env=_env_for(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / SLUG / NAME).read_text() == PAYLOAD


class TestReadRecordCli:
    def test_reads_existing_record_to_stdout(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            run_script(
                WRITE_RECORD_SCRIPT,
                "--slug",
                SLUG,
                "--name",
                NAME,
                stdin=PAYLOAD,
                env=_env_for(tmp_path),
                check=True,
            )
        result = run_script(
            READ_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            env=_env_for(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == PAYLOAD

    def test_missing_record_exits_non_zero(self, tmp_path: pathlib.Path) -> None:
        result = run_script(
            READ_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            "absent.json",
            env=_env_for(tmp_path),
        )
        assert result.returncode != 0


class TestDeleteRecordCli:
    def test_deletes_existing_record_and_exits_zero(
        self, tmp_path: pathlib.Path
    ) -> None:
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            stdin=PAYLOAD,
            env=_env_for(tmp_path),
            check=True,
        )
        result = run_script(
            DELETE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            env=_env_for(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        assert not (tmp_path / SLUG / NAME).exists()


class TestListRecordsCli:
    def test_lists_record_names_one_per_line(self, tmp_path: pathlib.Path) -> None:
        env = _env_for(tmp_path)
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            "a.json",
            stdin="{}",
            env=env,
            check=True,
        )
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            "b.md",
            stdin="# h\n",
            env=env,
            check=True,
        )
        result = run_script(LIST_RECORDS_SCRIPT, "--slug", SLUG, env=env)
        assert result.returncode == 0, result.stderr
        names = set(result.stdout.split())
        assert names == {"a.json", "b.md"}

    def test_empty_thread_exits_zero_with_no_output(
        self, tmp_path: pathlib.Path
    ) -> None:
        result = run_script(
            LIST_RECORDS_SCRIPT,
            "--slug",
            SLUG,
            env=_env_for(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == ""


class TestCliJsonRoundTrip:
    """End-to-end: write, read, verify the same JSON payload survives."""

    def test_full_round_trip(self, tmp_path: pathlib.Path) -> None:
        env = _env_for(tmp_path)
        payload = json.dumps({"k": "v", "n": 1})
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            stdin=payload,
            env=env,
            check=True,
        )
        result = run_script(
            READ_RECORD_SCRIPT,
            "--slug",
            SLUG,
            "--name",
            NAME,
            env=env,
            check=True,
        )
        assert json.loads(result.stdout) == {"k": "v", "n": 1}


class TestSlugDerivationWhenOmitted:
    """When ``--slug`` is omitted the CLIs derive via ``thread_store.current_slug()``.

    Source precedence: ``SPX_VERIFY_BRANCH`` env beats ``git symbolic-ref
    --short HEAD``; detached HEAD or missing git aborts with a structured
    stderr message naming the override so the operator can recover.
    """

    def test_env_branch_yields_derived_slug(self, tmp_path: pathlib.Path) -> None:
        env = {**_env_for(tmp_path), "SPX_VERIFY_BRANCH": "feature/x"}
        expected_slug = load_branch_slug_module().branch_slug("feature/x")
        result = run_script(
            WRITE_RECORD_SCRIPT,
            "--name",
            NAME,
            stdin=PAYLOAD,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / expected_slug / NAME).read_text() == PAYLOAD

    def test_git_current_branch_yields_derived_slug(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo, branch="feature/y")
        store_root = tmp_path / "store"
        store_root.mkdir()
        env = {
            **os.environ,
            "SPX_VERIFY_BACKEND": "local",
            "SPX_VERIFY_LOCAL_ROOT": str(store_root),
            "PWD": str(repo),
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
        }
        env.pop("SPX_VERIFY_BRANCH", None)
        expected_slug = load_branch_slug_module().branch_slug("feature/y")
        result = subprocess.run(  # noqa: S603 — script path is from the harness
            ["python3", str(WRITE_RECORD_SCRIPT), "--name", NAME],
            cwd=repo,
            env=env,
            input=PAYLOAD,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert (store_root / expected_slug / NAME).read_text() == PAYLOAD

    def test_detached_head_without_env_override_aborts(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo, branch="feature/z")
        # Switch to detached HEAD at the same commit.
        subprocess.run(  # noqa: S603
            ["git", "switch", "--detach", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        env = {
            **os.environ,
            "SPX_VERIFY_BACKEND": "local",
            "SPX_VERIFY_LOCAL_ROOT": str(tmp_path / "store"),
            "PWD": str(repo),
        }
        env.pop("SPX_VERIFY_BRANCH", None)
        result = subprocess.run(  # noqa: S603
            ["python3", str(WRITE_RECORD_SCRIPT), "--name", NAME],
            cwd=repo,
            env=env,
            input=PAYLOAD,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "SPX_VERIFY_BRANCH" in result.stderr

    def test_git_unavailable_without_env_override_aborts(
        self, tmp_path: pathlib.Path
    ) -> None:
        import sys

        repo = tmp_path / "repo"
        repo.mkdir()
        # No git init — the cwd is not a git repo, and PATH is wiped of
        # everything except sys.executable's directory so the Python
        # binary still runs but the script's git subprocess can't find git.
        python_dir = str(pathlib.Path(sys.executable).parent)
        env = {
            "SPX_VERIFY_BACKEND": "local",
            "SPX_VERIFY_LOCAL_ROOT": str(tmp_path / "store"),
            "PWD": str(repo),
            "PATH": python_dir,
            # Python needs HOME for some imports on macOS; keep a benign value.
            "HOME": str(tmp_path),
        }
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(WRITE_RECORD_SCRIPT), "--name", NAME],
            cwd=repo,
            env=env,
            input=PAYLOAD,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        # The error should name either git or SPX_VERIFY_BRANCH so the
        # operator knows how to recover.
        assert "git" in result.stderr.lower() or "SPX_VERIFY_BRANCH" in result.stderr
