"""Count what saved session list pages show about a pinned scope, overall and per agent version.

Reads `kitaru session list --output json` pages already saved locally. This
offline helper never contacts Kitaru.
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pick_sample import load_items

CONCENTRATION_MIN_SESSIONS = 20
TOP_SHARE = 0.1


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
    rows = [t for i in items if isinstance(t := i.get("tokens"), dict) and t.get("cached_input_tokens") is not None]
    input_total = sum(int(t.get("input_tokens") or 0) for t in rows)
    cached_total = sum(int(t["cached_input_tokens"]) for t in rows)
    # Sources disagree on whether input_tokens includes cache reads; a session reading more
    # from cache than its input total proves that source counts the two separately.
    exclusive = any(int(t["cached_input_tokens"]) > int(t.get("input_tokens") or 0) for t in rows)
    result: dict[str, Any] = {"sessions_reporting": len(rows), "input_tokens": input_total, "cached_input_tokens": cached_total, "convention": "exclusive" if exclusive else "unknown"}
    if not rows:
        return result
    if exclusive:
        result["share"] = round(cached_total / (input_total + cached_total), 4) if input_total + cached_total else None
    else:
        result["share_if_inclusive"] = round(cached_total / input_total, 4) if input_total else None
        result["share_if_exclusive"] = round(cached_total / (input_total + cached_total), 4) if input_total + cached_total else None
    return result


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
        "tool_calls": percentiles([float(i["tool_call_count"]) for i in items if isinstance(i.get("tool_call_count"), int)]),
        "llm_calls": percentiles([float(i["llm_call_count"]) for i in items if isinstance(i.get("llm_call_count"), int)]),
        "cost": cost_concentration(items),
        "cache": cache_reads(items),
    }


def build(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Count the whole scope and each agent version in it."""
    versions: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        versions.setdefault(str(item.get("agent_version_id")), []).append(item)
    return {"schema_version": 1, "scope": summarize(items), "by_version": {v: summarize(group) for v, group in sorted(versions.items())}}


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", type=Path, help="session list JSON pages")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        document = build(load_items(args.pages))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    scope = document["scope"]
    print(json.dumps({"sessions": scope["sessions"], "versions": len(document["by_version"]), "cost_top_share": scope["cost"].get("top_share"), "cache_convention": scope["cache"]["convention"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
