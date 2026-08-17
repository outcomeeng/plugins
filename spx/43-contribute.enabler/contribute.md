# Contribute

PROVIDES one sanctioned path for changes and reports sent to a repository the operator does not control
SO THAT a coding agent working in a fork or a read-only checkout
CAN publish a pull request, an issue, or a reply to that repository without resolving the target from a default, inferring permission from a git remote, or acting outside the operator's authorization

The plugin exposes `/upstream`, which resolves the contribution target once and publishes it for the rest of the contribution, and five workflow skills that consume that target — `/open-upstream-pr`, `/manage-upstream-pr`, `/open-upstream-issue`, `/manage-upstream-issue`, and `/sync-fork` — over one composed-only reference skill, `contribution-standards`, that carries the invariants holding for every artifact regardless of its type. The plugin depends on no other plugin and on no CLI beyond `git`, `gh`, and a Python interpreter, so a consumer installs it without adopting a methodology.

`/upstream` carries the name of the artifact one invocation produces, which `spx/14-skill-naming.pdr.md` requires of every workflow skill. That artifact is the relationship a contribution runs against, and the marker the invocation emits carries the base, head, permission, and classification that relationship resolves to. Every verb available for it — resolve, establish, target — names the skill's own mechanism rather than anything an operator asks for, so the relationship's own term is the name. It is the marketplace's only user-invocable skill in that position, and `spx/local/skills.md` states the test this case meets.

Resolution happens once per contribution, not once per skill. A contribution is one arc — resolve the target, cut the branch, publish, then answer review — and the skills are its stages, so each stage reads the resolved target rather than re-deriving it. Re-resolution per stage would also repeat the fork search across every account and organization the operator holds.

The surface is the complement of the outward-safety stop that a controlled-repository pull-request flow performs. That flow resolves the base repository, reads the operator's permission on it, and stops when the permission is `READ`, `TRIAGE`, or `NONE` or when the base resolves to a fork's parent. Those two stops are the cases this plugin handles, so the two surfaces partition every pull request between them and neither infers the other's case.

A contribution never reaches the operator's own default branch, so the merge lifecycle that authorizes integration does not govern it. Merge authority over the base repository belongs to its maintainer, and the flow's authority ends at publication and iteration.

The **upstream** is the repository a fork came from — the operator's word for the relationship, and the plugin's name for it. **parent** is what `gh repo view --json parent` calls the same thing, so it belongs to the resolver that reads that field rather than to the surface an operator invokes.

Commands carry resolved values, never a relationship name. The **base** repository receives the contribution and is named by `--repo` and `--base`; the **head** repository and branch supply it and are named by `--head owner:branch`. A git remote named `origin` or `upstream` is a local label that may point anywhere, so every flow confirms what a remote resolves to before pushing or fetching through it.

The plugin's assertions declare a contract for the consumer repositories it installs into. A consumer's own product truth binds its agent independently, and where both bind, the stricter governs.

## Assertions

### Compliance

- ALWAYS: every artifact leaving the operator's control — pull-request title and body, issue title and body, comment, and review reply — passes a prose review before it is sent, because the notification reaches every watcher when the artifact appears and deleting the artifact does not recall it ([audit])
- ALWAYS: a prose review runs whether or not a prose plugin is installed, and a review that ran unassisted is reported as such — the composition is an aid, never the condition for reviewing ([audit])
- ALWAYS: a defect claim carries the tool versions involved, the base commit it was observed against, the command that produced the observation, and at least one negative control showing the same method reporting the opposite result — without the control the claim cannot distinguish a defect from a broken measurement ([audit])
- ALWAYS: a contribution conforms to the base repository's own conventions — its contributing guide, its fixture and metadata schemas, the documents a change of that kind updates, and the commit style of its recent history — because a contribution shaped like the operator's repository is rework for the maintainer ([audit])
- NEVER: a lookalike stands in for the condition under observation — an environment that cannot be reproduced yields a claim marked unverified with the reason, never a substitute reported as observed ([audit])
- ALWAYS: the plugin's authored surface is `/upstream` and five workflow skills that consume its result — `/open-upstream-pr`, `/manage-upstream-pr`, `/open-upstream-issue`, `/manage-upstream-issue`, `/sync-fork` — over the composed-only `contribution-standards`, beside the lifecycle skill the build emits for every plugin ([audit])
- ALWAYS: the contribution target is resolved once per contribution by `/upstream` and published for every later stage to read; a stage that needs the target invokes `/upstream` only when no resolved target is available ([audit])
- ALWAYS: a skill names the relationship as upstream where an operator reads it, and carries the resolved `base` and `head` in every command — because a relationship name identifies no repository and a remote carrying that name may point anywhere ([audit])
- NEVER: the plugin requires another plugin or a methodology CLI to run — every skill completes with `git`, `gh`, and a Python interpreter alone ([audit])
