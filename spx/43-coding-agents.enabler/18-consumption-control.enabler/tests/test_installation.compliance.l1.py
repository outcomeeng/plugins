"""Managed assets and job failures cross the recording command boundary."""

from outcomeeng_testing.harnesses.consumption_control import (
    MalformedRetainedFieldObservation,
    MalformedRetainedRecordObservation,
    NamespaceReinstallObservation,
    NamespaceReturnObservation,
    NamespaceScopeObservation,
    OutsideRetentionObservation,
    RetainedBoundObservation,
    RetentionPlanObservation,
    RetainedRecordMalformation,
    RetentionGap,
    RetentionGapObservation,
    installation_observation,
    malformed_namespace_field_property,
    malformed_namespace_string_property,
    malformed_retained_field_property,
    malformed_retained_record_property,
    namespace_reinstall_property,
    namespace_return_property,
    namespace_scope_property,
    outside_retention_property,
    retained_bound_property,
    retention_gap_property,
    retention_plan_property,
    workspace,
)


def test_versioned_assets_restart_and_unknown_job_state() -> None:
    with workspace() as work:
        observed = installation_observation(work)
        assert not observed.inactive_assets_exist
        assert not observed.inactive_calls
        assert observed.owned_assets == observed.expected_assets
        assert all(
            observed.stable_root in arguments for arguments in observed.stable_arguments
        )
        assert all(
            observed.source_root not in argument
            for arguments in observed.stable_arguments
            for argument in arguments
        )
        assert not any(observed.stopped_loaded)
        assert all(observed.restarted_loaded)
        assert observed.failed_status == observed.expected_failed_status
        assert all(loaded is None for loaded in observed.unknown_loaded)
        assert observed.calls


def test_jobs_are_read_stopped_and_replaced_only_under_the_namespace() -> None:
    def check(observed: NamespaceScopeObservation) -> None:
        prefix = observed.namespace + "."
        assert observed.installed_labels
        assert all(label.startswith(prefix) for label in observed.installed_labels)
        assert observed.touched_labels
        assert all(label.startswith(prefix) for label in observed.touched_labels)
        assert observed.foreign_labels.isdisjoint(observed.touched_labels)
        assert observed.foreign_labels <= observed.loaded_after

    namespace_scope_property(check)


def test_reinstall_under_another_namespace_replaces_only_its_own_jobs() -> None:
    def check(observed: NamespaceReinstallObservation) -> None:
        assert observed.record_after[observed.namespace_key] == observed.second
        assert observed.reinstall_labels
        assert observed.reinstall_labels <= observed.second_labels
        assert observed.first_labels <= observed.loaded_after_install
        assert observed.second_labels <= observed.loaded_after_install
        assert observed.first_files_after == observed.first_files_before

    namespace_reinstall_property(check)


def test_reinstall_under_a_previously_used_namespace_replaces_only_its_own_jobs() -> (
    None
):
    def check(observed: NamespaceReturnObservation) -> None:
        assert observed.record_after[observed.namespace_key] == observed.first
        assert observed.return_labels
        assert observed.return_labels <= observed.first_labels
        assert observed.first_labels <= observed.loaded_after_return
        assert observed.second_labels <= observed.loaded_after_return
        assert observed.second_files_after == observed.second_files_before

    namespace_return_property(check)


def test_status_stop_and_restart_act_on_the_namespace_the_record_names() -> None:
    def check(observed: NamespaceReinstallObservation) -> None:
        assert observed.status_labels == observed.second_labels
        assert observed.stop_labels == observed.second_labels
        assert observed.restart_labels == observed.second_labels
        assert observed.first_labels <= observed.loaded_after_stop
        assert observed.second_labels.isdisjoint(observed.loaded_after_stop)
        assert observed.first_labels <= observed.loaded_after_restart
        assert observed.second_labels <= observed.loaded_after_restart

    namespace_reinstall_property(check)


def test_retained_jobs_are_bounded_and_older_jobs_are_stopped_and_removed() -> None:
    def check(observed: RetainedBoundObservation) -> None:
        assert len(observed.retained_labels) <= observed.limit
        assert observed.retained_labels == observed.expected_retained
        assert observed.pruned_labels
        assert observed.pruned_labels.isdisjoint(observed.retained_labels)
        assert not observed.pruned_files_remaining
        assert observed.pruned_labels.isdisjoint(observed.loaded_after)
        assert set(observed.retained_labels) <= observed.loaded_after
        assert observed.record_bytes < observed.record_ceiling
        assert not observed.gaps

    retained_bound_property(check)


