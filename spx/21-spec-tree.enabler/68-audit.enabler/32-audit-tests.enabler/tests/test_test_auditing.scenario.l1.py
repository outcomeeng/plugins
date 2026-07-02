from outcomeeng_testing.harnesses.audit_tests import (
    async_helper_declarations_are_detected,
    python_binding_declarations_are_detected,
    test_owned_declaration_is_rejected,
)


def test_rejects_test_owned_declarations() -> None:
    assert test_owned_declaration_is_rejected()


def test_detects_async_helper_declarations() -> None:
    assert async_helper_declarations_are_detected()


def test_detects_python_binding_declarations() -> None:
    assert python_binding_declarations_are_detected()
