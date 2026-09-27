<failure_modes>

**Infrastructure encoded the verdict**

- **What happened:** A harness returned booleans whose names and implementations already decided whether each requirement passed, leaving the linked test to assert only that boolean.
- **Why it failed:** The predicate moved out of the linked test, so reversing the linked assertion no longer changed the harness behavior and the spec-to-test evidence chain became indirect.
- **How to avoid:** Infrastructure exposes observations, resources, and recording collaborators. The linked test alone applies assertion APIs and owns the behavioral predicate.

**Implementation logic generated both actual and expected values**

- **What happened:** Expected outputs came from the same table, parser, branch logic, or collaborator verdict method that produced the actual output.
- **Why it failed:** The oracle repeated the implementation; the same defect changed both sides and the test stayed green.
- **How to avoid:** Derive expectations from an independent contract, source-owned finite mapping, generated invariant, or real-system response.

**Test-local bindings laundered domain truth**

- **What happened:** Constants, local functions, fixture parameters, or renamed variables stored expected outputs, boundary bags, runner settings, or source-owned singleton values in the executed test file.
- **Why it failed:** Renaming the declaration preserved test ownership of data and configuration, hiding an invalid seam instead of correcting it.
- **How to avoid:** Move source truth to the production contract, variable domains to generators, execution policy to harnesses, and whole payloads to inert fixtures. Keep only the assertion flow in the test.

**A heading selected the assertion type**

- **What happened:** An `ALWAYS` or `NEVER` rule under a Compliance section was labeled `compliance`, or a universal rule was labeled `scenario`, without examining its quantifier and evidence domain.
- **Why it failed:** Section organization replaced semantic classification, producing an evidence strategy that could not prove the assertion.
- **How to avoid:** Read the quantifier first, then select mapping, conformance, compliance, or property from the universal domain, oracle, or violating boundary.

**A finite example bag impersonated stronger evidence**

- **What happened:** A few hand-picked cases were presented as a mapping over a complete domain or as a property over an open domain.
- **Why it failed:** The examples established only those cases; they provided neither source-owned finite completeness nor generated open-domain coverage.
- **How to avoid:** Import the complete finite domain from its source owner for mapping, or use a meaningful shrinking generator for property evidence.

**A mock replaced the behavior under assertion**

- **What happened:** A framework mock, fake repository, monkeypatch, intercepted response, or stub replaced persistence, transport, or another boundary while the test claimed that boundary worked.
- **Why it failed:** The test proved the replacement's configured response instead of production behavior.
- **How to avoid:** Use the real system at the lowest viable level. Permit a controlled implementation only after one Stage 5 exception matches, and preserve the real behavior boundary the assertion claims.

**Tool choice determined execution level**

- **What happened:** Filesystem, subprocess, browser, or runner labels automatically promoted a cheap local test to a heavier level.
- **Why it failed:** Runner identity and dependency category replaced measured execution pain, availability, safety, determinism, and observability.
- **How to avoid:** Classify level from operational reality. Temporary files and standard local tools remain `L1` when cheap and dependable; remote or credentialed systems remain `L3` regardless of runner.

**Property syntax wrapped a constant domain**

- **What happened:** A property framework generated one constant or selected from a copied handful of literals while the test claimed an open-domain invariant.
- **Why it failed:** Framework syntax added no domain variation, shrinking value, or systematic exploration.
- **How to avoid:** Generate a meaningful variable domain with replayable seeds and shrinking, or reclassify the evidence to the finite assertion type it actually supports.

**Boundary wiring multiplied across property cases**

- **What happened:** A CLI property test created a temporary Git repository and ran the full command for every generated input even though the generator varied a product-owned rule behind that boundary.
- **Why it failed:** The execution level permitted each dependency, while the property quantifier applied only to the product-owned input domain. Repeating boundary wiring multiplied setup cost without strengthening the invariant.
- **How to avoid:** Exercise the invariant over generated product-owned inputs at the narrow seam, then cover the real filesystem, Git, or CLI wiring with separately typed finite evidence. Keep the boundary inside the property only when the boundary itself is the variable behavior under assertion.

</failure_modes>
