"""Compliance evidence: the audit at close makes three format comparisons and reports each failure as its own finding.

The rule is the spec assertion that at close the runner reports a failing
comparison as its own finding: the format command leaves each declared
replacement unchanged, leaves the file at the merge commit unchanged, and the
file on the default branch equals the declared replacement once its linked
evidence tags are removed. Each violating case breaks one comparison and
conforms to the other two, so a runner that conflates the comparisons, or
compares tag-bearing text exactly, reports the wrong set. The format command
is a stand-in executable the harness places beside the replayed ``gh``; it
reads the text on stdin and writes the formatted text on stdout, as the rule
requires.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_run import (
    FORMAT_CLEAN,
    FORMAT_DECLARED_PATH,
    FORMAT_DIRTY,
    FORMAT_OTHER_PATH,
    FORMAT_TAGGED,
    AuditWorkspace,
    RunnerCall,
    audit_workspace,
    body_declaring,
    load_runner,
)

runner = load_runner()
Operation = runner.Operation
Field = runner.RequestField
Result = runner.ResultField
Status = runner.ResultStatus
Rule = runner.FormatRule
ExitCode = runner.ExitCode
DECLARED_PATH = FORMAT_DECLARED_PATH


def _text(source: object) -> str:
    return source.read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _close_audit(
    workspace: AuditWorkspace, *, declared: str, merged: str, on_default: str
) -> tuple[RunnerCall, str]:
    """Declare ``declared``, commit ``merged`` then ``on_default``, and audit the close."""
    identity = workspace.place_issue()
    workspace.set_body(identity, body_declaring(DECLARED_PATH, declared))
    merge_commit = workspace.commit({DECLARED_PATH: merged}, message="merge")
    head = workspace.commit({DECLARED_PATH: on_default}, message="later")
    workspace.publish_default_branch(head)
    formatter = workspace.install_formatter()
    call = workspace.invoke(
        {
            Field.OPERATION: Operation.FORMAT_AT_CLOSE,
            Field.ISSUE: identity,
            Field.ROOT: str(workspace.root),
            Field.MERGE_COMMIT: merge_commit,
            Field.FORMAT_COMMAND: [str(formatter), runner.PATH_PLACEHOLDER],
        }
    )
    return call, identity


def _rules(call: RunnerCall) -> list[object]:
    return [finding[Result.RULE] for finding in call.result[Result.FINDINGS]]  # type: ignore[union-attr]


def test_a_close_that_meets_all_three_comparisons_reports_no_finding() -> None:
    clean, tagged = _text(FORMAT_CLEAN), _text(FORMAT_TAGGED)
    with audit_workspace() as workspace:
        call, _identity = _close_audit(
            workspace, declared=clean, merged=clean, on_default=tagged
        )

        assert call.exit_code == ExitCode.OK, call.result
        assert call.result[Result.STATUS] == Status.OK
        assert call.result[Result.FINDINGS] == []
        assert call.runner_writes == ()


def test_a_declared_replacement_the_format_command_changes_is_its_own_finding() -> None:
    clean, dirty = _text(FORMAT_CLEAN), _text(FORMAT_DIRTY)
    with audit_workspace() as workspace:
        call, _identity = _close_audit(
            workspace, declared=dirty, merged=clean, on_default=dirty
        )

        assert _rules(call) == [Rule.BASE_FORMATTER]


def test_a_file_at_the_merge_commit_the_format_command_changes_is_its_own_finding() -> (
    None
):
    clean, dirty = _text(FORMAT_CLEAN), _text(FORMAT_DIRTY)
    with audit_workspace() as workspace:
        call, _identity = _close_audit(
            workspace, declared=clean, merged=dirty, on_default=clean
        )

        assert _rules(call) == [Rule.MERGE_FORMATTER]
        assert call.result[Result.FINDINGS][0][Result.WHERE] == DECLARED_PATH  # type: ignore[index]


def test_a_default_branch_file_that_differs_from_the_declared_replacement_is_its_own_finding() -> (
    None
):
    clean, dirty = _text(FORMAT_CLEAN), _text(FORMAT_DIRTY)
    with audit_workspace() as workspace:
        call, _identity = _close_audit(
            workspace, declared=clean, merged=clean, on_default=dirty
        )

        assert _rules(call) == [Rule.DEFAULT_BRANCH]


def test_a_merge_commit_that_holds_no_file_at_the_declared_path_is_a_merge_finding() -> (
    None
):
    clean, tagged = _text(FORMAT_CLEAN), _text(FORMAT_TAGGED)
    with audit_workspace() as workspace:
        identity = workspace.place_issue()
        workspace.set_body(identity, body_declaring(DECLARED_PATH, clean))
        merge_commit = workspace.commit({FORMAT_OTHER_PATH: clean}, message="merge")
        head = workspace.commit({DECLARED_PATH: tagged}, message="later")
        workspace.publish_default_branch(head)
        formatter = workspace.install_formatter()

        call = workspace.invoke(
            {
                Field.OPERATION: Operation.FORMAT_AT_CLOSE,
                Field.ISSUE: identity,
                Field.ROOT: str(workspace.root),
                Field.MERGE_COMMIT: merge_commit,
                Field.FORMAT_COMMAND: [str(formatter), runner.PATH_PLACEHOLDER],
            }
        )

        assert _rules(call) == [Rule.MERGE_FORMATTER]
