# Status Derivation

DEFINES attributed result AS a verification result pinned to the declaration, the verification artifact, and the subject it covers

CONSTRAINS the state of an output node
TO derive from its declarations, required verification artifacts, and attributed results against its declared malleability, with the projector as the sole writer of the committed `spx.status.json` claim
SO THAT the same declarations and results always yield the same state, and no manually assigned label overrides evidence

## Verification

### Test.Property: derivation

- state-deterministic: Identical declarations, artifacts, attributed results, and pins produce identical state.
- current-results-only: Only current results satisfy a node's verification requirements.
- pin-invalidates: An attributed result is invalid when a path named by its pin changes.

### Test.Compliance: validity

- no-invalid-satisfaction: NEVER an invalidated result satisfies a required verification result.

### Audit: state writer

- projector-sole-writer: The projector alone writes the committed `spx.status.json` claim.
- no-manual-state: A manually assigned label never overrides evidence-derived state.
