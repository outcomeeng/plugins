# Issues - workflow observability

## Consent flag order differs between the spec and CLI contract

The authorized mutation scenario documents
`mutation_gate.py check <command> --user-instructed`, while the CLI parses the
command through `argparse.REMAINDER` and requires `--user-instructed` before the
command tokens. The linked scenario evidence exercises the CLI's required
order.

Reconcile the assertion with the source-owned CLI contract, then rerun the
node's scenario evidence and test-evidence audit.
