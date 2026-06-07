"""Compliance evidence: a re-render reflects only the template and the declared config.

The NEVER rule in ``update-spx.md`` — an update keeps no unmodeled hand-prose edit to
the guide body. A rendered guide is tampered with junk body text; the re-render drops
it and equals a render from the same config, proving the body edit has no effect on
the output.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.update_spx import (
    LANG_PRIMARY,
    PRODUCT_NAME,
    build_template,
    load_update_spx_module,
)

VERSION = "0.18.0"
JUNK_EDIT = "HAND-EDITED JUNK THAT MUST NOT SURVIVE A RE-RENDER"


def test_re_render_ignores_unmodeled_body_edits() -> None:
    module = load_update_spx_module()
    template = build_template(VERSION)
    config = module.GuideConfig(product_name=PRODUCT_NAME, languages=(LANG_PRIMARY,))
    guide = module.render(template, config, VERSION)

    tampered = guide + f"\n\n## Hand Section\n\n{JUNK_EDIT}\n"
    updated = module.render(template, module.parse_config(tampered), VERSION)

    assert JUNK_EDIT not in updated
    assert updated == module.render(template, config, VERSION)
