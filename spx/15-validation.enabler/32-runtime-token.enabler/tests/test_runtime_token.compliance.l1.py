from outcomeeng.validation.runtime_tokens import forbidden_names
from outcomeeng_testing.generators.runtime_tokens import (
    lint_enforced_runtime_names,
    raw_token_source,
    review_only_runtime_names,
)
from outcomeeng_testing.harnesses.runtime_tokens import (
    authored_tree_enforcement,
    observe_source,
)


def test_non_ignored_raw_tokens_fail_validation() -> None:
    for case in lint_enforced_runtime_names():
        observed = observe_source(raw_token_source(case))

        assert observed.violations
        assert observed.exit_code != 0


def test_review_only_names_are_excluded() -> None:
    cases = review_only_runtime_names()

    assert cases
    enforced = frozenset(forbidden_names())
    for case in cases:
        assert case.name not in enforced


def test_authored_tree_default_enforcement_matches_contract() -> None:
    enforcement = authored_tree_enforcement()

    assert enforcement.gate_files, "the gate selects no authored file at all"
    assert enforcement.gate_files == enforcement.expected_files, (
        "gate selection differs from the authored-tree inventory: "
        f"{sorted(enforcement.gate_files ^ enforcement.expected_files)}"
    )
    # Every enforced root contributes, so widening the contract to a new tree
    # fails here if the selector was not widened with it.
    for root in enforcement.enforced_roots:
        if not root.is_dir():
            continue
        assert any(path.is_relative_to(root) for path in enforcement.gate_files), (
            f"no file under the enforced root {root} is selected by the gate"
        )
    assert not enforcement.raw_token_violations, (
        f"authored source carries raw runtime tokens: "
        f"{enforcement.raw_token_violations}"
    )
    assert enforcement.ignored_files == enforcement.ignore_listed_files, (
        "ignore status disagrees with the declared ignore-list: "
        f"{sorted(enforcement.ignored_files ^ enforcement.ignore_listed_files)}"
    )
