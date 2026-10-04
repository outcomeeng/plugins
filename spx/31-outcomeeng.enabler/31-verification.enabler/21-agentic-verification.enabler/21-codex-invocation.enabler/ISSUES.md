# Issues: Codex invocation

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The node is a declared placeholder without assertions

The node declares the Codex invocation substrate and holds no assertion, decision or implementation. They wait on the adapter implementations in the external component that `spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md` places outside this repository, and on a spike that establishes the Codex adapter's bounded headless invocation shape.

**Settlement condition.** The spike's result is recorded, the component's Codex adapter implementation exists, and this node gains the assertions and decisions it complies with, or the node is removed.
