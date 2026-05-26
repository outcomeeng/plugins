"""Abstract ``Backend`` protocol for thread-store persistence.

Every concrete backend implements the five-method CRUD surface declared
here. The ``thread_store`` facade selects a registered backend at
runtime via the ``SPX_VERIFY_BACKEND`` environment variable and dispatches
read/write/delete/list operations through it.

Stdlib-only by design — no third-party Protocol library, no ``Pydantic``,
no ``attrs``.
"""

from __future__ import annotations

import pathlib
from typing import Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Persistence contract every concrete backend implements.

    The ``runtime_checkable`` decoration enables structural-conformance
    checks at registration time: the facade verifies that a registered
    backend exposes every method before honoring it.
    """

    def thread_path(self, slug: str) -> pathlib.Path:
        """Return the path the backend uses for the thread keyed by ``slug``.

        The path is stable across repeated calls — a backend may compute
        the path on the fly, but the result must not change between
        invocations for the same slug.
        """
        ...

    def write(self, slug: str, name: str, payload: bytes) -> None:
        """Persist ``payload`` under ``(slug, name)`` atomically.

        ``write`` is atomic: a crash between the temp-write and the
        rename leaves the prior content of ``name`` intact. Backends
        that cannot honor atomicity natively implement it via
        temp-write-plus-rename or an equivalent two-phase protocol.
        """
        ...

    def read(self, slug: str, name: str) -> bytes:
        """Return the payload stored under ``(slug, name)``.

        Raises a ``NotFound``-class exception when no record exists at
        ``(slug, name)``. The exception's message names both ``slug``
        and ``name`` so consumers can produce actionable errors.
        """
        ...

    def delete(self, slug: str, name: str) -> None:
        """Remove the record at ``(slug, name)``.

        Raises a ``NotFound``-class exception when no record exists.
        Removal is best-effort across backends — local filesystems
        unlink, remote backends issue a delete API call — but the
        post-condition is uniform: a subsequent ``read`` raises
        ``NotFound``.
        """
        ...

    def list(self, slug: str) -> list[str]:
        """Return the record names present under ``slug``.

        Returns an empty list when the thread has no records (the
        backend may or may not have created the thread directory).
        Ordering is not guaranteed; consumers that need sorted output
        sort the result themselves.
        """
        ...