def test_install_plan_names_the_launch_agents_a_reinstall_would_remove() -> None:
    def check(observed: RetentionPlanObservation) -> None:
        assert observed.expected_removals
        assert observed.planned_removals == observed.expected_removals
        assert observed.removals_remaining_after_plan == observed.planned_removals
        assert not observed.calls_during_plan

    retention_plan_property(check)


def test_retained_job_with_a_nonconforming_path_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedRecordObservation) -> None:
        assert observed.message, observed.rejected_path
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_record_property(check)


def test_a_retained_job_without_a_path_is_rejected_naming_file_and_field() -> None:
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(RetainedRecordMalformation.MISSING_PATH, check)


def test_a_retained_jobs_value_that_is_not_a_list_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(RetainedRecordMalformation.NON_LIST_VALUE, check)


def test_a_retained_job_entry_that_is_not_an_object_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(
        RetainedRecordMalformation.NON_MAPPING_ENTRY, check
    )


def test_a_retained_job_with_a_label_no_namespace_owns_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(RetainedRecordMalformation.FOREIGN_LABEL, check)


def test_a_namespace_that_is_not_a_string_is_rejected_naming_file_and_field() -> None:
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_namespace_field_property(check)


def test_a_namespace_that_breaks_the_grammar_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_namespace_string_property(check)


def test_retention_preserves_a_retained_launch_agent_outside_the_install_directory() -> (
    None
):
    def check(observed: OutsideRetentionObservation) -> None:
        assert observed.outside_paths
        assert observed.outside_files_remaining == observed.outside_paths
        assert observed.gaps

    outside_retention_property(check)


def test_a_retained_launch_agent_changed_on_disk_stays_owned_and_reported() -> None:
    def check(observed: RetentionGapObservation) -> None:
        assert observed.targeted_paths
        assert observed.gaps
        assert observed.files_remaining == observed.targeted_paths
        assert observed.targeted_paths <= observed.owned_paths_after

    retention_gap_property(RetentionGap.CHANGED_PLIST, check)


def test_a_retained_launch_agent_with_unestablished_status_stays_owned_and_reported() -> (
    None
):
    def check(observed: RetentionGapObservation) -> None:
        assert observed.targeted_paths
        assert observed.gaps
        assert observed.files_remaining == observed.targeted_paths
        assert observed.targeted_paths <= observed.owned_paths_after
        assert not observed.reinstall_rejection

    retention_gap_property(RetentionGap.STATUS_UNESTABLISHED, check)


def test_a_retained_launch_agent_that_cannot_be_read_stays_owned_and_reported() -> None:
    def check(observed: RetentionGapObservation) -> None:
        assert observed.targeted_paths
        assert observed.gaps
        assert observed.files_remaining == observed.targeted_paths
        assert observed.targeted_paths <= observed.owned_paths_after
        assert not observed.reinstall_rejection

    retention_gap_property(RetentionGap.UNREADABLE_PLIST, check)


def test_a_retained_launch_agent_whose_stop_is_refused_stays_owned_and_reported() -> (
    None
):
    def check(observed: RetentionGapObservation) -> None:
        assert observed.targeted_paths
        assert observed.gaps
        assert observed.files_remaining == observed.targeted_paths
        assert observed.targeted_paths <= observed.owned_paths_after
        assert not observed.reinstall_rejection

    retention_gap_property(RetentionGap.STOP_REFUSED, check)


def test_a_retained_job_whose_plist_label_differs_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(
        RetainedRecordMalformation.MISMATCHED_PLIST_LABEL, check
    )


def test_a_retained_job_whose_program_arguments_differ_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(
        RetainedRecordMalformation.MISMATCHED_PROGRAM_ARGUMENTS, check
    )


def test_a_retained_job_whose_working_directory_differs_is_rejected_naming_file_and_field() -> (
    None
):
    def check(observed: MalformedRetainedFieldObservation) -> None:
        assert observed.message
        assert observed.record_path in observed.message
        assert observed.field in observed.message

    malformed_retained_field_property(
        RetainedRecordMalformation.MISMATCHED_WORKING_DIRECTORY, check
    )
