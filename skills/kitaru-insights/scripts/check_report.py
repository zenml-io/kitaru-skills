"""Check drafted insight reports against Kitaru's structured report contract and Zuri's chart limits.

Validates a single InsightInput JSON object or an array of 1 to 100 reports:
top-level report fields, coverage, highlight pointer, ordered findings, all 17
typed InsightArtifact schemas (including Zuri's 11 chart limits), plain-text
summaries, skill provenance, and no leaked run metadata. Optionally prints a
safely quoted `kitaru insight create --insight-file` command. This offline
helper never contacts Kitaru.
"""

import argparse
import json
import math
import re
import shlex
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

NAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?$")
LEGACY_SHARED_KEY = "kitaru.insights/v1"
SKILL_KEY = "kitaru.insights.skill/v1"
REPORT_FIELDS = {
    "name",
    "title",
    "summary",
    "source_provider",
    "coverage",
    "highlight",
    "next_step",
    "findings",
    "suggested_questions",
    "metadata",
}
COVERAGE_FIELDS = {
    "sessions_analyzed",
    "sessions_available",
    "skipped",
    "failed",
    "started_after",
    "started_before",
    "caveats",
}
HIGHLIGHT_FIELDS = {"finding_id", "artifact_index"}
ACTION_FIELDS = {"label", "prompt", "summary"}
QUESTION_FIELDS = {"label", "prompt"}
FINDING_FIELDS = {
    "id",
    "title",
    "summary",
    "body",
    "tier",
    "kind",
    "severity",
    "change_status",
    "artifacts",
    "contributing_session_ids",
    "check_first",
    "action",
    "suggested_questions",
}

TONES = {"neutral", "risk", "danger", "good", "warn"}
SEVERITIES = {"high", "medium", "low"}
FINDING_KINDS = {"finding", "bright_spot", "opportunity", "coverage_gap"}
CHANGE_STATUSES = {"new", "recurring", "narrowed", "resolved"}
VERDICTS = {"pass", "fail", "unclear"}
TIERS = {"primary", "secondary"}
LEVELS = {"standard", "deep"}
RATE_METHODS = {None, "readers", "subagents", "jev", "mixed"}
RATE_BASES = {"census", "exact_proxy", "measurement", "random_slice", "targeted_only"}
IMPACT_UNITS = {"tokens", "usd", "seconds", "sessions", "calls"}
TABLE_FORMATS = {"text", "mono", "number", "percent", "percent_bar", "delta", "badge", "session_link"}
STEP_ROLES = {"user", "agent", "tool", "system"}
ALIGNED_STATUSES = {"present", "missing", "highlight_bad", "highlight_good"}
TEXT_STYLES = {"body", "callout", "hypothesis"}
MATRIX_STATES = {"tool", "span", "node", "step"}

MAX_PRIMARY_FINDINGS = 8
SERVER_MAX_FINDINGS = 30
MAX_ARTIFACTS_PER_FINDING = 12
MAX_SUGGESTED_QUESTIONS = 5
MAX_CONTRIBUTING_SESSIONS = 1000
SERVER_MAX_BATCH = 100
SUMMARY_MAX = 320
SPLIT_BAR_MIN_SHARE = 0.02
MARKDOWN_IN_PLAIN_TEXT = re.compile(r"`|\*\*|__|\]\(|^\s*(?:#|[-*+] |\d+\. )", re.MULTILINE)


def _is_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _finite(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def _text(value: Any, limit: int | None = None) -> bool:
    return isinstance(value, str) and bool(value.strip()) and (limit is None or len(value) <= limit)


def _opt_text(value: Any, limit: int | None = None) -> bool:
    return value is None or _text(value, limit)


def _aware_iso(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _reject_constant(name: str) -> None:
    raise ValueError(f"{name} is not valid JSON")


def _unknown_keys(obj: dict[str, Any], allowed: set[str], where: str) -> list[str]:
    return [f"{where}: unknown field {k}" for k in sorted(set(obj) - allowed)]


def _check_plain_summary(value: Any, where: str, *, required: bool = False) -> list[str]:
    if value is None:
        return [f"{where}: required, one plain-text line of at most {SUMMARY_MAX} characters"] if required else []
    if not _text(value, SUMMARY_MAX) or "\n" in value:
        return [f"{where}: one plain-text line of at most {SUMMARY_MAX} characters"]
    if MARKDOWN_IN_PLAIN_TEXT.search(value):
        return [f"{where}: plain text only; put Markdown formatting in body or a text artifact"]
    return []


def _check_action(action: Any, where: str) -> list[str]:
    if not isinstance(action, dict):
        return [f"{where}: expected an object"]
    errors = _unknown_keys(action, ACTION_FIELDS, where)
    if not _text(action.get("label"), 60):
        errors.append(f"{where}.label: required, at most 60 characters")
    if not _text(action.get("prompt"), 16_000):
        errors.append(f"{where}.prompt: required, at most 16000 characters")
    if not _opt_text(action.get("summary"), 300):
        errors.append(f"{where}.summary: at most 300 characters")
    return errors


def _check_questions(questions: Any, where: str) -> list[str]:
    if questions is None:
        return []
    if not isinstance(questions, list) or len(questions) > MAX_SUGGESTED_QUESTIONS:
        return [f"{where}: expected a list of at most {MAX_SUGGESTED_QUESTIONS} questions"]
    errors = []
    for index, item in enumerate(questions):
        item_where = f"{where}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_where}: expected an object")
            continue
        errors += _unknown_keys(item, QUESTION_FIELDS, item_where)
        if not _text(item.get("label"), 80):
            errors.append(f"{item_where}.label: required, at most 80 characters")
        if not _opt_text(item.get("prompt"), 2_000):
            errors.append(f"{item_where}.prompt: at most 2000 characters")
    return errors


def _check_coverage(coverage: Any, where: str) -> list[str]:
    if not isinstance(coverage, dict):
        return [f"{where}: required object accounting for sessions_analyzed"]
    errors = _unknown_keys(coverage, COVERAGE_FIELDS, where)
    analyzed = coverage.get("sessions_analyzed")
    if not _is_int(analyzed) or analyzed < 0:
        errors.append(f"{where}.sessions_analyzed: non-negative integer required")
    available = coverage.get("sessions_available")
    if available is not None and (not _is_int(available) or available < 0):
        errors.append(f"{where}.sessions_available: non-negative integer or null")
    elif _is_int(analyzed) and _is_int(available) and analyzed > available:
        errors.append(f"{where}: sessions_analyzed cannot exceed sessions_available")
    for field in ("skipped", "failed"):
        val = coverage.get(field, 0)
        if not _is_int(val) or val < 0:
            errors.append(f"{where}.{field}: non-negative integer")
    for field in ("started_after", "started_before"):
        if coverage.get(field) is not None and not _aware_iso(coverage[field]):
            errors.append(f"{where}.{field}: timezone-aware ISO 8601 datetime required")
    caveats = coverage.get("caveats", [])
    if not isinstance(caveats, list) or len(caveats) > 10 or not all(_text(c) for c in caveats):
        errors.append(f"{where}.caveats: list of at most 10 non-empty strings")
    return errors


def check_artifact(artifact: Any, where: str = "artifact") -> list[str]:
    """Validate one typed InsightArtifact block against Kitaru's schema and Zuri's 11 limits."""
    if not isinstance(artifact, dict):
        return [f"{where}: expected an object"]
    kind = artifact.get("type")
    if not isinstance(kind, str):
        return [f"{where}: missing string type"]
    checker = ARTIFACT_CHECKERS.get(kind)
    if checker is None:
        return [f"{where}: unknown artifact type {kind!r}"]
    return checker(artifact, where)


def _check_stat_grid(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "items"}, where)
    items = data.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 6:
        return errors + [f"{where}.items: 1 to 6 stat items required"]
    for i, item in enumerate(items):
        iw = f"{where}.items[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{iw}: expected an object")
            continue
        errors += _unknown_keys(item, {"label", "value", "unit", "tone", "chat_prompt"}, iw)
        if not _text(item.get("label"), 60):
            errors.append(f"{iw}.label: required, at most 60 characters")
        val = item.get("value")
        if not (_finite(val) or isinstance(val, str)):
            errors.append(f"{iw}.value: finite number or string required")
        if not _opt_text(item.get("unit"), 32):
            errors.append(f"{iw}.unit: at most 32 characters")
        if item.get("tone", "neutral") not in TONES:
            errors.append(f"{iw}.tone: invalid tone")
        if not _opt_text(item.get("chat_prompt"), 1_000):
            errors.append(f"{iw}.chat_prompt: at most 1000 characters")
    return errors


