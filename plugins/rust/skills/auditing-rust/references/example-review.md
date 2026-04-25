<overview>
These examples show the expected review shape for an approved change, a design rejection, and a mechanical-gate rejection.
</overview>

<approved_review>
Reviewing `src/config/` for a CLI crate after the repository validation sequence passed.

```text
CODE REVIEW

Decision: APPROVED

Verdict

| # | Concern                | Status | Detail                                          |
| - | ---------------------- | ------ | ----------------------------------------------- |
| 1 | Automated gates        | PASS   | `cargo fmt --check`, `clippy`, and tests passed |
| 2 | Test execution         | PASS   | 47/47 tests pass                                |
| 3 | Function comprehension | PASS   | 12 functions, no surprises                      |
| 4 | Design coherence       | PASS   | seams are explicit and ownership is clear       |
| 5 | Import structure       | PASS   | `crate::` and local `super::` usage is coherent |
| 6 | ADR/PDR compliance     | PASS   | build ADR constraints are reflected in code     |
```

Code meets standards.
</approved_review>

<rejected_design_review>
Reviewing `src/orders/`.

```text
CODE REVIEW

Decision: REJECTED

Verdict

| # | Concern                | Status | Detail                                             |
| - | ---------------------- | ------ | -------------------------------------------------- |
| 1 | Automated gates        | PASS   | full validation sequence passed                    |
| 2 | Test execution         | PASS   | 23/23 tests pass                                   |
| 3 | Function comprehension | REJECT | `process_orders` mixes pricing logic and email I/O |
| 4 | Design coherence       | REJECT | pure computation and boundary calls are tangled    |
| 5 | Import structure       | PASS   | module imports are coherent                        |
| 6 | ADR/PDR compliance     | REJECT | ADR requires injected email boundary               |
```

<findings>
<finding name="process_orders_tangles_logic_with_io">
Where: `src/orders/processor.rs:42`
Concern: Function comprehension, Design coherence
Why this fails: Predict: `process_orders` computes and returns order summaries. Verify: the function computes totals, persists state, and sends emails through a concrete client. The boundary call prevents isolated verification of the pricing logic.

Correct approach:

```rust
fn compute_order_summaries(orders: &[Order]) -> Vec<OrderSummary> {
    orders.iter().map(OrderSummary::from).collect()
}

trait EmailSender {
    fn send(&self, summary: &OrderSummary) -> Result<(), EmailError>;
}

fn process_orders<S: EmailSender>(
    orders: &[Order],
    sender: &S,
) -> Result<(), ProcessOrdersError> {
    for summary in compute_order_summaries(orders) {
        sender.send(&summary)?;
    }
    Ok(())
}
```

</finding>

<finding name="direct_email_client_dependency_violates_adr">
Where: `src/orders/processor.rs:3`
Concern: ADR/PDR compliance
Why this fails: The module imports a concrete email client directly even though the ADR requires an injected seam for external services.

Correct approach:

```rust
trait EmailSender {
    fn send(&self, summary: &OrderSummary) -> Result<(), EmailError>;
}
```

</finding>
</findings>

<required_changes>

1. Extract pure pricing logic from `process_orders`
2. Inject the email boundary through a trait or narrow function seam
3. Add a regression test covering the separated logic path

</required_changes>
</rejected_design_review>

<rejected_mechanical_gate_review>

```text
CODE REVIEW

Decision: REJECTED

Verdict

| # | Concern                | Status | Detail                         |
| - | ---------------------- | ------ | ------------------------------ |
| 1 | Automated gates        | REJECT | `cargo clippy` reports warning |
| 2 | Test execution         | --     | Blocked by Phase 1 failure     |
| 3 | Function comprehension | --     | Blocked by Phase 1 failure     |
| 4 | Design coherence       | --     | Blocked by Phase 1 failure     |
| 5 | Import structure       | --     | Blocked by Phase 1 failure     |
| 6 | ADR/PDR compliance     | --     | Blocked by Phase 1 failure     |
```

<required_changes>

1. Fix the `clippy` failure and rerun the full validation sequence

</required_changes>
</rejected_mechanical_gate_review>
