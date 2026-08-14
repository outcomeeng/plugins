# Targeting

PROVIDES the resolved base repository, head repository, operator permission, and authorization state for one contribution
SO THAT the pull-request, issue, and fork-currency flows
CAN name their target explicitly on every write instead of accepting whatever `gh` resolves from the checkout

`gh` resolves a fork's base to its parent, so a command that names no repository says nothing about where its artifact lands: a branch pushed to one repository and a pull request opened from it can reach a different organization entirely. Resolution runs before the first write and produces one classification the flows consume.

Permission is read from `viewerPermission` on the resolved base. `ADMIN`, `MAINTAIN`, and `WRITE` mean the operator controls that repository and the contribution belongs to a controlled-repository flow instead. `READ`, `TRIAGE`, and `NONE` mean another party owns it, which is this plugin's case and the case that requires authorization. `TRIAGE` carries issue and pull-request management without code-write access, so a collaborator holding it contributes to the base rather than controlling it. A git remote, the authenticated account name, and a successful push each report something other than the permission that governs the base, because an operator holds repositories across several organizations.

A contribution needs a head repository the operator can push to. When no fork of the base exists, the destination is a choice among the operator's accounts and organizations that resolution has no evidence to make.

## Assertions

### Mappings

- The observed fork state, resolved parent, and `viewerPermission` value map to exactly one classification — a controlled base, a parent contribution, an absent-fork target, or a blocked target ([test](tests/test_target_resolution.mapping.l1.py))
- Each skill that resolves a target carries its own entrypoint, and every one of them loads the single shared resolver rather than a copy ([test](tests/test_resolver_entrypoint.mapping.l1.py))

### Properties

- Every `viewerPermission` value outside the permission sets the resolver names blocks the target, under either fork state — the reported permission is an open string, and a value whose access level neither set states cannot be sorted into either one, so it blocks instead of defaulting ([test](tests/test_target_resolution.property.l1.py))

### Compliance

- ALWAYS: every write to the base repository names it explicitly, because a command that omits the repository publishes wherever `gh` resolves the default ([audit])
- ALWAYS: the operator's permission on the base comes from `viewerPermission` on the resolved base repository ([audit])
- ALWAYS: a base repository whose permission is `READ`, `TRIAGE`, or `NONE` requires authorization naming that base in the same turn before any artifact is created there ([audit])
- ALWAYS: authorization covers the artifact it named and that artifact's later revisions; a new pull request, a new issue, or a comment on an unrelated thread each require their own ([audit])
- ALWAYS: an absent fork stops the flow with the resolved parent, the accounts and organizations that could hold the fork, and the exact fork command — the destination is the operator's choice, never resolution's ([audit])
- NEVER: a permission class is inferred from a git remote, the authenticated account, or a successful push — none of the three reports the permission governing the base ([test](tests/test_target_resolution.compliance.l1.py))
- NEVER: an entrypoint whose provider skill is absent resolves quietly — the missing resolver raises at load, naming the path it looked for, because a grant reaching into the provider's directory would instead stop matching and degrade to a permission prompt ([test](tests/test_resolver_entrypoint.compliance.l1.py))