def _check_rate(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(
        data,
        {"type", "presentation", "rate", "ci_low", "ci_high", "numerator", "denominator", "label", "basis", "tone", "chat_prompt"},
        where,
    )
    if data.get("presentation") not in {None, "range", "share_bar"}:
        errors.append(f"{where}.presentation: expected 'range', 'share_bar', or null")
    rate = data.get("rate")
    if not _finite(rate) or not 0 <= rate <= 1:
        errors.append(f"{where}.rate: number between 0 and 1 required")
    ci_low, ci_high = data.get("ci_low"), data.get("ci_high")
    if (ci_low is None) != (ci_high is None):
        errors.append(f"{where}: provide both ci_low and ci_high, or omit both")
    elif ci_low is not None:
        if not (_finite(ci_low) and _finite(ci_high) and 0 <= ci_low <= 1 and 0 <= ci_high <= 1):
            errors.append(f"{where}: ci_low and ci_high must be between 0 and 1")
        elif _finite(rate) and not ci_low <= rate <= ci_high:
            errors.append(f"{where}: expected ci_low <= rate <= ci_high")
    num, den = data.get("numerator"), data.get("denominator")
    if num is not None and (not _is_int(num) or num < 0):
        errors.append(f"{where}.numerator: non-negative integer or null")
    if den is not None and (not _is_int(den) or den < 1):
        errors.append(f"{where}.denominator: positive integer or null")
    if _is_int(num) and _is_int(den) and num > den:
        errors.append(f"{where}: numerator cannot exceed denominator")
    if not _opt_text(data.get("label"), 120):
        errors.append(f"{where}.label: at most 120 characters")
    if not _opt_text(data.get("basis"), 120):
        errors.append(f"{where}.basis: at most 120 characters")
    if data.get("tone", "risk") not in TONES:
        errors.append(f"{where}.tone: invalid tone")
    if not _opt_text(data.get("chat_prompt"), 1_000):
        errors.append(f"{where}.chat_prompt: at most 1000 characters")
    return errors


def _check_categorical(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "presentation", "unit", "baseline_value", "values"}, where)
    pres = data.get("presentation")
    if pres not in {None, "ranked_bars", "focus_bars", "baseline_bars", "path_bars", "split_bar", "donut"}:
        errors.append(f"{where}.presentation: invalid categorical presentation")
    if data.get("unit") is not None and not isinstance(data["unit"], str):
        errors.append(f"{where}.unit: string or null")
    baseline = data.get("baseline_value")
    if baseline is not None and (not _finite(baseline) or baseline < 0):
        errors.append(f"{where}.baseline_value: non-negative finite number or null")
    values = data.get("values")
    if not isinstance(values, list) or len(values) < 2:
        return errors + [f"{where}.values: at least 2 categories required (use stat_grid or rate for one number)"]
    labels = []
    numeric_values = []
    for i, item in enumerate(values):
        iw = f"{where}.values[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{iw}: expected an object")
            continue
        errors += _unknown_keys(item, {"label", "value", "total", "tone", "focus", "chat_prompt"}, iw)
        if not _text(item.get("label")):
            errors.append(f"{iw}.label: non-empty string required")
        else:
            labels.append(item["label"])
        val = item.get("value")
        if not _finite(val) or val < 0:
            errors.append(f"{iw}.value: non-negative finite number required")
        else:
            numeric_values.append(float(val))
        total = item.get("total")
        if total is not None:
            if not _finite(total) or total < 0:
                errors.append(f"{iw}.total: non-negative finite number or null")
            elif _finite(val) and val > total:
                errors.append(f"{iw}: value cannot exceed total")
        if item.get("tone") is not None and item["tone"] not in TONES:
            errors.append(f"{iw}.tone: invalid tone")
        if "focus" in item and not isinstance(item["focus"], bool):
            errors.append(f"{iw}.focus: boolean expected")
        if not _opt_text(item.get("chat_prompt"), 1_000):
            errors.append(f"{iw}.chat_prompt: at most 1000 characters")
    if len(labels) != len(set(labels)):
        errors.append(f"{where}.values: category labels must be unique")
    count = len(values)
    if pres == "donut" and not 3 <= count <= 4:
        errors.append(f"{where}: donut requires 3 to 4 parts; use rate (share_bar) for 2 or ranked_bars for 5+")
    if pres == "split_bar":
        if count > 4:
            errors.append(f"{where}: split_bar allows at most 4 segments; fold smaller segments into 'Other' or use ranked_bars")
        total_sum = sum(numeric_values)
        if total_sum > 0 and any(0 < (v / total_sum) < SPLIT_BAR_MIN_SHARE for v in numeric_values):
            errors.append(f"{where}: every non-zero split_bar segment must be at least 2% of total; fold smaller ones into 'Other'")
    if pres in (None, "ranked_bars", "path_bars") and count > 8:
        errors.append(f"{where}: ranked_bars and path_bars allow at most 8 rows; fold the rest into 'Other', always last")
    return errors


