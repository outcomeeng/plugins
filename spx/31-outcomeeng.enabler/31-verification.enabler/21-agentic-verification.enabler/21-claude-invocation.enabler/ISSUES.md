# Issues: Claude invocation

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The node is a declared placeholder without assertions

The node declares the Claude Code invocation substrate and holds no assertion, decision or implementation. They wait on the adapter implementations in the external component that [`spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md) places outside this repository, on a trace-provenance decision no record holds yet, and on the prompt-caching re-derivation `spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/ISSUES.md` records.

**Settlement condition.** The component's Claude adapter implementation exists and this node gains the assertions and decisions it complies with, or the node is removed.
