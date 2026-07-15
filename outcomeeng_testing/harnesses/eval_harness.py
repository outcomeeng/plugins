"""Evidence harness for eval case loading, grading, and suite execution."""

from __future__ import annotations

import json
import subprocess
import time
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

import pytest

from outcomeeng_evals.case import (
    CASE_ID_FIELD,
    CASE_INPUT_FIELD,
    EXPECTED_VERDICT_FIELD,
    MAX_EXPECTED_LIST_LENGTH,
    MUST_CONTAIN_FIELD,
    MUST_NOT_CONTAIN_FIELD,
    Case,
    load_cases,
)
from outcomeeng_evals.cli.commands.run import _render_prompt
from outcomeeng_evals.grader import grade, is_subset, parse_verdict
from outcomeeng_evals.runner import DEFAULT_CLAUDE_BINARY, RunResult
from outcomeeng_evals.settings import DEFAULT_TIMEOUT_SECONDS
from outcomeeng_evals.suite import TIMEOUT_ERROR_PREFIX, run_suite
from outcomeeng_testing.evals.fakes import (
    ConcurrencyTrackingRunner,
    RaisingModelRunner,
    StubModelRunner,
)
from outcomeeng_testing.generators.evals import expected_list_boundary_record

_FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures/evals"


def assert_case_loader_matches_complete_fixture() -> None:
    fixture_path = _fixture_path("eval_case_valid.jsonl")
    with fixture_path.open(encoding="utf-8") as fixture_file:
        record = json.load(fixture_file)

    cases = load_cases(fixture_path)

    assert len(cases) == 1
    case = cases[0]
    expected_verdict = record[EXPECTED_VERDICT_FIELD]
    assert case.id == record[CASE_ID_FIELD]
    assert case.input == record[CASE_INPUT_FIELD]
    assert case.must_contain == tuple(expected_verdict[MUST_CONTAIN_FIELD])
    assert case.must_not_contain == tuple(expected_verdict[MUST_NOT_CONTAIN_FIELD])


def assert_case_loader_rejects_invalid_complete_fixtures() -> None:
    for fixture_name in (
        "eval_case_missing_id.jsonl",
        "eval_case_blank_id.jsonl",
    ):
        with pytest.raises(ValueError):
            load_cases(_fixture_path(fixture_name))


def assert_case_loader_enforces_expected_list_boundary() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "cases.jsonl"
        _write_jsonl_record(path, expected_list_boundary_record(over_limit=False))
        case = load_cases(path)[0]
        assert len(case.must_contain[0]["findings"]) == MAX_EXPECTED_LIST_LENGTH

        _write_jsonl_record(path, expected_list_boundary_record(over_limit=True))
        with pytest.raises(ValueError):
            load_cases(path)


def assert_verdict_parser_matches_complete_response_fixtures() -> None:
    expected_path = _fixture_path("verdict_rejected.json")
    with expected_path.open(encoding="utf-8") as expected_file:
        expected = json.load(expected_file)

    assert parse_verdict(expected_path.read_text(encoding="utf-8")) == expected
    assert (
        parse_verdict(_fixture_path("verdict_fenced.md").read_text(encoding="utf-8"))
        == expected
    )
    assert (
        parse_verdict(
            _fixture_path("verdict_fenced_untagged.md").read_text(encoding="utf-8")
        )
        == expected
    )
    assert (
        parse_verdict(_fixture_path("verdict_invalid.txt").read_text(encoding="utf-8"))
        is None
    )


def assert_subset_matching_follows_fixture_matrix() -> None:
    with _fixture_path("subset_cases.json").open(encoding="utf-8") as fixture_file:
        cases = json.load(fixture_file)

    for case in cases:
        assert is_subset(case["expected"], case["actual"]) is case["matches"]


def assert_grader_uses_fixture_expectations() -> None:
    case = load_cases(_fixture_path("eval_case_valid.jsonl"))[0]
    rejected = _fixture_path("verdict_rejected.json").read_text(encoding="utf-8")
    approved = _fixture_path("verdict_approved.json").read_text(encoding="utf-8")
    invalid = _fixture_path("verdict_invalid.txt").read_text(encoding="utf-8")

    assert grade(case, rejected).passed
    assert not grade(case, approved).passed
    assert not grade(case, invalid).passed


def assert_suite_replays_fixture_cases_and_bounds_trials() -> None:
    case_path = _fixture_path("eval_case_valid.jsonl")
    responses = _response_sequences()
    majority = iter(responses["majority"])
    result = run_suite(
        cases_path=case_path,
        runner=StubModelRunner(responder=lambda _prompt: next(majority)),
        build_prompt=_fixture_prompt,
        trials_per_case=len(responses["majority"]),
    )

    assert result.passed
    assert result.outcomes[0].trial_pass_count == sum(
        parse_verdict(response) is not None for response in responses["majority"]
    )

    below_majority = iter(responses["below_majority"])
    result = run_suite(
        cases_path=case_path,
        runner=StubModelRunner(responder=lambda _prompt: next(below_majority)),
        build_prompt=_fixture_prompt,
        trials_per_case=len(responses["below_majority"]),
    )
    assert not result.outcomes[0].passed

    half_passed = iter(responses["half_passed"])
    result = run_suite(
        cases_path=case_path,
        runner=StubModelRunner(responder=lambda _prompt: next(half_passed)),
        build_prompt=_fixture_prompt,
        trials_per_case=len(responses["half_passed"]),
    )
    assert result.outcomes[0].trial_pass_rate == pytest.approx(
        sum(
            parse_verdict(response) is not None for response in responses["half_passed"]
        )
        / len(responses["half_passed"])
    )


