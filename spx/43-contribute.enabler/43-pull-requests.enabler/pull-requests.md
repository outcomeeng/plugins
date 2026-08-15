# Pull Requests

PROVIDES the opening and management of a pull request against a repository the operator does not control
SO THAT a change developed in a fork
CAN reach that repository's maintainer already verified against the maintainer's own checks, and continue through review without a second flow

The operator cannot push to the base repository and cannot merge there, so the flow's authority ends at publication and iteration. Every revision is a push to the head branch, which updates the open pull request in place.

The maintainer's own verification is the verification that matters. A contribution that passes the base repository's declared checks before it opens spends its review on substance; one that does not spends it on what a local run would have reported.

The review loop runs on comments. Requesting a reviewer, dismissing a review, and clearing a changes-requested decision are maintainer-side actions that a contributor's permission does not reach, so a comment stating what changed is the re-request.

## Assertions

### Compliance

- ALWAYS: a contribution branch is cut from the base repository's default branch, because a branch cut from a stale head default carries unrelated divergence into the diff ([audit])
- ALWAYS: the base repository's own declared verification — its contributing guide, its workflow files, and its build and test targets — runs locally and reports success before the pull request opens ([audit])
- ALWAYS: a declared check that cannot run locally is named in the pull-request body as unverified, with the reason it could not run ([audit])
- ALWAYS: a revision is appended to the head branch as a new push, never force-pushed over a branch a reviewer has already read ([audit])
- ALWAYS: re-requesting review is a comment stating what changed — the contributor-side permission failure on reviewer request is the expected path, not an error to retry ([audit])
- ALWAYS: an unsolicited contribution, or one whose conformance to the base repository's conventions remains uncertain, opens as a draft ([audit])
- NEVER: the management pass polls, watches, or waits on the pull request — it reads current state once, acts on it, and returns ([audit])