def _check_comparison(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "presentation", "before_label", "after_label", "unit", "rows"}, where)
    pres = data.get("presentation")
    if pres not in {None, "side_by_side", "slopegraph", "dumbbell", "dot_plot", "split_pair", "import_status"}:
        errors.append(f"{where}.presentation: invalid comparison presentation")
    if not _text(data.get("before_label"), 60):
        errors.append(f"{where}.before_label: required, at most 60 characters")
    if not _text(data.get("after_label"), 60):
        errors.append(f"{where}.after_label: required, at most 60 characters")
    if not _opt_text(data.get("unit"), 32):
        errors.append(f"{where}.unit: at most 32 characters")
    rows = data.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 12:
        return errors + [f"{where}.rows: 1 to 12 comparison rows required"]
    if pres in ("dot_plot", "slopegraph") and len(rows) > 8:
        errors.append(f"{where}: {pres} allows at most 8 items; keep the top 8 by change")
    if pres == "side_by_side" and len(rows) > 3:
        errors.append(f"{where}: side_by_side allows at most 3 items; switch to dot_plot or slopegraph")
    for i, row in enumerate(rows):
        rw = f"{where}.rows[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{rw}: expected an object")
            continue
        errors += _unknown_keys(
            row,
            {"label", "before", "after", "before_detail", "after_detail", "status", "tone", "focus", "chat_prompt"},
            rw,
        )
        if not _text(row.get("label"), 120):
            errors.append(f"{rw}.label: required, at most 120 characters")
        if not _finite(row.get("before")):
            errors.append(f"{rw}.before: finite number required")
        if not _finite(row.get("after")):
            errors.append(f"{rw}.after: finite number required")
        if not _opt_text(row.get("before_detail"), 80):
            errors.append(f"{rw}.before_detail: at most 80 characters")
        if not _opt_text(row.get("after_detail"), 80):
            errors.append(f"{rw}.after_detail: at most 80 characters")
        if row.get("status") is not None and row["status"] not in CHANGE_STATUSES:
            errors.append(f"{rw}.status: invalid change status")
        if row.get("tone") is not None and row["tone"] not in TONES:
            errors.append(f"{rw}.tone: invalid tone")
        if "focus" in row and not isinstance(row["focus"], bool):
            errors.append(f"{rw}.focus: boolean expected")
        if not _opt_text(row.get("chat_prompt"), 1_000):
            errors.append(f"{rw}.chat_prompt: at most 1000 characters")
    return errors


def _check_table(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "columns", "rows"}, where)
    cols = data.get("columns")
    if not isinstance(cols, list) or not 1 <= len(cols) <= 10:
        errors.append(f"{where}.columns: 1 to 10 columns required")
    else:
        keys = []
        for i, col in enumerate(cols):
            cw = f"{where}.columns[{i}]"
            if not isinstance(col, dict):
                errors.append(f"{cw}: expected an object")
                continue
            errors += _unknown_keys(col, {"key", "label", "format"}, cw)
            if not _text(col.get("key"), 64):
                errors.append(f"{cw}.key: required, at most 64 characters")
            else:
                keys.append(col["key"])
            if not _text(col.get("label"), 80):
                errors.append(f"{cw}.label: required, at most 80 characters")
            if col.get("format", "text") not in TABLE_FORMATS:
                errors.append(f"{cw}.format: invalid column format")
        if len(keys) != len(set(keys)):
            errors.append(f"{where}.columns: column keys must be unique")
    rows = data.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 50 or not all(isinstance(r, dict) for r in rows):
        errors.append(f"{where}.rows: 1 to 50 row objects required")
    return errors


def _check_binned(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "presentation", "unit", "median", "p95", "bins"}, where)
    if data.get("presentation") not in {None, "columns", "horizontal", "micro"}:
        errors.append(f"{where}.presentation: expected 'columns', 'horizontal', 'micro', or null")
    if data.get("unit") is not None and not isinstance(data["unit"], str):
        errors.append(f"{where}.unit: string or null")
    for stat in ("median", "p95"):
        if data.get(stat) is not None and not _finite(data[stat]):
            errors.append(f"{where}.{stat}: finite number or null")
    bins = data.get("bins")
    if not isinstance(bins, list) or not 2 <= len(bins) <= 12 or not all(isinstance(b, dict) for b in bins):
        return errors + [f"{where}.bins: 2 to 12 ascending contiguous bins required"]
    last = len(bins) - 1
    prev_upper: float | None = None
    for i, item in enumerate(bins):
        bw = f"{where}.bins[{i}]"
        errors += _unknown_keys(item, {"lower_bound", "upper_bound", "count", "focus"}, bw)
        lower, upper = item.get("lower_bound"), item.get("upper_bound")
        if any(b is not None and not _finite(b) for b in (lower, upper)):
            errors.append(f"{bw}: bounds must be finite numbers or null")
            continue
        if lower is None and i != 0:
            errors.append(f"{bw}: only the first bin may have a null lower_bound")
        if upper is None and i != last:
            errors.append(f"{bw}: only the last bin may have a null upper_bound")
        if lower is not None and upper is not None and lower >= upper:
            errors.append(f"{bw}: lower_bound must be less than upper_bound")
        if i != 0 and lower != prev_upper:
            errors.append(f"{bw}: lower_bound must equal previous bin's upper_bound")
        prev_upper = upper
        if not _is_int(item.get("count")) or item["count"] < 0:
            errors.append(f"{bw}.count: non-negative integer required")
        if "focus" in item and not isinstance(item["focus"], bool):
            errors.append(f"{bw}.focus: boolean expected")
    return errors


def _check_session_dots(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "unit", "scale_min", "scale_max", "points"}, where)
    if not _opt_text(data.get("unit"), 32):
        errors.append(f"{where}.unit: at most 32 characters")
    smin, smax = data.get("scale_min"), data.get("scale_max")
    if smin is not None and not _finite(smin):
        errors.append(f"{where}.scale_min: finite number or null")
    if smax is not None and not _finite(smax):
        errors.append(f"{where}.scale_max: finite number or null")
    if _finite(smin) and _finite(smax) and smin >= smax:
        errors.append(f"{where}: scale_min must be less than scale_max")
    points = data.get("points")
    if not isinstance(points, list) or not 1 <= len(points) <= 100:
        return errors + [f"{where}.points: 1 to 100 session points required (past 100 use binned)"]
    for i, pt in enumerate(points):
        pw = f"{where}.points[{i}]"
        if not isinstance(pt, dict):
            errors.append(f"{pw}: expected an object")
            continue
        errors += _unknown_keys(pt, {"session_id", "session_label", "value", "highlight"}, pw)
        if not _is_uuid(pt.get("session_id")):
            errors.append(f"{pw}.session_id: UUID required")
        if not _opt_text(pt.get("session_label"), 80):
            errors.append(f"{pw}.session_label: at most 80 characters")
        if not _finite(pt.get("value")):
            errors.append(f"{pw}.value: finite number required")
        if "highlight" in pt and not isinstance(pt["highlight"], bool):
            errors.append(f"{pw}.highlight: boolean expected")
    return errors


