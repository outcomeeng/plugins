"""Level 1 conformance evidence for gate summary JSON shape."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import cast

import pytest

from outcomeeng.validation import (
    AD_HOC_SUMMARY_SCHEMA,
    CHECK_SUMMARY_SCHEMA,
    GATE_SUMMARY_SCHEMA,
    PHASE_PREFLIGHT,
    PRIMITIVE_SUMMARY_SCHEMA,
    PURPOSE_CONFORMANCE,
    RECIPE_AD_HOC,
    RECIPE_VALIDATION,
    SUMMARY_KEY_SUMMARY_PATH,
    SUMMARY_PATH_LABEL,
    VERIFICATION_TYPE_VALIDATION,
    Recipe,
    Step,
    assert_json_schema,
    run,
    run_check,
    run_recipe,
)
from outcomeeng_testing.harnesses.gate import RecordingSpawner

PASS = 0
FAIL = 2
FAILING_OUTPUT = "failure detail"


def _recipe() -> Recipe:
    return Recipe(
        name=RECIPE_VALIDATION,
        verification_type=VERIFICATION_TYPE_VALIDATION,
        purpose=PURPOSE_CONFORMANCE,
        preflight_steps=(Step(label="preflight", argv=("preflight",)),),
        steps=(Step(label="validate", argv=("validate",)),),
    )


def _read_summary(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_check_summary_conforms_to_schema_for_primitive_and_wrapper(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "summary.json"
    recipe = _recipe()
    spawner = RecordingSpawner(exit_codes=[PASS, PASS])
    sink = io.StringIO()

    exit_code = run_check(
        spawner=spawner,
        sink=sink,
        recipes=(recipe,),
        summary_path=summary_path,
    )

    raw_summary = _read_summary(summary_path)
    assert isinstance(raw_summary, dict)
    summary = cast(dict[str, object], raw_summary)
    assert_json_schema(summary, CHECK_SUMMARY_SCHEMA)
    assert exit_code == PASS


def test_failed_primitive_summary_conforms_to_schema(tmp_path: Path) -> None:
    summary_path = tmp_path / "failure-summary.json"
    recipe = _recipe()
    spawner = RecordingSpawner(
        exit_codes=[PASS, FAIL],
        outputs=["", FAILING_OUTPUT],
    )
    sink = io.StringIO()

    exit_code = run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=recipe,
        summary_path=summary_path,
    )

    raw_summary = _read_summary(summary_path)
    assert isinstance(raw_summary, dict)
    summary = cast(dict[str, object], raw_summary)
    assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert exit_code == FAIL


def test_ad_hoc_run_summary_conforms_to_gate_schema(tmp_path: Path) -> None:
    spawner = RecordingSpawner(exit_codes=[PASS])
    sink = io.StringIO()

    exit_code = run(
        spawner=spawner,
        sink=sink,
        steps=(Step(label="ad-hoc-step", argv=("ad-hoc-step",)),),
    )

    summary_path = Path(sink.getvalue().split(f"{SUMMARY_PATH_LABEL} ")[1].strip())
    raw_summary = _read_summary(summary_path)
    assert isinstance(raw_summary, dict)
    summary = cast(dict[str, object], raw_summary)
    assert_json_schema(summary, AD_HOC_SUMMARY_SCHEMA)
    assert_json_schema(summary, GATE_SUMMARY_SCHEMA)
    assert summary["recipe"] == RECIPE_AD_HOC
    assert exit_code == PASS


def test_primitive_summary_schema_requires_summary_path(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary-path-required.json"
    recipe = _recipe()
    spawner = RecordingSpawner(exit_codes=[PASS, PASS])
    sink = io.StringIO()

    exit_code = run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=recipe,
        summary_path=summary_path,
    )

    raw_summary = _read_summary(summary_path)
    assert isinstance(raw_summary, dict)
    summary = cast(dict[str, object], raw_summary)
    summary.pop(SUMMARY_KEY_SUMMARY_PATH)
    with pytest.raises(AssertionError, match=SUMMARY_KEY_SUMMARY_PATH):
        assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert exit_code == PASS


def test_failed_preflight_primitive_summary_conforms_to_schema(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "preflight-failure-summary.json"
    recipe = _recipe()
    spawner = RecordingSpawner(
        exit_codes=[FAIL],
        outputs=[FAILING_OUTPUT],
    )
    sink = io.StringIO()

    exit_code = run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=recipe,
        summary_path=summary_path,
    )

    raw_summary = _read_summary(summary_path)
    assert isinstance(raw_summary, dict)
    summary = cast(dict[str, object], raw_summary)
    assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert summary["phase"] == PHASE_PREFLIGHT
    assert exit_code == FAIL


def test_failed_preflight_wrapper_summary_conforms_to_schema(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "preflight-wrapper-summary.json"
    recipe = _recipe()
    spawner = RecordingSpawner(
        exit_codes=[FAIL],
        outputs=[FAILING_OUTPUT],
    )
    sink = io.StringIO()

    exit_code = run_check(
        spawner=spawner,
        sink=sink,
        recipes=(recipe,),
        summary_path=summary_path,
    )

    raw_summary = _read_summary(summary_path)
    assert isinstance(raw_summary, dict)
    summary = cast(dict[str, object], raw_summary)
    assert_json_schema(summary, CHECK_SUMMARY_SCHEMA)
    assert summary["phase"] == PHASE_PREFLIGHT
    assert exit_code == FAIL
