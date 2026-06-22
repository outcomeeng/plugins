# Issues: Sessions Enabler

## 1. Pickup claim verifier cannot parse the current session frontmatter

`src/plugins/spec-tree/skills/pickup/scripts/verify_session_claims.py` extracts claims with line-anchored regexes (`_scalar`, `_string_list`) that match only the bare-key YAML form (`git_ref:`). The session serializer emits quoted keys (`"git_ref":`) and folded double-quoted scalars for long values, so `parse_session` matches nothing and `verify()` returns `[]` — no verdicts, no error. Claim reconciliation at pickup silently produces nothing for any current-format session.

### Root layer

The producer (spx) owns the session format — `spx session handoff` writes it with a real YAML writer. The verifier re-implementing a YAML reader is the wrong layer, and a regex reader cannot reliably parse folded double-quoted scalars with escapes. `spx/12-shipped-scripting.adr.md` already says complex parsing belongs in the tested CLI, not a shipped script.

The node's current tests (`tests/test_pickup_verification.{mapping,compliance}.l1.py`) and the harness `write_session_file` in `outcomeeng_testing/harnesses/verify_session_claims.py` write the bare-key form (`git_ref: "value"`), which the regex does match — so they pass while never exercising the quoted-key, folded-scalar format real sessions use. They give false confidence: the regression is invisible to the suite. Phase 2 must move the harness and tests onto the real serializer format and pin the regression.

### Fix (blocked on spx)

The verifier should read parsed claims from `spx session show --format json` and reconcile those, never parse YAML itself.

- Blocked on spx repo session `2026-06-22_14-28-45` (add `spx session show --format json`). The published-floor rule forbids depending on an unpublished spx capability, so this cannot ship until that capability is published.
- Tracked for pickup as plugins session `2026-06-22_14-38-40`.

Once unblocked:

- Advance `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) to the published version; bump CI `SPX_VERSION` (`.github/workflows/check.yml`).
- Amend `spx/21-spec-tree.enabler/76-sessions.enabler/65-pickup-claim-verification.adr.md`: the `NEVER: the verification depends on an spx CLI capability beyond the published spx spec status contract` assertion is over-narrow. The verification script complies with it today — it parses the file itself and calls only `spx spec status` — but the redesign needs `spx session show --format json`, and the surrounding pickup skill already depends on `spx session show`, `spx session pickup`, and `spx session handoff`, so the boundary the assertion draws is not a real guardrail. Replace it with the published-floor rule scoped to the spx session capabilities the verifier uses. This is a decision change (adr-auditor gate, downstream alignment), not part of this coordination note.
- Rewrite `verify_session_claims.py` to consume `spx session show --format json`; drop the regex parser.
- Align `sessions.md` assertions; add tests covering quoted keys and folded scalars; gate with test-evidence and skill auditors; then `/merge`.
