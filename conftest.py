"""Pytest discovery: registers the plugin that bounds every run's temp files."""

pytest_plugins = ["outcomeeng_testing.harnesses.run_temp_root"]
