"""Count what saved session list pages show about a pinned scope, overall, per agent version, and per time window.

Reads `kitaru session list --output json` pages already saved locally. With
two or more `--window` options it also compares each window with the one
before it and flags the changes that clear a fixed bar. This offline helper
never contacts Kitaru.
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pick_sample import load_items, parse_time, parse_windows
from tally_notes import wilson

CONCENTRATION_MIN_SESSIONS = 20
TOP_SHARE = 0.1
# A window smaller than this is too small to compare; a median or mean must move by at least
# this factor before it is flagged. Both bars are deliberately simple so a card can state them.
WINDOW_MIN_SESSIONS = 20
SHIFT_FACTOR = 1.5


def _number(value: Any) -> float | None:
    try:
        number = None if value is None else float(value)
    except (TypeError, ValueError):
        return None
    return number if number is not None and math.isfinite(number) else None


def _duration(item: dict[str, Any]) -> float | None:
    start, end = item.get("started_at"), item.get("ended_at")
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def percentiles(values: list[float]) -> dict[str, float] | None:
    """Return nearest-rank p50, p90, and max, or None without values."""
    if not values:
        return None
    ordered = sorted(values)

    def rank(q: float) -> float:
        return ordered[max(0, math.ceil(q * len(ordered)) - 1)]

    return {"p50": rank(0.5), "p90": rank(0.9), "max": ordered[-1]}


def cost_concentration(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Share of recorded cost from the costliest tenth of sessions that have a cost."""
    costs = sorted(((c, i["id"]) for i in items if (c := _number(i.get("cost"))) is not None), reverse=True)
    total = sum(c for c, _ in costs)
    result: dict[str, Any] = {"sessions_with_cost": len(costs), "sessions_without_cost": len(items) - len(costs), "total": round(total, 6)}
    if len(costs) < CONCENTRATION_MIN_SESSIONS or total <= 0:
        result["top_share"] = None
        return result
    top = costs[: max(1, math.ceil(len(costs) * TOP_SHARE))]
    result.update({"top_sessions": len(top), "top_share": round(sum(c for c, _ in top) / total, 4), "top_session_ids": [s for _, s in top[:10]]})
    return result


