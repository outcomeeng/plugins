"""Repository access for build-orchestration evidence."""

from dataclasses import dataclass
from pathlib import Path

from outcomeeng.distribution.codex_project import CODEX_LOCAL_RECIPE_NAME
from outcomeeng.distribution.orchestration import (
    JUSTFILE_PATH,
    just_recipe_commands,
    just_recipe_names,
)


@dataclass(frozen=True)
class CheckoutLocalCodexRecipeObservation:
    """Parsed checkout-local recipe state from the repository Justfile."""

    recipe_names: tuple[str, ...]
    commands: tuple[tuple[str, ...], ...]


def observe_checkout_local_codex_recipe() -> CheckoutLocalCodexRecipeObservation:
    """Return the parsed checkout-local Codex recipe declaration."""
    justfile = (Path.cwd() / JUSTFILE_PATH).read_text(encoding="utf-8")
    return CheckoutLocalCodexRecipeObservation(
        recipe_names=just_recipe_names(justfile),
        commands=just_recipe_commands(justfile, CODEX_LOCAL_RECIPE_NAME),
    )
