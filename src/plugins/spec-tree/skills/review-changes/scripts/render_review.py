"""CLI: render a review-result into the human-readable ``review.md`` surface.

Reads ``review-result.json`` from the thread store under the given
slug, parses it through ``review_result.parse_json`` (which enforces
the canonical schema), and writes a
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
import string
import sys
from types import ModuleType

REVIEW_RESULT_RECORD_NAME = "review-result.json"


def _load_thread_store() -> ModuleType:
    cached = sys.modules.get("thread_store")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "manage-thread-store"
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


RENDER_DIR = pathlib.Path(__file__).resolve().parent.parent / "references" / "render"
DEFAULT_TITLE = "Change Review"

# Severity wire value → render template filename. Mirrors the spec
# clause that maps the two severities to render-class headings.
_SEVERITY_TO_TEMPLATE = {
    "blocking": "finding-blocking.md",
    "debt": "finding-debt.md",
}

# Severity wire value → census-marker template filename. Emitted in place
# of a severity's findings when that bucket is empty, so every severity is
# reported uniformly (the reviewer states the census; the consumer judges
# which present findings block the merge, by validity and phase).
_SEVERITY_TO_EMPTY = {
    "blocking": "none-blocking.md",
    "debt": "none-debt.md",
}


def _load_template(name: str) -> string.Template:
    """Load and return a ``string.Template`` for the named render template.

    Templates live under ``references/render/`` — one markdown file per
    render section. Substituted via stdlib ``string.Template`` so the
    rendered shape is data, not f-string concatenation. The GH-hosted
    CI review workflow can consume the same files.
    """
    return string.Template((RENDER_DIR / name).read_text(encoding="utf-8"))


def _load_static(name: str) -> str:
    """Load a render template that has no placeholders; return its text."""
    return (RENDER_DIR / name).read_text(encoding="utf-8").rstrip()


def _location(finding: "object") -> str:
    """Return the ``file:line`` location string used in finding headings."""
    return f"{finding.file}:{finding.line}"  # type: ignore[attr-defined]


def _render_finding(template: string.Template, finding: "object") -> str:
    """Substitute a finding's fields into a per-class template."""
    return template.substitute(
        concern=str(finding.concern),  # type: ignore[attr-defined]
        location=_location(finding),
        message=finding.message,  # type: ignore[attr-defined]
        rule=finding.rule,  # type: ignore[attr-defined]
        action=finding.action,  # type: ignore[attr-defined]
    ).rstrip()


def _partition_findings(
    findings: list["object"],
) -> dict[str, list["object"]]:
    """Split findings into two buckets keyed by severity wire value."""
    buckets: dict[str, list["object"]] = {
        "blocking": [],
        "debt": [],
    }
    for finding in findings:
        buckets[str(finding.severity)].append(finding)  # type: ignore[attr-defined]
    return buckets


def _render_markdown(result: "object") -> str:
    """Render a parsed ``ReviewResult`` into the ``review.md`` surface.

    Loads per-section templates from ``references/render/``, partitions
    findings by severity, substitutes placeholders via stdlib
    ``string.Template``, and assembles the body in severity order
    (BLOCKING → DEBT → acknowledgements). Every severity is
    reported uniformly: a bucket with findings renders them, an empty
    bucket renders its ``none-<severity>.md`` census marker — no severity
    is privileged and the render states a census, never a merge verdict.
    Both blocking and debt render ``message``/``action`` as
    Evidence/Required in the templates.
    """
    document_tpl = _load_template("document.md")
    severity_templates = {
        sev: _load_template(name) for sev, name in _SEVERITY_TO_TEMPLATE.items()
    }
    empty_markers = {
        sev: _load_static(name) for sev, name in _SEVERITY_TO_EMPTY.items()
    }
    acks_tpl = _load_template("acknowledgements.md")

    findings = list(result.findings)  # type: ignore[attr-defined]
    buckets = _partition_findings(findings)
    for bucket in buckets.values():
        bucket.sort(key=lambda f: (str(f.concern), f.id))  # type: ignore[attr-defined]

    body_parts: list[str] = []
    for severity in ("blocking", "debt"):
        bucket = buckets[severity]
        if bucket:
            body_parts.extend(
                _render_finding(severity_templates[severity], f) for f in bucket
            )
        else:
            body_parts.append(empty_markers[severity])

    acknowledgements = list(result.acknowledgements)  # type: ignore[attr-defined]
    if acknowledgements:
        items = "\n".join(f"- {a}" for a in acknowledgements)
        body_parts.append(acks_tpl.substitute(items=items).rstrip())

    body = "\n\n".join(body_parts)
    summary = result.summary or ""  # type: ignore[attr-defined]
    return (
        document_tpl.substitute(title=DEFAULT_TITLE, summary=summary, body=body) + "\n"
    )


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
