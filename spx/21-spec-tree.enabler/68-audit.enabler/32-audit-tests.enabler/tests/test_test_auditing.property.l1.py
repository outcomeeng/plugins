from outcomeeng_testing.harnesses.audit_tests import (
    coupling_taxonomy_classifies_distinct_failure_modes,
)


def test_coupling_taxonomy_classifies_distinct_failure_modes() -> None:
    assert coupling_taxonomy_classifies_distinct_failure_modes()
