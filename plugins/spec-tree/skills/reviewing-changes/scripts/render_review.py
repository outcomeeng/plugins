"""CLI: render a review-result into the human-readable ``review.md`` surface.

Reads ``review-result.json`` from the thread store under the given
slug, parses it through ``review_result.parse_json`` (which enforces
the canonical schema and the consistency invariant), and writes a
markdown surface to stdout. The wrapper agent pipes the stdout payload
into ``write_record.py`` to persist ``review.md``.

Exit codes:

- ``0`` — markdown was rendered.
- non-zero — the slug has no ``review-result.json``, or the document
  fails ``parse_json``; no markdown is emitted on the rejection path.

Every filesystem effect routes through the ``thread_store`` facade.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
from types import ModuleType

REVIEW_RESULT_RECORD_NAME = "review-result.json"


def _load_thread_store() -> ModuleType:
    cached = sys.modules.get("thread_store")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "thread-store"
        / "scripts"
        / "thread_store.py"
    )
    spec = importlib.util.spec_from_file_location("thread_store", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load thread_store from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["thread_store"] = module
    spec.loader.exec_module(module)
    return module


def _load_review_result() -> ModuleType:
    cached = sys.modules.get("review_result")
    if cached is not None:
        return cached
    path = pathlib.Path(__file__).resolve().parent / "review_result.py"
    spec = importlib.util.spec_from_file_location("review_result", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load review_result from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_result"] = module
    spec.loader.exec_module(module)
    return module


def _render_markdown(result: "object") -> str:
    """Render a parsed ``ReviewResult`` into the ``review.md`` surface.

    The shape is deterministic: a header naming the decision, the
    summary paragraph, an acknowledgements section when present, and a
    findings table sorted by severity then concern. The renderer keeps
    no policy of its own — the decision and severity wire values flow
    through unchanged so a downstream reader can grep on them.
    """
    decision = str(result.decision)  # type: ignore[attr-defined]
    summary = result.summary  # type: ignore[attr-defined]
    findings = result.findings  # type: ignore[attr-defined]
    acknowledgements = result.acknowledgements  # type: ignore[attr-defined]

    lines: list[str] = []
    lines.append(f"# Review: {decision}")
    lines.append("")
    if summary:
        lines.append(summary)
        lines.append("")

    if acknowledgements:
        lines.append("## Acknowledgements")
        lines.append("")
        for ack in acknowledgements:
            lines.append(f"- {ack}")
        lines.append("")

    if findings:
        lines.append("## Findings")
        lines.append("")
        lines.append("| ID | Severity | Concern | File:Line | Rule | Message |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        # Severity sort order: must_fix first, then suggestion, then nit.
        severity_order = {"must_fix": 0, "suggestion": 1, "nit": 2}
        sorted_findings = sorted(
            findings,
            key=lambda f: (
                severity_order.get(str(f.severity), 99),
                str(f.concern),
                f.id,
            ),
        )
        for finding in sorted_findings:
            location = f"{finding.file}:{finding.line}"
            # Pipe characters in messages would break the markdown
            # table; escape them with a backslash so the table parses.
            message = finding.message.replace("|", r"\|")
            lines.append(
                f"| {finding.id} | {finding.severity} | {finding.concern} "
                f"| {location} | {finding.rule} | {message} |"
            )
        lines.append("")
    else:
        lines.append("## Findings")
        lines.append("")
        lines.append("_No findings._")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a review-result JSON document into review.md content."
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="thread slug; derived via thread_store.current_slug() when omitted",
    )
    args = parser.parse_args(argv)

    thread_store = _load_thread_store()
    slug = args.slug
    if slug is None:
        try:
            slug = thread_store.current_slug()
        except thread_store.ConfigurationError as exc:
            sys.stderr.write(f"{exc}\n")
            return 1
    try:
        payload = thread_store.read(slug, REVIEW_RESULT_RECORD_NAME)
    except thread_store.NotFound as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except thread_store.ThreadStoreError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    review_result = _load_review_result()
    try:
        result = review_result.parse_json(payload.decode("utf-8"))
    except UnicodeDecodeError as exc:
        sys.stderr.write(f"{REVIEW_RESULT_RECORD_NAME} is not valid UTF-8: {exc}\n")
        return 1
    except review_result.ReviewResultValidationError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    sys.stdout.write(_render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
