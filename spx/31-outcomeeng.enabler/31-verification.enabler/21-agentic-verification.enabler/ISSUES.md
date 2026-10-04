# Issues: Agentic verification

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The prompt-caching decision's gate condition is stale

`spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md` re-derives with the external component's invocation design per `spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md`, and its gate condition names `anthropics/claude-code#34629`. That issue closed without resolution and the fork-session cache regression persists, so the three realization paths — the community request interceptor, partial amortization within one session, or staying single-turn — are an operator decision that no record holds. The old decision stays authoritative for the shipped harness until the cutover.

**Settlement condition.** The operator selects one realization path when the invocation-design work begins, and the caching decision records it with a gate condition that holds.
