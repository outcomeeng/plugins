"""Compliance evidence for the operate-change script.

Each test exercises one ALWAYS or NEVER rule of the spec with a case that
breaks it and, where the rule admits one, a case that keeps it. The script
reaches the Change Store only through its command runner, so each case runs
it against the simulated GitHub store of
`outcomeeng_testing.harnesses.operate_change`, which records every command,
fails a chosen one, or lands another writer's edit between two of them.
"""

from __future__ import annotations

import inspect

import pytest

from outcomeeng_testing.harnesses.operate_change import (
    LOGIN,
    MERGE_COMMIT,
    OTHER_SESSION,
    PRODUCT_REPOSITORY,
    STORE,
    UNMERGED_COMMIT,
    SimulatedGitHub,
    claim_block,
    held,
    is_write,
    load_script,
    product_repository,
    request,
    run,
    run_main,
    sha256,
    write_kind,
)

script = load_script()

BASE = "c" * 40
SOI = (
    "## Statement of Intent\n\n"
    "- Output: An example Output.\n"
    "- Why: An example reason.\n"
    "- Verification: An example verification.\n"
)
TARGET = "spx/20-example.enabler/example.md"
LEAF = (
    SOI
    + f"\n## Declarations\n\n### {TARGET}\n\n```diff\n+ - one: ALWAYS: an example\n```\n\nInfrastructure: one none\n"
)
HANDOFF = {"branch": "work/example", "head": "d" * 40, "next": TARGET}
CLOSE = {
    "merge_gates_passed": True,
    "results_complete": True,
    "declarations_on_default": True,
    "audit_at_close": "approved",
}
CHANGESET = {
    "url": f"https://github.com/{PRODUCT_REPOSITORY}/pull/7",
    "merge_commit": MERGE_COMMIT,
}


def store(
    maturity: str, lifecycle: str, body: str = LEAF, base: str = BASE, number: int = 10
) -> SimulatedGitHub:
    github = SimulatedGitHub()
    github.add(number, body, Maturity=maturity, Lifecycle=lifecycle, Base=base)
    return github


