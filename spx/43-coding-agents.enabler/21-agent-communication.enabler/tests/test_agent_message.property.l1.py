from types import ModuleType

from outcomeeng_testing.generators.coding_agents import message_content
from outcomeeng_testing.harnesses.coding_agents import (
    run_handback_preservation_property,
)


def test_production_requests_preserve_source_generated_handbacks() -> None:
    def assert_handback(
        module: ModuleType,
        sender: dict[str, str],
        recipient: dict[str, str],
        handback: dict[str, object],
    ) -> None:
        content = message_content(module.MessageKind.FACT, 1)
        envelope = module.build_envelope(
            kind=module.MessageKind.FACT,
            sender=sender,
            recipient=recipient,
            subject=content.subject,
            facts=list(content.facts),
            request=content.request,
            handback=handback,
        )

        assert envelope[module.HANDBACK_FIELD] == handback
        assert module.validate_envelope(envelope)[module.HANDBACK_FIELD] == handback

    run_handback_preservation_property(assert_handback)
