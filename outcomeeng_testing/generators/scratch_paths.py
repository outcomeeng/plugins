"""Generated scratch-path categories for fixed-temporary-path evidence."""

from __future__ import annotations

from outcomeeng.validation.scratch_paths import (
    ABSOLUTE_TEMPORARY_ROOTS,
    ENVIRONMENT_TEMPORARY_ROOTS,
    HOME_TEMPORARY_ROOTS,
    PORTABLE_SCRATCH_SOURCES,
)
from outcomeeng_testing.generators.source_and_templating import source_scenarios


def fixed_temporary_paths() -> tuple[str, ...]:
    """Compose one variable reference for every prohibited scratch category."""
    scenario = source_scenarios()[0]
    bare_roots = ABSOLUTE_TEMPORARY_ROOTS
    absolute_with_child = tuple(
        f"{root}/{scenario.plugin}-{scenario.skill}.txt"
        for root in ABSOLUTE_TEMPORARY_ROOTS
    )
    home_relative = tuple(
        f"{root}/{scenario.skill}.log" for root in HOME_TEMPORARY_ROOTS
    )
    # A shell parameter-expansion fallback reintroduces the literal the rule
    # removes, so it is prohibited rather than treated as a portable idiom.
    expansion_fallback = f'dir="${{TMPDIR:-{ABSOLUTE_TEMPORARY_ROOTS[0]}}}"'
    # A redirect target and a flag value are the two shapes shipped content
    # uses most, and neither is preceded by whitespace.
    redirect_target = f"2>{ABSOLUTE_TEMPORARY_ROOTS[0]}/{scenario.skill}.err"
    flag_value = f"--destination={ABSOLUTE_TEMPORARY_ROOTS[0]}/{scenario.outer_topic}"
    # A fixed segment under the environment's own root resolves to one path for
    # every invocation in that environment, so it collides exactly as the same
    # segment under an absolute root does.
    environment_root_child = tuple(
        f'socket="{root}/{scenario.plugin}.sock"'
        for root in ENVIRONMENT_TEMPORARY_ROOTS
    )
    return (
        *bare_roots,
        *absolute_with_child,
        *home_relative,
        expansion_fallback,
        redirect_target,
        flag_value,
        *environment_root_child,
    )


def portable_scratch_sources() -> tuple[str, ...]:
    """Compose variable references for every allowed scratch category."""
    scenario = source_scenarios()[0]
    unique_per_invocation = tuple(
        f"{source} for {scenario.skill}" for source in PORTABLE_SCRATCH_SOURCES
    )
    # The root itself, and nothing appended to it: the root resolves per
    # environment, so naming it collides with nothing.
    environment_root = tuple(f'dir="{root}"' for root in ENVIRONMENT_TEMPORARY_ROOTS)
    # Paths whose final segment merely ends in the prohibited token, and
    # identifiers that contain it, are not fixed temporary paths.
    near_misses = (
        "/tmpfs",
        f"/opt/tmp/{scenario.skill}",
        f"{scenario.plugin}_tmp/{scenario.skill}",
        "tmp_path",
        "tempfile::tempdir()?",
        # The doubled slash after a URL scheme names a host, not a path root.
        f"https://tmp.{scenario.plugin}.example.com/{scenario.skill}",
    )
    return (*unique_per_invocation, *environment_root, *near_misses)