def _check_time_series(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "presentation", "x_labels", "unit", "series", "annotations"}, where)
    pres = data.get("presentation")
    if pres not in {None, "line", "highlight_line", "ordered_columns", "stacked_columns", "sparkline", "small_multiples"}:
        errors.append(f"{where}.presentation: invalid time_series presentation")
    if not _opt_text(data.get("unit"), 32):
        errors.append(f"{where}.unit: at most 32 characters")
    x_labels = data.get("x_labels")
    if not isinstance(x_labels, list) or len(x_labels) < 3 or not all(isinstance(x, str) for x in x_labels):
        return errors + [f"{where}.x_labels: at least 3 points required (use comparison for 2 points)"]
    series = data.get("series")
    if not isinstance(series, list) or not 1 <= len(series) <= 12:
        return errors + [f"{where}.series: 1 to 12 series required"]
    focus_count = 0
    for i, line in enumerate(series):
        sw = f"{where}.series[{i}]"
        if not isinstance(line, dict):
            errors.append(f"{sw}: expected an object")
            continue
        errors += _unknown_keys(line, {"label", "values", "tone", "focus"}, sw)
        if not _text(line.get("label"), 80):
            errors.append(f"{sw}.label: required, at most 80 characters")
        vals = line.get("values")
        if not isinstance(vals, list) or len(vals) != len(x_labels) or not all(v is None or _finite(v) for v in vals):
            errors.append(f"{sw}.values: must match x_labels length ({len(x_labels)}) with finite numbers or null")
        if line.get("tone") is not None and line["tone"] not in TONES:
            errors.append(f"{sw}.tone: invalid tone")
        if "focus" in line and not isinstance(line["focus"], bool):
            errors.append(f"{sw}.focus: boolean expected")
        if line.get("focus") is True:
            focus_count += 1
    annotations = data.get("annotations", [])
    if not isinstance(annotations, list) or len(annotations) > 6:
        errors.append(f"{where}.annotations: at most 6 annotations")
    else:
        for i, ann in enumerate(annotations):
            aw = f"{where}.annotations[{i}]"
            if not isinstance(ann, dict):
                errors.append(f"{aw}: expected an object")
                continue
            errors += _unknown_keys(ann, {"x_index", "label"}, aw)
            if not _is_int(ann.get("x_index")) or not 0 <= ann["x_index"] < len(x_labels):
                errors.append(f"{aw}.x_index: integer within x_labels range required")
            if not _text(ann.get("label"), 60):
                errors.append(f"{aw}.label: required, at most 60 characters")
    if pres in ("ordered_columns", "stacked_columns") and len(x_labels) > 12:
        errors.append(f"{where}: column charts allow at most 12 buckets; switch presentation to 'line'")
    if pres == "stacked_columns" and len(series) > 3:
        errors.append(f"{where}: stacked_columns allows at most 3 segments; switch to 'small_multiples'")
    if pres in (None, "line") and len(series) > 5:
        errors.append(f"{where}: line allows at most 5 series; switch to 'highlight_line' with one focused series")
    if pres == "highlight_line" and focus_count != 1:
        errors.append(f"{where}: highlight_line requires exactly one series with focus=true")
    if pres == "small_multiples" and len(series) > 6:
        errors.append(f"{where}: small_multiples allows at most 6 panels; keep the top 6")
    return errors


def _check_step_strip(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "presentation", "total_steps", "rows"}, where)
    pres = data.get("presentation", "rows")
    if pres not in {"rows", "small_multiples"}:
        errors.append(f"{where}.presentation: expected 'rows' or 'small_multiples'")
    total = data.get("total_steps")
    if not _is_int(total) or not 2 <= total <= 30:
        errors.append(f"{where}.total_steps: integer from 2 to 30 required")
    rows = data.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 12:
        return errors + [f"{where}.rows: 1 to 12 rows required"]
    if pres == "small_multiples" and len(rows) > 6:
        errors.append(f"{where}: small_multiples allows at most 6 panels; keep the top 6")
    for i, row in enumerate(rows):
        rw = f"{where}.rows[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{rw}: expected an object")
            continue
        errors += _unknown_keys(
            row,
            {"label", "session_count", "last_good_step", "first_wrong_step", "severity", "session_ids", "chat_prompt"},
            rw,
        )
        if not _text(row.get("label"), 120):
            errors.append(f"{rw}.label: required, at most 120 characters")
        if row.get("session_count") is not None and (not _is_int(row["session_count"]) or row["session_count"] < 0):
            errors.append(f"{rw}.session_count: non-negative integer or null")
        for field in ("last_good_step", "first_wrong_step"):
            step = row.get(field)
            if step is not None:
                if not _is_int(step) or step < 1:
                    errors.append(f"{rw}.{field}: positive integer or null")
                elif _is_int(total) and step > total:
                    errors.append(f"{rw}.{field}: cannot exceed total_steps ({total})")
        if row.get("severity") is not None and row["severity"] not in SEVERITIES:
            errors.append(f"{rw}.severity: invalid severity")
        sids = row.get("session_ids", [])
        if not isinstance(sids, list) or len(sids) > 50 or not all(_is_uuid(s) for s in sids):
            errors.append(f"{rw}.session_ids: at most 50 session UUIDs")
        if not _opt_text(row.get("chat_prompt"), 1_000):
            errors.append(f"{rw}.chat_prompt: at most 1000 characters")
    return errors


