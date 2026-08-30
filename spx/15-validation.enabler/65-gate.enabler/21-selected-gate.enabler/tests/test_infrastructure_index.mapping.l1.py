"""Mapping evidence for import-statement resolution in the static import index."""

from __future__ import annotations

import pytest

from outcomeeng.validation.infrastructure_index import (
    TEST_INFRASTRUCTURE_PACKAGE,
    import_dependencies,
)
from outcomeeng_testing.generators.infrastructure_index import (
    ImportStatementCase,
    import_statement_cases,
)


@pytest.mark.parametrize("case", import_statement_cases(), ids=lambda case: case.form)
def test_import_statement_form_resolves_to_its_module_path(
    case: ImportStatementCase,
) -> None:
    resolved = import_dependencies(
        case.source,
        importing_package=case.importing_package,
        package=TEST_INFRASTRUCTURE_PACKAGE,
        modules=case.modules,
    )

    assert resolved == case.expected
