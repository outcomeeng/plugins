"""Scenario tests for the ``thread_store`` facade.

Covers the Scenario clauses on facade-level CRUD and ``get_backend()``
env-var resolution in ``../thread-store.md``:

- write/read round-trips bytes verbatim under the filesystem backend
- write overwrites in place (happy path)
- delete makes a subsequent read raise ``NotFound``
- read on a missing record raises ``NotFound`` with a structured message
- list returns the set of record names present in a thread
- ``get_backend()`` selects the filesystem backend by default
- ``get_backend()`` honors ``SPX_VET_BACKEND``
- ``get_backend()`` rejects unknown backend names with a clear error

Atomicity (the universal rule under crash conditions) lives in
``test_thread_store.compliance.l1.py``. The harness-surface contract
also lives in the compliance file. This file contains only scenario
evidence.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.thread_store import (
    load_fs_backend_module,
    load_thread_store_module,
    with_temp_local_store,
)


SLUG = "feature__x"
NAME = "result.json"
PAYLOAD = b'{"verdict":"APPROVED"}'


class TestWriteReadRoundTrip:
    def test_write_then_read_returns_bytes_verbatim(
        self, tmp_path: pathlib.Path
    ) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            ts.write(SLUG, NAME, PAYLOAD)
            assert ts.read(SLUG, NAME) == PAYLOAD

    def test_write_to_subdirectory_of_root(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            ts.write(SLUG, NAME, PAYLOAD)
            backend = ts.get_backend()
            thread_dir = backend.thread_path(SLUG)
            assert thread_dir.is_dir()
            assert (thread_dir / NAME).is_file()


class TestOverwrite:
    def test_overwrite_replaces_payload(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            ts.write(SLUG, NAME, PAYLOAD)
            new_payload = b'{"verdict":"REJECTED"}'
            ts.write(SLUG, NAME, new_payload)
            assert ts.read(SLUG, NAME) == new_payload


class TestDelete:
    def test_delete_removes_record(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            ts.write(SLUG, NAME, PAYLOAD)
            ts.delete(SLUG, NAME)
            with pytest.raises(ts.NotFound):
                ts.read(SLUG, NAME)

    def test_delete_missing_raises_not_found(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            with pytest.raises(ts.NotFound):
                ts.delete(SLUG, NAME)


class TestNotFound:
    def test_read_missing_raises_not_found_with_slug_and_name(
        self, tmp_path: pathlib.Path
    ) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            with pytest.raises(ts.NotFound) as excinfo:
                ts.read(SLUG, NAME)
            message = str(excinfo.value)
            assert SLUG in message
            assert NAME in message


class TestList:
    def test_list_returns_set_of_record_names(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            ts.write(SLUG, "a.json", b"{}")
            ts.write(SLUG, "b.md", b"# heading\n")
            names = ts.list(SLUG)
            assert set(names) == {"a.json", "b.md"}

    def test_list_empty_thread_returns_empty(self, tmp_path: pathlib.Path) -> None:
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            assert list(ts.list(SLUG)) == []


class TestGetBackend:
    def test_default_returns_local_filesystem_backend_rooted_at_spx_reviews(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When ``SPX_VET_BACKEND`` and ``SPX_VET_LOCAL_ROOT`` are both unset,
        ``get_backend()`` returns the filesystem backend whose root is the
        canonical default path ``.spx/reviews/``.

        The spec asserts the default rooting; verifying the class name
        alone permits a regression where the root path silently changes.
        """
        monkeypatch.delenv("SPX_VET_BACKEND", raising=False)
        monkeypatch.delenv("SPX_VET_LOCAL_ROOT", raising=False)
        ts = load_thread_store_module()
        fs_backend = load_fs_backend_module()
        backend = ts.get_backend()
        assert backend.__class__.__name__ == "FilesystemBackend"
        assert backend.root == fs_backend.DEFAULT_LOCAL_ROOT
        assert backend.root == pathlib.Path(".spx") / "reviews"

    def test_explicit_local_selection(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPX_VET_BACKEND", "local")
        monkeypatch.setenv("SPX_VET_LOCAL_ROOT", str(tmp_path))
        ts = load_thread_store_module()
        backend = ts.get_backend()
        assert backend.__class__.__name__ == "FilesystemBackend"

    def test_unknown_backend_raises_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SPX_VET_BACKEND", "nonexistent-backend")
        ts = load_thread_store_module()
        with pytest.raises(ts.ConfigurationError) as excinfo:
            ts.get_backend()
        message = str(excinfo.value)
        assert "nonexistent-backend" in message
        # The error must enumerate the registered backends so the user
        # can correct the misconfiguration without reading source.
        assert "local" in message
