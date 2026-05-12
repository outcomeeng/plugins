"""Eval result serialization and a thin HTML viewer.

The data artifact is a JSON document with a stable schema; the HTML file is
a presentation layer that reads the same JSON (embedded inline so ``file://``
opens work) and renders it client-side. Downstream tooling — including any
future Next.js app — consumes the JSON directly and never parses the HTML.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from outcomeeng_evals.case import Case
from outcomeeng_evals.runner import RunMetadata
from outcomeeng_evals.suite import SuiteResult, TrialResult


# Integer-as-string schema version for the JSON results document and the
# history.jsonl rows. Bumped on incompatible changes; the committed
# baseline history rows carry the same value.
JSON_SCHEMA_VERSION = "1"


def serialize_result(result: SuiteResult, title: str) -> dict[str, Any]:
    """Serialize a ``SuiteResult`` to a JSON-stable plain dict."""
    case_count = len(result.outcomes)
    passed_count = sum(1 for o in result.outcomes if o.passed)
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "title": title,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "suite": {
            "passed": result.passed,
            "pass_rate": result.pass_rate,
            "threshold": result.threshold,
            "cases_total": case_count,
            "cases_passed": passed_count,
        },
        "cost_summary": _cost_summary(result),
        "trial_stability": _trial_stability(result),
        "outcomes": [
            {
                "case": _case_to_dict(outcome.case),
                "passed": outcome.passed,
                "trial_pass_count": outcome.trial_pass_count,
                "trial_count": len(outcome.trials),
                "trial_pass_rate": outcome.trial_pass_rate,
                "trials": [_trial_to_dict(t) for t in outcome.trials],
            }
            for outcome in result.outcomes
        ],
    }


def _trial_stability(result: SuiteResult) -> dict[str, Any]:
    """Aggregate per-case trial pass rates across the suite.

    For k=1 the per-case rate is always 0 or 1; mean and stddev describe
    the across-case distribution. Stddev is ``null`` when fewer than two
    cases were run (variance is undefined).
    """
    if not result.outcomes:
        return {
            "max_trials_per_case": 0,
            "min_trials_per_case": 0,
            "mean_trial_pass_rate": None,
            "stddev_trial_pass_rate": None,
            "min_trial_pass_rate": None,
            "max_trial_pass_rate": None,
        }
    rates = [outcome.trial_pass_rate for outcome in result.outcomes]
    trial_counts = [len(outcome.trials) for outcome in result.outcomes]
    return {
        "max_trials_per_case": max(trial_counts),
        "min_trials_per_case": min(trial_counts),
        "mean_trial_pass_rate": statistics.fmean(rates),
        "stddev_trial_pass_rate": (statistics.stdev(rates) if len(rates) > 1 else None),
        "min_trial_pass_rate": min(rates),
        "max_trial_pass_rate": max(rates),
    }


def _cost_summary(result: SuiteResult) -> dict[str, Any]:
    """Aggregate per-trial cost and timing across the whole suite."""
    trials_total = 0
    trials_with_metadata = 0
    total_cost_usd: float | None = None
    total_duration_ms: float | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    for outcome in result.outcomes:
        for trial in outcome.trials:
            trials_total += 1
            md = trial.metadata
            if (
                md.total_cost_usd is None
                and md.duration_ms is None
                and md.input_tokens is None
                and md.output_tokens is None
            ):
                continue
            trials_with_metadata += 1
            total_cost_usd = _add(total_cost_usd, md.total_cost_usd)
            total_duration_ms = _add(total_duration_ms, md.duration_ms)
            total_input_tokens = _add_int(total_input_tokens, md.input_tokens)
            total_output_tokens = _add_int(total_output_tokens, md.output_tokens)
    return {
        "trials_total": trials_total,
        "trials_with_metadata": trials_with_metadata,
        "total_cost_usd": total_cost_usd,
        "total_duration_ms": total_duration_ms,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
    }


def _add(accum: float | None, value: float | None) -> float | None:
    if value is None:
        return accum
    return value if accum is None else accum + value


def _add_int(accum: int | None, value: int | None) -> int | None:
    if value is None:
        return accum
    return value if accum is None else accum + value


def _case_to_dict(case: Case) -> dict[str, Any]:
    # ``must_contain`` / ``must_not_contain`` entries are returned by
    # reference (just unwrapped from their tuples into lists for JSON).
    # ``serialize_result`` hands the result straight to ``json.dumps`` and
    # never mutates it; the previous ``dict(e)`` was only a shallow copy,
    # so it isolated nothing the nested values would care about anyway.
    return {
        "id": case.id,
        "input": case.input,
        "must_contain": list(case.must_contain),
        "must_not_contain": list(case.must_not_contain),
    }


def _trial_to_dict(trial: TrialResult) -> dict[str, Any]:
    return {
        "trial_index": trial.trial_index,
        "prompt": trial.prompt,
        "response": trial.response,
        "verdict": trial.verdict,
        "grade": {
            "passed": trial.grade.passed,
            "reasons": list(trial.grade.reasons),
        },
        "metadata": _metadata_to_dict(trial.metadata),
    }


def _metadata_to_dict(metadata: RunMetadata) -> dict[str, Any]:
    return {
        "duration_ms": metadata.duration_ms,
        "total_cost_usd": metadata.total_cost_usd,
        "input_tokens": metadata.input_tokens,
        "output_tokens": metadata.output_tokens,
        "cache_read_input_tokens": metadata.cache_read_input_tokens,
        "cache_creation_input_tokens": metadata.cache_creation_input_tokens,
        "num_turns": metadata.num_turns,
        "stop_reason": metadata.stop_reason,
    }


def write_json_report(result: SuiteResult, output_path: Path, title: str) -> Path:
    """Write the JSON results document to ``output_path``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_result(result, title)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def write_html_report(result: SuiteResult, output_path: Path, title: str) -> Path:
    """Write the HTML viewer to ``output_path``.

    The viewer embeds the JSON payload in a ``<script type="application/json">``
    tag so the page renders under ``file://`` without a CORS-restricted fetch.
    A sibling ``.json`` file with the same name is also written, so external
    tooling can consume the data directly without parsing HTML.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_result(result, title)
    sidecar = output_path.with_suffix(".json")
    sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_path.write_text(_render_html_shell(payload), encoding="utf-8")
    return output_path


def _render_html_shell(payload: dict[str, Any]) -> str:
    # Escape ``</`` → ``<\/`` inside the JSON so an embedded ``</script>``
    # (or any ``</…``) in a string value cannot terminate the surrounding
    # ``<script type="application/json">`` block. That block's content model
    # is raw text terminated only by ``</script>``, so escaping ``</`` is
    # the necessary and sufficient hardening here. Do NOT also HTML-entity-
    # escape ``<``/``>``/``&`` in the payload: inside a ``<script>`` element
    # the bytes are not HTML-parsed, so ``&lt;`` would reach ``JSON.parse``
    # verbatim and corrupt the data. (HTML-entity escaping is correct for
    # the page ``<title>`` — see ``_escape`` — because that is HTML text.)
    embedded = json.dumps(payload).replace("</", "<\\/")
    title = payload.get("title", "Eval report")
    safe_title = _escape(str(title))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<style>{_STYLE}</style>
</head>
<body>
<div id="root"></div>
<script id="eval-results" type="application/json">{embedded}</script>
<script>{_VIEWER_JS}</script>
</body>
</html>
"""


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_STYLE = """
:root {
  color-scheme: light dark;
  --bg: #fafafa;
  --fg: #1f2328;
  --muted: #57606a;
  --pass: #1f883d;
  --fail: #cf222e;
  --card: #ffffff;
  --border: #d0d7de;
  --code-bg: #f6f8fa;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117;
    --fg: #e6edf3;
    --muted: #8b949e;
    --pass: #3fb950;
    --fail: #f85149;
    --card: #161b22;
    --border: #30363d;
    --code-bg: #161b22;
  }
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--fg); font-family: -apple-system, system-ui, BlinkMacSystemFont, sans-serif; margin: 0; padding: 2rem 1.5rem 4rem; }
.container { max-width: 1080px; margin: 0 auto; }
header { margin-bottom: 1.5rem; }
h1 { font-size: 1.5rem; margin: 0 0 0.25rem; }
.meta { color: var(--muted); font-size: 0.9rem; }
.suite-card, .case-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1rem; }
.suite-card h2, .case-card h3 { margin: 0 0 0.5rem; font-size: 1.1rem; }
.stat { display: inline-block; margin-right: 1.5rem; }
.stat-label { color: var(--muted); font-size: 0.85rem; }
.stat-value { font-weight: 600; }
.verdict { font-weight: 700; padding: 0.15rem 0.6rem; border-radius: 999px; font-size: 0.85rem; margin-left: 0.5rem; }
.verdict.pass { background: rgba(63, 185, 80, 0.15); color: var(--pass); }
.verdict.fail { background: rgba(248, 81, 73, 0.15); color: var(--fail); }
.case-card.pass { border-left: 4px solid var(--pass); }
.case-card.fail { border-left: 4px solid var(--fail); }
.case-id { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
details { margin: 0.5rem 0; }
summary { cursor: pointer; font-weight: 500; color: var(--muted); padding: 0.25rem 0; }
summary:hover { color: var(--fg); }
pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px; padding: 0.75rem 1rem; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; line-height: 1.4; margin: 0.5rem 0; }
.expected-list { font-size: 0.9rem; padding-left: 1.2rem; margin: 0.25rem 0; }
.expected-list li { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.trial-block { margin: 1rem 0 0; padding-top: 1rem; border-top: 1px dashed var(--border); }
.trial-header h4 { margin: 0; font-size: 0.95rem; display: inline-block; }
.reason { color: var(--fail); font-size: 0.85rem; margin: 0.25rem 0; padding-left: 1rem; }
.error-banner { background: rgba(248, 81, 73, 0.15); color: var(--fail); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
"""


