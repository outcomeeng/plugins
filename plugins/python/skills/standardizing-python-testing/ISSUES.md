# Issues

## Testing methodology rename gap

The canonical testing methodology now separates:

- evidence mode
- execution level
- runner

This skill still encodes legacy filename and level language.

## Mismatches to remove

- `.unit.py`
- `.integration.py`
- `.e2e.py`
- tables and examples that present those labels as canonical categories
- success criteria that require those suffixes

## Target naming model

Use:

```text
test_<subject>.<evidence>.<level>[.<runner>].py
```

Examples:

- `test_config_loader.mapping.l1.py`
- `test_browser_auth.scenario.l2.playwright.py`
- `test_checkout_flow.scenario.l3.py`

## Required follow-up

Update this standardizing skill so it defines:

- evidence tokens: `scenario`, `mapping`, `conformance`, `property`, `compliance`
- level tokens: `l1`, `l2`, `l3`
- runner-token rule: omit for the default runner, add one for a non-default runner
- the orthogonality rule: runner does not imply level, and level does not imply runner

## Downstream impact

`testing-python` and `auditing-python-tests` must later consume these updated standards instead of carrying independent naming policy.
