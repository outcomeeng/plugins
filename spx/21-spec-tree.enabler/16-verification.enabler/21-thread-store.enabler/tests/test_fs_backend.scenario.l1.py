"""Scenario tests for the filesystem backend.

Covers the Scenario clause on the filesystem backend's ``thread_path``
in ``../manage-thread-store.md``:

- ``thread_path(slug)`` resolves to ``<root>/<slug>``
- ``thread_path(slug)`` returns the same path across repeated calls
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.thread_store import load_fs_backend_module


SLUG = "feature__x"


class TestThreadPath:
    def test_resolves_under_configured_root(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        path = backend.thread_path(SLUG)
        assert path == tmp_path / SLUG

    def test_is_stable_across_repeated_calls(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        first = backend.thread_path(SLUG)
        second = backend.thread_path(SLUG)
        assert first == second
