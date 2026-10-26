"""Version floors above a version the `spx` CLI reports.

Each floor raises one dotted component of the reported version by one and keeps
the others, so every component position yields a floor the reported version
does not meet.
"""

from __future__ import annotations

from outcomeeng.validation.spx_version import VERSION_SEPARATOR


def floors_above(reported: str) -> tuple[str, ...]:
    """Return one floor per component of ``reported``, that component raised by one."""

    parts = tuple(int(part) for part in reported.split(VERSION_SEPARATOR))
    return tuple(
        VERSION_SEPARATOR.join(
            str(part + 1 if index == raised else part)
            for index, part in enumerate(parts)
        )
        for raised in range(len(parts))
    )
