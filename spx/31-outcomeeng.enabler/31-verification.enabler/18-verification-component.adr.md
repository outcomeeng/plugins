# Verification Component Sourcing

The verification toolchain's runtime machinery — the trace event schema implementation, contract schema, conformance checker, contract inference, run aggregation, eval-harness runners, and coding-agent runtime adapters — is implemented in a separately versioned component outside this repository, released independently and consumed as a pinned third-party dependency. The spec tree under `spx/31-outcomeeng.enabler/31-verification.enabler/` stays authoritative for the semantics; the component complies. The one in-consumer exception is the trace emitter shipped inside plugins, which is standard-library-only Python rendered into the plugin trees because shipped plugin scripts import no third-party package.

## Rationale

This mirrors the trusted-third-party lifecycle in `spx/12-shipped-scripting.adr.md`: proven logic lives in a component fully tested in its own right that this product consumes rather than maintains inline. Verification machinery serves any product consuming the methodology, so binding it to this repository's release cycle would couple every consumer's harness upgrade to a marketplace release and foreclose independent adoption of the conformance tooling; a separately versioned component gives the checker, schema, and adapters their own test, release, and publication cycle. The rejected alternative — implementing the verification machinery inside this repository — keeps every capability change a marketplace concern and makes the marketplace's own CI the only consumer that can prove it.

## Verification

- ALWAYS: a skill, spec, or CI surface depends on a component capability only when a release carrying it is published and the repository's pinned floor is advanced to that release
- NEVER: a shipped plugin script imports the component — the in-plugin emitter is standard-library-only
- ALWAYS: verification semantics are declared under `spx/31-outcomeeng.enabler/31-verification.enabler/` and the component complies — a component behavior contradicting a declaration is a component defect, never grounds to weaken the declaration
- ALWAYS: runner and framework selection inside the component is the component's implementation concern, judged by the contracts this subtree declares rather than prescribed by them