_VIEWER_JS = r"""
(function () {
  "use strict";
  const root = document.getElementById("root");
  const dataEl = document.getElementById("eval-results");
  let data;
  try {
    data = JSON.parse(dataEl.textContent);
  } catch (err) {
    root.innerHTML = "<div class='error-banner'>Could not parse embedded eval results: " + String(err) + "</div>";
    return;
  }
  render(root, data);

  function render(container, data) {
    const wrap = el("div", { class: "container" });
    wrap.appendChild(renderHeader(data));
    wrap.appendChild(renderSuite(data.suite));
    if (data.cost_summary) wrap.appendChild(renderCostSummary(data.cost_summary));
    if (data.trial_stability && data.trial_stability.max_trials_per_case > 1) {
      wrap.appendChild(renderStability(data.trial_stability));
    }
    (data.outcomes || []).forEach((o) => wrap.appendChild(renderCase(o)));
    container.appendChild(wrap);
  }

  function renderStability(stability) {
    const card = el("section", { class: "suite-card" });
    card.appendChild(el("h2", {}, "Trial stability"));
    const stats = el("div", {});
    stats.appendChild(renderStat("Trials per case", stability.min_trials_per_case === stability.max_trials_per_case ? stability.max_trials_per_case : stability.min_trials_per_case + "–" + stability.max_trials_per_case));
    stats.appendChild(renderStat("Mean pass rate", pct(stability.mean_trial_pass_rate)));
    if (stability.stddev_trial_pass_rate != null) {
      stats.appendChild(renderStat("Stddev", pct(stability.stddev_trial_pass_rate)));
    }
    stats.appendChild(renderStat("Range", pct(stability.min_trial_pass_rate) + " – " + pct(stability.max_trial_pass_rate)));
    card.appendChild(stats);
    return card;
  }

  function renderCostSummary(summary) {
    const card = el("section", { class: "suite-card" });
    card.appendChild(el("h2", {}, "Cost and timing"));
    const stats = el("div", {});
    stats.appendChild(renderStat("Trials", summary.trials_total));
    if (summary.total_cost_usd != null) stats.appendChild(renderStat("Cost", "$" + summary.total_cost_usd.toFixed(4)));
    if (summary.total_duration_ms != null) stats.appendChild(renderStat("Duration", fmtDuration(summary.total_duration_ms)));
    if (summary.total_input_tokens != null) stats.appendChild(renderStat("Input tokens", summary.total_input_tokens));
    if (summary.total_output_tokens != null) stats.appendChild(renderStat("Output tokens", summary.total_output_tokens));
    if (summary.trials_with_metadata !== summary.trials_total) {
      stats.appendChild(renderStat("With metadata", summary.trials_with_metadata + " / " + summary.trials_total));
    }
    card.appendChild(stats);
    return card;
  }

  function fmtDuration(ms) {
    if (ms < 1000) return ms.toFixed(0) + "ms";
    return (ms / 1000).toFixed(2) + "s";
  }

  function renderHeader(data) {
    const h = el("header");
    h.appendChild(el("h1", {}, data.title || "Eval report"));
    h.appendChild(el("div", { class: "meta" }, "Generated " + (data.generated_at || "")));
    return h;
  }

  function renderSuite(suite) {
    const klass = suite.passed ? "pass" : "fail";
    const card = el("section", { class: "suite-card" });
    card.appendChild(el("h2", {}, "Suite verdict"));
    card.appendChild(el("span", { class: "verdict " + klass }, suite.passed ? "PASS" : "FAIL"));
    const stats = el("div", { style: "margin-top: 0.75rem" });
    stats.appendChild(renderStat("Pass rate", pct(suite.pass_rate)));
    stats.appendChild(renderStat("Threshold", pct(suite.threshold)));
    stats.appendChild(renderStat("Cases passed", suite.cases_passed + " / " + suite.cases_total));
    card.appendChild(stats);
    return card;
  }

  function renderStat(label, value) {
    const stat = el("div", { class: "stat" });
    stat.appendChild(el("div", { class: "stat-label" }, label));
    stat.appendChild(el("div", { class: "stat-value" }, value));
    return stat;
  }

  function renderCase(outcome) {
    const klass = outcome.passed ? "pass" : "fail";
    const card = el("section", { class: "case-card " + klass });
    const h3 = el("h3");
    h3.appendChild(el("span", { class: "case-id" }, outcome.case.id));
    h3.appendChild(el("span", { class: "verdict " + klass }, outcome.passed ? "PASS" : "FAIL"));
    if (outcome.trial_count > 1) {
      h3.appendChild(el("span", { class: "meta", style: "margin-left: 0.75rem; font-size: 0.85rem;" },
        outcome.trial_pass_count + " / " + outcome.trial_count + " trials passed (" + pct(outcome.trial_pass_rate) + ")"));
    }
    card.appendChild(h3);
    card.appendChild(disclosure("Input payload", el("pre", {}, JSON.stringify(outcome.case.input, null, 2))));
    card.appendChild(renderExpectations(outcome.case));
    (outcome.trials || []).forEach((t) => card.appendChild(renderTrial(t)));
    return card;
  }

  function renderExpectations(caseObj) {
    const list = el("ul", { class: "expected-list" });
    (caseObj.must_contain || []).forEach((e) => list.appendChild(el("li", {}, "must_contain: " + describe(e))));
    (caseObj.must_not_contain || []).forEach((e) => list.appendChild(el("li", {}, "must_not_contain: " + describe(e))));
    return disclosure("Expected verdict structure", list);
  }

  function describe(e) {
    return JSON.stringify(e);
  }

  function renderTrial(trial) {
    const klass = trial.grade.passed ? "pass" : "fail";
    const block = el("div", { class: "trial-block" });
    const header = el("div", { class: "trial-header" });
    header.appendChild(el("h4", {}, "Trial " + trial.trial_index));
    header.appendChild(el("span", { class: "verdict " + klass }, trial.grade.passed ? "PASS" : "FAIL"));
    block.appendChild(header);
    const meta = renderTrialMetadata(trial.metadata);
    if (meta) block.appendChild(meta);
    (trial.grade.reasons || []).forEach((reason) => block.appendChild(el("div", { class: "reason" }, reason)));
    if (trial.verdict != null) {
      block.appendChild(disclosure("Parsed JSON verdict", el("pre", {}, JSON.stringify(trial.verdict, null, 2)), true));
    }
    block.appendChild(disclosure("Raw assistant response", el("pre", {}, trial.response)));
    block.appendChild(disclosure("Prompt sent", el("pre", {}, trial.prompt)));
    return block;
  }

  function renderTrialMetadata(md) {
    if (!md) return null;
    const fields = [];
    if (md.duration_ms != null) fields.push(fmtDuration(md.duration_ms));
    if (md.total_cost_usd != null) fields.push("$" + md.total_cost_usd.toFixed(4));
    if (md.input_tokens != null && md.output_tokens != null) {
      fields.push(md.input_tokens + " in / " + md.output_tokens + " out");
    }
    if (md.stop_reason) fields.push("stop=" + md.stop_reason);
    if (!fields.length) return null;
    return el("div", { class: "meta", style: "font-size: 0.85rem; margin-bottom: 0.5rem;" }, fields.join("  ·  "));
  }

  function disclosure(summaryText, contentNode, openByDefault) {
    const det = el("details");
    if (openByDefault) det.setAttribute("open", "");
    det.appendChild(el("summary", {}, summaryText));
    det.appendChild(contentNode);
    return det;
  }

  function el(tag, attrs, text) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) node.setAttribute(k, attrs[k]);
    }
    if (text != null) node.textContent = String(text);
    return node;
  }

  function pct(x) {
    if (typeof x !== "number") return String(x);
    return (x * 100).toFixed(1) + "%";
  }
})();
"""
