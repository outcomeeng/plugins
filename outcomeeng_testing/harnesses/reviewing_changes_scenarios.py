"""End-to-end scenario tests for the review-changes script chain.

Covers the Scenario clauses in ``../reviewing-changes.md`` that govern
how ``compute_diff.py`` resolves refs and how the end-to-end chain validates
and renders outputs:

1. ``SPX_VERIFY_BASE_REF`` env set -> env value is used as ``base_ref``.
2. No env + ``refs/remotes/origin/HEAD`` resolves -> derived from that symbolic
   ref, stripped of the prefix.
3. No source available -> non-zero exit; stderr names the env and git sources.
4. ``SPX_VERIFY_HEAD_REF`` env set -> env value is used as ``head_ref``.
5. No ``SPX_VERIFY_HEAD_REF`` env -> ``HEAD`` is used as ``head_ref``.

The tests are ``l2`` because they spawn ``git`` and multiple Python
subprocesses against a synthetic git repository seeded under ``tmp_path``;
they do not depend on remote services or credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib

import pytest

from outcomeeng_testing.harnesses.changeset_scope import build_stale_local_base_repo
from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    COMPUTE_DIFF_SCRIPT,
    JOURNAL_EMIT_SCRIPT,
    REVIEW_RUN_SCRIPT,
    REVIEW_START_CHANGED_FILES,
    REVIEW_START_DIFF_PATH,
    REVIEW_START_FIELDS,
    REVIEW_START_MANIFEST_PATH,
    REVIEW_START_RUN_TOKEN,
    REVIEW_START_STATE_PATH,
    REVIEW_SUMMARY_BLOCKING_FIELD,
    REVIEW_SUMMARY_DEBT_FIELD,
    REVIEW_SUMMARY_FIELD,
    REVIEW_SUMMARY_OVERALL_FIELD,
    init_renamed_review_git_repo,
    init_review_git_repo,
    isolated_review_env,
    load_review_result_module,
    make_finding_dict,
    make_review_result_dict,
    review_git_repo,
    review_git_repo_with_secondary_head,
    review_finding_payloads,
    review_run_journal_env_from_state,
    review_run_journal_env_keys,
    run_git,
    run_compute_diff_in_process,
    run_journal_emit_in_process,
    run_script,
    set_origin_head,
    stream_review_prefix,
    write_fake_spx,
)


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists() or not JOURNAL_EMIT_SCRIPT.exists(),
    reason=(
        "Reviewing-changes scripts are not yet present; the orchestration "
        "test runs once the verification skill scripts are implemented."
    ),
)
class TestSkillOrchestrationChain:
    """End-to-end streaming chain: diff -> live journal events -> render.

    Audit-parity shape: there is no parallel validation or renderer script. The run
    streams its events live — scope-entered, a scope-advanced per examined
    file, a finding-reported per finding (the per-finding parse is the
    validity gate), and a run-completed sealing the run — and the human
    surface is rendered only from the sealed event prefix.
    """

    def test_chain_streams_and_renders_review_run(self, tmp_path: pathlib.Path) -> None:
        # 1. Real git repo with a base branch and a feature branch.
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)

        # 2. compute_diff.py reads the explicit base ref, runs git diff against
        #    that base, and emits the diff to stdout.
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        diff_result = run_compute_diff_in_process(repo=repo, env=env)
        assert diff_result.returncode == 0, diff_result.stderr
        # The diff must reference the modified file. A truly empty diff
        # means compute_diff did not pick up the base ref correctly.
        assert "README.md" in diff_result.stdout

        # 3. Derive run identity once at the start of the run.
        metadata_result = run_journal_emit_in_process(
            "metadata", "--started-at", "2026-06-23T00:00:00Z", repo=repo, env=env
        )
        assert metadata_result.returncode == 0, metadata_result.stderr

        # 4. Stream the run: scope-entered, a scope-advanced for the examined
        #    file, one finding-reported per finding (each through the parse
        #    gate), and the terminal run-completed. The default fixture carries
        #    one debt-severity finding under the architecture concern.
        findings = make_review_result_dict()["findings"]
        finding = findings[0]
        review_result = load_review_result_module()
        sealed_prefix = stream_review_prefix(
            env, metadata_result.stdout, findings, units=["README.md"]
        )

        # 5. The human surface is rendered only from the sealed event prefix.
        prefix_render = run_journal_emit_in_process(
            "render", stdin=json.dumps(sealed_prefix), env=env
        )
        assert prefix_render.returncode == 0, prefix_render.stderr
        prefix_surface = json.loads(prefix_render.stdout)
        assert prefix_surface["countLine"] == "BLOCKING: 0, DEBT: 1"
        # The surface shows the run advancing: a progress line for the examined
        # file precedes the finding line.
        surface = prefix_surface["surface"]
        assert "- examined README.md" in surface
        # The finding event carries the full review finding: severity maps to
        # the audit-shared `warning`, and the concern and action ride along.
        assert (
            f"- [warning {finding[review_result.FINDING_CONCERN_FIELD]}] "
            f"{finding[review_result.FINDING_FILE_FIELD]}:"
            f"{finding[review_result.FINDING_LINE_FIELD]}"
        ) in surface
        assert f"Required: {finding[review_result.FINDING_ACTION_FIELD]}" in surface
        # No verdict the reviewer decides; the rollup footer is a computed
        # status, not a `decision` field.
        assert "decision" not in surface

    def test_clean_review_streams_a_zero_count(self, tmp_path: pathlib.Path) -> None:
        # A fully-clean review (no findings) streams scope-entered, the examined
        # file, and run-completed, and renders a zero count line with no finding
        # body to act on.
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref

        metadata_result = run_journal_emit_in_process(
            "metadata", "--started-at", "2026-06-23T00:00:00Z", repo=repo, env=env
        )
        assert metadata_result.returncode == 0, metadata_result.stderr
        sealed_prefix = stream_review_prefix(
            env, metadata_result.stdout, [], units=["README.md"]
        )
        prefix_render = run_journal_emit_in_process(
            "render", stdin=json.dumps(sealed_prefix), env=env
        )
        assert prefix_render.returncode == 0, prefix_render.stderr
        surface = json.loads(prefix_render.stdout)
        assert surface["countLine"] == "BLOCKING: 0, DEBT: 0"
        assert surface["blocking"] == "0"
        assert surface["debt"] == "0"


@pytest.mark.skipif(
    not REVIEW_RUN_SCRIPT.exists(),
    reason="review_run.py is not yet present.",
)
class TestReviewRunnerBoundary:
    """The public runner seals a journal run and returns only the run token."""

    def test_runner_preserves_journal_namespace_across_subcommands(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        journal_path = tmp_path / "journal.json"
        write_fake_spx(bin_dir, journal_path)

        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["SPX_FAKE_JOURNAL_PATH"] = str(journal_path)
        env["SPX_FAKE_NAMESPACE_KEYS"] = json.dumps(review_run_journal_env_keys())
        later_env = env.copy()
        for key in review_run_journal_env_keys():
            later_env[key] = "contaminating-later-env"

        started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
        assert started.returncode == 0, started.stderr
        start_payload = json.loads(started.stdout)
        assert set(start_payload) == set(REVIEW_START_FIELDS)
        assert pathlib.Path(start_payload[REVIEW_START_DIFF_PATH]).is_file()
        assert pathlib.Path(start_payload[REVIEW_START_MANIFEST_PATH]).is_file()
        assert isinstance(start_payload[REVIEW_START_CHANGED_FILES], list)
        state_path = pathlib.Path(start_payload[REVIEW_START_STATE_PATH])
        expected_namespace = review_run_journal_env_from_state(state_path)

        scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            str(state_path),
            "README.md",
            env=later_env,
            cwd=repo,
        )
        assert scoped.returncode == 0, scoped.stderr

        findings = review_finding_payloads()
        for finding in findings:
            appended = run_script(
                REVIEW_RUN_SCRIPT,
                "append-finding",
                "--state",
                str(state_path),
                stdin=json.dumps(finding),
                env=later_env,
                cwd=repo,
            )
            assert appended.returncode == 0, appended.stderr

        finished = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            str(state_path),
            env=later_env,
            cwd=repo,
        )
        assert finished.returncode == 0, finished.stderr

        assert finished.stdout == f"{start_payload[REVIEW_START_RUN_TOKEN]}\n"
        assert state_path.exists() is False

        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        projection = load_journal_projection_module()
        expected_event_types = [
            projection.SCOPE_ENTERED,
            projection.SCOPE_ADVANCED,
            *[projection.FINDING_REPORTED for _finding in findings],
            projection.RUN_COMPLETED,
        ]
        assert journal["sealed"] is True
        assert journal["commands"] == [
            "open",
            *["append" for _event in expected_event_types[:-1]],
            "read",
            "append",
            "seal",
        ]
        event_types = [event["type"] for event in journal["events"]]
        assert event_types == expected_event_types
        finding_events = [
            event
            for event in journal["events"]
            if event["type"] == projection.FINDING_REPORTED
        ]
        assert [event["data"]["id"] for event in finding_events] == [
            finding["id"] for finding in findings
        ]
        assert journal["namespace"] == expected_namespace
        terminal_event = journal["events"][-1]
        assert terminal_event["data"]["status"] == projection.JournalRunStatus.REJECTED
        summary = terminal_event["data"][REVIEW_SUMMARY_FIELD]
        review_result = load_review_result_module()
        assert summary[REVIEW_SUMMARY_BLOCKING_FIELD] == sum(
            finding["severity"] == review_result.Severity.BLOCKING
            for finding in findings
        )
        assert summary[REVIEW_SUMMARY_DEBT_FIELD] == sum(
            finding["severity"] == review_result.Severity.DEBT for finding in findings
        )
        assert summary[REVIEW_SUMMARY_OVERALL_FIELD] == projection.Outcome.REJECTED

    def test_runner_rejects_finish_before_scope_coverage(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        journal_path = tmp_path / "journal.json"
        write_fake_spx(bin_dir, journal_path)

        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["SPX_FAKE_JOURNAL_PATH"] = str(journal_path)
        env["SPX_FAKE_NAMESPACE_KEYS"] = json.dumps(review_run_journal_env_keys())

        started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
        assert started.returncode == 0, started.stderr
        start_payload = json.loads(started.stdout)

        finished = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            env=env,
            cwd=repo,
        )
        assert finished.returncode == 1
        assert "missing scope-advanced events for: README.md" in finished.stderr

        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        event_types = [event["type"] for event in journal["events"]]
        assert event_types == ["verification.scope.entered"]
        assert journal["sealed"] is False

    def test_runner_requires_rename_source_and_destination_scope(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = init_renamed_review_git_repo(repo)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        journal_path = tmp_path / "journal.json"
        write_fake_spx(bin_dir, journal_path)

        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["SPX_FAKE_JOURNAL_PATH"] = str(journal_path)
        env["SPX_FAKE_NAMESPACE_KEYS"] = json.dumps(review_run_journal_env_keys())

        started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
        assert started.returncode == 0, started.stderr
        start_payload = json.loads(started.stdout)
        assert start_payload[REVIEW_START_CHANGED_FILES] == ["README.md", "RENAMED.md"]

        scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            "RENAMED.md",
            env=env,
            cwd=repo,
        )
        assert scoped.returncode == 0, scoped.stderr

        missing_source = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            env=env,
            cwd=repo,
        )
        assert missing_source.returncode == 1
        assert "missing scope-advanced events for: README.md" in missing_source.stderr

        source_scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            "README.md",
            env=env,
            cwd=repo,
        )
        assert source_scoped.returncode == 0, source_scoped.stderr

        finished = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            env=env,
            cwd=repo,
        )
        assert finished.returncode == 0, finished.stderr
        assert finished.stdout == "run-001\n"


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists(),
    reason="compute_diff.py is not yet present.",
)
class TestComputeDiffBaseRefDerivation:
    """compute_diff.py resolves base_ref from env -> git, in that order."""

    def test_env_base_ref_works(self, tmp_path: pathlib.Path) -> None:
        repo, base_ref = review_git_repo(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        result = run_compute_diff_in_process(repo=repo, env=env)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_includes_committed_staged_unstaged_and_untracked_diffs(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref = review_git_repo(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref

        (repo / "STAGED.md").write_text("staged\n", encoding="utf-8")
        run_git("add", "STAGED.md", cwd=repo)
        (repo / "README.md").write_text("hello\nworld\nunstaged\n", encoding="utf-8")
        (repo / "UNTRACKED.md").write_text("untracked\n", encoding="utf-8")

        result = run_compute_diff_in_process(repo=repo, env=env)
        assert result.returncode == 0, result.stderr
        assert "### Committed diff" in result.stdout
        assert "### Staged diff" in result.stdout
        assert "### Unstaged diff" in result.stdout
        assert "### Untracked files" in result.stdout
        assert "world" in result.stdout
        assert "STAGED.md" in result.stdout
        assert "unstaged" in result.stdout
        assert "UNTRACKED.md" in result.stdout
        assert "untracked" in result.stdout

    def test_bundle_dir_writes_random_access_diff_and_manifest(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref = review_git_repo(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        bundle_dir = tmp_path / "review-input"

        (repo / "STAGED.md").write_text("staged\n", encoding="utf-8")
        run_git("add", "STAGED.md", cwd=repo)
        (repo / "README.md").write_text("hello\nworld\nunstaged\n", encoding="utf-8")
        (repo / "UNTRACKED.md").write_text("untracked\n", encoding="utf-8")

        result = run_compute_diff_in_process(
            repo=repo,
            env=env,
            args=["--bundle-dir", str(bundle_dir)],
        )
        assert result.returncode == 0, result.stderr
        summary = json.loads(result.stdout)
        diff_path = pathlib.Path(summary["diff_path"])
        manifest_path = pathlib.Path(summary["manifest_path"])
        assert diff_path == bundle_dir / "diff.md"
        assert manifest_path == bundle_dir / "manifest.json"
        assert diff_path.is_file()
        assert manifest_path.is_file()

        diff_text = diff_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        diff_bytes = diff_text.encode("utf-8")
        assert summary["diff_bytes"] == len(diff_bytes)
        assert summary["section_count"] == 4
        assert manifest["schema_version"] == 1
        assert manifest["base_ref"] == base_ref
        assert manifest["head_ref"] == "HEAD"
        assert manifest["diff_path"] == "diff.md"
        assert manifest["diff_sha256"] == hashlib.sha256(diff_bytes).hexdigest()
        section_titles = [section["title"] for section in manifest["sections"]]
        assert section_titles == [
            "Committed diff",
            "Staged diff",
            "Unstaged diff",
            "Untracked files",
        ]
        files_by_section = {
            section["title"]: section["files"] for section in manifest["sections"]
        }
        assert files_by_section["Committed diff"] == ["README.md"]
        assert files_by_section["Staged diff"] == ["STAGED.md"]
        assert files_by_section["Unstaged diff"] == ["README.md"]
        assert files_by_section["Untracked files"] == ["UNTRACKED.md"]
        for section in manifest["sections"]:
            section_text = diff_bytes[
                section["byte_start"] : section["byte_start"] + section["byte_length"]
            ].decode("utf-8")
            section_lines = section_text.splitlines()
            manifest_line_slice = diff_text.splitlines()[
                section["start_line"] - 1 : section["start_line"]
                - 1
                + section["line_count"]
            ]
            assert (
                section["start_line"]
                == diff_bytes[: section["byte_start"]].decode("utf-8").count("\n") + 1
            )
            assert section["line_count"] == len(section_lines)
            assert manifest_line_slice == section_lines
            assert section_text.startswith(f"### {section['title']}")

    def test_bundle_dir_rejects_existing_file(self, tmp_path: pathlib.Path) -> None:
        repo, base_ref = review_git_repo(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        bundle_file = tmp_path / "review-input"
        bundle_file.write_text("not a directory\n", encoding="utf-8")

        result = run_compute_diff_in_process(
            repo=repo,
            env=env,
            args=["--bundle-dir", str(bundle_file)],
        )

        assert result.returncode == 1
        assert "--bundle-dir exists and is not a directory" in result.stderr

    def test_bundle_dir_rejects_paths_inside_git_worktree(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref = review_git_repo(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref

        result = run_compute_diff_in_process(
            repo=repo,
            env=env,
            args=["--bundle-dir", str(repo / ".review-input")],
        )

        assert result.returncode == 1
        assert "--bundle-dir must be outside the git worktree" in result.stderr
        assert not (repo / ".review-input").exists()

    def test_git_origin_head_works_without_changes_or_env(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref = review_git_repo(tmp_path)
        set_origin_head(repo, base_ref)
        env = isolated_review_env(cwd=repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        result = run_compute_diff_in_process(repo=repo, env=env)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_aborts_when_no_source_yields_base_ref(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, _base_ref = review_git_repo(tmp_path)
        env = isolated_review_env(cwd=repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        # No env; no origin/HEAD symbolic ref.
        result = run_compute_diff_in_process(repo=repo, env=env)
        assert result.returncode != 0
        # The error must name every source so the operator can pick one.
        for token in ("SPX_VERIFY_BASE_REF", "origin/HEAD"):
            assert token in result.stderr, (
                f"stderr should name {token!r}; got: {result.stderr!r}"
            )


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists(),
    reason="compute_diff.py is not yet present.",
)
class TestComputeDiffHeadRefDerivation:
    """compute_diff.py resolves head_ref from env -> literal HEAD.

    Asserts the parallel precedence chain to TestComputeDiffBaseRefDerivation
    so the spec's new head_ref scenarios carry executed evidence. A secondary
    branch with its own distinct filename gives each scenario a falsifiable
    signal: when head_ref selects the secondary branch, the diff surfaces
    that file; when head_ref defaults to literal HEAD (feature/x), it does
    not.
    """

    def test_env_head_ref_selects_alternate_head(self, tmp_path: pathlib.Path) -> None:
        repo, base_ref, secondary = review_git_repo_with_secondary_head(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env["SPX_VERIFY_HEAD_REF"] = secondary
        result = run_compute_diff_in_process(repo=repo, env=env)
        assert result.returncode == 0, result.stderr
        # head_ref pointed at the secondary branch — its file appears, not
        # feature/x's README change. This is what distinguishes head_ref
        # selection from the default-HEAD behaviour.
        assert "SECONDARY.md" in result.stdout
        assert "world" not in result.stdout

    def test_head_ref_defaults_to_literal_head_when_no_source(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref, _secondary = review_git_repo_with_secondary_head(tmp_path)
        env = isolated_review_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env.pop("SPX_VERIFY_HEAD_REF", None)
        # No SPX_VERIFY_HEAD_REF; HEAD is feature/x, so the diff must surface
        # feature/x's payload, not secondary's SECONDARY.md.
        result = run_compute_diff_in_process(repo=repo, env=env)
        assert result.returncode == 0, result.stderr
        assert "world" in result.stdout
        assert "SECONDARY.md" not in result.stdout


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists(),
    reason="compute_diff.py is not yet present.",
)
class TestComputeDiffStaleLocalBase:
    """A git-derived base scopes against origin/<base>, not a stale local ref.

    Reproduces the multi-worktree staleness bug: the feature branch holds a
    commit already merged into ``origin/main`` while the local ``main`` ref lags
    behind it. With no ``SPX_VERIFY_BASE_REF``, ``compute_diff`` auto-derives
    the base from ``origin/HEAD``; the derived base must resolve to the
    remote-tracking ref ``origin/main`` so the already-merged commit stays out
    of the diff. Diffing against the bare local ``main`` would re-include it.
    """

    def test_git_derived_base_excludes_already_merged_commit(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        stale = build_stale_local_base_repo(repo)
        env = isolated_review_env(cwd=stale.repo)
        env.pop("SPX_VERIFY_BASE_REF", None)

        result = run_compute_diff_in_process(repo=stale.repo, env=env)
        assert result.returncode == 0, result.stderr
        # The feature change is in scope; the already-merged commit is not —
        # auto-derivation must scope against origin/<base>, not the stale local
        # ref.
        assert stale.feature_file in result.stdout
        assert stale.merged_file not in result.stdout
