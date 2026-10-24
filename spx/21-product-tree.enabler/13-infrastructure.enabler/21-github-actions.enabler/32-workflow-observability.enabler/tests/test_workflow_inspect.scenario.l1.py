"""Scenario evidence for the `workflow_inspect.py` subcommands over recorded `gh` output."""

from __future__ import annotations

import json
import sys

from outcomeeng_testing.harnesses.workflow_inspect import (
    HANGING_COMMAND,
    SCRIPT_NAME,
    GhReply,
    fixture_json,
    fixture_text,
    run_cli,
    run_real_runner,
    run_script_process,
)

SUBCOMMANDS = (
    "runs",
    "run",
    "jobs",
    "log",
    "checks",
    "artifacts",
    "workflow-files",
)


def test_runs_returns_recorded_list_and_passes_branch_and_limit() -> None:
    sample = fixture_json("runs_list.json")

    observed = run_cli(
        ["runs", "--branch", "feature", "--limit", "5"],
        GhReply(0, fixture_text("runs_list.json")),
    )

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["runs"] == sample
    assert payload["error"] is None
    assert payload["schema_version"] == 1
    assert len(observed.gh_calls) == 1
    call = observed.gh_calls[0]
    assert call[:3] == ("gh", "run", "list")
    assert call[call.index("--limit") + 1] == "5"
    assert call[call.index("--branch") + 1] == "feature"


def test_runs_omits_branch_filter_when_none_given() -> None:
    observed = run_cli(["runs"], GhReply(0, fixture_text("runs_list.json")))

    assert observed.exit_code == 0
    assert "--branch" not in observed.gh_calls[0]


def test_run_projects_run_fields_and_per_job_fields() -> None:
    sample = fixture_json("run_view.json")

    observed = run_cli(["run", "9001"], GhReply(0, fixture_text("run_view.json")))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["error"] is None
    for field in (
        "databaseId",
        "status",
        "conclusion",
        "workflowName",
        "headBranch",
        "headSha",
        "createdAt",
    ):
        assert payload[field] == sample[field]
    assert payload["jobs"] == [
        {
            "databaseId": job["databaseId"],
            "name": job["name"],
            "status": job["status"],
            "conclusion": job["conclusion"],
        }
        for job in sample["jobs"]
    ]
    assert observed.gh_calls[0][:4] == ("gh", "run", "view", "9001")


def test_jobs_projects_per_job_fields_with_timestamps() -> None:
    sample = fixture_json("run_view.json")

    observed = run_cli(["jobs", "9001"], GhReply(0, fixture_text("run_view.json")))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["error"] is None
    assert payload["jobs"] == [
        {
            "databaseId": job["databaseId"],
            "name": job["name"],
            "status": job["status"],
            "conclusion": job["conclusion"],
            "startedAt": job["startedAt"],
            "completedAt": job["completedAt"],
        }
        for job in sample["jobs"]
    ]


def test_log_returns_whole_log_verbatim_and_requests_full_log() -> None:
    log_text = "step one\n  indented line\r\n\ttabbed\n\n"

    observed = run_cli(["log", "9001"], GhReply(0, log_text))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["log"] == log_text
    assert payload["byte_count"] == len(log_text.encode("utf-8"))
    assert payload["truncated"] is False
    assert payload["failed_only"] is False
    assert payload["error"] is None
    assert observed.gh_calls == (("gh", "run", "view", "9001", "--log"),)


