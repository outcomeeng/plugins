"""Compliance evidence for the operate-change script.

Each test exercises one ALWAYS or NEVER rule of the spec with a case that
breaks it and, where the rule admits one, a case that keeps it. The script
reaches the Change Store only through its command runner, so each case runs
it against the simulated GitHub store of
`outcomeeng_testing.harnesses.operate_change`, which records every command,
fails a chosen one, or lands another writer's edit between two of them. The
records, the case domains, and the orders and closed sets the spec states come
from `outcomeeng_testing.generators.operate_change`; the vocabulary comes from
the script that owns it.
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Any

import pytest

from outcomeeng_testing.generators.operate_change import (
    ANOTHER_ACCOUNT,
    BASE,
    DELEGATE_KEY,
    OTHER_BASE,
    POSITION_KEY,
    RACES,
    REASON,
    SPEC_HANDOFF_KEYS,
    SPEC_LOG_EXTRAS,
    SPEC_LOG_KEYS,
    SPEC_WRITE_ORDER,
    TARGET,
    UNRESOLVED_BASE,
    add_child,
    applicable_held,
    breaking_cases,
    carrying_cases,
    change_store,
    declaration,
    edited,
    every_transition,
    intent,
    leaf_record,
    part_cases,
)
from outcomeeng_testing.generators.operate_change import (
    CarryCase,
    PartCase,
)
from outcomeeng_testing.harnesses.operate_change import (
    APPROVED,
    LOGIN,
    MERGE_COMMIT,
    OTHER_SESSION,
    REJECTED,
    STORE,
    UNMERGED_COMMIT,
    ChangesetKey,
    Field,
    IssueState,
    Lifecycle,
    LogKey,
    LowerCause,
    Maturity,
    Mover,
    PairKey,
    Reason,
    RequestKey,
    SimulatedGitHub,
    Status,
    Transition,
    WriteKind,
    bound_pair,
    changeset,
    claim_block,
    close_check,
    handoff,
    held,
    is_write,
    pair_of,
    passing_form_check,
    product_repository,
    request,
    run,
    run_main,
    script,
    sha256,
    write_kind,
)

CLOSE_KEYS = tuple(close_check())


def blocks(github: SimulatedGitHub, number: int = 10) -> list[dict[str, str]]:
    return [script.parse_block(body) for body in github.blocks(number)]


def to_applicable(github: SimulatedGitHub, **values: object) -> dict[str, Any]:
    payload = request(
        Transition.ADVANCE,
        10,
        Mover.HOLDER,
        form_check=passing_form_check(github),
        audit=bound_pair(github),
        audit_status=APPROVED,
    )
    payload.update(values)
    return payload


def maturity_write(command: Sequence[str]) -> bool:
    return is_write(command) and write_kind(command) == WriteKind.MATURITY


# ----------------------------------------------------------------- closing


@pytest.mark.parametrize("broken", ["ancestor", *CLOSE_KEYS])
def test_leaf_applied_only_on_its_close_condition(broken: str) -> None:
    github = applicable_held()
    if broken == "ancestor":
        payload = request(
            Transition.APPLIED,
            10,
            Mover.HOLDER,
            changeset=changeset(UNMERGED_COMMIT),
            close_check=close_check(),
        )
    else:
        met = close_check()[broken]
        payload = request(
            Transition.APPLIED,
            10,
            Mover.HOLDER,
            changeset=changeset(),
            close_check=close_check(**{broken: REJECTED if met == APPROVED else False}),
        )

    result = run(github, payload)

    assert result["status"] == Status.REFUSED
    assert github.issues[10].fields[Field.LIFECYCLE] == Lifecycle.AVAILABLE
    assert (
        run(
            github,
            request(
                Transition.APPLIED,
                10,
                Mover.HOLDER,
                changeset=changeset(),
                close_check=close_check(),
            ),
        )["status"]
        == Status.DONE
    )


@pytest.mark.parametrize("terminal", [Lifecycle.APPLIED, Lifecycle.ABANDONED])
@pytest.mark.parametrize("move", list(Transition))
def test_terminal_change_never_moves(terminal: Lifecycle, move: Transition) -> None:
    github = change_store(Maturity.APPLICABLE, terminal)
    github.issues[10].state = IssueState.CLOSED.value
    held(github, 10)

    result = run(
        github,
        request(
            move,
            10,
            Mover.OPERATOR,
            target=Maturity.SLICED,
            reason=REASON,
            lower_cause=LowerCause.REOPENED,
            handoff=handoff(),
            changeset=changeset(),
            close_check=close_check(),
        ),
    )

    assert result["status"] == Status.REFUSED
    assert github.writes() == []


def test_terminal_kept_no_delete_command() -> None:
    github = applicable_held()
    github.add(
        11,
        leaf_record(),
        {Field.MATURITY: Maturity.APPLICABLE, Field.LIFECYCLE: Lifecycle.AVAILABLE},
    )
    github.issues[11].blocked_by.append(10)

    run(
        github,
        request(
            Transition.LOWER,
            10,
            Mover.HOLDER,
            target=Maturity.SLICED,
            reason=REASON,
            lower_cause=LowerCause.DECISION_LINE,
        ),
    )
    run(github, request(Transition.ABANDONED, 10, Mover.OPERATOR))

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
            Transition.LOWER,
            10,
            Mover.HOLDER,
            target=Maturity.SLICED,
            reason=REASON,
            lower_cause=LowerCause.DECISION_LINE,
        ),
    )
    assert result["status"] == Status.DONE
    assert Transition.RELEASE not in result
    assert kept.issues[10].assignees == [LOGIN]

    released = applicable_held()
    result = run(
        released,
        request(
            Transition.LOWER,
            10,
            Mover.HOLDER,
            target=Maturity.SLICED,
            reason=REASON,
            lower_cause=LowerCause.APPLICATION_CHECK,
            handoff=handoff(),
        ),
    )
    assert result["status"] == Status.DONE
    assert result["release"]["status"] == Status.DONE
    assert released.issues[10].assignees == []
    assert [b[LogKey.TRANSITION] for b in blocks(released)][-2:] == [
        Transition.LOWER,
        Transition.RELEASE,
    ]

    missing = applicable_held()
    result = run(
        missing,
        request(
            Transition.LOWER,
            10,
            Mover.HOLDER,
            target=Maturity.SLICED,
            reason=REASON,
            lower_cause=LowerCause.APPLICATION_CHECK,
        ),
    )
    assert result["status"] == Status.REFUSED
    assert missing.writes() == []


# ----------------------------------------------------------------- binding


def test_review_binding_on_advance_to_sliced() -> None:
    github = change_store(Maturity.FRAMED, Lifecycle.SUBMITTED)
    stale = pair_of(edited(github.issues[10].body), BASE)

    refused = run(
        github,
        request(
            Transition.ADVANCE,
            10,
            Mover.OPERATOR,
            form_check=passing_form_check(github),
            review=stale,
        ),
    )
    assert refused["status"] == Status.REFUSED
    assert refused["reason"] == Reason.REVIEW_BINDING

    done = run(
        github,
        request(
            Transition.ADVANCE,
            10,
            Mover.OPERATOR,
            form_check=passing_form_check(github),
            review=bound_pair(github),
        ),
    )
    assert done["status"] == Status.DONE


def test_review_binding_on_claim_for_application() -> None:
    github = change_store(Maturity.APPLICABLE, Lifecycle.AVAILABLE)
    stale = pair_of(edited(github.issues[10].body), BASE)

    assert (
        run(github, request(Transition.CLAIM, 10, Mover.AGENT, review=stale))["status"]
        == Status.REFUSED
    )
    assert github.writes() == []
    assert (
        run(
            github,
            request(Transition.CLAIM, 10, Mover.AGENT, review=bound_pair(github)),
        )["status"]
        == Status.DONE
    )


def land_race(github: SimulatedGitHub, race: str) -> None:
    """Make another writer's edit land after the Maturity write of a Transition."""

    def edit_after_maturity(sim: SimulatedGitHub, command: Sequence[str]) -> None:
        if not maturity_write(command):
            return
        if race == "body":
            sim.edit_body(10, edited(sim.issues[10].body))
        else:
            sim.set_field(10, Field.BASE, OTHER_BASE)

    github.after = edit_after_maturity


