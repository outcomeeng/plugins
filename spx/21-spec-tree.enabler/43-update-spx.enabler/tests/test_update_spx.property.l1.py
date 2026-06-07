"""Property evidence for the update-spx render helper.

Universal invariants in ``update-spx.md``: after a render the output's
``template_version`` equals the installed version, and staleness ordering matches
dotted-numeric version order (catching lexicographic defects such as 0.9.0 vs
0.10.0). Hypothesis owns the generated version domain; Python tuple ordering is the
independent oracle.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.update_spx import (
    PRODUCT_NAME,
    TEMPLATE_LANGUAGES,
    build_template,
    load_update_spx_module,
)

_VERSION_PART = st.integers(min_value=0, max_value=999)
_VERSION = st.tuples(_VERSION_PART, _VERSION_PART, _VERSION_PART)


def _to_version(parts: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in parts)


@given(installed=_VERSION)
def test_render_output_version_equals_installed(
    installed: tuple[int, int, int],
) -> None:
    module = load_update_spx_module()
    installed_str = _to_version(installed)
    config = module.GuideConfig(product_name=PRODUCT_NAME, languages=TEMPLATE_LANGUAGES)
    rendered = module.render(build_template("0.0.0"), config, installed_str)
    assert module.parse_template_version(rendered) == installed_str


@given(left=_VERSION, right=_VERSION)
def test_is_stale_matches_numeric_version_order(
    left: tuple[int, int, int], right: tuple[int, int, int]
) -> None:
    module = load_update_spx_module()
    assert module.is_stale(_to_version(left), _to_version(right)) is (left < right)
