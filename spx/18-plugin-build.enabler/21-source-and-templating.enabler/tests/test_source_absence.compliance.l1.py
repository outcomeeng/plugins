"""Compliance evidence for skill and template directories without a manifest.

A directory holding no authored source is absent to validation and emission;
a directory holding an authored file without `SKILL.md` is rejected.
"""

from pathlib import Path

import pytest

from outcomeeng.distribution.build import SourceFormatError, project_emissions
from outcomeeng_testing.generators.source_and_templating import (
    SourceScenario,
    source_scenarios,
)
from outcomeeng_testing.harnesses.source_absence import (
    IgnoreRule,
    arrange_cache_only_skill_directory,
    arrange_cache_only_template_directory,
    arrange_empty_skill_directory,
    arrange_manifestless_skill_directory,
    arrange_manifestless_template_directory,
)


@pytest.mark.parametrize("rule", IgnoreRule)
@pytest.mark.parametrize("case", source_scenarios(), ids=lambda c: c.skill)
def test_cache_only_skill_directory_is_absent(
    tmp_path: Path, case: SourceScenario, rule: IgnoreRule
) -> None:
    arranged = arrange_cache_only_skill_directory(tmp_path, case, rule)

    projection = project_emissions(arranged.src_root)

    sources = [emission.source for emission in projection.emissions]
    assert arranged.authored_manifest in sources
    assert not [
        source for source in sources if source.is_relative_to(arranged.skill_root)
    ]


@pytest.mark.parametrize("case", source_scenarios(), ids=lambda c: c.skill)
def test_empty_skill_directory_is_absent(tmp_path: Path, case: SourceScenario) -> None:
    arranged = arrange_empty_skill_directory(tmp_path, case)

    projection = project_emissions(arranged.src_root)

    sources = [emission.source for emission in projection.emissions]
    assert arranged.authored_manifest in sources
    assert not [
        source for source in sources if source.is_relative_to(arranged.skill_root)
    ]


@pytest.mark.parametrize("case", source_scenarios(), ids=lambda c: c.skill)
def test_manifestless_skill_directory_with_authored_source_is_rejected(
    tmp_path: Path, case: SourceScenario
) -> None:
    arranged = arrange_manifestless_skill_directory(tmp_path, case)

    with pytest.raises(SourceFormatError) as raised:
        project_emissions(arranged.src_root)

    assert str(arranged.skill_root.relative_to(arranged.src_root)) in str(raised.value)


@pytest.mark.parametrize("rule", IgnoreRule)
@pytest.mark.parametrize("case", source_scenarios(), ids=lambda c: c.skill)
def test_cache_only_template_directory_is_absent(
    tmp_path: Path, case: SourceScenario, rule: IgnoreRule
) -> None:
    arranged = arrange_cache_only_template_directory(tmp_path, case, rule)

    projection = project_emissions(arranged.src_root)

    sources = [emission.source for emission in projection.emissions]
    assert arranged.authored_manifest in sources
    assert not [
        source for source in sources if source.is_relative_to(arranged.template_root)
    ]


@pytest.mark.parametrize("case", source_scenarios(), ids=lambda c: c.skill)
def test_manifestless_template_directory_with_authored_source_is_rejected(
    tmp_path: Path, case: SourceScenario
) -> None:
    arranged = arrange_manifestless_template_directory(tmp_path, case)

    with pytest.raises(SourceFormatError) as raised:
        project_emissions(arranged.src_root)

    assert str(arranged.template_root.relative_to(arranged.src_root)) in str(
        raised.value
    )