def _check_failure_matrix(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "state_by", "rows", "cols", "total_failed", "cells"}, where)
    if data.get("state_by", "tool") not in MATRIX_STATES:
        errors.append(f"{where}.state_by: expected tool, span, node, or step")
    rows, cols = data.get("rows"), data.get("cols")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 6 or not all(_text(r) for r in rows):
        errors.append(f"{where}.rows: 1 to 6 state labels required (fold rare steps into 'Other')")
    if not isinstance(cols, list) or not 1 <= len(cols) <= 6 or not all(_text(c) for c in cols):
        errors.append(f"{where}.cols: 1 to 6 state labels required (fold rare steps into 'Other')")
    if not _is_int(data.get("total_failed")) or data["total_failed"] < 0:
        errors.append(f"{where}.total_failed: non-negative integer required")
    cells = data.get("cells")
    if not isinstance(cells, list):
        return errors + [f"{where}.cells: list required"]
    row_set = set(rows) if isinstance(rows, list) else set()
    col_set = set(cols) if isinstance(cols, list) else set()
    for i, cell in enumerate(cells):
        cw = f"{where}.cells[{i}]"
        if not isinstance(cell, dict):
            errors.append(f"{cw}: expected an object")
            continue
        errors += _unknown_keys(cell, {"from_state", "to_state", "count", "attempts", "sessions"}, cw)
        if cell.get("from_state") not in row_set or cell.get("to_state") not in col_set:
            errors.append(f"{cw}: from_state and to_state must appear in rows and cols")
        if not _is_int(cell.get("count")) or cell["count"] < 0:
            errors.append(f"{cw}.count: non-negative integer required")
        if cell.get("attempts") is not None and (not _is_int(cell["attempts"]) or cell["attempts"] < 0):
            errors.append(f"{cw}.attempts: non-negative integer or null")
        sessions = cell.get("sessions", [])
        if not isinstance(sessions, list) or len(sessions) > 20:
            errors.append(f"{cw}.sessions: at most 20 session refs")
        else:
            for j, ref in enumerate(sessions):
                rw = f"{cw}.sessions[{j}]"
                if not isinstance(ref, dict):
                    errors.append(f"{rw}: expected an object")
                    continue
                errors += _unknown_keys(ref, {"session_id", "session_label", "node_id", "step_label"}, rw)
                if not _is_uuid(ref.get("session_id")):
                    errors.append(f"{rw}.session_id: UUID required")
                if ref.get("node_id") is not None and not _is_uuid(ref["node_id"]):
                    errors.append(f"{rw}.node_id: UUID or null")
                if not _opt_text(ref.get("session_label"), 80):
                    errors.append(f"{rw}.session_label: at most 80 characters")
                if not _opt_text(ref.get("step_label"), 40):
                    errors.append(f"{rw}.step_label: at most 40 characters")
    return errors


def _check_flow_sankey(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "stages", "links"}, where)
    stages = data.get("stages")
    if not isinstance(stages, list) or not 2 <= len(stages) <= 3:
        return errors + [f"{where}.stages: 2 to 3 stages required (past 3 switch to categorical path_bars)"]
    node_ids = []
    for i, stage in enumerate(stages):
        sw = f"{where}.stages[{i}]"
        if not isinstance(stage, dict):
            errors.append(f"{sw}: expected an object")
            continue
        errors += _unknown_keys(stage, {"label", "nodes"}, sw)
        if not _opt_text(stage.get("label"), 60):
            errors.append(f"{sw}.label: at most 60 characters")
        nodes = stage.get("nodes")
        if not isinstance(nodes, list) or not 1 <= len(nodes) <= 8:
            errors.append(f"{sw}.nodes: 1 to 8 nodes required")
            continue
        for j, node in enumerate(nodes):
            nw = f"{sw}.nodes[{j}]"
            if not isinstance(node, dict):
                errors.append(f"{nw}: expected an object")
                continue
            errors += _unknown_keys(node, {"id", "label", "count", "tone"}, nw)
            if not _text(node.get("id"), 64):
                errors.append(f"{nw}.id: required, at most 64 characters")
            else:
                node_ids.append(node["id"])
            if not _text(node.get("label"), 80):
                errors.append(f"{nw}.label: required, at most 80 characters")
            if not _is_int(node.get("count")) or node["count"] < 0:
                errors.append(f"{nw}.count: non-negative integer required")
            if node.get("tone", "neutral") not in TONES:
                errors.append(f"{nw}.tone: invalid tone")
    if len(node_ids) > 8:
        errors.append(f"{where}: Sankey allows at most 8 nodes across at most 3 stages; use categorical path_bars")
    if len(node_ids) != len(set(node_ids)):
        errors.append(f"{where}: Sankey node IDs must be unique")
    links = data.get("links")
    known = set(node_ids)
    if not isinstance(links, list) or not links:
        errors.append(f"{where}.links: at least 1 link required")
    else:
        for i, link in enumerate(links):
            lw = f"{where}.links[{i}]"
            if not isinstance(link, dict):
                errors.append(f"{lw}: expected an object")
                continue
            errors += _unknown_keys(link, {"source", "target", "count", "tone"}, lw)
            if link.get("source") not in known or link.get("target") not in known:
                errors.append(f"{lw}: source and target must reference known node IDs")
            if not _is_int(link.get("count")) or link["count"] < 0:
                errors.append(f"{lw}.count: non-negative integer required")
            if link.get("tone", "neutral") not in TONES:
                errors.append(f"{lw}.tone: invalid tone")
    return errors


def _check_step_story(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "session_id", "session_label", "steps"}, where)
    if data.get("session_id") is not None and not _is_uuid(data["session_id"]):
        errors.append(f"{where}.session_id: UUID or null")
    if not _opt_text(data.get("session_label"), 80):
        errors.append(f"{where}.session_label: at most 80 characters")
    steps = data.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 12:
        return errors + [f"{where}.steps: 1 to 12 steps required"]
    for i, step in enumerate(steps):
        sw = f"{where}.steps[{i}]"
        if not isinstance(step, dict):
            errors.append(f"{sw}: expected an object")
            continue
        errors += _unknown_keys(step, {"number", "text", "role", "tool_name", "node_id", "tone", "note"}, sw)
        if not _is_int(step.get("number")) or step["number"] < 1:
            errors.append(f"{sw}.number: positive integer required")
        if not _text(step.get("text"), 400):
            errors.append(f"{sw}.text: required, at most 400 characters")
        if step.get("role") is not None and step["role"] not in STEP_ROLES:
            errors.append(f"{sw}.role: invalid role")
        if not _opt_text(step.get("tool_name"), 120):
            errors.append(f"{sw}.tool_name: at most 120 characters")
        if step.get("node_id") is not None and not _is_uuid(step["node_id"]):
            errors.append(f"{sw}.node_id: UUID or null")
        if step.get("tone", "neutral") not in TONES:
            errors.append(f"{sw}.tone: invalid tone")
        if not _opt_text(step.get("note"), 240):
            errors.append(f"{sw}.note: at most 240 characters")
    return errors


def _check_tool_cycle(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "steps", "repeat_count", "session_count", "note"}, where)
    steps = data.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 6:
        errors.append(f"{where}.steps: 1 to 6 cycle steps required")
    else:
        for i, step in enumerate(steps):
            sw = f"{where}.steps[{i}]"
            if not isinstance(step, dict):
                errors.append(f"{sw}: expected an object")
                continue
            errors += _unknown_keys(step, {"name", "status"}, sw)
            if not _text(step.get("name"), 120):
                errors.append(f"{sw}.name: required, at most 120 characters")
            if step.get("status", "ok") not in {"ok", "error"}:
                errors.append(f"{sw}.status: expected 'ok' or 'error'")
    if not _is_int(data.get("repeat_count")) or data["repeat_count"] < 2:
        errors.append(f"{where}.repeat_count: integer >= 2 required")
    if not _is_int(data.get("session_count")) or data["session_count"] < 1:
        errors.append(f"{where}.session_count: integer >= 1 required")
    if not _opt_text(data.get("note"), 200):
        errors.append(f"{where}.note: at most 200 characters")
    return errors


