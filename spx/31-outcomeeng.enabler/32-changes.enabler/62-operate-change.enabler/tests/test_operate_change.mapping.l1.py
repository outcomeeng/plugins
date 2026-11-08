"""Mapping evidence for the operate-change script.

Each row of the spec's transitions, maturity-ready, and store-writes tables is
one case. The script reaches the Change Store only through its command runner,
so each case runs it against the simulated GitHub store of
`outcomeeng_testing.harnesses.operate_change`; what each row requires and
changes is read from the spec row the case names.
"""

from __future__ import annotations

from typing import Any

import pytest

from outcomeeng_testing.harnesses.operate_change import (
    LOGIN,
    MERGE_COMMIT,
    PRODUCT_REPOSITORY,
    SimulatedGitHub,
    held,
    load_script,
    request,
    run,
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


def leaf_body(node_subsections: int = 1, infrastructure: str = "none") -> str:
    parts = [SOI, "\n## Declarations\n"]
    for index in range(node_subsections):
        parts.append(
            f"\n### spx/{20 + index}-example.enabler/example.md\n\n```diff\n+ - one: ALWAYS: an example\n```\n\n"
            f"Infrastructure: one {infrastructure}\n"
        )
    return "".join(parts)


def store(maturity: str, lifecycle: str, body: str | None = None) -> SimulatedGitHub:
    github = SimulatedGitHub()
    github.add(
        10, body or leaf_body(), Maturity=maturity, Lifecycle=lifecycle, Base=BASE
    )
    return github


def form_check(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    return {"status": "pass", "body_sha256": sha256(github.issues[number].body)}


def bound(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    return {"body_sha256": sha256(github.issues[number].body), "base": BASE}


def observed(github: SimulatedGitHub, number: int = 10) -> dict[str, Any]:
    issue = github.issues[number]
    return {
        "maturity": issue.fields.get("Maturity"),
        "lifecycle": issue.fields.get("Lifecycle"),
        "holder": tuple(issue.assignees),
        "state": issue.state,
    }


# ------------------------------------------------------------ transitions


def admitted(case: str) -> tuple[SimulatedGitHub, dict[str, Any]]:
    """A Change in the state the case's row requires, with its request."""
    if case == "claim":
        github = store("Sliced", "Available")
        return github, request("claim", 10, "agent")
    if case == "release":
        github = store("Sliced", "Submitted")
        held(github, 10)
        return github, request(
            "release",
            10,
            "holder",
            handoff={"branch": "work/x", "head": "d" * 40, "next": "spx/x"},
        )
    if case == "submit":
        github = store("Proposed", "Available")
        held(github, 10)
        return github, request(
            "submit",
            10,
            "holder",
            reopened="the Base moved under a settled replacement",
        )
    if case == "advance":
        github = store("Proposed", "Submitted")
        return github, request("advance", 10, "operator", form_check=form_check(github))
    if case == "lower":
        github = store("Sliced", "Available")
        return github, request(
            "lower",
            10,
            "operator",
            target="Framed",
            reason="a settled judgment reopened",
            lower_cause="reopened",
        )
    if case == "applied":
        github = store("Applicable", "Available")
        held(github, 10)
        return github, request(
            "applied",
            10,
            "holder",
            changeset={
                "url": f"https://github.com/{PRODUCT_REPOSITORY}/pull/7",
                "merge_commit": MERGE_COMMIT,
            },
            close_check={
                "merge_gates_passed": True,
                "results_complete": True,
                "declarations_on_default": True,
                "audit_at_close": "approved",
            },
        )
    github = store("Framed", "Available")
    return github, request("abandoned", 10, "operator")


#: What each row changes, read from the transitions table of the spec.
CHANGES = {
    "claim": {"holder": (LOGIN,)},
    "release": {"holder": (), "lifecycle": "Available"},
    "submit": {"lifecycle": "Submitted"},
    "advance": {"maturity": "Framed"},
    "lower": {"maturity": "Framed"},
    "applied": {"lifecycle": "Applied", "state": "CLOSED"},
    "abandoned": {"lifecycle": "Abandoned", "state": "CLOSED"},
}


@pytest.mark.parametrize("case", [member.value for member in script.Transition])
def test_transition_changes_only_what_its_row_states(case: str) -> None:
    github, payload = admitted(case)
    before = observed(github)

    result = run(github, payload)

    after = observed(github)
    assert result["status"] == "done", result
    changed = {key: after[key] for key in after if after[key] != before[key]}
    assert changed == CHANGES[case]


#: A state each row does not admit: the next Maturity or Lifecycle the row excludes.
REFUSED = {
    "claim": ("Sliced", "Submitted"),
    "release": ("Sliced", "Available"),
    "submit": ("Proposed", "Submitted"),
    "advance": ("Proposed", "Available"),
    "lower": ("Proposed", "Available"),
    "applied": ("Applicable", "Available"),
    "abandoned": ("Framed", "Applied"),
}


@pytest.mark.parametrize("case", [member.value for member in script.Transition])
def test_transition_reports_any_other_state_without_a_write(case: str) -> None:
    _, payload = admitted(case)
    maturity, lifecycle = REFUSED[case]
    github = store(maturity, lifecycle)

    result = run(github, payload)

    assert result["status"] == "refused"
    assert github.writes() == []


# ---------------------------------------------------------- maturity-ready


def ready(case: str, *, met: bool = True) -> tuple[SimulatedGitHub, dict[str, Any]]:
    """An advance into the case's Maturity, its record meeting that row and every row above it.

    With `met` false the record misses the case's row alone.
    """
    if case in ("proposed", "framed"):
        body = leaf_body() if met or case == "proposed" else SOI + "\n## Declarations\n"
        github = store("Proposed", "Submitted", body)
        check = form_check(github)
        if not met and case == "proposed":
            check = {"status": "fail", "body_sha256": check["body_sha256"]}
        return github, request("advance", 10, "operator", form_check=check)
    if case == "sliced":
        github = store("Framed", "Submitted", leaf_body(5 if met else 6))
        return github, request(
            "advance",
            10,
            "operator",
            form_check=form_check(github),
            review=bound(github),
        )
    github = store("Sliced", "Available", leaf_body(1, "`spx/15-infra.enabler`"))
    held(github, 10)
    return github, request(
        "advance",
        10,
        "holder",
        form_check=form_check(github),
        audit=bound(github),
        audit_status="approved",
        infrastructure={"spx/15-infra.enabler": "Passing" if met else "Specified"},
    )


@pytest.mark.parametrize(
    "case", [member.value.lower() for member in script.MATURITY_ORDER]
)
def test_advance_only_when_the_record_meets_its_row(case: str) -> None:
    github, payload = ready(case)
    target = script.MATURITY_ORDER[max(script.rank(case.capitalize()), 1)]

    assert run(github, payload)["status"] == "done"
    assert github.issues[10].fields["Maturity"] == target

    missed, missed_payload = ready(case, met=False)
    before = missed.issues[10].fields["Maturity"]

    assert run(missed, missed_payload)["status"] == "refused"
    assert missed.issues[10].fields["Maturity"] == before


# ------------------------------------------------------------- store-writes


#: Each part a Transition changes, and the transition whose writes reach it.
STORE_WRITES = {
    "maturity": "advance",
    "lifecycle": "submit",
    "holder": "claim",
    "transition": "claim",
}

#: The GitHub home each part's row names, as the simulated store names the command.
HOMES = {
    "maturity": "maturity",
    "lifecycle": "lifecycle",
    "holder": "assignee",
    "transition": "comment",
}


@pytest.mark.parametrize("case", list(STORE_WRITES))
def test_each_part_reaches_its_one_home(case: str) -> None:
    github, payload = admitted(STORE_WRITES[case])

    assert run(github, payload)["status"] == "done"

    kinds = [write_kind(command) for command in github.writes()]
    assert HOMES[case] in kinds
    if case == "holder":
        assert github.issues[10].assignees == [LOGIN]
        comments = github.blocks(10)
        assert (
            script.parse_block(comments[-1])["session"]
            == payload["identity"]["session"]
        )
    if case == "transition":
        assert script.parse_block(github.blocks(10)[-1])["transition"] == "claim"