@pytest.mark.parametrize("race", RACES)
def test_review_binding_comment_only_while_the_pair_stands(race: str) -> None:
    github = change_store(Maturity.FRAMED, Lifecycle.SUBMITTED)
    reviewed = bound_pair(github)
    land_race(github, race)

    result = run(
        github,
        request(
            Transition.ADVANCE,
            10,
            Mover.OPERATOR,
            form_check=passing_form_check(github),
            review=reviewed,
        ),
    )

    assert result["status"] == Status.FAILED
    assert result["reason"] == Reason.BINDING_RACED
    assert result["failed_write"] == WriteKind.COMMENT
    assert all(write_kind(command) != WriteKind.COMMENT for command in github.writes())


@pytest.mark.parametrize("race", RACES)
def test_audit_binding_comment_only_while_the_pair_stands(race: str) -> None:
    github = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    held(github, 10)
    payload = to_applicable(github)
    land_race(github, race)

    result = run(github, payload)

    assert result["status"] == Status.FAILED
    assert result["reason"] == Reason.BINDING_RACED
    assert result["failed_write"] == WriteKind.COMMENT
    assert all(write_kind(command) != WriteKind.COMMENT for command in github.writes())


@pytest.mark.parametrize("broken", ["body", "base", "status"])
def test_audit_binding(broken: str) -> None:
    github = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    held(github, 10)
    audit = bound_pair(github)
    status = APPROVED
    if broken == "body":
        audit = {**audit, PairKey.BODY_SHA256: sha256(edited(github.issues[10].body))}
    elif broken == "base":
        audit = {**audit, PairKey.BASE: OTHER_BASE}
    else:
        status = REJECTED

    refused = run(github, to_applicable(github, audit=audit, audit_status=status))

    assert refused["status"] == Status.REFUSED
    assert refused["reason"] == Reason.AUDIT_BINDING
    assert github.issues[10].fields[Field.MATURITY] == Maturity.SLICED
    assert run(github, to_applicable(github))["status"] == Status.DONE


