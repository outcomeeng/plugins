"""Mapping evidence: a language block renders exactly when the language is enabled.

Over the languages the template defines blocks for (``TEMPLATE_LANGUAGES``),
parametrize every enabled subset and assert each language's heading is present in the
rendered instruction block iff that language is in the enabled set. The expected output
is derived from the input subset, not hand-picked.
"""

from __future__ import annotations

import itertools
import pathlib

import pytest

from outcomeeng_testing.harnesses.instruction_block import (
    HARNESS_CLAUDE,
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_VERSION,
    OLD_VERSION,
    TEMPLATE_LANGUAGES,
    build_template,
    load_instruction_block_module,
    write_both_instruction_files,
    write_spx_tree_with_tests,
    write_template,
)


def _all_language_subsets() -> list[tuple[str, ...]]:
    subsets: list[tuple[str, ...]] = []
    for size in range(len(TEMPLATE_LANGUAGES) + 1):
        subsets.extend(itertools.combinations(TEMPLATE_LANGUAGES, size))
    return subsets


@pytest.mark.parametrize("enabled", _all_language_subsets())
def test_language_block_present_iff_enabled(enabled: tuple[str, ...]) -> None:
    module = load_instruction_block_module()
    rendered = module.render(
        build_template(NEW_VERSION), enabled, NEW_VERSION, HARNESS_CLAUDE
    )
    for language in TEMPLATE_LANGUAGES:
        heading = f"### {language.capitalize()}"
        assert (heading in rendered) is (language in enabled)


def test_each_test_extension_maps_to_its_language() -> None:
    module = load_instruction_block_module()
    for extension, language in module.LANGUAGE_BY_EXTENSION.items():
        assert module.language_for_extension(extension) == language
        assert module.language_for_extension(f".{extension}") == language
        assert module.detect_languages((extension,)) == (language,)


def test_detected_language_set_is_the_mapped_extensions() -> None:
    module = load_instruction_block_module()
    all_extensions = tuple(module.LANGUAGE_BY_EXTENSION)
    expected = tuple(sorted(set(module.LANGUAGE_BY_EXTENSION.values())))
    assert module.detect_languages(all_extensions) == expected
    # An extension with no language mapping contributes nothing.
    assert module.detect_languages(("md", "txt")) == ()


def test_each_fixed_slot_name_maps_to_its_recognized_fence() -> None:
    module = load_instruction_block_module()
    scaffolded = module.ensure_slot_fences("")
    # Every fixed slot name maps to a recognized slot fence — the module's own source-owned
    # `slot_open_marker`, never a fence format re-spelled here.
    present = tuple(
        slot
        for slot in module.FIXED_COMMAND_SLOTS
        if module.parse_command_slot(scaffolded, slot) is not None
    )
    assert present == module.FIXED_COMMAND_SLOTS
    for slot in module.FIXED_COMMAND_SLOTS:
        assert module.slot_open_marker(slot) in scaffolded


def test_a_name_outside_the_fixed_slot_set_maps_to_no_recognized_slot() -> None:
    module = load_instruction_block_module()
    scaffolded = module.ensure_slot_fences("")
    outsiders = tuple(
        name
        for name in ("deploy", "release", "spec", "test")
        if name not in module.FIXED_COMMAND_SLOTS
    )
    for name in outsiders:
        assert module.parse_command_slot(scaffolded, name) is None


@pytest.mark.parametrize(
    ("state", "check_languages", "expected"),
    [
        ("missing", LANG_PRIMARY, "absent"),
        ("version-behind", LANG_PRIMARY, "stale"),
        ("version-current", LANG_PRIMARY, "current"),
        ("language-mismatch", f"{LANG_PRIMARY},{LANG_SECONDARY}", "stale"),
    ],
)
def test_check_maps_router_block_state_to_report(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    state: str,
    check_languages: str,
    expected: str,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    if state == "version-behind":
        write_both_instruction_files(module, tmp_path, (LANG_PRIMARY,), OLD_VERSION)
    elif state in ("version-current", "language-mismatch"):
        write_both_instruction_files(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    # "missing": neither root file is written, so no router block exists.
    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(tmp_path),
            "--check",
            "--languages",
            check_languages,
        ]
    )
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == expected


def test_check_treats_the_recorded_language_set_order_insensitively(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    write_both_instruction_files(
        module, tmp_path, (LANG_SECONDARY, LANG_PRIMARY), NEW_VERSION
    )
    base = ["--template", str(template), "--repo-root", str(tmp_path), "--check"]

    # Recorded set {secondary, primary} equals the supplied set regardless of order -> current.
    assert module.main([*base, "--languages", f"{LANG_PRIMARY},{LANG_SECONDARY}"]) == 0
    assert capsys.readouterr().out.strip() == "current"


def test_check_maps_detected_tree_language_drift_to_stale(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    write_both_instruction_files(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    extensions = tuple(
        next(ext for ext, lang in module.LANGUAGE_BY_EXTENSION.items() if lang == want)
        for want in (LANG_PRIMARY, LANG_SECONDARY)
    )
    write_spx_tree_with_tests(tmp_path / "spx", extensions)

    # No --languages: the check detects {primary, secondary} from the tree, differing from the
    # recorded {primary} -> stale.
    assert (
        module.main(
            ["--template", str(template), "--repo-root", str(tmp_path), "--check"]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"
