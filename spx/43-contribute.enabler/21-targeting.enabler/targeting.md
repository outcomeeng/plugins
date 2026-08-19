# Targeting

PROVIDES the resolved base repository, head repository, operator permission, and authorization state for one contribution
SO THAT the pull-request, issue, and fork-currency flows
CAN name their target explicitly on every write instead of accepting whatever `gh` resolves from the checkout

`gh` resolves a fork's base to its parent, so a command that names no repository says nothing about where its artifact lands: a branch pushed to one repository and a pull request opened from it can reach a different organization entirely. Resolution runs before the first write and produces one classification the flows consume.

Permission is read from `viewerPermission` on the resolved base. `ADMIN`, `MAINTAIN`, and `WRITE` mean the operator controls that repository and the contribution belongs to a controlled-repository flow instead. `READ`, `TRIAGE`, and `NONE` mean another party owns it, which is this plugin's case and the case that requires authorization. `TRIAGE` carries issue and pull-request management without code-write access, so a collaborator holding it contributes to the base rather than controlling it. A git remote, the authenticated account name, and a successful push each report something other than the permission that governs the base, because an operator holds repositories across several organizations.

A contribution needs a head repository the operator can push to. The checkout supplies one only when it is itself a fork; working from a clone of the base repository is ordinary, and the head then sits in some account or organization the operator holds. Resolution therefore searches for a fork of the resolved base across the authenticated account and its organizations rather than inferring absence from the checkout.

Reading the checkout is where that default bites first. `gh` applies the same base-repository resolution to a read that names no repository, so a nameless read of a fork checkout answers for the parent: its fork state, its parent, and — in a chain of forks — a base two repositories from the one the contribution targets. The checkout's own repository comes from `origin` and is named in the read, so the rule the flows' writes obey binds the resolution that precedes them.

A search that matches once yields the head. A search that matches several times names them and stops, because the destination among them is the operator's choice. A search that matches nothing establishes absence, which is what makes the fork command it reports correct rather than a guess GitHub rejects.

## Assertions

### Mappings

- The observed fork state, resolved parent, permission class, and fork-search result map to exactly one classification — a controlled base, an upstream contribution, an ambiguous-head target, an absent-fork target, or a blocked target ([test](tests/test_target_resolution.mapping.l1.py))
- Each fork the search reports maps to the base it was forked from by that fork's own parent owner and name, matched without regard to case, because GitHub preserves a repository's case while matching it without one ([test](tests/test_fork_search.mapping.l1.py))

### Properties

- Every `viewerPermission` value outside the permission sets the resolver names blocks the target, under either fork state — the reported permission is an open string, and a value whose access level neither set states cannot be sorted into either one, so it blocks instead of defaulting ([test](tests/test_target_resolution.property.l1.py))

### Compliance

- ALWAYS: every write to the base repository names it explicitly, because a command that omits the repository publishes wherever `gh` resolves the default ([audit])
- ALWAYS: the checkout's own repository is read by naming it, because `gh` resolves a nameless read to the base it would publish to — for a fork checkout the parent, whose own fork state and parent then stand in for the head the contribution pushes from ([test](tests/test_target_resolution.compliance.l1.py))
- ALWAYS: a parent `gh` reports is read as its owner login and its name, in the single-repository view and the fork listing alike, because no `parent` object carries the repository's full name ([test](tests/test_target_resolution.compliance.l1.py))
- ALWAYS: an origin the checkout cannot name blocks the target, whether the read fails or succeeds reporting nothing, because the repository the contribution pushes from is then unknown and no later read establishes it ([test](tests/test_target_resolution.compliance.l1.py))
- ALWAYS: the operator's permission on the base comes from `viewerPermission` on the resolved base repository ([audit])
- ALWAYS: the controlling permission class is exactly `ADMIN`, `MAINTAIN`, and `WRITE`, and the contributing class is exactly `READ`, `TRIAGE`, and `NONE`; the resolver complies with this declaration, and the mapping evidence quantifies over the two classes rather than their members, because an oracle for the membership itself would restate the declaration in an artifact with no authority to make one ([audit])
- ALWAYS: a fork search that does not cover the accounts and organizations it enumerates blocks the target — a failed account read, a failed organization read, a failed owner listing, and a listing filling the page the search reads each leave absence unestablished ([test](tests/test_target_resolution.compliance.l1.py))
- ALWAYS: a base repository whose permission is `READ`, `TRIAGE`, or `NONE` requires authorization naming that base in the same turn before any artifact is created there ([audit])
- ALWAYS: authorization covers the artifact it named and that artifact's later revisions; a new pull request, a new issue, or a comment on an unrelated thread each require their own ([audit])
- ALWAYS: an absent fork stops the flow with the resolved base, the accounts and organizations that could hold the fork, and the exact fork command — the destination is the operator's choice, never resolution's ([audit])
- ALWAYS: absence of a head is established by searching the authenticated account and its organizations for a fork of the resolved base, never inferred from the checkout not being a fork ([test](tests/test_target_resolution.compliance.l1.py))
- NEVER: resolution selects among several forks of the resolved base — it names every match and stops, because the destination among them is the operator's choice ([test](tests/test_target_resolution.compliance.l1.py))
- NEVER: a permission class is inferred from a git remote, the authenticated account, or a successful push — none of the three reports the permission governing the base ([test](tests/test_target_resolution.compliance.l1.py))
