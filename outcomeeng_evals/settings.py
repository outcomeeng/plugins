"""Source-owned defaults for eval execution."""

from typing import Final


DEFAULT_MAX_BUDGET_USD: Final = 0.75
DEFAULT_MAX_BUDGET_USD_TEXT: Final = f"{DEFAULT_MAX_BUDGET_USD:.2f}"
DEFAULT_TIMEOUT_SECONDS: Final = 180
DEFAULT_TIMEOUT_SECONDS_TEXT: Final = str(DEFAULT_TIMEOUT_SECONDS)
ADVISOR_MODEL_SETTING: Final = "advisorModel"
DISABLED_ADVISOR_MODEL: Final = ""
