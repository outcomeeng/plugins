from outcomeeng_testing.harnesses.prowl_environment import (
    observe_delegation_cli_fields,
    observe_delegation_sender_pane,
    verify_prowl_compliance,
)


def test_prowl_environment_compliance() -> None:
    assert verify_prowl_compliance() == []


def test_delegation_cli_rejects_an_unsupported_field() -> None:
    detail = observe_delegation_cli_fields("returnAddress")

    assert detail is not None, (
        "an unsupported delegation field was accepted; a caller inventing a "
        "field would send a delegation missing the data it believed it supplied"
    )
    assert "returnAddress" in detail, f"rejection did not name the field: {detail!r}"


def test_delegation_cli_accepts_the_supported_fields() -> None:
    assert observe_delegation_cli_fields(None) is None


def test_delegation_envelope_carries_the_sender_pane() -> None:
    submitted, carried = observe_delegation_sender_pane()

    assert carried == submitted, (
        f"envelope carried sender pane {carried!r}, not the submitted {submitted!r}; "
        "the recipient reads its return path from this field alone"
    )
