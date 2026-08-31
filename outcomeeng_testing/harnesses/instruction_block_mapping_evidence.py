"""Mapping observations for the instruction-block render model.

Each function here drives one finite, source-owned domain member through the generator and
returns what it produced. None of them decides anything: the linked mapping test owns every
predicate, so inverting a mapping changes that test and nothing in this module. The domains
themselves come from the generator's own constants, so the test file owns no boundary values.
"""

from __future__ import annotations

import pathlib
from contextlib import redirect_stderr
from dataclasses import dataclass
from io import StringIO

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


@dataclass(frozen=True)
class DuplicateFlagObservation:
    """What one repeated CLI flag produced: the detected option, exit code, and stderr."""

    detected: str | None
    exit_code: int
    stderr: str


@dataclass(frozen=True)
class LanguageBlockObservation:
    """One language's heading beside the documents rendered with and without that language."""

    heading: str
    enabled: str
    disabled: str


@dataclass(frozen=True)
class SpanRatioObservation:
    """One body pair's biggest identical span, its ratio, and the wrap it produced."""

    span: str
    ratio: float
    wrapped_regions: tuple[dict[str, str], dict[str, str]]


@dataclass(frozen=True)
class RouterStateObservation:
    """Source facts and the report observed for one router-block state."""

    name: str
    block_present: bool
    installed_version: str
    block_version: str | None
    recorded_languages: tuple[str, ...]
    detected_languages: tuple[str, ...]
    exit_code: int
    report: str


@dataclass(frozen=True)
class SharedRegionStateObservation:
    """Source region facts and the report observed for one shared-region state."""

    name: str
    claude_region: str | None
    agents_region: str | None
    exit_code: int
    report: str


def observe_duplicate_cli_flag(option: str) -> DuplicateFlagObservation:
    """Run the CLI with ``option`` repeated and report what it detected and printed."""
    with redirect_stderr(StringIO()) as stderr:
        exit_code = MODULE.main([option, option])
    return DuplicateFlagObservation(
        detected=MODULE.duplicate_cli_option((option, option)),
        exit_code=exit_code,
        stderr=stderr.getvalue().strip(),
    )


def observe_extension_language(extension: str) -> tuple[str | None, str | None]:
    """Report the language the bare and dotted spellings of ``extension`` each denote."""
    return (
        MODULE.language_for_extension(extension),
        MODULE.language_for_extension(f".{extension}"),
    )


