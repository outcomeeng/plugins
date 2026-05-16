"""Filesystem implementation of the ``Backend`` protocol.

Stores records as flat files under ``<root>/<slug>/<name>``. Writes are
atomic via the standard temp-write-plus-``os.replace`` two-phase
protocol so a crash mid-write leaves the prior content intact.

The default root is ``.spx/reviews/`` relative to the current working
directory; the ``SPX_VET_LOCAL_ROOT`` environment variable overrides
this for tests and runtime customization.

Stdlib-only.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
from types import ModuleType


def _errors_module() -> ModuleType:
    """Load the sibling ``errors`` module via ``importlib`` if needed.

    The scripts directory is not a package on every consumer install;
    the sibling-load pattern keeps imports working under both
    ``python3 path/to/fs_backend.py`` and the test harness's importlib
    loader.
    """
    cached = sys.modules.get("errors")
    if cached is not None:
        return cached
    module_path = pathlib.Path(__file__).resolve().parent / "errors.py"
    spec = importlib.util.spec_from_file_location("errors", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load errors module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["errors"] = module
    spec.loader.exec_module(module)
    return module


DEFAULT_LOCAL_ROOT = pathlib.Path(".spx") / "reviews"
ENV_LOCAL_ROOT = "SPX_VET_LOCAL_ROOT"


class FilesystemBackend:
    """Persist records as files under ``root/<slug>/<name>``.

    The constructor accepts an explicit ``root`` so tests can point the
    backend at a ``tmp_path``-rooted location without monkey-patching
    environment variables; production callers go through
    ``FilesystemBackend.from_env`` which honors ``SPX_VET_LOCAL_ROOT``.
    """

    def __init__(self, root: pathlib.Path) -> None:
        self.root = pathlib.Path(root)

    @classmethod
    def from_env(cls) -> FilesystemBackend:
        """Construct a backend whose root resolves from the environment.

        Reads ``SPX_VET_LOCAL_ROOT`` and falls back to ``.spx/reviews``
        relative to the current working directory. The root is
        materialized on first write; ``from_env`` itself performs no
        filesystem I/O.
        """
        raw = os.environ.get(ENV_LOCAL_ROOT)
        root = pathlib.Path(raw) if raw else DEFAULT_LOCAL_ROOT
        return cls(root=root)

    def thread_path(self, slug: str) -> pathlib.Path:
        return self.root / slug

    def write(self, slug: str, name: str, payload: bytes) -> None:
        """Persist ``payload`` to ``thread_path(slug) / name`` atomically.

        Writes the payload to a temporary file in the same directory
        and then renames it onto the target via ``os.replace``. The
        in-directory placement keeps the rename atomic on every POSIX
        filesystem (cross-filesystem renames are not atomic on most
        kernels).
        """
        target_dir = self.thread_path(slug)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / name
        # ``mkstemp`` returns an open file descriptor; we wrap the fd
        # with the standard ``os.write`` + ``os.close`` pair so the file
        # is closed (and flushed) before the rename.
        fd, temp_path_str = tempfile.mkstemp(
            prefix=f".{name}.", suffix=".tmp", dir=target_dir
        )
        temp_path = pathlib.Path(temp_path_str)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            os.replace(temp_path, target)
        except BaseException:
            # If anything failed before or during the rename, drop the
            # temp file so subsequent runs do not see partial state.
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    # Best-effort cleanup; the temp filename is prefixed
                    # with ``.`` so it does not surface in ``list()``.
                    pass
            raise

    def read(self, slug: str, name: str) -> bytes:
        target = self.thread_path(slug) / name
        if not target.is_file():
            raise _errors_module().NotFound(slug=slug, name=name)
        with open(target, "rb") as handle:
            return handle.read()

    def delete(self, slug: str, name: str) -> None:
        target = self.thread_path(slug) / name
        if not target.is_file():
            raise _errors_module().NotFound(slug=slug, name=name)
        os.remove(target)

    def list(self, slug: str) -> list[str]:
        thread = self.thread_path(slug)
        if not thread.is_dir():
            return []
        # Filter out hidden temp files (prefixed with ``.``) and any
        # nested directories — only durable record files are listed.
        return [
            entry.name
            for entry in thread.iterdir()
            if entry.is_file() and not entry.name.startswith(".")
        ]
