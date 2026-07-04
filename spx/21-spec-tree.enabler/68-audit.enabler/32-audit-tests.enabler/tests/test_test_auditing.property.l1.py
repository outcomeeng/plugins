from outcomeeng.test_evidence import CouplingEvidence
from outcomeeng_testing.harnesses.audit_tests import (
    coupling_taxonomy_category_is_distinct_failure_mode,
    coupling_taxonomy_property,
)


@coupling_taxonomy_property
def test_coupling_taxonomy_classifies_distinct_failure_modes(
    category: CouplingEvidence,
) -> None:
    assert coupling_taxonomy_category_is_distinct_failure_mode(category)
