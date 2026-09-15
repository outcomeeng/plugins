# Native Session Authentication

PROVIDES explicit native-session authentication with bounded saved-login access
SO THAT isolated role discovery and execution
CAN use the selected credential channel while preserving native refresh writes and preventing credential disclosure

## Assertions

### Mappings

- Each unsupported saved-login condition — a missing file, a malformed document, or a non-subscription credential — maps to a diagnostic before any native command runs. ([test](tests/test_authentication.mapping.l1.py))

### Compliance

- ALWAYS: discovery selects subscription by default locally, requires an explicit authentication mode in CI, and requires the selected mode's credential without falling back to another mode. ([test](tests/test_authentication.compliance.l1.py))

- ALWAYS: subscription discovery checks native file-store write-through compatibility before linking only the selected saved-login file into disposable state, then serializes participating uses and reports detected file, link, or account replacement without restoring an older copy. ([test](tests/test_authentication.compliance.l1.py))

- NEVER: subscription discovery implements OAuth refresh, migrates a credential store, or invokes login or logout against a home linked to the saved login; native refresh persists through the file link and cleanup leaves its target intact. ([test](tests/test_authentication.compliance.l1.py))

- NEVER: discovery exposes initial or refreshed credentials in arguments, child credential variables, returned captures, or exceptions; API and workspace-token login receive their respective credential only through stdin in disposable state. ([test](tests/test_authentication.compliance.l1.py))

- NEVER: the fresh-session subagent-discovery probe continues without its credential or stores a captured stream carrying the credential substring — absence raises a loud error before any agent process runs, and capture-time scrubbing replaces every occurrence in stored streams and messages. ([test](tests/test_authentication.compliance.l1.py))