def pair(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    issue = github.issues[number]
    return {"body_sha256": sha256(issue.body), "base": issue.fields["Base"]}


def check(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    return {"status": "pass", "body_sha256": sha256(github.issues[number].body)}


def blocks(github: SimulatedGitHub, number: int = 10) -> list[dict[str, str]]:
    return [script.parse_block(body) for body in github.blocks(number)]


def applicable_held() -> SimulatedGitHub:
    github = store("Applicable", "Available")
    held(github, 10)
    return github


def to_applicable(github: SimulatedGitHub, **values: object) -> dict[str, object]:
    payload = request(
        "advance",
        10,
        "holder",
        form_check=check(github),
        audit=pair(github),
        audit_status="approved",
    )
    payload.update(values)
    return payload


# ----------------------------------------------------------------- closing


@pytest.mark.parametrize("broken", ["ancestor", *CLOSE])
def test_leaf_applied_only_on_its_close_condition(broken: str) -> None:
    github = applicable_held()
    if broken == "ancestor":
        payload = request(
            "applied",
            10,
            "holder",
            changeset={**CHANGESET, "merge_commit": UNMERGED_COMMIT},
            close_check=CLOSE,
        )
    else:
        payload = request(
            "applied",
            10,
            "holder",
            changeset=CHANGESET,
            close_check={
                **CLOSE,
                broken: False if broken != "audit_at_close" else "rejected",
            },
        )

    result = run(github, payload)

    assert result["status"] == "refused"
    assert github.issues[10].fields["Lifecycle"] == "Available"
    assert (
        run(
            github,
            request("applied", 10, "holder", changeset=CHANGESET, close_check=CLOSE),
        )["status"]
        == "done"
    )


@pytest.mark.parametrize("terminal", ["Applied", "Abandoned"])
@pytest.mark.parametrize("move", [member.value for member in script.Transition])
def test_terminal_change_never_moves(terminal: str, move: str) -> None:
    github = store("Applicable", terminal)
    github.issues[10].state = "CLOSED"
    held(github, 10)

    result = run(
        github,
        request(
            move,
            10,
            "operator",
            target="Sliced",
            reason="r",
            lower_cause="reopened",
            handoff=HANDOFF,
            changeset=CHANGESET,
            close_check=CLOSE,
        ),
    )

    assert result["status"] == "refused"
    assert github.writes() == []


def test_terminal_kept_no_delete_command() -> None:
    github = applicable_held()
    github.add(11, LEAF, Maturity="Applicable", Lifecycle="Available", Base=BASE)
    github.issues[11].blocked_by.append(10)

    run(
        github,
        request(
            "lower",
            10,
            "holder",
            target="Sliced",
            reason="a decision line",
            lower_cause="decision-line",
        ),
    )
    run(github, request("abandoned", 10, "operator"))

    assert github.writes()
    for command in github.commands:
        text = " ".join(command).lower()
        assert "delete" not in text and "--method delete" not in text
        assert "remove-label" not in text and "transfer" not in text


def test_lower_claim_keeps_or_releases() -> None:
    kept = applicable_held()
    result = run(
        kept,
        request(
            "lower",
            10,
            "holder",
            target="Sliced",
            reason="a decision line",
            lower_cause="decision-line",
        ),
    )
    assert result["status"] == "done"
    assert "release" not in result
    assert kept.issues[10].assignees == [LOGIN]

    released = applicable_held()
    result = run(
        released,
        request(
            "lower",
            10,
            "holder",
            target="Sliced",
            reason="the Application check failed",
            lower_cause="application-check",
            handoff=HANDOFF,
        ),
    )
    assert result["status"] == "done"
    assert result["release"]["status"] == "done"
    assert released.issues[10].assignees == []
    assert [b["transition"] for b in blocks(released)][-2:] == ["lower", "release"]

    missing = applicable_held()
    result = run(
        missing,
        request(
            "lower",
            10,
            "holder",
            target="Sliced",
            reason="the Application check failed",
            lower_cause="application-check",
        ),
    )
    assert result["status"] == "refused"
    assert missing.writes() == []


# ----------------------------------------------------------------- binding


def test_review_binding_on_advance_to_sliced() -> None:
    github = store("Framed", "Submitted")
    stale = {"body_sha256": sha256("another body"), "base": BASE}

    refused = run(
        github,
        request("advance", 10, "operator", form_check=check(github), review=stale),
    )
    assert refused["status"] == "refused"
    assert refused["reason"] == "review-binding"

    done = run(
        github,
        request(
            "advance", 10, "operator", form_check=check(github), review=pair(github)
        ),
    )
    assert done["status"] == "done"


def test_review_binding_on_claim_for_application() -> None:
    github = store("Applicable", "Available")
    stale = {"body_sha256": sha256("another body"), "base": BASE}

    assert (
        run(github, request("claim", 10, "agent", review=stale))["status"] == "refused"
    )
    assert github.writes() == []
    assert (
        run(github, request("claim", 10, "agent", review=pair(github)))["status"]
        == "done"
    )


def test_review_binding_comment_only_while_the_pair_stands() -> None:
    github = store("Framed", "Submitted")
    reviewed = pair(github)

    def edit_after_maturity(sim: SimulatedGitHub, command: tuple[str, ...]) -> None:
        if is_write(command) and write_kind(command) == "maturity":
            sim.edit_body(10, LEAF + "\nan edit from another writer\n")

    github.after = edit_after_maturity
    result = run(
        github,
        request("advance", 10, "operator", form_check=check(github), review=reviewed),
    )

    assert result["status"] == "failed"
    assert result["reason"] == "binding-raced"
    assert result["failed_write"] == "comment"
    assert all(write_kind(command) != "comment" for command in github.writes())


@pytest.mark.parametrize("broken", ["body", "base", "status"])
def test_audit_binding(broken: str) -> None:
    github = store("Sliced", "Available")
    held(github, 10)
    audit = pair(github)
    status = "approved"
    if broken == "body":
        audit = {**audit, "body_sha256": sha256(LEAF + "\nanother revision\n")}
    elif broken == "base":
        audit = {**audit, "base": "e" * 40}
    else:
        status = "rejected"

    assert (
        run(github, to_applicable(github, audit=audit, audit_status=status))["status"]
        == "refused"
    )
    assert github.issues[10].fields["Maturity"] == "Sliced"
    assert run(github, to_applicable(github))["status"] == "done"


def reviewed_repository(
    target_texts: tuple[str, str],
    record_texts: tuple[str, str] = ("decision", "decision"),
):
    return product_repository(
        [
            {
                TARGET: target_texts[0],
                "spx/20-example.enabler/15-rule.pdr.md": record_texts[0],
            },
            {
                TARGET: target_texts[1],
                "spx/20-example.enabler/15-rule.pdr.md": record_texts[1],
                "other.txt": "x",
            },
        ]
    )


def carried_advance(
    github: SimulatedGitHub, root: str, reviewed_body: str, reviewed_base: str
) -> dict[str, object]:
    payload = request(
        "advance",
        10,
        "operator",
        form_check=check(github),
        review={"body_sha256": sha256(reviewed_body), "base": reviewed_base},
        review_body=reviewed_body,
    )
    return run(github, payload, root=root)


def test_review_carry_forward() -> None:
    with reviewed_repository(("same", "same")) as (root, (old, new)):
        github = store(
            "Framed",
            "Submitted",
            body=LEAF.replace("An example reason.", "An edited reason."),
            base=new,
        )
        assert carried_advance(github, root, LEAF, old)["status"] == "done"

    with reviewed_repository(("same", "same")) as (root, (old, new)):
        github = store(
            "Framed",
            "Submitted",
            body=LEAF.replace("an example", "an edited example"),
            base=new,
        )
        assert carried_advance(github, root, LEAF, old)["status"] == "refused"

    with reviewed_repository(("before", "after")) as (root, (old, new)):
        github = store("Framed", "Submitted", body=LEAF, base=new)
        assert carried_advance(github, root, LEAF, old)["status"] == "refused"

    with reviewed_repository(("same", "same"), ("decision", "amended decision")) as (
        root,
        (old, new),
    ):
        github = store("Framed", "Submitted", body=LEAF, base=new)
        assert carried_advance(github, root, LEAF, old)["status"] == "refused"

    with reviewed_repository(("same", "same")) as (root, (old, new)):
        github = store("Framed", "Submitted", body=LEAF, base=new)
        assert carried_advance(github, root, LEAF, "f" * 40)["status"] == "refused"


def test_review_part_context() -> None:
    table = "### spx/20-example.enabler/example.md\n\n```diff\n  | Case | Value |\n+ | one | x |\n```\n"
    reviewed = SOI + "\n## Declarations\n\n" + table
    context_changed = reviewed.replace("| Case | Value |", "| Case | Other |")
    with reviewed_repository(("same", "same")) as (root, (old, new)):
        github = store("Framed", "Submitted", body=context_changed, base=new)
        assert carried_advance(github, root, reviewed, old)["status"] == "refused"

    node = "### spx/20-example.enabler\n\n```diff\ndeleted file\n```\n"
    reviewed = SOI + "\n## Declarations\n\n" + node
    with product_repository(
        [
            {TARGET: "a", "spx/20-example.enabler/child/child.md": "one"},
            {TARGET: "a", "spx/20-example.enabler/child/child.md": "two"},
        ]
    ) as (root, (old, new)):
        github = store("Framed", "Submitted", body=reviewed, base=new)
        assert carried_advance(github, root, reviewed, old)["status"] == "refused"


# ------------------------------------------------------ structure and blockers


def with_child(github: SimulatedGitHub, state: str = "OPEN") -> None:
    github.add(11, LEAF, Maturity="Proposed", Lifecycle="Available", Parent=10)
    github.issues[11].state = state


def test_change_type_derives_from_relations() -> None:
    parent = store("Sliced", "Available", body=SOI)
    with_child(parent)
    held(parent, 10)
    result = run(parent, to_applicable(parent))
    assert result["status"] == "refused"
    assert result["reason"] == "parent"

    leaf = store("Sliced", "Available")
    held(leaf, 10)
    assert run(leaf, to_applicable(leaf))["status"] == "done"


def test_parent_maturity() -> None:
    github = store("Proposed", "Submitted", body=SOI)
    with_child(github)
    assert (
        run(github, request("advance", 10, "operator", form_check=check(github)))[
            "status"
        ]
        == "done"
    )

    child_moves = SimulatedGitHub()
    child_moves.add(10, SOI, Maturity="Framed", Lifecycle="Available", Base=BASE)
    child_moves.add(
        11, LEAF, Maturity="Proposed", Lifecycle="Submitted", Parent=10, Base=BASE
    )
    assert (
        run(
            child_moves,
            request("advance", 11, "operator", form_check=check(child_moves, 11)),
        )["status"]
        == "done"
    )
    assert all(
        command[3] != "10" for command in child_moves.writes() if command[1] == "issue"
    )
    assert all("I_10" not in " ".join(command) for command in child_moves.writes())


def test_blocker_abandoned_passes_or_returns() -> None:
    merged = SimulatedGitHub()
    merged.add(10, LEAF, Maturity="Sliced", Lifecycle="Available", Base=BASE)
    merged.add(11, LEAF, Maturity="Applicable", Lifecycle="Available", Base=BASE)
    merged.add(12, LEAF, Maturity="Sliced", Lifecycle="Available", Base=BASE)
    merged.issues[11].blocked_by.append(10)
    result = run(merged, request("abandoned", 10, "agent", merged_into=12))
    assert result["status"] == "done"
    assert 12 in merged.issues[11].blocked_by

    unmerged = SimulatedGitHub()
    unmerged.add(10, LEAF, Maturity="Sliced", Lifecycle="Available", Base=BASE)
    unmerged.add(11, LEAF, Maturity="Applicable", Lifecycle="Available", Base=BASE)
    unmerged.issues[11].blocked_by.append(10)
    result = run(unmerged, request("abandoned", 10, "operator"))
    assert result["status"] == "done"
    assert unmerged.issues[11].fields["Maturity"] == "Sliced"


def test_blocker_cycle_never_advances_or_claims() -> None:
    github = SimulatedGitHub()
    github.add(10, LEAF, Maturity="Framed", Lifecycle="Submitted", Base=BASE)
    github.add(11, LEAF, Maturity="Applicable", Lifecycle="Available", Base=BASE)
    github.issues[10].blocked_by.append(11)
    github.issues[11].blocked_by.append(10)

    assert (
        run(
            github,
            request(
                "advance", 10, "operator", form_check=check(github), review=pair(github)
            ),
        )["status"]
        == "refused"
    )
    assert (
        run(github, request("claim", 11, "agent", review=pair(github, 11)))["status"]
        == "refused"
    )
    assert github.writes() == []

    github.issues[11].blocked_by.clear()
    assert (
        run(
            github,
            request(
                "advance", 10, "operator", form_check=check(github), review=pair(github)
            ),
        )["status"]
        == "done"
    )


# ------------------------------------------------------- transition function


def test_transition_function_is_what_main_writes() -> None:
    assert inspect.isfunction(script.transition)
    first = store("Sliced", "Available")
    second = store("Sliced", "Available")
    payload = request("claim", 10, "agent")

    returned = script.transition(payload, run=first)
    code, written = run_main(second, payload)

    assert code == 0
    assert {k: v for k, v in returned.items() if k != "comment_url"} == {
        k: v for k, v in written.items() if k != "comment_url"
    }


# ---------------------------------------------------------- transition log


def every_transition() -> list[tuple[SimulatedGitHub, dict[str, object]]]:
    claim = store("Sliced", "Available")
    release = store("Sliced", "Submitted")
    held(release, 10)
    submit = store("Proposed", "Available")
    held(submit, 10)
    advance = store("Proposed", "Submitted")
    lower = store("Sliced", "Available")
    applied = applicable_held()
    abandoned = store("Framed", "Available")
    return [
        (claim, request("claim", 10, "agent")),
        (
            release,
            request(
                "release",
                10,
                "holder",
                handoff={
                    **HANDOFF,
                    "pull_request": f"https://github.com/{PRODUCT_REPOSITORY}/pull/7",
                },
            ),
        ),
        (
            submit,
            request(
                "submit",
                10,
                "holder",
                reopened="the Base moved under a settled replacement",
            ),
        ),
        (advance, request("advance", 10, "operator", form_check=check(advance))),
        (
            lower,
            request(
                "lower",
                10,
                "operator",
                target="Framed",
                reason="a settled judgment reopened",
                lower_cause="reopened",
            ),
        ),
        (
            applied,
            request("applied", 10, "holder", changeset=CHANGESET, close_check=CLOSE),
        ),
        (abandoned, request("abandoned", 10, "operator")),
    ]


def test_log_block_one_fenced_block_per_transition() -> None:
    for github, payload in every_transition():
        before = len(github.blocks(10))
        assert run(github, payload)["status"] == "done"
        posted = github.blocks(10)[before:]
        assert len(posted) == 1
        text = posted[0].strip()
        assert (
            text.startswith("```yaml\n")
            and text.endswith("```")
            and text.count("```") == 2
        )


def test_log_keys() -> None:
    for github, payload in every_transition():
        run(github, payload)
        block = blocks(github)[-1]
        identity = payload["identity"]
        assert block["transition"] == payload["transition"]
        assert block["maturity"] == github.issues[10].fields["Maturity"]
        assert (
            block["harness"],
            block["session"],
            block["machine"],
            block["worktree"],
        ) == (
            identity["harness"],
            identity["session"],
            identity["machine"],
            identity["worktree"],
        )


def test_log_extras_and_handoff_keys() -> None:
    texts = {}
    for github, payload in every_transition():
        run(github, payload)
        texts[payload["transition"]] = github.blocks(10)[-1]
    assert "reason:" in texts["lower"]
    assert "reason:" in texts["submit"]
    assert "handoff:" in texts["release"]
    for key in ("branch:", "head:", "next:", "pull_request:"):
        assert f"  {key}" in texts["release"]
    assert (
        "changeset:" in texts["applied"]
        and "  merge_commit: " + MERGE_COMMIT in texts["applied"]
    )
    assert all(
        "reason:" not in texts[t] for t in ("claim", "advance", "applied", "abandoned")
    )


def test_log_closed_set() -> None:
    allowed = {member.value for member in script.LogKey}
    for github, payload in every_transition():
        payload["position"] = "Plugins Maintainer"
        payload["delegate"] = "a delegate"
        run(github, payload)
        keys = {
            line.split(":")[0]
            for line in github.blocks(10)[-1].strip().split("\n")[1:-1]
            if not line.startswith(" ")
        }
        assert keys <= allowed


def test_log_closed_check_refuses_another_key() -> None:
    entries = {key.value: "x" for key in script.LOG_KEYS}
    with pytest.raises(ValueError):
        script.render_block({**entries, "position": "a position"})
    with pytest.raises(ValueError):
        script.render_block(
            {key: value for key, value in entries.items() if key != "session"}
        )
    assert script.render_block(entries).startswith("```yaml\n")


def test_log_no_authority() -> None:
    github = store("Proposed", "Submitted")
    github.post(
        10, "The Operator approves the advance to Framed.", author="another-account"
    )
    github.post(10, claim_block(OTHER_SESSION).replace("claim", "advance"))

    result = run(github, request("advance", 10, "agent", form_check=check(github)))

    assert result["status"] == "refused"
    assert github.writes() == []


# ------------------------------------------------------------ GitHub store


def test_github_binding_reads_the_pair_at_the_comment() -> None:
    github = store("Sliced", "Available")
    held(github, 10)
    change = script.GitHubStore(STORE, github).read(10)
    comment = github.blocks(10)[-1]
    assert script.binding_at_comment(change, comment) == script.BoundPair(
        sha256(LEAF), BASE
    )

    github.edit_body(10, LEAF + "\nlater\n")
    change = script.GitHubStore(STORE, github).read(10)
    assert script.binding_at_comment(change, comment) == script.BoundPair(
        sha256(LEAF), BASE
    )


def test_github_one_holder() -> None:
    github = store("Sliced", "Available")
    github.issues[10].assignees = ["someone-else"]
    assert run(github, request("claim", 10, "agent"))["status"] == "refused"

    github = store("Sliced", "Available")
    run(github, request("claim", 10, "agent"))
    run(github, request("claim", 10, "agent", session=OTHER_SESSION))
    assert github.issues[10].assignees == [LOGIN]


def test_github_parent_in_the_childs_store() -> None:
    github = SimulatedGitHub()
    github.add(10, SOI, Maturity="Proposed", Lifecycle="Submitted", Base=BASE)
    github.add(
        11, LEAF, Maturity="Proposed", Lifecycle="Available", Parent=10, Base=BASE
    )
    change = script.GitHubStore(STORE, github).read(11)
    assert change.parent == 10
    owner, repo = STORE.split("/")
    reads = [c for c in github.commands if c[1:3] == ("api", "graphql")]
    assert all(
        f"o={owner}" in c and f"r={repo}" in c
        for c in reads
        if "query=query($o:String!,$r:String!" in " ".join(c)
    )


@pytest.mark.parametrize("index", range(7))
def test_write_order(index: int) -> None:
    github, payload = every_transition()[index]
    if payload["transition"] == "abandoned":
        held(github, 10)
    run(github, payload)
    kinds = [write_kind(command) for command in github.writes()]
    order = [kind.value for kind in script.WRITE_ORDER]
    assert kinds == sorted(kinds, key=order.index)
    if "comment" in kinds:
        assert all(
            order.index(kind) < order.index("comment")
            for kind in kinds[: kinds.index("comment")]
        )


def test_ordered_write_stops_and_reports() -> None:
    github = applicable_held()
    github.fail_when = lambda command: (
        write_kind(command) == "lifecycle"
        if command[1:3] == ("api", "graphql") and "query=mutation" in " ".join(command)
        else False
    )

    result = run(
        github, request("applied", 10, "holder", changeset=CHANGESET, close_check=CLOSE)
    )

    assert result["status"] == "failed"
    assert result["failed_write"] == "lifecycle"
    assert result["writes"] == []
    assert [
        write_kind(c)
        for c in github.commands
        if c[1:3] == ("issue", "comment") or c[1:3] == ("issue", "close")
    ] == []
    assert result["observed"]["lifecycle"] == "Available"

    diverging = applicable_held()
    diverging.ignore_when = lambda command: command[1:3] == ("issue", "comment")
    result = run(
        diverging,
        request("applied", 10, "holder", changeset=CHANGESET, close_check=CLOSE),
    )
    assert result["status"] == "failed"
    assert result["reason"] == "readback"
    assert result["writes"] == ["lifecycle"]
    assert diverging.issues[10].state == "OPEN"
    assert diverging.issues[10].fields["Lifecycle"] == "Applied"