def test_log_failed_flag_requests_failed_step_log() -> None:
    observed = run_cli(["log", "9001", "--failed"], GhReply(0, "boom\n"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["failed_only"] is True
    assert observed.gh_calls == (("gh", "run", "view", "9001", "--log-failed"),)


def test_log_keeps_the_tail_when_the_log_exceeds_max_bytes() -> None:
    observed = run_cli(["log", "9001", "--max-bytes", "4"], GhReply(0, "head-tail"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["log"] == "tail"
    assert payload["byte_count"] == 9
    assert payload["truncated"] is True


def test_log_at_exactly_max_bytes_is_not_truncated() -> None:
    observed = run_cli(["log", "9001", "--max-bytes", "9"], GhReply(0, "head-tail"))

    payload = json.loads(observed.stdout)
    assert payload["log"] == "head-tail"
    assert payload["truncated"] is False


def test_log_one_byte_over_max_bytes_is_truncated_by_one_byte() -> None:
    observed = run_cli(["log", "9001", "--max-bytes", "8"], GhReply(0, "head-tail"))

    payload = json.loads(observed.stdout)
    assert payload["log"] == "ead-tail"
    assert payload["truncated"] is True


def test_log_truncation_inside_a_multibyte_character_yields_replacement_text() -> None:
    observed = run_cli(["log", "9001", "--max-bytes", "2"], GhReply(0, "é-"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["truncated"] is True
    assert payload["byte_count"] == 3
    assert payload["log"].endswith("-")
    assert "�" in payload["log"]


def test_checks_returns_number_branch_and_rollup_only() -> None:
    sample = fixture_json("pr_view.json")

    observed = run_cli(["checks", "42"], GhReply(0, fixture_text("pr_view.json")))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["number"] == sample["number"]
    assert payload["headRefName"] == sample["headRefName"]
    assert payload["statusCheckRollup"] == sample["statusCheckRollup"]
    assert "title" not in payload
    assert payload["error"] is None
    assert observed.gh_calls[0][:4] == ("gh", "pr", "view", "42")


def test_artifacts_lists_recorded_artifacts_and_requests_no_download_url() -> None:
    sample = fixture_json("artifacts.json")

    observed = run_cli(
        ["artifacts", "9001"], GhReply(0, fixture_text("artifacts.json"))
    )

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["artifacts"] == sample["artifacts"]
    assert payload["error"] is None
    command = observed.gh_calls[0]
    assert command[:2] == ("gh", "api")
    assert "archive_download_url" not in " ".join(command)


def test_workflow_files_returns_recorded_workflow_definitions() -> None:
    sample = fixture_json("workflow_list.json")

    observed = run_cli(
        ["workflow-files"], GhReply(0, fixture_text("workflow_list.json"))
    )

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["workflows"] == sample
    assert payload["error"] is None
    assert observed.gh_calls[0][:3] == ("gh", "workflow", "list")


def test_gh_timeout_exit_reports_a_timeout_with_its_own_next_action() -> None:
    observed = run_cli(
        ["run", "9001"], GhReply(124, "", "subprocess timed out after 60s: gh run view")
    )

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["error"] == (
        "run 9001: gh run view exited 124: subprocess timed out after 60s: gh run view. "
        "Next: retry once; if it times out again, narrow the request or check network access."
    )


def test_gh_failure_without_diagnostics_reports_no_output() -> None:
    observed = run_cli(["workflow-files"], GhReply(1, ""))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["workflows"] == []
    assert payload["error"] == (
        "workflow-files: gh workflow list exited 1: no output. "
        "Next: run python3 gh_access.py to check gh authentication and repository access, then retry."
    )


def test_log_gh_failure_names_the_log_flag_in_the_gh_subcommand() -> None:
    observed = run_cli(["log", "9001", "--failed"], GhReply(1, "", "run not found"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["log"] == ""
    assert payload["truncated"] is False
    assert payload["error"] == (
        "log 9001: gh run view --log-failed exited 1: run not found. "
        "Next: run python3 gh_access.py to check gh authentication and repository access, then retry."
    )


def test_gh_output_that_is_not_json_reports_the_decoder_message() -> None:
    observed = run_cli(["jobs", "9001"], GhReply(0, "<html>not json</html>"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["jobs"] == []
    assert payload["error"].startswith(
        "jobs 9001: gh run view returned output that is not JSON ("
    )
    assert payload["error"].endswith(
        "). Next: run python3 gh_access.py to check the gh version and authentication, then retry."
    )


def test_run_wrong_shape_names_the_run_and_the_next_action() -> None:
    observed = run_cli(["run", "9001"], GhReply(0, "[1, 2]"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["error"] == (
        "run 9001: gh run view returned no run object. "
        "Next: confirm the run id with `workflow_inspect.py runs`."
    )


def test_real_runner_returns_exit_code_stdout_verbatim_and_stripped_stderr() -> None:
    code, out, err = run_real_runner(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('  out\\n'); sys.stderr.write('  err  \\n'); sys.exit(3)",
        ]
    )

    assert code == 3
    assert out == "  out\n"
    assert err == "err"


def test_real_runner_reports_a_hung_child_as_exit_124_naming_the_command() -> None:
    code, out, err = run_real_runner(HANGING_COMMAND)

    assert code == 124
    assert out == ""
    assert err.startswith("subprocess timed out after ")
    assert " ".join(HANGING_COMMAND) in err


def test_help_lists_the_seven_subcommands_without_calling_gh() -> None:
    observed = run_script_process(["--help"])

    assert observed.exit_code == 0
    for subcommand in SUBCOMMANDS:
        assert subcommand in observed.stdout


def test_log_help_lists_failed_and_max_bytes_options() -> None:
    observed = run_script_process(["log", "--help"])

    assert observed.exit_code == 0
    assert "--failed" in observed.stdout
    assert "--max-bytes" in observed.stdout
    assert SCRIPT_NAME in observed.stdout
