<!-- Generated from the complete producer set:
{producer_paths}
-->

Apply the complete producer below to the supplied changeset package. The package carries what the producer's own commands return for one exact committed changeset: `scope` holds the full `base` and `head` commit identities and the `changed_paths` the scope resolver reports; `commits` holds the commit messages of the changeset; `artifacts` holds, for each changed path, the added and deleted line counts `git diff` reports and the committed content `git show` returns, where `elided_lines` counts committed lines the package leaves out; `repository_declarations` holds the committed declaration files that the producer's attribution step reads, with `null` marking a declaration the repository does not carry.

This evaluation resolves no scope, loads no foundation, plugin version, or request, runs no `spx` command, and writes no run file. Treat the producer's request contract, plugin version, scope resolution, foundation load, and run start as satisfied by the package, and read the package in place of the producer's `git diff`, `git show`, and `Read` commands. Perform the producer's judgment steps against the package and report the sealed run those steps would record and finish. Return only one JSON object with these fields:

- `terminalStatus`: `approved` or `rejected`, derived as the producer's finish step derives it.
- `units`: one object per unit the run records, each carrying `unitId` (the unit key the producer's unit identities form from the package's `base` and `head` commit identities, verbatim), `auditKind`, and `coverageStatus`.
- `findings`: one object per recorded finding, each carrying `unitId` (the key of the unit that records it) and `rule` (an identifier from the producer's rule catalog). A `split-required` finding also carries `clusters`, one object per cluster line of its `evidence.observed` with `id`, `authored`, `generated`, and `dependsOn` (the cluster identifiers its line names, empty for none), and `reviewUnitSequence`, one object per line of its `evidence.expected` with `reviewUnit`, `clusters`, and `dependsOn` (the review-unit identifiers its line names, empty for none). The list is empty when the run records no finding.

<pre><code>
{producer_files}
</code></pre>

The changeset package (JSON-encoded):

```json
{input_json}
```
