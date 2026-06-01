# Marketplace Skill Authoring Overrides

Loaded by `/standardizing-skills` `<repo_local_overlay>` when authoring or auditing skills in this repository. These specialize the base skill-authoring standards for the Outcome Engineering marketplace.

## Imperative names for standalone decision-record audit skills

The base standard prefers gerund skill names. In this marketplace the standalone decision-record audit skills use imperative `audit-{artifact}` names:

- `audit-adr`
- `audit-pdr`

Each is invoked as a direct command (`/audit-adr <path>`, `/audit-pdr <path>`) and ships no gerund command shim. `/auditing-skills` does not flag `audit-adr` or `audit-pdr` against the gerund preference.

The gerund preference still governs every other skill in the marketplace — the language audit skills (`auditing-python`, `auditing-typescript`, and their `-tests` / `-architecture` variants) and the generic `/auditing` orchestrator. This override is scoped to the two standalone decision-record audit skills only.
