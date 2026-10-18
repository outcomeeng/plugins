"""Scheduled jobs stay inside the configured launchd namespace."""

from outcomeeng_testing.harnesses.consumption_control import (
    NamespaceScopeObservation,
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