def _check_session_side(side: Any, where: str) -> list[str]:
    if not isinstance(side, dict):
        return [f"{where}: expected an object"]
    errors = _unknown_keys(side, {"session_id", "session_label", "verdict", "steps"}, where)
    if not _is_uuid(side.get("session_id")):
        errors.append(f"{where}.session_id: UUID required")
    if not _opt_text(side.get("session_label"), 80):
        errors.append(f"{where}.session_label: at most 80 characters")
    if side.get("verdict") not in VERDICTS:
        errors.append(f"{where}.verdict: expected pass, fail, or unclear")
    steps = side.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 15:
        return errors + [f"{where}.steps: 1 to 15 aligned steps required"]
    for i, step in enumerate(steps):
        sw = f"{where}.steps[{i}]"
        if not isinstance(step, dict):
            errors.append(f"{sw}: expected an object")
            continue
        errors += _unknown_keys(step, {"label", "node_id", "status"}, sw)
        if not _opt_text(step.get("label"), 120):
            errors.append(f"{sw}.label: at most 120 characters or null")
        if step.get("node_id") is not None and not _is_uuid(step["node_id"]):
            errors.append(f"{sw}.node_id: UUID or null")
        if step.get("status", "present") not in ALIGNED_STATUSES:
            errors.append(f"{sw}.status: invalid aligned step status")
    return errors


def _check_session_comparison(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "left", "right"}, where)
    errors += _check_session_side(data.get("left"), f"{where}.left")
    errors += _check_session_side(data.get("right"), f"{where}.right")
    return errors


def _check_session_timeline(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "session_id", "session_label", "total_duration_ms", "spans"}, where)
    if not _is_uuid(data.get("session_id")):
        errors.append(f"{where}.session_id: UUID required")
    if not _opt_text(data.get("session_label"), 80):
        errors.append(f"{where}.session_label: at most 80 characters")
    if not _is_int(data.get("total_duration_ms")) or data["total_duration_ms"] < 1:
        errors.append(f"{where}.total_duration_ms: positive integer required")
    spans = data.get("spans")
    if not isinstance(spans, list) or not 1 <= len(spans) <= 40:
        return errors + [f"{where}.spans: 1 to 40 spans required"]
    for i, span in enumerate(spans):
        sw = f"{where}.spans[{i}]"
        if not isinstance(span, dict):
            errors.append(f"{sw}: expected an object")
            continue
        errors += _unknown_keys(span, {"name", "node_id", "start_ms", "duration_ms", "tone"}, sw)
        if not _text(span.get("name"), 120):
            errors.append(f"{sw}.name: required, at most 120 characters")
        if span.get("node_id") is not None and not _is_uuid(span["node_id"]):
            errors.append(f"{sw}.node_id: UUID or null")
        if not _is_int(span.get("start_ms")) or span["start_ms"] < 0:
            errors.append(f"{sw}.start_ms: non-negative integer required")
        if not _is_int(span.get("duration_ms")) or span["duration_ms"] < 0:
            errors.append(f"{sw}.duration_ms: non-negative integer required")
        if span.get("tone", "neutral") not in TONES:
            errors.append(f"{sw}.tone: invalid tone")
    return errors


def _check_evidence(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "presentation", "total_sessions", "rows"}, where)
    if data.get("presentation", "table") not in {"table", "compact"}:
        errors.append(f"{where}.presentation: expected 'table' or 'compact'")
    if not _is_int(data.get("total_sessions")) or data["total_sessions"] < 1:
        errors.append(f"{where}.total_sessions: positive integer required")
    rows = data.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 25:
        return errors + [f"{where}.rows: 1 to 25 evidence rows required"]
    for i, row in enumerate(rows):
        rw = f"{where}.rows[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{rw}: expected an object")
            continue
        errors += _unknown_keys(
            row,
            {"session_id", "session_label", "node_id", "step_label", "signal", "verdict", "is_counterexample", "counterexample_note"},
            rw,
        )
        if not _is_uuid(row.get("session_id")):
            errors.append(f"{rw}.session_id: UUID required")
        if not _opt_text(row.get("session_label"), 80):
            errors.append(f"{rw}.session_label: at most 80 characters")
        if row.get("node_id") is not None and not _is_uuid(row["node_id"]):
            errors.append(f"{rw}.node_id: UUID or null")
        if not _opt_text(row.get("step_label"), 40):
            errors.append(f"{rw}.step_label: at most 40 characters")
        if not _opt_text(row.get("signal"), 120):
            errors.append(f"{rw}.signal: at most 120 characters")
        if row.get("verdict") is not None and row["verdict"] not in VERDICTS:
            errors.append(f"{rw}.verdict: expected pass, fail, or unclear")
        if "is_counterexample" in row and not isinstance(row["is_counterexample"], bool):
            errors.append(f"{rw}.is_counterexample: boolean expected")
        if not _opt_text(row.get("counterexample_note"), 160):
            errors.append(f"{rw}.counterexample_note: at most 160 characters")
    return errors


def _check_text(data: dict[str, Any], where: str) -> list[str]:
    errors = _unknown_keys(data, {"type", "style", "label", "content", "file_path", "revision"}, where)
    if data.get("style", "body") not in TEXT_STYLES:
        errors.append(f"{where}.style: expected 'body', 'callout', or 'hypothesis'")
    if not _opt_text(data.get("label"), 60):
        errors.append(f"{where}.label: at most 60 characters")
    if not _text(data.get("content")):
        errors.append(f"{where}.content: non-empty Markdown string required")
    if not _opt_text(data.get("file_path"), 300):
        errors.append(f"{where}.file_path: at most 300 characters")
    if not _opt_text(data.get("revision"), 64):
        errors.append(f"{where}.revision: at most 64 characters")
    return errors


ARTIFACT_CHECKERS = {
    "stat_grid": _check_stat_grid,
    "rate": _check_rate,
    "categorical": _check_categorical,
    "comparison": _check_comparison,
    "table": _check_table,
    "binned": _check_binned,
    "session_dots": _check_session_dots,
    "time_series": _check_time_series,
    "step_strip": _check_step_strip,
    "failure_matrix": _check_failure_matrix,
    "flow_sankey": _check_flow_sankey,
    "step_story": _check_step_story,
    "tool_cycle": _check_tool_cycle,
    "session_comparison": _check_session_comparison,
    "session_timeline": _check_session_timeline,
    "evidence": _check_evidence,
    "text": _check_text,
}