def cache_reads(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Total cache reads, and their share of input under the convention the data shows."""
    # Kitaru reports a session total as null when any call lacks it, so a null input total is
    # unknown, not zero; comparing against it would misread the convention.
    rows = [t for i in items if isinstance(t := i.get("tokens"), dict) and t.get("cached_input_tokens") is not None and t.get("input_tokens") is not None]
    input_total = sum(int(t["input_tokens"]) for t in rows)
    cached_total = sum(int(t["cached_input_tokens"]) for t in rows)
    # Sources disagree on whether input_tokens includes cache reads; a session reading more
    # from cache than its input total proves that source counts the two separately.
    exclusive = any(int(t["cached_input_tokens"]) > int(t["input_tokens"]) for t in rows)
    result: dict[str, Any] = {"sessions_reporting": len(rows), "input_tokens": input_total, "cached_input_tokens": cached_total, "convention": "exclusive" if exclusive else "unknown"}
    if not rows:
        return result
    if exclusive:
        result["share"] = round(cached_total / (input_total + cached_total), 4) if input_total + cached_total else None
    else:
        result["share_if_inclusive"] = round(cached_total / input_total, 4) if input_total else None
        result["share_if_exclusive"] = round(cached_total / (input_total + cached_total), 4) if input_total + cached_total else None
    return result


def cache_writes(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Total prompt-cache writes over the sessions that report them."""
    # A null count is unknown, not zero: older Kitaru and many sources never report cache writes.
    values = [int(t["cache_write_input_tokens"]) for i in items if isinstance(t := i.get("tokens"), dict) and t.get("cache_write_input_tokens") is not None]
    return {"sessions_reporting": len(values), "sessions_unknown": len(items) - len(values), "cache_write_input_tokens": sum(values) if values else None}


def summarize_value(items: list[dict[str, Any]], key: str) -> dict[str, float] | None:
    """Percentiles of one integer session field."""
    return percentiles([float(i[key]) for i in items if isinstance(i.get(key), int)])


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Count one group of sessions."""
    def tally(key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            counts[str(item.get(key))] = counts.get(str(item.get(key)), 0) + 1
        return dict(sorted(counts.items()))

    return {
        "sessions": len(items),
        "status": tally("status"),
        "origin": tally("origin"),
        "duration_seconds": percentiles([d for i in items if (d := _duration(i)) is not None]),
        "tool_calls": summarize_value(items, "tool_call_count"),
        "llm_calls": summarize_value(items, "llm_call_count"),
        "cost": cost_concentration(items),
        "cache": cache_reads(items),
        "cache_writes": cache_writes(items),
    }


def _mean_cost(items: list[dict[str, Any]]) -> float | None:
    costs = [c for i in items if (c := _number(i.get("cost"))) is not None]
    return sum(costs) / len(costs) if costs else None


def compare_windows(name_before: str, before: list[dict[str, Any]], name_after: str, after: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare two windows' failure share, medians, and mean cost, flagging changes that clear the bar."""
    enough = len(before) >= WINDOW_MIN_SESSIONS and len(after) >= WINDOW_MIN_SESSIONS
    changes: list[dict[str, Any]] = []
    failed = [sum(i.get("status") == "failed" for i in group) for group in (before, after)]
    ranges = [wilson(failed[0], len(before)), wilson(failed[1], len(after))]
    # Flag a failure-share change only when the two 95% ranges do not overlap: a conservative test
    # that a card can explain in one sentence.
    apart = enough and None not in ranges and (ranges[0][1] < ranges[1][0] or ranges[1][1] < ranges[0][0])
    changes.append({
        "metric": "failed_share",
        "before": round(failed[0] / len(before), 4) if before else None,
        "after": round(failed[1] / len(after), 4) if after else None,
        "before_range": ranges[0],
        "after_range": ranges[1],
        "notable": bool(apart),
        "basis": "95% ranges do not overlap",
    })
    measures = {
        "tool_calls_p50": lambda group: (summarize_value(group, "tool_call_count") or {}).get("p50"),
        "llm_calls_p50": lambda group: (summarize_value(group, "llm_call_count") or {}).get("p50"),
        "duration_seconds_p50": lambda group: (percentiles([d for i in group if (d := _duration(i)) is not None]) or {}).get("p50"),
        "cost_mean": _mean_cost,
    }
    for metric, measure in measures.items():
        values = [measure(before), measure(after)]
        ratio = values[1] / values[0] if None not in values and values[0] else None
        notable = enough and ratio is not None and (ratio >= SHIFT_FACTOR or ratio <= 1 / SHIFT_FACTOR)
        changes.append({"metric": metric, "before": values[0], "after": values[1], "ratio": round(ratio, 3) if ratio is not None else None, "notable": bool(notable), "basis": f"moved by at least {SHIFT_FACTOR}x"})
    return [{"before_window": name_before, "after_window": name_after, "comparable": enough, **change} for change in changes]


def build(items: list[dict[str, Any]], windows: list[tuple[str, datetime, datetime]] | None = None) -> dict[str, Any]:
    """Count the whole scope, each agent version in it, and each named time window."""
    versions: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        versions.setdefault(str(item.get("agent_version_id")), []).append(item)
    document = {"schema_version": 1, "scope": summarize(items), "by_version": {v: summarize(group) for v, group in sorted(versions.items())}}
    if windows:
        groups = {name: [i for i in items if (started := parse_time(i.get("started_at"))) is not None and start <= started < end] for name, start, end in windows}
        document["by_window"] = {name: {"start": start.isoformat(), "end": end.isoformat(), **summarize(groups[name])} for name, start, end in windows}
        document["window_changes"] = [change for (a, _, _), (b, _, _) in zip(windows, windows[1:], strict=False) for change in compare_windows(a, groups[a], b, groups[b])]
    return document


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", type=Path, help="session list JSON pages")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--window", action="append", default=[], metavar="NAME=START/END", help="count sessions that started in this window; repeat in time order to compare each window with the one before")
    args = parser.parse_args(argv)
    try:
        document = build(load_items(args.pages), parse_windows(args.window))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    scope = document["scope"]
    print(json.dumps({"sessions": scope["sessions"], "versions": len(document["by_version"]), "cost_top_share": scope["cost"].get("top_share"), "cache_convention": scope["cache"]["convention"], "notable_window_changes": sum(c["notable"] for c in document.get("window_changes", []))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
