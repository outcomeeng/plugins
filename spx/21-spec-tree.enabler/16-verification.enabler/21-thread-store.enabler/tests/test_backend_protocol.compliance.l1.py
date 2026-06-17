"""Compliance tests for the ``Backend`` protocol.

Covers the Compliance clauses on backend protocol conformance in
``../thread-store.md``:

- A conformant backend module exposes ``thread_path``, ``write``,
  ``read``, ``delete``, and ``list`` with the declared signatures.
- ``thread_store.get_backend()`` refuses to return a non-conforming
  backend — registration-time conformance is enforced, not deferred.
"""

from __future__ import annotations

import inspect
import pathlib

import pytest

from outcomeeng_testing.harnesses.thread_store import (
    load_backend_module,
    load_fs_backend_module,
    load_thread_store_module,
    with_temp_local_store,
)


# The spec declares exactly five required Backend methods. Hard-coding
# the roster (rather than deriving it from the protocol at runtime)
# means a future commit that silently shrinks the protocol — e.g.,
# removes ``delete`` — fails this test instead of weakening it.
REQUIRED_METHODS: tuple[str, ...] = (
    "thread_path",
    "write",
    "read",
    "delete",
    "list",
)


class TestBackendProtocolShape:
    def test_protocol_declares_required_methods(self) -> None:
        backend_module = load_backend_module()
        protocol = backend_module.Backend
        for name in REQUIRED_METHODS:
            assert hasattr(protocol, name), f"Backend protocol missing {name!r}"

    def test_filesystem_backend_implements_required_methods(
        self, tmp_path: pathlib.Path
    ) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        for name in REQUIRED_METHODS:
            method = getattr(backend, name, None)
            assert method is not None, f"FilesystemBackend missing {name!r}"
            assert callable(method)


class TestFilesystemBackendSignatures:
    def test_thread_path_signature(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        sig = inspect.signature(backend.thread_path)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["slug"]

    def test_write_signature(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        sig = inspect.signature(backend.write)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["slug", "name", "payload"]

    def test_read_signature(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        sig = inspect.signature(backend.read)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["slug", "name"]

    def test_delete_signature(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        sig = inspect.signature(backend.delete)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["slug", "name"]

    def test_list_signature(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        sig = inspect.signature(backend.list)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["slug"]


class TestNonConformingBackendRefused:
    """``thread_store.get_backend()`` refuses partial implementations.

    The Compliance rule says ``get_backend()`` refuses to return a
    non-conforming backend at facade-registration time. The facade
    exposes a ``register_backend`` entry point that performs the check;
    registering a partial implementation must raise before the call
    returns.
    """

    def test_register_backend_rejects_missing_method(
        self, tmp_path: pathlib.Path
    ) -> None:
        ts = load_thread_store_module()

        class PartialBackend:
            def __init__(self, root: pathlib.Path) -> None:
                self.root = root

            def thread_path(self, slug: str) -> pathlib.Path:
                return self.root / slug

            # Missing: write, read, delete, list.

        with pytest.raises(ts.ConfigurationError):
            ts.register_backend("partial-test", lambda: PartialBackend(tmp_path))

    def test_register_backend_accepts_full_implementation(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A full implementation registers without error and resolves via env var."""
        ts = load_thread_store_module()

        class FullBackend:
            def __init__(self, root: pathlib.Path) -> None:
                self.root = root

            def thread_path(self, slug: str) -> pathlib.Path:
                return self.root / slug

            def write(self, slug: str, name: str, payload: bytes) -> None:
                target = self.thread_path(slug) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)

            def read(self, slug: str, name: str) -> bytes:
                return (self.thread_path(slug) / name).read_bytes()

            def delete(self, slug: str, name: str) -> None:
                (self.thread_path(slug) / name).unlink()

            def list(self, slug: str) -> list[str]:
                thread = self.thread_path(slug)
                if not thread.is_dir():
                    return []
                return sorted(p.name for p in thread.iterdir())

        ts.register_backend("full-test", lambda: FullBackend(tmp_path))
        monkeypatch.setenv("SPX_VERIFY_BACKEND", "full-test")
        with with_temp_local_store(tmp_path):
            # Re-set after with_temp_local_store overrode SPX_VERIFY_BACKEND.
            monkeypatch.setenv("SPX_VERIFY_BACKEND", "full-test")
            backend = ts.get_backend()
        assert isinstance(backend, FullBackend)
