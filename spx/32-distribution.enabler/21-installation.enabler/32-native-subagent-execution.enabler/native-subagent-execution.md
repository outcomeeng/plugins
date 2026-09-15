# Native Subagent Execution

PROVIDES installed-role discovery and native profile execution with retained observations
SO THAT marketplace maintainers
CAN inspect definition loading, child execution, and process cleanup against disposable installed state

## Assertions

### Scenarios

- Given a native probe command whose parent emits a byte sequence that is invalid UTF-8 and exits while a descendant keeps the captured output stream open, when the runner collects the result, then it returns the parent's completed result promptly, replaces undecodable bytes, and terminates the descendant before returning. ([test](tests/test_native_profile_process.scenario.l1.py))

- Given a native probe command whose parent and descendant remain running, when the execution timeout expires, then the runner reports the timeout promptly and terminates the descendant before returning. ([test](tests/test_native_profile_process.scenario.l1.py))

- Given a disposable `CODEX_HOME` that isolated installation populated and authentication from the explicitly selected mode, when a fresh non-interactive Codex session in that home is asked for its available subagent names as structured output, then the returned subagent name set contains every canonical subagent name whose definition the installation placed under that home's `agents/` directory. ([test](tests/test_native_subagent_execution.scenario.l3.py))

### Mappings

- Every target/profile pair in `outcomeeng.distribution.profiles.AGENT_PROFILES`
  maps to one native-profile probe row whose immutable identifier, complete native
  configuration, disposable state root, and artifact paths derive from that
  registry entry. ([test](tests/test_native_profile_execution.mapping.l1.py))

### Compliance

- ALWAYS: for every native-profile probe row, the producer materializes the
  native definition, retains configuration/loading/result artifacts, removes
  ambient model and effort overrides, passes only the selected harness
  credential, and invokes its native-child command exactly once; a failed row
  records its terminal condition without a retry, credential fallback, profile
  substitution, or alternate launch. ([test](tests/test_native_profile_execution.compliance.l1.py))

- ALWAYS: release acceptance is established independently for each supported
  harness and retains configuration, native loading, and one minimal isolated
  execution result for all three of that harness's profiles declared in
  `spx/15-subagent-execution.pdr.md`. Evidence for one harness establishes no
  execution claim for another; a combined acceptance claim requires complete
  evidence for every harness it names. Each row derives
  its complete configuration from the central profile owner, uses disposable
  state, and makes one native subagent invocation. The retained artifacts
  distinguish definition loading, parent-session configuration, and the child
  invocation result. For Codex, the retained result includes one native
  parent-filtered app-server listing of active and archived spawned children,
  complete pagination, and one read of the sole child from disposable state.
  The read carries the configured role, recorded model and effort, and
  completion; recorded configuration is not per-turn execution telemetry. An independent Auditor judges the actual artifacts and result.
  A missing credential, failed load, or unusable launch is reported
  without retry, credential fallback, profile substitution, or another launch
  mechanism ([audit]).
