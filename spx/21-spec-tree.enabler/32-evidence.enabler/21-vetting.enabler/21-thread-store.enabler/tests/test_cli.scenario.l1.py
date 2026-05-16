"""Scenario tests for the CRUD CLIs.

Covers the Scenario clauses on the CLI surface in
``../thread-store.md``:

- ``write_record.py``, ``read_record.py``, ``delete_record.py``, and
  ``list_records.py`` accept slug + name + payload via stdin or
  ``--file`` and exit 0 on success.

The compliance clauses on the CLI surface (every CLI invokes the
facade; no CLI calls direct filesystem primitives) live in
``test_cli.compliance.l1.py`` — one evidence type per file.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.thread_store import (
    DELETE_RECORD_SCRIPT,
    LIST_RECORDS_SCRIPT,
    READ_RECORD_SCRIPT,
    WRITE_RECORD_SCRIPT,
    run_script,
    with_temp_local_store,
)


SLUG = "feature__x"
NAME = "result.json"
PAYLOAD = '{"verdict":"APPROVED"}'


def _env_for(tmp_path: pathlib.Path) -> dict[str, str]:
    import os

    return {
        **os.environ,
        "SPX_VET_BACKEND": "local",
        "SPX_VET_LOCAL_ROOT": str(tmp_path),
    }


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
