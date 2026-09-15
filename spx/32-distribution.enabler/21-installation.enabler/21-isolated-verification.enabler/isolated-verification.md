# Isolated Verification

PROVIDES full-catalog and subset installation from the invocation checkout in disposable homes
SO THAT marketplace verification
CAN observe real installed artifacts, repeated installation, and failures while preserving persistent installation state

## Assertions

- Given a selected plugin absent from the registered checkout marketplace, when isolated installation runs, then the absence is terminal at that plugin's install. ([test](tests/test_isolated_verification.scenario.l1.py))

- Given a generated subset omitting `spec-tree`, when isolated installation plans that selection, then it reports the invalid subset before an agent CLI mutates state. ([test](tests/test_isolated_verification.scenario.l1.py))

- Given unchanged committed catalogs and checkout content, when isolated installation runs twice against the same disposable homes, then the first run places every shipped Codex agent definition in the disposable home's agent directory beside the skills it invokes, and the second run succeeds with the same installed and home-placed state. ([test](tests/test_isolated_verification.scenario.l3.py))

- Each isolated verification selection — the complete committed catalogs and a generated valid subset containing `spec-tree` — maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI. ([test](tests/test_isolated_verification.mapping.l3.py))

- For each supported agent, an explicitly selected valid isolated subset maps to a plan containing exactly its members in catalog order. ([test](tests/test_isolated_verification.mapping.l1.py))

- NEVER: isolated installation reads or mutates persistent marketplace registration, plugin caches, or agent definitions; subscription discovery may read and natively refresh only the selected saved-login file. ([test](tests/test_isolated_verification.compliance.l3.py))
