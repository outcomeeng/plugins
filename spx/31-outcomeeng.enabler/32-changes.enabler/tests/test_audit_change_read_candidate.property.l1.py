"""Property evidence: read-candidate returns every candidate in bounded, maximal pieces.

The rule is the spec assertion for the ``audit-change`` runner's
``read-candidate`` operation: each piece is the longest run of the remaining
characters that fits at most 16,000 characters and a complete serialized
response, its line terminator included, of at most 16,000 UTF-8 bytes, every
piece of a non-empty candidate
carries at least one character, an empty candidate returns one empty piece whose
``next`` is ``null``, and each piece carries the candidate's ``sha256`` and
``length`` with its ``offset`` and the ``next`` offset (``null`` after the last
piece, both counting characters). The generated domain is the candidate text,
varied in length, UTF-8 width, and escaping growth and including the empty
candidate, and a candidate past 100,000 characters read from offsets that leave
one final piece at the byte limit, with the offsets spanning every remainder
from where a response nears the byte limit to the character limit. Each case
takes its pieces from the runner's text seam; the request, file, and Git
boundary, the printed line, a request without ``offset``, and the refusal of an
``offset`` at or past the ``length`` are the wiring evidence in
``test_audit_change_read_candidate.scenario.l1.py``.

The size the text-seam cases measure is a reconstruction of the printed
response, so a second property reads generated candidates of escaped and wide
characters through the entry point, piece by piece, and compares the bytes the
runner wrote with the reconstruction at the same offset: each call writes
exactly the reconstructed number of bytes, within the byte limit, and the
pieces concatenate to the candidate. The generated domain is the candidate
text, varied in length and in the characters whose serialized form differs most
from their text. One Git repository holds the candidate for the whole run, and
each case replaces its text.

Offsets count characters of the candidate from 0, so a request whose ``offset``
is not a non-negative integer is refused as ``invalid-request``. The generated
domain is every JSON value outside that set: a negative integer, a number with a
fractional part, a string, a boolean, ``null``, an array, or an object. Each
case sends one request to the runner's request validation, which starts no
process and reads no file.

Independent oracles: the sha256 and length come from the generated text, the
size bounds from the contract's two limits, the growth of each added
character and of the ``next`` value from JSON's own encoding of them, and the
terminator written after each response from the runner's declaration of it, and
the bytes the runner wrote from the output sink the entry point wrote to; the
refused offsets are outside the non-negative integers by the construction of
each generated value.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.audit_change_read_candidate import (
    CANDIDATE_PATH,
    CandidateReading,
    FinalPieceReading,
    Piece,
    WireReading,
    exercise_candidate_readings,
    exercise_final_piece_readings,
    exercise_invalid_offsets,
    exercise_wire_readings,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Field = runner.RequestField
Reason = runner.BlockReason
Result = runner.ResultField


def _serialization_growth(character: str) -> int:
    """The UTF-8 bytes one more character adds to a response serialized as JSON.

    The response is a standard JSON document, so JSON's default encoding of a
    character is the growth the runner pays.
    """
    return len(json.dumps(character)[1:-1].encode("utf-8"))


def _extended_response_bytes(piece: Piece, text: str, consumed: int, end: int) -> int:
    """The bytes the response takes when the piece reaches ``end`` instead of ``consumed``.

    The extension adds JSON's own encoding of each character in
    ``text[consumed:end]`` and replaces the ``next`` value ``consumed`` with
    ``end``, which is JSON ``null`` when ``end`` is the end of the candidate.
    """
    added = sum(_serialization_growth(character) for character in text[consumed:end])
    following = None if end == len(text) else end
    return (
        piece.response_bytes
        + added
        + len(json.dumps(following))
        - len(json.dumps(consumed))
    )


def test_every_candidate_is_returned_whole_in_bounded_maximal_pieces() -> None:
    def assert_longest_run(piece: Piece, text: str, consumed: int) -> None:
        # A response grows with each added character while ``next`` is a number,
        # and ``next`` is ``null`` only when the piece reaches the end of the
        # candidate, so a longer run fits only if one more character fits or the
        # whole remainder, ending the candidate, fits.
        start = int(piece.result[Result.OFFSET])
        for end in sorted({consumed + 1, len(text)}):
            if end - start > runner.PIECE_CHARACTER_LIMIT:
                continue
            assert (
                _extended_response_bytes(piece, text, consumed, end)
                > runner.PIECE_BYTE_LIMIT
            )

    def assert_piece(piece: Piece, text: str) -> None:
        offset = piece.offset
        content = str(piece.result[Result.CONTENT])
        following = piece.result[Result.NEXT]
        consumed = offset + len(content)

        assert piece.result[Result.PATH] == CANDIDATE_PATH
        assert (
            piece.result[Result.SHA256]
            == hashlib.sha256(text.encode("utf-8")).hexdigest()
        )
        assert piece.result[Result.LENGTH] == len(text)
        assert piece.result[Result.OFFSET] == offset
        assert text[offset:consumed] == content
        assert len(content) <= runner.PIECE_CHARACTER_LIMIT
        assert piece.response_bytes <= runner.PIECE_BYTE_LIMIT
        if text:
            assert len(content) >= 1
        else:
            assert content == ""
            assert following is None
        if consumed == len(text):
            assert following is None
        else:
            assert following == consumed
            assert_longest_run(piece, text, consumed)

    def assert_reading(reading: CandidateReading) -> None:
        text = reading.text

        assert reading.pieces[0].offset == 0
        assert (
            "".join(str(piece.result[Result.CONTENT]) for piece in reading.pieces)
            == text
        )
        if not text:
            assert len(reading.pieces) == 1
        for piece in reading.pieces:
            assert_piece(piece, text)
        assert reading.pieces[-1].result[Result.NEXT] is None
        assert [piece.offset for piece in reading.pieces] == [
            sum(
                len(str(earlier.result[Result.CONTENT]))
                for earlier in reading.pieces[:index]
            )
            for index in range(len(reading.pieces))
        ]

    def assert_final_pieces(reading: FinalPieceReading) -> None:
        for piece in reading.pieces:
            assert_piece(piece, reading.text)

    exercise_candidate_readings(assert_reading)
    exercise_final_piece_readings(assert_final_pieces)


def test_every_emitted_response_takes_the_bytes_of_its_reconstruction() -> None:
    def assert_reading(reading: WireReading) -> None:
        assert (
            "".join(str(wired.call.result[Result.CONTENT]) for wired in reading.pieces)
            == reading.text
        )
        for wired in reading.pieces:
            assert wired.call.exit_code == runner.ExitCode.OK
            assert wired.call.output_bytes == wired.seam.response_bytes
            assert wired.call.output_bytes <= runner.PIECE_BYTE_LIMIT
            assert (
                wired.call.result[Result.CONTENT] == wired.seam.result[Result.CONTENT]
            )
            assert wired.call.result[Result.NEXT] == wired.seam.result[Result.NEXT]

    exercise_wire_readings(assert_reading)


def test_every_offset_that_is_not_a_non_negative_integer_is_refused_as_invalid_request() -> (
    None
):
    def assert_refused(root: Path, offset: object) -> None:
        request = {
            Field.OPERATION: runner.Operation.READ_CANDIDATE,
            Field.PATH: CANDIDATE_PATH,
            Field.ROOT: str(root),
            Field.OFFSET: offset,
        }

        with pytest.raises(runner.Blocked) as refusal:
            runner.validate_request(request)

        assert refusal.value.reason == Reason.INVALID_REQUEST

    exercise_invalid_offsets(assert_refused)
