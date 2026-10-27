# Issues

## The CI gate harness types parsed workflow data as unjustified `Any` (SH-19644-02)

Standing finding SH-19644-02 on `outcomeeng_testing/harnesses/ci_gate.py`. The harness stands on main, outside the changeset of https://github.com/outcomeeng/plugins/pull/706, by the range `git diff --stat 39d028747bc38610adb6d74d4bba5488a861b65f...1efe32296f4afdbf35c7f91db0724576f24d3710 -- outcomeeng_testing/harnesses/ci_gate.py`, which prints nothing.

**Evidence**: `workflow`, `gate_job`, `gate_steps`, `setup_python_version`, and the workflow-job observer return or `cast` to `dict[str, Any]` and `list[dict[str, Any]]`. The observers `observe_gate_triggers`, `observe_gate_run_commands`, `observe_ci_toolchain`, `observe_gate_steps`, and `observe_workflow_jobs` then narrow each field with `cast` and no shape check.

**Impact**: a workflow whose shape differs from the cast reaches the tests as a wrong-typed value instead of a typed failure at the parse boundary, and the type checker accepts every use of the parsed data.

**Settlement condition**: parsed workflow and pyproject data cross the harness boundary as typed records, validated at the parse, with no unjustified `Any` and no unchecked `cast`. https://github.com/outcomeeng/changes/issues/816 carries that remedy.

## The CI gate test owns a gate-step predicate and a workflow file name

Standing finding on `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/tests/test_ci_gate.compliance.l1.py`. The changeset of https://github.com/outcomeeng/plugins/pull/706 changes only the test's step-environment checks; `_inlined_gate_steps`, `test_gate_workflow_never_inlines_a_gate_step`, `test_inlined_gate_steps_are_detected`, and `test_yaml_suffixed_workflow_jobs_are_observed` stand as on main.

**Evidence**: the module-level function `_inlined_gate_steps` decides which workflow shell lines count as an inlined gate step, and `test_gate_workflow_never_inlines_a_gate_step` and `test_inlined_gate_steps_are_detected` both call it. `test_yaml_suffixed_workflow_jobs_are_observed` compares the observation with the literal file name `unbounded.yaml`, which the test chooses rather than imports.

**Impact**: the inlined-step rule lives in a test helper, outside both the linked test bodies and any production module, and the expected file name is test-owned data; neither the enforcement nor the expectation has a source owner.

**Settlement condition**: a production validator owns the inlined-step rule and the tests import it, and the expected workflow file name comes from the fixture's source rather than a test literal. https://github.com/outcomeeng/changes/issues/816 carries that remedy.
