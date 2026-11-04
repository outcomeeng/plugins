from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.document_levels import (
    document_path,
    document_text,
    expected_view,
    fixture_documents,
    load_document_levels,
)

module = load_document_levels()


@pytest.mark.parametrize("directory", fixture_documents(), ids=lambda path: path.name)
@pytest.mark.parametrize("level", list(module.Level), ids=module.level_label)
def test_level_view_of_each_document_form(directory: Path, level: object) -> None:
    text = document_text(directory)
    expected = (
        text
        if level is module.Level.THREE
        else expected_view(directory, module.level_label(level))
    )

    assert module.derive_view(text, document_path(directory), level) == expected
