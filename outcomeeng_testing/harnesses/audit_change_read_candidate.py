"""Candidate piece-reading harness for the audit-change runner.

Backs the ``[test]`` evidence for the ``read-candidate`` operation's pieces in
two parts that keep the generated domain apart from the real boundary.

The generated readings call the runner's text seam, ``_candidate_piece``, with
generated candidate text, its relative path, and an offset: no file, Git
repository, request, or entry-point call belongs to a generated case. A reading
follows the client protocol, taking the piece at offset 0 and then the piece at
each ``next`` offset until it is ``null``, and each piece is observed with the
bytes of the complete response the entry point prints for it, which JSON's own
serialization of the response fields gives, followed by the line terminator the
runner writes after it.

The request wiring is one real Git repository holding one candidate in a
temporary directory, and the entry point receives the requests a client sends.
Each call is returned as observed, with the request that produced it, the whole
output the runner wrote, the line within it, and the decoded result.

The wire readings read generated candidates through that entry point. One Git
repository holds the candidate for the whole run, and each generated case
replaces the candidate's text, follows ``next`` from offset 0, and returns every
call beside the piece the text seam gives at the same offset, so the linked test
compares the bytes the runner wrote with the size the harness reconstructs.

The invalid-offset cases hand each generated value that is not a non-negative
integer to the linked test, which sends it to the runner's request validation.

The harness decides nothing: every predicate belongs to the linked test. The
harness owns the property's seed, example count, and replay command.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator, Mapping
from contextlib import chdir, contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.audit_change_candidate_text import (
    candidate_texts,
    final_piece_remainders,
    invalid_offsets,
    long_candidate_texts,
    wire_candidate_texts,
)
from outcomeeng_testing.harnesses.audit_change_run import (
    CAPTURED_CHANGE_RECORD,
    load_runner,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

CANDIDATE_PATH: Final = "changes/candidate.md"
READ_CANDIDATE_PROPERTY_SEED: Final = 20261027
READ_CANDIDATE_PROPERTY_EXAMPLES: Final = settings().max_examples
READ_CANDIDATE_PROPERTY_REPLAY: Final = (
    "just test spx/31-outcomeeng.enabler/32-changes.enabler/tests/"
    "test_audit_change_read_candidate.property.l1.py"
)
# Each long candidate is read at every final-piece remainder, hundreds of calls,
# so the long-candidate property runs few generated texts.
FINAL_PIECE_PROPERTY_EXAMPLES: Final = 3
# Each wire text is read piece by piece through the entry point, one process per
# piece, so the wire property runs few generated texts.
WIRE_PROPERTY_EXAMPLES: Final = 20
# A loop that has not seen ``next`` null after one call per character plus this
# many calls stops, so a runner that never ends the pieces cannot hang a run.
_CALL_BOUND_MARGIN: Final = 2
_TEXT_ENCODING: Final = "utf-8"
# The captured record is repeated until it exceeds the character limit this
# many times over, so the wired candidate needs more than one piece.
_WIRED_CANDIDATE_LIMIT_MULTIPLE: Final = 2


@dataclass(frozen=True)
class Piece:
    """One piece taken at an offset, with the bytes of the response that carries it."""

    offset: int
    result: Mapping[str, object]
    response_bytes: int


@dataclass(frozen=True)
class FinalPieceReading:
    """One long candidate and the piece taken at each final-piece offset."""

    text: str
    pieces: tuple[Piece, ...]


@dataclass(frozen=True)
class CandidateReading:
    """What a client observes reading one candidate to its end."""

    text: str
    pieces: tuple[Piece, ...]


@dataclass(frozen=True)
class RequestCall:
    """One ``read-candidate`` request, the output printed for it, and its decoded result."""

    request: Mapping[str, object]
    exit_code: int
    output: str
    line: str
    result: Mapping[str, object]

    @property
    def output_bytes(self) -> int:
        """The size in UTF-8 bytes of everything the runner wrote, line terminator included."""
        return len(self.output.encode(_TEXT_ENCODING))


@dataclass(frozen=True)
class WirePiece:
    """One piece read through the entry point, beside the text seam's piece at its offset."""

    call: RequestCall
    seam: Piece