def carried_advance(
    github: SimulatedGitHub, root: str, reviewed_body: str, reviewed_base: str
) -> dict[str, Any]:
    payload = request(
        Transition.ADVANCE,
        10,
        Mover.OPERATOR,
        form_check=passing_form_check(github),
        review=pair_of(reviewed_body, reviewed_base),
        review_body=reviewed_body,
    )
    return run(github, payload, root=root)


def carry(case: CarryCase) -> dict[str, Any]:
    with product_repository(case.commits) as (root, (old, new)):
        github = change_store(
            Maturity.FRAMED, Lifecycle.SUBMITTED, body=case.current_body, base=new
        )
        base = old if case.reviewed_base_resolves else UNRESOLVED_BASE
        return carried_advance(github, root, case.reviewed_body, base)


@pytest.mark.parametrize("case", carrying_cases(), ids=lambda case: case.name)
def test_review_carry_forward_while_parts_read_the_same(case: CarryCase) -> None:
    assert carry(case)["status"] == Status.DONE


@pytest.mark.parametrize("case", breaking_cases(), ids=lambda case: case.name)
def test_review_carry_forward_stops_when_a_part_moves(case: CarryCase) -> None:
    result = carry(case)

    assert result["status"] == Status.REFUSED
    assert result["reason"] == Reason.REVIEW_BINDING


