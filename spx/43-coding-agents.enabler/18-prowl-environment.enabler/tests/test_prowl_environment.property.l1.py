from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.prowl_environment import DelegationTextCase
from outcomeeng_testing.harnesses.prowl_environment import run_terminal_property


def test_prowl_environment_properties() -> None:
    def assert_terminal(
        module: ModuleType,
        sender: dict[str, str],
        recipient: dict[str, str],
        property_text: DelegationTextCase,
        reference: str,
        terminal_kind: object,
        result_form: tuple[str | None, str | None, str | None],
    ) -> None:
        inline_result, result_reference, projection = result_form
        delegation = module.delegation_request(
            sender=sender,
            recipient=recipient,
            subject=property_text.subject,
            instruction=property_text.instruction,
            completion_text=property_text.completion_text,
            coordination_reference=reference,
        )
        terminal = module.terminal_handback(
            delegation,
            terminal_kind,
            inline_result=inline_result,
            result_reference=result_reference,
            projection=projection,
        )
        first = module.reduce_terminal(None, terminal)

        assert module.reduce_terminal(first, terminal) == first

        conflicting_kind = next(
            kind for kind in module.TerminalKind if kind is not terminal_kind
        )
        conflicting_terminals = (
            module.terminal_handback(
                delegation,
                conflicting_kind,
                inline_result=property_text.inline_result,
            ),
            module.terminal_handback(
                delegation,
                terminal_kind,
                inline_result=(
                    f"{inline_result}!"
                    if inline_result is not None
                    else property_text.inline_result
                ),
            ),
            module.terminal_handback(
                delegation,
                terminal_kind,
                result_reference=f"{property_text.result_reference}-conflict",
                projection=f"{property_text.projection}-conflict",
            ),
        )
        for conflicting_terminal in conflicting_terminals:
            try:
                module.reduce_terminal(first, conflicting_terminal)
            except module.ProwlEnvironmentError as error:
                assert error.status == module.ExecutionStatus.INVALID_SCHEMA
            else:
                raise AssertionError("conflicting terminal handback was accepted")

        assert cast(str, first[module.COORDINATION_REFERENCE_FIELD]) == reference

    run_terminal_property(assert_terminal)
