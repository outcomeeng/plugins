"""Property evidence for verbatim include reads."""

from __future__ import annotations

from outcomeeng_testing.harnesses.source_and_templating import (
    include_body_property_holds,
)


def test_body_returned_verbatim() -> None:
    assert include_body_property_holds()
