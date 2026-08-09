# Contribute

PROVIDES one sanctioned path for changes and reports sent to a repository the operator does not control
SO THAT a coding agent working in a fork or a read-only checkout
CAN publish a pull request, an issue, or a reply to that repository without resolving the target from a default, inferring permission from a git remote, or acting outside the operator's authorization

The plugin exposes five workflow skills — `/open-parent-pr`, `/manage-parent-pr`, `/open-parent-issue`, `/manage-parent-issue`, and `/sync-fork` — over one composed-only reference skill, `contribution-standards`, that carries the invariants holding for every artifact regardless of its type. The plugin depends on no other plugin and on no CLI beyond `git`, `gh`, and a Python interpreter, so a consumer installs it without adopting a methodology.

The surface is the complement of the outward-safety stop that a controlled-repository pull-request flow performs. That flow resolves the base repository, reads the operator's permission on it, and stops when the permission is `READ` or `NONE` or when the base resolves to a fork's parent. Those two stops are the cases this plugin handles, so the two surfaces partition every pull request between them and neither infers the other's case.

A contribution never reaches the operator's own default branch, so the merge lifecycle that authorizes integration does not govern it. Merge authority over the base repository belongs to its maintainer, and the flow's authority ends at publication and iteration.

Vocabulary is GitHub's. The **base** repository receives the contribution and is named by `--repo` and `--base`. The **head** repository and branch supply it and are named by `--head owner:branch`. The **parent** is what `gh repo view --json parent` reports for a fork. `upstream` names a git remote and nothing else; it is relative, because the base repository has a parent of its own, so it never identifies a target.

The plugin's assertions declare a contract for the consumer repositories it installs into. A consumer's own product truth binds its agent independently, and where both bind, the stricter governs.

## Assertions

### Compliance

- ALWAYS: every artifact leaving the operator's control — pull-request title and body, issue title and body, comment, and review reply — passes a prose review before it is sent, because the notification reaches every watcher when the artifact appears and deleting the artifact does not recall it ([audit])
- ALWAYS: a prose review runs whether or not a prose plugin is installed, and a review that ran unassisted is reported as such — the composition is an aid, never the condition for reviewing ([audit])
- ALWAYS: a defect claim carries the tool versions involved, the base commit it was observed against, the command that produced the observation, and at least one negative control showing the same method reporting the opposite result — without the control the claim cannot distinguish a defect from a broken measurement ([audit])
- ALWAYS: a contribution conforms to the base repository's own conventions — its contributing guide, its fixture and metadata schemas, the documents a change of that kind updates, and the commit style of its recent history — because a contribution shaped like the operator's repository is rework for the maintainer ([audit])
- NEVER: a lookalike stands in for the condition under observation — an environment that cannot be reproduced yields a claim marked unverified with the reason, never a substitute reported as observed ([audit])
- ALWAYS: the plugin's authored surface is five workflow skills — `/open-parent-pr`, `/manage-parent-pr`, `/open-parent-issue`, `/manage-parent-issue`, `/sync-fork` — over the composed-only `contribution-standards`, beside the lifecycle skill the build emits for every plugin ([audit])
- NEVER: the plugin requires another plugin or a methodology CLI to run — every skill completes with `git`, `gh`, and a Python interpreter alone ([audit])