def check_impact(impact: Any, where: str) -> list[str]:
    """Validate an impact estimate attached to one finding's provenance."""
    if not isinstance(impact, dict) or set(impact) - {"summary", "sessions", "amount", "unit"}:
        return [f"{where}: expected an object with summary, sessions, amount, and unit"]
    errors = []
    if not _text(impact.get("summary"), 160):
        errors.append(f"{where}.summary: required, at most 160 characters")
    sessions = impact.get("sessions")
    if sessions is not None and (not _is_int(sessions) or sessions < 0):
        errors.append(f"{where}.sessions: non-negative integer or null")
    amount, unit = impact.get("amount"), impact.get("unit")
    if (amount is None) != (unit is None):
        errors.append(f"{where}: amount and unit are set together or both null")
    elif amount is not None and (not _finite(amount) or amount < 0 or unit not in IMPACT_UNITS):
        errors.append(f"{where}: amount must be non-negative and unit one of {', '.join(sorted(IMPACT_UNITS))}")
    return errors


def check_provenance(skill: Any, primary_ids: list[str]) -> list[str]:
    """Check the report's skill provenance block."""
    where = f"metadata.{SKILL_KEY}"
    if not isinstance(skill, dict):
        return [f"{where}: expected an object"]
    errors = []
    if skill.get("schema_version") != 2:
        errors.append(f"{where}.schema_version: expected 2")
    if not _is_uuid(skill.get("run_id")):
        errors.append(f"{where}.run_id: expected a UUID")
    if skill.get("level") not in LEVELS:
        errors.append(f"{where}.level: expected standard or deep")
    for key in ("scope", "sample", "findings"):
        if not isinstance(skill.get(key), dict):
            errors.append(f"{where}.{key}: expected an object")
    scope = skill.get("scope") if isinstance(skill.get("scope"), dict) else {}
    if not _is_int(scope.get("population_count")) or not re.fullmatch(r"[0-9a-f]{64}", str(scope.get("population_sha256"))):
        errors.append(f"{where}.scope: needs integer population_count and 64-hex population_sha256")
    findings_prov = skill.get("findings") if isinstance(skill.get("findings"), dict) else {}
    for fid in primary_ids:
        if fid not in findings_prov:
            errors.append(f"{where}.findings.{fid}: missing provenance for primary finding")
    for fid, entry in findings_prov.items():
        fw = f"{where}.findings.{fid}"
        if not isinstance(entry, dict):
            errors.append(f"{fw}: expected an object")
            continue
        rate = entry.get("rate")
        if not isinstance(rate, dict):
            errors.append(f"{fw}.rate: expected an object")
        else:
            if rate.get("method") not in RATE_METHODS:
                errors.append(f"{fw}.rate.method: expected readers, subagents, jev, mixed, or null")
            basis = rate.get("basis")
            if basis not in RATE_BASES:
                errors.append(f"{fw}.rate.basis: expected one of {', '.join(sorted(RATE_BASES))}")
            elif basis != "measurement" and (rate.get("low") is not None or rate.get("high") is not None):
                errors.append(f"{fw}.rate: {basis} must not carry an interval")
        errors += check_impact(entry.get("impact"), f"{fw}.impact")
    return errors


def _check_finding(finding: Any, index: int) -> tuple[list[str], str | None, str, int]:
    """Validate one InsightFinding; returns (errors, finding_id, tier, artifact_count)."""
    where = f"findings[{index}]"
    if not isinstance(finding, dict):
        return [f"{where}: expected an object"], None, "primary", 0
    errors = _unknown_keys(finding, FINDING_FIELDS, where)
    fid = finding.get("id")
    if not _text(fid, 120):
        errors.append(f"{where}.id: required, at most 120 characters")
        fid = None
    if not _text(finding.get("title"), 255):
        errors.append(f"{where}.title: required, at most 255 characters")
    tier = finding.get("tier", "primary")
    if tier not in TIERS:
        errors.append(f"{where}.tier: expected 'primary' or 'secondary'")
        tier = "primary"
    errors += _check_plain_summary(finding.get("summary"), f"{where}.summary", required=(tier == "primary"))
    if finding.get("body") is not None and not isinstance(finding["body"], str):
        errors.append(f"{where}.body: string or null")
    if finding.get("kind", "finding") not in FINDING_KINDS:
        errors.append(f"{where}.kind: expected one of {', '.join(sorted(FINDING_KINDS))}")
    if finding.get("severity") is not None and finding["severity"] not in SEVERITIES:
        errors.append(f"{where}.severity: invalid severity")
    if finding.get("change_status") is not None and finding["change_status"] not in CHANGE_STATUSES:
        errors.append(f"{where}.change_status: invalid change_status")
    ids = finding.get("contributing_session_ids", [])
    if not isinstance(ids, list) or len(ids) > MAX_CONTRIBUTING_SESSIONS or not all(_is_uuid(i) for i in ids) or len(set(ids)) != len(ids):
        errors.append(f"{where}.contributing_session_ids: unique session UUIDs (at most {MAX_CONTRIBUTING_SESSIONS})")
        id_set: set[str] = set()
    else:
        if tier == "primary" and not ids:
            errors.append(f"{where}.contributing_session_ids: primary findings need at least 1 session UUID")
        id_set = {i.lower() for i in ids}
    if not _opt_text(finding.get("check_first"), 1_000):
        errors.append(f"{where}.check_first: at most 1000 characters")
    action = finding.get("action")
    if action is not None:
        errors += _check_action(action, f"{where}.action")
    elif tier == "primary":
        errors.append(f"{where}.action: primary findings need an investigate handoff action")
    errors += _check_questions(finding.get("suggested_questions"), f"{where}.suggested_questions")
    artifacts = finding.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) > MAX_ARTIFACTS_PER_FINDING:
        errors.append(f"{where}.artifacts: list of at most {MAX_ARTIFACTS_PER_FINDING} artifacts")
        artifact_count = 0
    else:
        artifact_count = len(artifacts)
        for a_idx, artifact in enumerate(artifacts):
            aw = f"{where}.artifacts[{a_idx}]"
            errors += check_artifact(artifact, aw)
            if isinstance(artifact, dict) and artifact.get("type") == "evidence" and isinstance(artifact.get("rows"), list) and id_set:
                stray = [
                    r.get("session_id")
                    for r in artifact["rows"]
                    if isinstance(r, dict)
                    and not r.get("is_counterexample", False)
                    and isinstance(r.get("session_id"), str)
                    and r["session_id"].lower() not in id_set
                ]
                if stray:
                    errors.append(f"{aw}: non-counterexample sessions not in contributing_session_ids: {', '.join(stray)}")
    return errors, fid, tier, artifact_count