def observe_detected_language_set(
    spx_dir: pathlib.Path,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Write one test file per known extension, then report the detected and mapped sets."""
    extensions = tuple(MODULE.LANGUAGE_BY_EXTENSION)
    harness.write_spx_tree_with_tests(spx_dir, extensions)
    return (
        MODULE.detect_languages_from_tree(spx_dir),
        MODULE.normalize_languages(MODULE.LANGUAGE_BY_EXTENSION.values()),
    )


def observe_language_block(language: str) -> LanguageBlockObservation:
    """Render the router block with ``language`` enabled and with every other language."""
    template = harness.build_template(harness.NEW_VERSION)
    others = tuple(name for name in harness.TEMPLATE_LANGUAGES if name != language)
    return LanguageBlockObservation(
        heading=f"### {language.capitalize()}",
        enabled=MODULE.render(
            template, (language,), harness.NEW_VERSION, harness.HARNESS_CLAUDE
        ),
        disabled=MODULE.render(
            template, others, harness.NEW_VERSION, harness.HARNESS_CLAUDE
        ),
    )


def observe_check_router_states(
    tmp_path: pathlib.Path,
) -> tuple[RouterStateObservation, ...]:
    """Drive the router block through each recognized state; report `--check` per state."""
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)
    claude = repo / harness.INSTRUCTION_CLAUDE
    observed: list[RouterStateObservation] = []

    # freshly written at the installed version and language
    exit_code, report = harness.run_generator_check(repo, template)
    observed.append(
        RouterStateObservation(
            name="current",
            block_present=True,
            installed_version=harness.NEW_VERSION,
            block_version=harness.NEW_VERSION,
            recorded_languages=(harness.LANG_PRIMARY,),
            detected_languages=(harness.LANG_PRIMARY,),
            exit_code=exit_code,
            report=report,
        )
    )

    claude.unlink()
    exit_code, report = harness.run_generator_check(repo, template)
    observed.append(
        RouterStateObservation(
            name="absent",
            block_present=False,
            installed_version=harness.NEW_VERSION,
            block_version=None,
            recorded_languages=(),
            detected_languages=(harness.LANG_PRIMARY,),
            exit_code=exit_code,
            report=report,
        )
    )

    # a version numerically behind the installed one
    stale_block = MODULE.render(
        harness.build_template(harness.OLD_VERSION),
        (harness.LANG_PRIMARY,),
        harness.OLD_VERSION,
        harness.HARNESS_CLAUDE,
    )
    claude.write_text(MODULE.prepend_router_block(stale_block, ""), encoding="utf-8")
    exit_code, report = harness.run_generator_check(repo, template)
    observed.append(
        RouterStateObservation(
            name="version-behind",
            block_present=True,
            installed_version=harness.NEW_VERSION,
            block_version=harness.OLD_VERSION,
            recorded_languages=(harness.LANG_PRIMARY,),
            detected_languages=(harness.LANG_PRIMARY,),
            exit_code=exit_code,
            report=report,
        )
    )

    # the recorded language set differs from the detected/expected set
    current_block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    claude.write_text(MODULE.prepend_router_block(current_block, ""), encoding="utf-8")
    exit_code, report = harness.run_generator_check(
        repo, template, languages=harness.LANG_SECONDARY
    )
    observed.append(
        RouterStateObservation(
            name="language-set-differs",
            block_present=True,
            installed_version=harness.NEW_VERSION,
            block_version=harness.NEW_VERSION,
            recorded_languages=(harness.LANG_PRIMARY,),
            detected_languages=(harness.LANG_SECONDARY,),
            exit_code=exit_code,
            report=report,
        )
    )
    return tuple(observed)


def observe_check_shared_region_states(
    tmp_path: pathlib.Path,
) -> tuple[SharedRegionStateObservation, ...]:
    """Drive a `shared` region through each recognized state; report `--check` per state."""
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    observed: list[SharedRegionStateObservation] = []

    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    exit_code, report = harness.run_generator_check(repo, template)
    observed.append(
        SharedRegionStateObservation(
            name="byte-identical",
            claude_region=harness.SHARED_REGION_BODY,
            agents_region=harness.SHARED_REGION_BODY,
            exit_code=exit_code,
            report=report,
        )
    )

    harness.write_both_root_files_with_shared_region(
        MODULE,
        repo,
        languages=(harness.LANG_PRIMARY,),
        version=harness.NEW_VERSION,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
    )
    exit_code, report = harness.run_generator_check(repo, template)
    observed.append(
        SharedRegionStateObservation(
            name="diverged",
            claude_region=harness.SHARED_REGION_BODY,
            agents_region=harness.SHARED_REGION_BODY_ALT,
            exit_code=exit_code,
            report=report,
        )
    )

    codex_block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CODEX,
    )
    (repo / harness.INSTRUCTION_AGENTS).write_text(
        MODULE.prepend_router_block(codex_block, harness.ROOT_AGENTS_BODY),
        encoding="utf-8",
    )
    exit_code, report = harness.run_generator_check(repo, template)
    observed.append(
        SharedRegionStateObservation(
            name="one-sided",
            claude_region=harness.SHARED_REGION_BODY,
            agents_region=None,
            exit_code=exit_code,
            report=report,
        )
    )
    return tuple(observed)


def observe_span_ratio(body_a: str, body_b: str) -> SpanRatioObservation:
    """Report the biggest identical span of two bodies and the regions a wrap produced."""
    span, ratio = MODULE.biggest_identical_span(body_a, body_b)
    wrapped_a, wrapped_b = MODULE.bootstrap_wrap(body_a, body_b)
    return SpanRatioObservation(
        span=span,
        ratio=ratio,
        wrapped_regions=(
            MODULE.parse_shared_regions(wrapped_a),
            MODULE.parse_shared_regions(wrapped_b),
        ),
    )
