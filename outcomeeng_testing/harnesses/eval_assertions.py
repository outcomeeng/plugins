"""Typed resource runners for binding-free eval assertion entrypoints."""

from __future__ import annotations

import io
from collections.abc import Callable
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest


class CapturedStderr:
    def __init__(self, stream: io.StringIO) -> None:
        self._stream = stream

    def readouterr(self) -> SimpleNamespace:
        value = self._stream.getvalue()
        self._stream.seek(0)
        self._stream.truncate(0)
        return SimpleNamespace(out="", err=value)


def run_plain(assertion: Callable[[], None]) -> None:
    assertion()


def run_with_tmp_path(assertion: Callable[[Path], None]) -> None:
    with TemporaryDirectory() as directory:
        assertion(Path(directory))


def run_with_monkeypatch(
    assertion: Callable[[pytest.MonkeyPatch], None],
) -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        assertion(monkeypatch)


def run_with_monkeypatch_tmp_path(
    assertion: Callable[[pytest.MonkeyPatch, Path], None],
) -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        with TemporaryDirectory() as directory:
            assertion(monkeypatch, Path(directory))


def run_with_captured_stderr(
    assertion: Callable[[CapturedStderr], None],
) -> None:
    stream = io.StringIO()
    with redirect_stderr(stream):
        assertion(CapturedStderr(stream))
