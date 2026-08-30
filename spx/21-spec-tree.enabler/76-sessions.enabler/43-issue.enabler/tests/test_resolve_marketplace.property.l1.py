"""Property tests for the /issue marketplace resolver script."""

from __future__ import annotations

import json

from hypothesis import assume, given

from outcomeeng_testing.generators.resolve_marketplace import (
    absent_marketplace_names,
    json_payloads,
    non_json_text,
    runtimes,
)
from outcomeeng_testing.harnesses.resolve_marketplace import (
    RESOLVER,
    invalid_json_message_prefix,
    resolver_property_run,
    run_resolver,
    run_resolver_stdin,
)


@resolver_property_run
@given(
    payload=json_payloads(),
    name=absent_marketplace_names(),
    runtime=runtimes(),
)
def test_json_naming_no_matching_marketplace_maps_to_not_found(
    payload: object, name: str, runtime: str
) -> None:
    """Any JSON that names no matching marketplace resolves no path."""
    # Exclude only a payload carrying the name as a whole JSON string. A
    # bare substring test also discards every payload whose negative number
    # or hyphenated text happens to contain the sampled ``-`` name, which
    # drops the boundary case the generator keeps in every run.
    assume(json.dumps(name) not in json.dumps(payload))

    result = run_resolver(payload, runtime=runtime, name=name)

    assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
    assert result.stdout == ""


@resolver_property_run
@given(stdin=non_json_text(), runtime=runtimes())
def test_non_json_stdin_maps_to_the_invalid_json_status(
    stdin: str, runtime: str
) -> None:
    """Text that is not a JSON document is reported as invalid JSON."""
    result = run_resolver_stdin(stdin, runtime=runtime)

    assert result.returncode == RESOLVER.EXIT_INVALID_JSON
    assert result.stdout == ""
    assert result.stderr.startswith(invalid_json_message_prefix())