def assert_parallel_suite_preserves_fixture_case_order() -> None:
    cases_path = _fixture_path("eval_suite_cases.jsonl")
    cases = load_cases(cases_path)
    response = _fixture_path("verdict_rejected.json").read_text(encoding="utf-8")
    finish_order: list[str] = []
    lock = Lock()

    def responder(prompt: str) -> str:
        payload = json.loads(prompt)
        index = payload["index"]
        time.sleep(0.001 * (len(cases) - index))
        with lock:
            finish_order.append(cases[index].id)
        return response

    result = run_suite(
        cases_path=cases_path,
        runner=StubModelRunner(responder=responder),
        build_prompt=lambda case: json.dumps(case.input),
        workers=len(cases),
    )

    case_order = [case.id for case in cases]
    assert [outcome.case.id for outcome in result.outcomes] == case_order
    assert finish_order != case_order

    with _fixture_path("parallel_execution.json").open(
        encoding="utf-8"
    ) as fixture_file:
        parallel_config = json.load(fixture_file)
    tracking_runner = ConcurrencyTrackingRunner(
        result=RunResult(text=response),
        delay_seconds=parallel_config["delay_seconds"],
    )
    run_suite(
        cases_path=cases_path,
        runner=tracking_runner,
        build_prompt=_fixture_prompt,
        workers=parallel_config["workers"],
    )
    assert tracking_runner.max_active_calls > 1
    assert tracking_runner.max_active_calls <= parallel_config["workers"]


def assert_prompt_renderer_reports_fixture_placeholder_drift() -> None:
    case = load_cases(_fixture_path("eval_case_valid.jsonl"))[0]
    collision_case = load_cases(_fixture_path("eval_case_placeholder_collision.jsonl"))[
        0
    ]

    unknown_stderr = StringIO()
    with redirect_stderr(unknown_stderr):
        unknown_rendered = _render_prompt(
            _fixture_path("prompt_unknown_placeholder.md").read_text(encoding="utf-8"),
            case,
        )
    known_stderr = StringIO()
    with redirect_stderr(known_stderr):
        known_rendered = _render_prompt(
            _fixture_path("prompt_known_placeholders.md").read_text(encoding="utf-8"),
            collision_case,
        )

    assert unknown_rendered == _fixture_path("prompt_unknown_rendered.md").read_text(
        encoding="utf-8"
    )
    assert known_rendered == _fixture_path("prompt_known_rendered.txt").read_text(
        encoding="utf-8"
    )
    assert unknown_stderr.getvalue()
    assert not known_stderr.getvalue()


def assert_suite_isolates_runner_failures() -> None:
    cases_path = _fixture_path("eval_suite_cases.jsonl")
    errors = (
        RuntimeError(
            _fixture_path("verdict_invalid.txt").read_text(encoding="utf-8").strip()
        ),
        subprocess.TimeoutExpired(
            cmd=DEFAULT_CLAUDE_BINARY,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        ),
    )

    for error in errors:
        for workers in (1, len(load_cases(cases_path))):
            result = run_suite(
                cases_path=cases_path,
                runner=RaisingModelRunner(error=error),
                build_prompt=_fixture_prompt,
                workers=workers,
            )
            assert not result.passed
            assert all(not outcome.passed for outcome in result.outcomes)
            reasons = [
                reason
                for outcome in result.outcomes
                for trial in outcome.trials
                for reason in trial.grade.reasons
            ]
            if isinstance(error, subprocess.TimeoutExpired):
                assert all(
                    reason.startswith(TIMEOUT_ERROR_PREFIX) for reason in reasons
                )


def assert_suite_rejects_empty_case_file() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "cases.jsonl"
        path.touch()
        with pytest.raises(ValueError):
            run_suite(
                cases_path=path,
                runner=StubModelRunner(),
                build_prompt=_fixture_prompt,
            )


def _response_sequences() -> dict[str, tuple[str, ...]]:
    with _fixture_path("suite_response_sequences.json").open(
        encoding="utf-8"
    ) as fixture_file:
        paths = json.load(fixture_file)
    return {
        name: tuple(
            _fixture_path(filename).read_text(encoding="utf-8")
            for filename in filenames
        )
        for name, filenames in paths.items()
    }


def _fixture_prompt(case: Case) -> str:
    return json.dumps(case.input)


def _fixture_path(name: str) -> Path:
    return _FIXTURE_ROOT / name


def _write_jsonl_record(path: Path, record: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as output:
        json.dump(record, output)
        output.write("\n")
