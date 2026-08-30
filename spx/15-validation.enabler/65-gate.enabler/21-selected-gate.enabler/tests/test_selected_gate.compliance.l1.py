"""Compliance evidence for selected gate execution."""

from __future__ import annotations

import pytest

from outcomeeng.validation.infrastructure_index import InfrastructureReach
from outcomeeng.validation.selected_gate import (
    InfrastructureIndexRequired,
    build_selected_gate_plan,
)
from outcomeeng_testing.harnesses.gate import assert_selected_gate_compliance_contract
from outcomeeng_testing.harnesses.infrastructure_index import (
    reach_layout,
    synthetic_repository,
)


def test_selected_gate_compliance_contract() -> None:
    assert_selected_gate_compliance_contract()


def test_infrastructure_path_without_an_index_is_rejected_by_name() -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.NODE_LOCAL, repo)

    with pytest.raises(InfrastructureIndexRequired) as caught:
        build_selected_gate_plan((layout.changed_path,))

    assert caught.value.paths == (layout.changed_path,)
    assert layout.changed_path in str(caught.value)
