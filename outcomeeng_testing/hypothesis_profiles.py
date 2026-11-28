"""The Hypothesis profiles every pytest run of this repository registers.

pytest imports this module through the ``-p`` option in ``addopts`` of
``[tool.pytest.ini_options]``, before Hypothesis's own plugin reads
``--hypothesis-profile`` and before any test module is collected. Importing it
registers two profiles and loads ``full``, so a run that names no profile runs
every test at its full example count:

- ``full``: Hypothesis's default of 100 examples for a test that declares no
  count, and the declared count for a test whose harness or test file declares
  one through :func:`profile_examples`.
- ``local``: the ``full`` count or :data:`LOCAL_MAX_EXAMPLES`, whichever is
  lower, with every other setting as under ``full``.

A ``max_examples`` pinned in ``@settings`` overrides any profile, so every
declared count passes through :func:`profile_examples`, which reads the loaded
profile when the declaring module is imported, after pytest configured it.
"""

from __future__ import annotations

from typing import Final

from hypothesis import settings

from outcomeeng.validation._steps import (
    FULL_HYPOTHESIS_PROFILE,
    LOCAL_HYPOTHESIS_PROFILE,
)

FULL_PROFILE: Final = FULL_HYPOTHESIS_PROFILE
LOCAL_PROFILE: Final = LOCAL_HYPOTHESIS_PROFILE
PROFILE_NAMES: Final = (FULL_PROFILE, LOCAL_PROFILE)
# Hypothesis's own default, which a test that declares no count runs at.
FULL_MAX_EXAMPLES: Final = 100
LOCAL_MAX_EXAMPLES: Final = 10

settings.register_profile(FULL_PROFILE, max_examples=FULL_MAX_EXAMPLES)
settings.register_profile(
    LOCAL_PROFILE,
    parent=settings.get_profile(FULL_PROFILE),
    max_examples=LOCAL_MAX_EXAMPLES,
)
settings.load_profile(FULL_PROFILE)


def profile_examples(declared: int) -> int:
    """Return the example count a test declaring ``declared`` runs now.

    Under ``local`` the count is ``declared`` or :data:`LOCAL_MAX_EXAMPLES`,
    whichever is lower; under every other profile it is ``declared``.
    """

    if settings.get_current_profile_name() == LOCAL_PROFILE:
        return min(declared, LOCAL_MAX_EXAMPLES)
    return declared
