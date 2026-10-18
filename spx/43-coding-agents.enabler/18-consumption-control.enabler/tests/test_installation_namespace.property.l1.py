"""Scheduled jobs stay inside the configured launchd namespace."""

from outcomeeng_testing.harnesses.consumption_control import (
    NamespaceReinstallObservation,
    NamespaceScopeObservation,
    namespace_reinstall_property,
    namespace_scope_property,
)


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


def test_a_root_holds_one_namespace_and_a_second_namespace_changes_nothing() -> None:
    def check(observed: NamespaceReinstallObservation) -> None:
        assert observed.error is not None
        assert "namespace mismatch" in observed.error
        assert repr(observed.first) in observed.error
        assert repr(observed.second) in observed.error
        assert observed.record_after == observed.record_before
        assert observed.loaded_after == observed.loaded_before
        assert observed.second_labels.isdisjoint(observed.loaded_after)

    namespace_reinstall_property(check)
