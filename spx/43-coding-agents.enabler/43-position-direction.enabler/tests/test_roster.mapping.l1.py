from outcomeeng_testing.generators.position_direction import RosterCase, roster_cases
from outcomeeng_testing.harnesses.position_direction import (
    CLOCK_START,
    ROSTER_ROWS,
    check_examples,
    load_scripts,
)

scripts = load_scripts()


def test_roster_prints_each_position_and_group_member_as_the_inventories_show_them() -> (
    None
):
    column = {name: index for index, name in enumerate(scripts.roster.COLUMNS)}

    def check(case: RosterCase) -> None:
        text = scripts.roster.render(
            case.watch,
            case.inventories,
            CLOCK_START,
            read_context=lambda session: f"context of {session.handle}",
        )
        rows = [
            [cell.strip() for cell in line.strip("|").split("|")]
            for line in text.splitlines()
            if line.startswith("| ")
        ][2:]  # the header and its separator
        shown = sorted(
            (row[column["Position"]], row[column["Pane"]], row[column["State"]])
            for row in rows
        )

        expected = []
        for position, session in case.live.items():
            expected.append((position, session.handle, str(session.state)))
        for position in case.absent:
            expected.append((position, "-", scripts.roster.ABSENT))
        for name, message in case.failed.items():
            expected.append(
                (name, "?", f"{scripts.roster.INVENTORY_FAILED}: {message}")
            )
        for label, members in case.members.items():
            for member in members:
                expected.append(
                    (f"{label} {member.handle}", member.handle, str(member.state))
                )

        assert shown == sorted(expected)

        sessions = [
            *case.live.values(),
            *(m for ms in case.members.values() for m in ms),
        ]
        contexts = sorted(f"context of {session.handle}" for session in sessions)
        assert contexts == sorted(
            row[column["Context"]]
            for row in rows
            if row[column["Context"]].startswith("context of ")
        )

    check_examples(roster_cases(scripts.environment), check, ROSTER_ROWS)