@pytest.mark.parametrize("case", part_cases(), ids=lambda case: case.name)
def test_review_part_context(case: PartCase) -> None:
    reviewed = declaration(list(case.reviewed_lines))
    current = declaration(list(case.current_lines))
    carry_case = CarryCase(
        case.name,
        ({TARGET: "same"}, {TARGET: "same"}),
        reviewed,
        current,
    )

    result = carry(carry_case)

    assert result["status"] == Status.REFUSED
    assert result["reason"] == Reason.REVIEW_BINDING
    for line in case.lost:
        assert f"{TARGET}: {line}" in result["detail"]
    for line in case.kept:
        assert line not in result["detail"]


# ------------------------------------------------------ structure and blockers


def test_change_type_derives_from_relations() -> None:
    parent = change_store(Maturity.SLICED, Lifecycle.AVAILABLE, body=intent())
    add_child(parent)
    held(parent, 10)
    result = run(parent, to_applicable(parent))
    assert result["status"] == Status.REFUSED
    assert result["reason"] == Reason.PARENT

    leaf = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    held(leaf, 10)
    assert run(leaf, to_applicable(leaf))["status"] == Status.DONE


def test_parent_maturity() -> None:
    github = change_store(Maturity.PROPOSED, Lifecycle.SUBMITTED, body=intent())
    add_child(github)
    assert (
        run(
            github,
            request(
                Transition.ADVANCE,
                10,
                Mover.OPERATOR,
                form_check=passing_form_check(github),
            ),
        )["status"]
        == Status.DONE
    )

    child_moves = change_store(Maturity.FRAMED, Lifecycle.AVAILABLE, body=intent())
    child_moves.add(
        11,
        leaf_record(),
        {
            Field.MATURITY: Maturity.PROPOSED,
            Field.LIFECYCLE: Lifecycle.SUBMITTED,
            Field.PARENT: 10,
            Field.BASE: BASE,
        },
    )
    assert (
        run(
            child_moves,
            request(
                Transition.ADVANCE,
                11,
                Mover.OPERATOR,
                form_check=passing_form_check(child_moves, 11),
            ),
        )["status"]
        == Status.DONE
    )
    assert all(
        command[3] != "10" for command in child_moves.writes() if command[1] == "issue"
    )
    assert all("I_10" not in " ".join(command) for command in child_moves.writes())


def test_blocker_abandoned_passes_or_returns() -> None:
    merged = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    merged.add(
        11,
        leaf_record(),
        {
            Field.MATURITY: Maturity.APPLICABLE,
            Field.LIFECYCLE: Lifecycle.AVAILABLE,
            Field.BASE: BASE,
        },
    )
    merged.add(
        12,
        leaf_record(),
        {
            Field.MATURITY: Maturity.SLICED,
            Field.LIFECYCLE: Lifecycle.AVAILABLE,
            Field.BASE: BASE,
        },
    )
    merged.issues[11].blocked_by.append(10)
    result = run(merged, request(Transition.ABANDONED, 10, Mover.AGENT, merged_into=12))
    assert result["status"] == Status.DONE
    assert 12 in merged.issues[11].blocked_by

    unmerged = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    unmerged.add(
        11,
        leaf_record(),
        {
            Field.MATURITY: Maturity.APPLICABLE,
            Field.LIFECYCLE: Lifecycle.AVAILABLE,
            Field.BASE: BASE,
        },
    )
    unmerged.issues[11].blocked_by.append(10)
    result = run(unmerged, request(Transition.ABANDONED, 10, Mover.OPERATOR))
    assert result["status"] == Status.DONE
    assert unmerged.issues[11].fields[Field.MATURITY] == Maturity.SLICED


def test_blocker_cycle_never_advances_or_claims() -> None:
    github = change_store(Maturity.FRAMED, Lifecycle.SUBMITTED)
    github.add(
        11,
        leaf_record(),
        {
            Field.MATURITY: Maturity.APPLICABLE,
            Field.LIFECYCLE: Lifecycle.AVAILABLE,
            Field.BASE: BASE,
        },
    )
    github.issues[10].blocked_by.append(11)
    github.issues[11].blocked_by.append(10)

    def advance() -> dict[str, Any]:
        return run(
            github,
            request(
                Transition.ADVANCE,
                10,
                Mover.OPERATOR,
                form_check=passing_form_check(github),
                review=bound_pair(github),
            ),
        )

    assert advance()["status"] == Status.REFUSED
    assert (
        run(
            github,
            request(Transition.CLAIM, 11, Mover.AGENT, review=bound_pair(github, 11)),
        )["status"]
        == Status.REFUSED
    )
    assert github.writes() == []

    github.issues[11].blocked_by.clear()
    assert advance()["status"] == Status.DONE