@dataclass(frozen=True)
class WireReading:
    """What a client observes reading one candidate to its end through the entry point."""

    text: str
    pieces: tuple[WirePiece, ...]


def _take_piece(text: str, offset: int) -> Piece:
    runner = load_runner()
    result = runner._candidate_piece(text, CANDIDATE_PATH, offset)
    response = {
        runner.ResultField.OPERATION: runner.Operation.READ_CANDIDATE,
        runner.ResultField.STATUS: runner.ResultStatus.OK,
        **result,
    }
    printed = json.dumps(response, sort_keys=True) + runner.LINE_TERMINATOR
    return Piece(
        offset=offset,
        result=result,
        response_bytes=len(printed.encode(_TEXT_ENCODING)),
    )


def _read_to_end(text: str) -> CandidateReading:
    following = load_runner().ResultField.NEXT
    pieces: list[Piece] = []
    offset = 0
    for _ in range(len(text) + _CALL_BOUND_MARGIN):
        piece = _take_piece(text, offset)
        pieces.append(piece)
        next_offset = piece.result.get(following)
        if not isinstance(next_offset, int):
            break
        offset = next_offset
    return CandidateReading(text=text, pieces=tuple(pieces))


def exercise_candidate_readings(
    assert_case: Callable[[CandidateReading], None],
) -> None:
    """Read every generated candidate through the text seam and hand each reading over.

    ``assert_case`` receives the whole reading; a failing case reports the
    generated text itself.
    """

    @seed(READ_CANDIDATE_PROPERTY_SEED)
    @settings(
        max_examples=READ_CANDIDATE_PROPERTY_EXAMPLES,
        print_blob=True,
        deadline=None,
    )
    @given(text=candidate_texts())
    def run_cases(text: str) -> None:
        assert_case(_read_to_end(text))

    run_replayable_property(
        run_cases,
        seed_value=READ_CANDIDATE_PROPERTY_SEED,
        replay_path=READ_CANDIDATE_PROPERTY_REPLAY,
    )


def exercise_final_piece_readings(
    assert_case: Callable[[FinalPieceReading], None],
) -> None:
    """Read every generated long candidate near its end and hand each reading over.

    Each candidate is read once at every offset that leaves a remainder within
    the final-piece sweep; ``assert_case`` receives the pieces observed, each
    carrying the offset it was taken at.
    """

    runner = load_runner()
    byte_limit: int = runner.PIECE_BYTE_LIMIT
    character_limit: int = runner.PIECE_CHARACTER_LIMIT

    @seed(READ_CANDIDATE_PROPERTY_SEED)
    @settings(
        max_examples=FINAL_PIECE_PROPERTY_EXAMPLES,
        print_blob=True,
        deadline=None,
    )
    @given(text=long_candidate_texts(byte_limit))
    def run_cases(text: str) -> None:
        pieces = tuple(
            _take_piece(text, len(text) - remainder)
            for remainder in final_piece_remainders(byte_limit, character_limit)
        )
        assert_case(FinalPieceReading(text=text, pieces=pieces))

    run_replayable_property(
        run_cases,
        seed_value=READ_CANDIDATE_PROPERTY_SEED,
        replay_path=READ_CANDIDATE_PROPERTY_REPLAY,
    )


def _read_wire(
    send: Callable[[Mapping[str, object]], RequestCall], text: str
) -> WireReading:
    runner = load_runner()
    base = {
        runner.RequestField.OPERATION: runner.Operation.READ_CANDIDATE,
        runner.RequestField.PATH: CANDIDATE_PATH,
    }
    pieces: list[WirePiece] = []
    offset = 0
    request: Mapping[str, object] = base
    for _ in range(len(text) + _CALL_BOUND_MARGIN):
        call = send(request)
        pieces.append(WirePiece(call=call, seam=_take_piece(text, offset)))
        next_offset = call.result.get(runner.ResultField.NEXT)
        if not isinstance(next_offset, int):
            break
        offset = next_offset
        request = {**base, runner.RequestField.OFFSET: offset}
    return WireReading(text=text, pieces=tuple(pieces))


