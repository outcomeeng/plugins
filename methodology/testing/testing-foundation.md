# Testing Foundation

## Non-negotiable rules

- No mocking. Ever.
- Reality is the oracle. Prefer real systems whenever they are cheap, deterministic, safe, and observable enough to prove the behavior.
- Test doubles are exceptions, not defaults. The seven exception cases in `testing-router.md` are the only legitimate reasons to avoid the real dependency.
- Route every assertion through all five stages. Do not skip ahead.
- Name tests by subject, evidence mode, execution level, and optional runner.

## Why tests exist

Every test should serve at least one of these purposes:

1. **Prove behavior**: confirm that a requirement, scenario, or invariant holds in production-relevant execution.
2. **Catch failures early**: detect concrete breakages before users, operators, or downstream systems see them.
3. **Improve debugging economics**: place evidence at the lowest level that can prove the claim so diagnosis is fast when something breaks.

If a test serves none of these purposes, delete it.

## Before you write any test

Every test must answer these questions:

1. What production behavior could be wrong?
2. If this test passes, what does it prove about the real system?
3. What failure would this catch before users see it?

If you cannot answer all three, stop.

## The evidence trap

Agents often skip the evidence question. They see code and decide to test the shape of the code instead of the behavior that matters.

- **Wrong**: See `OrderProcessor` calling `repository.save()`, create an `InMemoryRepository`, and claim persistence is covered.
- **Right**: Ask what evidence is needed, realize the question is whether orders persist correctly, then test with a real database at the lowest level that can prove persistence.

## Separate the axes

Do not collapse evidence, execution pain, and tool choice into one label.

- **Evidence mode** describes what kind of proof the test provides.
- **Execution level** describes how painful the test is to run.
- **Runner** describes which tool executes the test.

Examples:

- A temporary-directory test can still be `L1` when the machine almost certainly has a filesystem, the setup cost is trivial, and the runtime is cheap.
- A Playwright test can be `L2` or `L3` depending on whether it uses only local infrastructure or requires remote systems and credentials.

The runner does not define the level, and the level does not define the runner.

## Evidence modes

Use evidence terms that describe what the test proves:

- `scenario`: an end-to-end behavior within the chosen level
- `mapping`: inputs map to outputs or requests map to actions
- `conformance`: behavior matches an external or internal contract
- `property`: an invariant holds across many generated cases
- `compliance`: required rules, boundaries, or safety constraints hold

## Execution levels

Use `L1`, `L2`, and `L3` to describe execution pain and environment dependence.

- `L1`: almost certainly available, cheap, local, safe, deterministic
- `L2`: real but heavier local infrastructure or setup
- `L3`: remote, shared, credentialed, or network-dependent systems

Examples:

- `L1`: pure logic, tmp files, normal filesystem work, git, repo-required test runners, and standard subprocesses expected on a working machine
- `L2`: local dev servers, Docker, browsers, project-specific binaries, full bootstrap or install costs, and other real local dependencies that are slower or less ubiquitous
- `L3`: network access, shared environments, live third-party services, and anything requiring credentials

## Runner selection

Assume a project default runner unless the file name says otherwise.

- Omit the runner token when the default runner is used.
- Add an explicit runner token for non-default runners.
- Keep runner choice orthogonal to the evidence mode and the execution level.

## Four-part progression

Follow this progression when deciding how to place evidence:

1. **Start with the proof you need**
   - What failure matters?
   - What behavior needs evidence?
2. **Choose the cheapest level that can prove it**
   - Keep the test close to the logic when the behavior can be proven there.
   - Move outward only when the evidence depends on real boundaries.
3. **Use real systems when they provide the truth economically**
   - Temporary directories, git, subprocesses, and other ubiquitous local facilities often belong in `L1`.
   - Heavier orchestration, browsers, containers, and long bootstrap flows often belong in `L2`.
   - Remote or credentialed dependencies belong in `L3`.
4. **Add doubles only for explicit exception cases**
   - Failure simulation
   - Interaction protocols
   - Time and concurrency control
   - Safety constraints
   - Combinatorial cost
   - Observability gaps
   - Contract probes

The detailed routing rules live in [testing-router.md](./testing-router.md). The naming rules live in [testing-naming.md](./testing-naming.md).

## Anti-patterns

Avoid these patterns:

- Writing tests because a layer or file class "should have tests"
- Choosing a label first and then searching for evidence to fit it
- Promoting cheap local-real tests into slower schedules just because they touch the filesystem, git, or subprocesses
- Treating browser coverage as inherently remote or credentialed
- Treating runner choice as a proxy for cost or realism
- Adding doubles when the real dependency is already cheap, deterministic, and observable
- Writing tests that cannot name the failure they would catch

## Co-location

Keep tests next to the governing spec work, and name them for what they prove and how painful they are to run.

See [testing-naming.md](./testing-naming.md) for the naming contract.
