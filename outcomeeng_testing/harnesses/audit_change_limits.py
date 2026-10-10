"""Change records sized to a measured limit, and the runner's ``count-limits`` answer.

Each arrangement writes one well-formed record whose measured quantity equals a
requested count by construction: ``n`` words in the title, ``n`` one-sentence
statements in an Intent part, ``n`` Decisions rows, or ``n`` one-sentence
statements in one answer. The returned observation carries the runner's answer and
the text the arranged section is named by in the record. The linked tests own every
predicate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from outcomeeng_testing.harnesses.audit_change_run import (
    RunnerCall,
    audit_workspace,
    load_runner,
)

_WORD: Final = "word"
_STATEMENT: Final = "Something holds."
_QUESTION: Final = "Which option?"
_INTENT_PART: Final = "What"
_DECISIONS_HEADING: Final = "Decisions"
_RECORD_PATH: Final = "changes/limits-record.md"


class Measure(StrEnum):
    """One quantity ``count-limits`` measures, valued by the text naming it in the record."""

    TITLE = "title"
    INTENT = _INTENT_PART
    ROWS = _DECISIONS_HEADING
    ANSWER = "answer"


@dataclass(frozen=True)
class LimitObservation:
    """The runner's answer for a record measuring ``count`` of ``measure``."""

    measure: Measure
    count: int
    call: RunnerCall


def limit_of(measure: Measure) -> int:
    """Return the limit the runner declares for ``measure``."""
    runner = load_runner()
    limits = {
        Measure.TITLE: runner.TITLE_WORD_LIMIT,
        Measure.INTENT: runner.INTENT_SENTENCE_LIMIT,
        Measure.ROWS: runner.DECISION_ROW_LIMIT,
        Measure.ANSWER: runner.ANSWER_SENTENCE_LIMIT,
    }
    return int(limits[measure])


def _record(measure: Measure, count: int) -> str:
    title_words = count if measure is Measure.TITLE else 1
    intent_statements = count if measure is Measure.INTENT else 1
    rows = count if measure is Measure.ROWS else 1
    answer_statements = count if measure is Measure.ANSWER else 1
    answer = " ".join([_STATEMENT] * answer_statements)
    decisions = "\n".join(
        f"{index}. {_QUESTION} {answer}" for index in range(1, rows + 1)
    )
    intent = " ".join([_STATEMENT] * intent_statements)
    title = " ".join([_WORD] * title_words)
    return (
        f"---\ntitle: {title}\nproduct: product\nmaturity: Proposed\n---\n"
        f"## Intent\n\n**{_INTENT_PART}:** {intent}\n\n"
        f"## {_DECISIONS_HEADING}\n\n{decisions}\n"
    )


def measure_record(measure: Measure, count: int) -> LimitObservation:
    """Write a record measuring ``count`` of ``measure`` and request ``count-limits`` over it."""
    runner = load_runner()
    field = runner.RequestField
    with audit_workspace() as workspace:
        target = workspace.root / _RECORD_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_record(measure, count), encoding=runner.TEXT_ENCODING)
        call = workspace.invoke(
            {field.OPERATION: runner.Operation.COUNT_LIMITS, field.PATH: _RECORD_PATH}
        )
    return LimitObservation(measure=measure, count=count, call=call)