# ------------------------------------------------------- transition function


def test_transition_function_is_what_main_writes() -> None:
    assert inspect.isfunction(script.transition)
    first = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    second = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    payload = request(Transition.CLAIM, 10, Mover.AGENT)

    returned = script.transition(payload, run=first)
    code, written = run_main(second, payload)

    assert code == 0
    assert {k: v for k, v in returned.items() if k != "comment_url"} == {
        k: v for k, v in written.items() if k != "comment_url"
    }


# ---------------------------------------------------------- transition log


def test_log_block_one_fenced_block_per_transition() -> None:
    for github, payload in every_transition():
        before = len(github.blocks(10))
        assert run(github, payload)["status"] == Status.DONE
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
        who = payload[RequestKey.IDENTITY]
        assert set(SPEC_LOG_KEYS) <= set(block)
        assert block[LogKey.TRANSITION] == payload[RequestKey.TRANSITION]
        assert block[LogKey.MATURITY] == github.issues[10].fields[Field.MATURITY]
        for key in (LogKey.HARNESS, LogKey.SESSION, LogKey.MACHINE, LogKey.WORKTREE):
            assert block[key] == who[key.value]


def test_log_extras_and_handoff_keys() -> None:
    texts = {}
    for github, payload in every_transition():
        run(github, payload)
        texts[payload[RequestKey.TRANSITION]] = github.blocks(10)[-1]
    reason = f"{LogKey.REASON}:"
    assert reason in texts[Transition.LOWER]
    assert reason in texts[Transition.SUBMIT]
    assert f"{LogKey.HANDOFF}:" in texts[Transition.RELEASE]
    for key in SPEC_HANDOFF_KEYS:
        assert f"  {key}:" in texts[Transition.RELEASE]
    assert f"{LogKey.CHANGESET}:" in texts[Transition.APPLIED]
    assert f"  {ChangesetKey.MERGE_COMMIT}: {MERGE_COMMIT}" in texts[Transition.APPLIED]
    for transition in (
        Transition.CLAIM,
        Transition.ADVANCE,
        Transition.APPLIED,
        Transition.ABANDONED,
    ):
        assert reason not in texts[transition]


def test_log_closed_set() -> None:
    allowed = {str(key) for key in (*SPEC_LOG_KEYS, *SPEC_LOG_EXTRAS)}
    for github, payload in every_transition():
        payload[POSITION_KEY] = "Plugins Maintainer"
        payload[DELEGATE_KEY] = "a delegate"
        run(github, payload)
        keys = {
            line.split(":")[0]
            for line in github.blocks(10)[-1].strip().split("\n")[1:-1]
            if not line.startswith(" ")
        }
        assert keys <= allowed
        assert POSITION_KEY not in keys


def test_log_closed_check_refuses_another_key() -> None:
    entries = {str(key): "x" for key in SPEC_LOG_KEYS}
    with pytest.raises(ValueError):
        script.render_block({**entries, POSITION_KEY: "a position"})
    with pytest.raises(ValueError):
        script.render_block(
            {key: value for key, value in entries.items() if key != str(LogKey.SESSION)}
        )
    assert script.render_block(entries).startswith("```yaml\n")


