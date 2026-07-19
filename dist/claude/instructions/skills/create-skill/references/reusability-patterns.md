<overview>

Create reusable skills by separating stable domain knowledge from choices that vary per request. Encode stable rules and procedures; resolve variable inputs through repository truth or focused operator questions.

</overview>

<knowledge_model>

Production skills combine two knowledge classes:

| Class                | Content                                                  | Typical location                                     |
| -------------------- | -------------------------------------------------------- | ---------------------------------------------------- |
| Procedural knowledge | Ordered actions, decisions, validation, failure handling | `SKILL.md` or `workflows/`                           |
| Domain knowledge     | Contracts, patterns, anti-patterns, external conventions | `references/` or a shared `{domain}-standards` skill |

Keep procedures near the route that executes them. Keep shared standards in a reference skill when multiple skills need the same rules.

</knowledge_model>

<varies_and_constant>

Before authoring, classify the domain:

| Question                                   | Authoring consequence                                       |
| ------------------------------------------ | ----------------------------------------------------------- |
| What changes between valid requests?       | Intake fields or conditional routes                         |
| What remains true for every request?       | Inline principles, workflow invariants, or domain standards |
| Which choices can repository truth settle? | Read and derive; do not ask                                 |
| Which choices belong to the operator?      | Ask only when the answer changes behavior or location       |
| Which boundaries reject the request?       | Explicit constraints and actionable failures                |

Never hardcode a variable merely because the first example supplied one value.

</varies_and_constant>

<domain_examples>

<example name="visualization">

| Varies                                                       | Constant                                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------------ |
| Data shape, chart type, rendering library, interaction level | Accessibility, responsive behavior, validation, loading and error states |

Resolve the data and presentation choices; encode the quality invariants.

</example>

<example name="web_application">

| Varies                                                                                     | Constant                                                                            |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Data store, styling system, authentication provider, deployment target, requested features | Component boundaries, error handling, security, performance, repository conventions |

Read the existing stack before asking for a preference.

</example>

<example name="deployment">

| Varies                                                            | Constant                                                                      |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Platform, orchestration, configuration system, environment, scale | Rollback, health checks, secret handling, observability, authority boundaries |

Treat every external mutation as an explicit authority boundary.

</example>

<example name="api_integration">

| Varies                                                   | Constant                                                                               |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Service, endpoints, authentication, schemas, rate limits | Input validation, timeouts, retry classification, response validation, secret handling |

Verify service-specific claims against current primary documentation.

</example>

</domain_examples>

<abstraction_levels>

| Level                            | Shape                                                      | Guidance                                                              |
| -------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------- |
| Domain-agnostic                  | Error handling, testing strategy, documentation generation | Reusable across products                                              |
| Domain-specific and tool-neutral | Visualization, deployment, API integration                 | Prefer when tools legitimately vary                                   |
| Tool-specific                    | Next.js, PostgreSQL, Kubernetes                            | Keep requests adaptable within the tool                               |
| Requirement-specific             | One sales chart or one fixed login form                    | Keep in project instructions or implementation, never a general skill |

</abstraction_levels>

<clarification_design>

Ask a question only when all conditions hold:

1. Repository truth and supplied context do not answer it.
2. Different answers materially change behavior, risk, ownership, or artifact location.
3. The operator owns the choice.

For bounded choices, present mutually exclusive options with their consequences. Preserve free-form input for product intent that cannot be reduced to safe options.

</clarification_design>

<validation>

- Variable fields, schemas, tools, and paths are derived or requested rather than embedded as one example.
- Stable domain constraints appear once in the owning standards or workflow surface.
- Every clarification changes a documented branch of behavior.
- The skill supports more than one valid request inside its declared abstraction level.
- Scope boundaries identify requests the skill does not own.

</validation>

<anti_patterns>

| Pattern                                  | Failure                                                   | Correction                                                    |
| ---------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------- |
| Hardcoded first example                  | One request becomes the domain contract                   | Separate variable input from stable rules                     |
| Tool lock-in in a domain-level skill     | Valid ecosystems become unsupported accidentally          | Ask or derive the tool; keep domain invariants stable         |
| Feature enumeration                      | A fixed product backlog replaces a reusable capability    | Ask for requested features and encode category-level patterns |
| Questions repository truth answers       | Intake becomes noisy and shifts decisions to the operator | Inspect the repository first                                  |
| Shared rules in one creator's references | Other consumers duplicate or cannot load them             | Extract a `{domain}-standards` reference skill                |

</anti_patterns>