def _collect_visible_text(report: dict[str, Any]) -> str:
    parts = [report.get("title"), report.get("summary")]
    for finding in report.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        parts += [finding.get("title"), finding.get("summary"), finding.get("body")]
        for artifact in finding.get("artifacts") or []:
            if isinstance(artifact, dict) and artifact.get("type") == "text":
                parts.append(artifact.get("content"))
    return " ".join(p for p in parts if isinstance(p, str))


def check_report(report: Any, max_primary_findings: int = MAX_PRIMARY_FINDINGS) -> list[str]:
    """Validate one structured InsightInput report."""
    if not isinstance(report, dict):
        return ["report: expected a JSON object"]
    errors = _unknown_keys(report, REPORT_FIELDS, "report")
    name = report.get("name")
    if not isinstance(name, str) or len(name) > 255 or not NAME.match(name):
        errors.append("report.name: 1-255 letters, digits, - or _, starting and ending alphanumeric")
    if not _text(report.get("title"), 255):
        errors.append("report.title: required, at most 255 characters")
    errors += _check_plain_summary(report.get("summary"), "report.summary", required=False)
    if not _opt_text(report.get("source_provider"), 80):
        errors.append("report.source_provider: at most 80 characters")
    errors += _check_coverage(report.get("coverage"), "report.coverage")
    if report.get("next_step") is not None:
        errors += _check_action(report["next_step"], "report.next_step")
    errors += _check_questions(report.get("suggested_questions"), "report.suggested_questions")

    findings = report.get("findings")
    finding_artifacts: dict[str, int] = {}
    primary_ids: list[str] = []
    if not isinstance(findings, list) or not 1 <= len(findings) <= SERVER_MAX_FINDINGS:
        errors.append(f"report.findings: 1 to {SERVER_MAX_FINDINGS} findings required")
    else:
        seen_ids: set[str] = set()
        for index, finding in enumerate(findings):
            f_errors, fid, tier, a_count = _check_finding(finding, index)
            errors += f_errors
            if fid is not None:
                if fid in seen_ids:
                    errors.append(f"report.findings[{index}].id: duplicate finding id {fid!r}")
                seen_ids.add(fid)
                finding_artifacts[fid] = a_count
                if tier == "primary":
                    primary_ids.append(fid)
        if len(primary_ids) > max_primary_findings:
            errors.append(f"report.findings: {len(primary_ids)} primary findings; keep at most {max_primary_findings}")

    highlight = report.get("highlight")
    if highlight is not None:
        if not isinstance(highlight, dict):
            errors.append("report.highlight: expected an object")
        else:
            errors += _unknown_keys(highlight, HIGHLIGHT_FIELDS, "report.highlight")
            hfid = highlight.get("finding_id")
            a_idx = highlight.get("artifact_index", 0)
            if not isinstance(hfid, str) or hfid not in finding_artifacts:
                errors.append(f"report.highlight.finding_id: {hfid!r} does not match any finding")
            elif not _is_int(a_idx) or a_idx < 0:
                errors.append("report.highlight.artifact_index: non-negative integer required")
            else:
                count = finding_artifacts[hfid]
                if (count > 0 and a_idx >= count) or (count == 0 and a_idx > 0):
                    errors.append(f"report.highlight.artifact_index: {a_idx} out of range for finding {hfid!r}")

    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("report.metadata: expected an object")
    else:
        if LEGACY_SHARED_KEY in metadata:
            errors.append(
                f"report.metadata.{LEGACY_SHARED_KEY}: legacy card key; use first-class finding fields "
                "(action, contributing_session_ids, check_first, and evidence artifacts) instead"
            )
        skill = metadata.get(SKILL_KEY)
        errors += check_provenance(skill, primary_ids)
        if isinstance(skill, dict):
            scope = skill.get("scope") if isinstance(skill.get("scope"), dict) else {}
            visible = _collect_visible_text(report)
            for label, value in (("run_id", skill.get("run_id")), ("population_sha256", scope.get("population_sha256"))):
                if isinstance(value, str) and value and value in visible:
                    errors.append(f"visible text: contains the {label}; keep run details in metadata")
    return errors


def check_payload(payload: Any, max_primary_findings: int = MAX_PRIMARY_FINDINGS) -> list[str]:
    """Validate either one InsightInput report object or a batch array of 1 to 100 reports."""
    if isinstance(payload, dict):
        return check_report(payload, max_primary_findings)
    if not isinstance(payload, list) or not 1 <= len(payload) <= SERVER_MAX_BATCH:
        return [f"payload: expected one report object or an array of 1 to {SERVER_MAX_BATCH} reports"]
    errors = []
    names, runs = [], set()
    for index, item in enumerate(payload):
        prefix = f"report {index}: "
        errors += [prefix + e for e in check_report(item, max_primary_findings)]
        if isinstance(item, dict):
            names.append(item.get("name"))
            skill = item.get("metadata", {}).get(SKILL_KEY) if isinstance(item.get("metadata"), dict) else None
            if isinstance(skill, dict):
                runs.add(skill.get("run_id"))
    if len(set(names)) != len(names):
        errors.append("payload: report names must be unique within a batch")
    if len(runs) > 1:
        errors.append("payload: every report in one batch must share one run_id")
    return errors


def build_command(report_path: Path, agent: str, idempotency_key: str) -> str:
    """Return a shell-quoted insight create command that writes the checked report file."""
    parts = [
        "env",
        "KITARU_ACTIVE_SKILL=kitaru-insights",
        "kitaru",
        "insight",
        "create",
        "--agent",
        agent,
        "--insight-file",
        str(report_path.resolve()),
        "--idempotency-key",
        idempotency_key,
        "--output",
        "json",
        "--machine",
        "--non-interactive",
        "--no-browser",
    ]
    return shlex.join(parts)


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JSON file holding one insight report or an array of reports")
    parser.add_argument("--max-primary-findings", type=int, default=MAX_PRIMARY_FINDINGS)
    parser.add_argument("--emit-command", metavar="AGENT", help="print the create command for AGENT")
    parser.add_argument("--idempotency-key", help="required with --emit-command")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    errors = check_payload(payload, args.max_primary_findings)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    if args.emit_command:
        if not args.idempotency_key:
            print("error: --emit-command needs --idempotency-key", file=sys.stderr)
            return 1
        print(build_command(args.report, args.emit_command, args.idempotency_key))
    else:
        reports = [payload] if isinstance(payload, dict) else payload
        findings_count = sum(len(r.get("findings", [])) for r in reports)
        print(json.dumps({"reports": len(reports), "findings": findings_count, "ok": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