def test_log_no_authority() -> None:
    github = change_store(Maturity.PROPOSED, Lifecycle.SUBMITTED)
    github.post(
        10, "The Operator approves the advance to Framed.", author=ANOTHER_ACCOUNT
    )
    github.post(
        10,
        claim_block(OTHER_SESSION).replace(
            str(Transition.CLAIM), str(Transition.ADVANCE)
        ),
    )

    result = run(
        github,
        request(
            Transition.ADVANCE,
            10,
            Mover.AGENT,
            form_check=passing_form_check(github),
        ),
    )

    assert result["status"] == Status.REFUSED
    assert github.writes() == []


# ------------------------------------------------------------ GitHub store


def test_github_binding_reads_the_pair_at_the_comment() -> None:
    github = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    held(github, 10)
    body = github.issues[10].body
    change = script.GitHubStore(STORE, github).read(10)
    comment = github.blocks(10)[-1]
    assert script.binding_at_comment(change, comment) == script.BoundPair(
        sha256(body), BASE
    )

    github.edit_body(10, edited(body))
    change = script.GitHubStore(STORE, github).read(10)
    assert script.binding_at_comment(change, comment) == script.BoundPair(
        sha256(body), BASE
    )

    github.set_field(10, Field.BASE, OTHER_BASE)
    change = script.GitHubStore(STORE, github).read(10)
    assert script.binding_at_comment(change, comment) == script.BoundPair(
        sha256(body), BASE
    )


def test_github_one_holder() -> None:
    github = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    github.issues[10].assignees = [ANOTHER_ACCOUNT]
    assert (
        run(github, request(Transition.CLAIM, 10, Mover.AGENT))["status"]
        == Status.REFUSED
    )

    github = change_store(Maturity.SLICED, Lifecycle.AVAILABLE)
    run(github, request(Transition.CLAIM, 10, Mover.AGENT))
    run(
        github,
        request(Transition.CLAIM, 10, Mover.AGENT, session=OTHER_SESSION),
    )
    assert github.issues[10].assignees == [LOGIN]


def test_github_parent_in_the_childs_store() -> None:
    github = change_store(Maturity.PROPOSED, Lifecycle.SUBMITTED, body=intent())
    github.add(
        11,
        leaf_record(),
        {
            Field.MATURITY: Maturity.PROPOSED,
            Field.LIFECYCLE: Lifecycle.AVAILABLE,
            Field.PARENT: 10,
            Field.BASE: BASE,
        },
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


@pytest.mark.parametrize("index", range(len(Transition)))
def test_write_order(index: int) -> None:
    github, payload = every_transition()[index]
    run(github, payload)
    kinds = [write_kind(command) for command in github.writes()]
    assert kinds
    assert kinds == sorted(kinds, key=SPEC_WRITE_ORDER.index)
    assert len(set(kinds)) == len(kinds)
    if WriteKind.COMMENT in kinds:
        after = kinds[kinds.index(WriteKind.COMMENT) + 1 :]
        assert all(kind == WriteKind.STATE for kind in after)


def test_ordered_write_stops_and_reports() -> None:
    github = applicable_held()
    github.fail_when = lambda command: (
        is_write(command) and write_kind(command) == WriteKind.LIFECYCLE
    )
    payload = request(
        Transition.APPLIED,
        10,
        Mover.HOLDER,
        changeset=changeset(),
        close_check=close_check(),
    )

    result = run(github, payload)

    assert result["status"] == Status.FAILED
    assert result["failed_write"] == WriteKind.LIFECYCLE
    assert result["writes"] == []
    assert [
        write_kind(c)
        for c in github.commands
        if write_kind(c) in (WriteKind.COMMENT, WriteKind.STATE)
    ] == []
    assert result["observed"]["lifecycle"] == Lifecycle.AVAILABLE

    diverging = applicable_held()
    diverging.ignore_when = lambda command: write_kind(command) == WriteKind.COMMENT
    result = run(diverging, payload)
    assert result["status"] == Status.FAILED
    assert result["reason"] == Reason.READBACK
    assert result["writes"] == [WriteKind.LIFECYCLE]
    assert diverging.issues[10].state == IssueState.OPEN
    assert diverging.issues[10].fields[Field.LIFECYCLE] == Lifecycle.APPLIED
