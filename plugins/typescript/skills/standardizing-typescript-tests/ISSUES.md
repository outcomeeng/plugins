# Issues

## Testing methodology rename gap

The canonical testing methodology now separates:

- evidence mode
- execution level
- runner

This skill still encodes legacy filename and level language.

## Mismatches to remove

- `.unit.test.ts`
- `.integration.test.ts`
- `.e2e.test.ts`
- browser `.spec.ts` guidance used as runner signaling
- tables, examples, and success criteria that treat those labels as canonical

## Target naming model

Use:

```text
<subject>.<evidence>.<level>[.<runner>].test.ts
```

Examples:

- `dispatch.mapping.l1.test.ts`
- `browser-auth.scenario.l2.playwright.test.ts`
- `payments.conformance.l3.test.ts`

## Required follow-up

Update this standardizing skill so it defines:

- evidence tokens: `scenario`, `mapping`, `conformance`, `property`, `compliance`
- level tokens: `l1`, `l2`, `l3`
- runner-token rule: omit for the default runner, add one for a non-default runner
- explicit `playwright` runner tokens instead of `.spec.ts` signaling
- the orthogonality rule: runner does not imply level, and level does not imply runner

## Downstream impact

`testing-typescript` and `auditing-typescript-tests` must later consume these updated standards instead of carrying independent naming policy.