def exercise_wire_readings(assert_case: Callable[[WireReading], None]) -> None:
    """Read every generated wire text through the entry point and hand each reading over.

    One Git repository holds the candidate for the whole run. Each case replaces
    the candidate's text, reads it from offset 0 and then at each ``next``
    offset, and hands over each call beside the text seam's piece at the same
    offset; ``assert_case`` states what the two have in common.
    """

    runner = load_runner()
    character_limit: int = runner.PIECE_CHARACTER_LIMIT

    with candidate_repository() as repository:

        @seed(READ_CANDIDATE_PROPERTY_SEED)
        @settings(
            max_examples=WIRE_PROPERTY_EXAMPLES,
            print_blob=True,
            deadline=None,
        )
        @given(text=wire_candidate_texts(character_limit))
        def run_cases(text: str) -> None:
            repository.hold(text)
            assert_case(_read_wire(repository.send, text))

        run_replayable_property(
            run_cases,
            seed_value=READ_CANDIDATE_PROPERTY_SEED,
            replay_path=READ_CANDIDATE_PROPERTY_REPLAY,
        )


def exercise_invalid_offsets(assert_case: Callable[[Path, object], None]) -> None:
    """Hand every generated value that is not a non-negative integer to ``assert_case``.

    The harness owns the seed, the example count, the replay command, and the
    checkout root of the Git repository the run holds, and decides nothing:
    ``assert_case`` receives that root and one offset and states what the runner
    does with them.
    """

    with candidate_repository() as repository:

        @seed(READ_CANDIDATE_PROPERTY_SEED)
        @settings(
            max_examples=READ_CANDIDATE_PROPERTY_EXAMPLES,
            print_blob=True,
            deadline=None,
        )
        @given(offset=invalid_offsets())
        def run_cases(offset: object) -> None:
            assert_case(repository.root, offset)

        run_replayable_property(
            run_cases,
            seed_value=READ_CANDIDATE_PROPERTY_SEED,
            replay_path=READ_CANDIDATE_PROPERTY_REPLAY,
        )


def wired_candidate_text() -> str:
    """Return the captured Change record repeated to need more than one piece."""
    runner = load_runner()
    record = Path(CAPTURED_CHANGE_RECORD).read_text(encoding=_TEXT_ENCODING)
    limit: int = runner.PIECE_CHARACTER_LIMIT
    repeats = _WIRED_CANDIDATE_LIMIT_MULTIPLE * limit // len(record) + 1
    return record * repeats


@dataclass(frozen=True)
class CandidateRepository:
    """A Git repository with a candidate file, and the sender for requests against it."""

    root: Path
    candidate: Path
    send: Callable[[Mapping[str, object]], RequestCall]

    def hold(self, text: str) -> None:
        """Replace the candidate's text."""
        self.candidate.write_bytes(text.encode(_TEXT_ENCODING))


@contextmanager
def candidate_repository() -> Iterator[CandidateRepository]:
    """Create a Git repository with an empty candidate file and yield it.

    The sender adds the repository's checkout root to a request as its ``root``,
    passes the request, as JSON on stdin, to the runner's entry point from the
    repository's working directory, and returns what the runner printed.
    """
    runner = load_runner()

    with TemporaryDirectory() as temporary:
        repository = Path(temporary)

        def send(request: Mapping[str, object]) -> RequestCall:
            sent = {**request, runner.RequestField.ROOT: str(repository)}
            sink = StringIO()
            exit_code = int(runner.main(stdin=StringIO(json.dumps(sent)), stdout=sink))
            output = sink.getvalue()
            line = output.removesuffix(runner.LINE_TERMINATOR)
            return RequestCall(
                request=sent,
                exit_code=exit_code,
                output=output,
                line=line,
                result=json.loads(line),
            )

        subprocess.run(  # noqa: S603
            ["git", "init", "--quiet", str(repository)],  # noqa: S607
            check=True,
        )
        candidate = repository / CANDIDATE_PATH
        candidate.parent.mkdir()
        candidate.touch()
        with chdir(repository):
            yield CandidateRepository(root=repository, candidate=candidate, send=send)


@contextmanager
def candidate_requests(
    text: str,
) -> Iterator[Callable[[Mapping[str, object]], RequestCall]]:
    """Hold ``text`` as a candidate in a Git repository and yield a request sender."""
    with candidate_repository() as repository:
        repository.hold(text)
        yield repository.send
