"""Thread-store exception hierarchy.

Defined in its own module so backend implementations can raise
exceptions without importing the facade (which would create a cycle:
the facade imports the backend module to register it). Both the
facade and the backend re-export the exception types from this
module.
"""

from __future__ import annotations


class ThreadStoreError(Exception):
    """Base for every error raised by the thread-store package."""


class NotFound(ThreadStoreError):
    """Raised when a read or delete targets a missing record.

    The message names both the slug and the record name so consumers
    can produce actionable errors without inspecting the exception's
    attributes.
    """

    def __init__(self, *, slug: str, name: str) -> None:
        super().__init__(f"record {name!r} not found under slug {slug!r}")
        self.slug = slug
        self.name = name


class ConfigurationError(ThreadStoreError):
    """Raised when ``SPX_VET_BACKEND`` selects an unknown or invalid backend.

    The message enumerates the registered backend names so the user can
    correct the misconfiguration without reading source.
    """
