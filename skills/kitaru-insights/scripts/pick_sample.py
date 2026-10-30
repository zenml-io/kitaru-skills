"""Pin a session scope and draw a targeted plus seeded random sample.

Reads `kitaru session list --output json` pages already saved locally. This
offline helper never contacts Kitaru.
"""

import argparse
import hashlib
import json
import random
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

EXTREME_BUCKETS = (
    "highest_cost",
    "most_tool_calls",
    "longest_duration",
    "lowest_cost",
    "shortest_duration",
)


def load_items(paths: list[Path]) -> list[dict[str, Any]]:
    """Read session rows from CLI envelopes, MCP pages, or bare arrays."""
    rows: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        # MCP results wrap the page in `data`; the CLI envelope carries `items` directly.
        if isinstance(data, dict) and isinstance(data.get("data"), dict | list):
            data = data["data"]
        items = data.get("items") if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError(f"{path}: expected an items array")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ValueError(f"{path}: every session needs a string id")
            rows[item["id"]] = item
    return list(rows.values())


def _duration(item: dict[str, Any]) -> float | None:
    start, end = item.get("started_at"), item.get("ended_at")
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    delta = datetime.fromisoformat(end) - datetime.fromisoformat(start)
    return delta.total_seconds()


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def rank_bucket(bucket: str, items: list[dict[str, Any]]) -> list[str]:
    """Order session IDs for one targeted bucket, best candidate first."""
    if bucket == "failed":
        return [i["id"] for i in items if i.get("status") == "failed"]
    key, reverse = {
        "highest_cost": (lambda i: _number(i.get("cost")), True),
        "lowest_cost": (lambda i: _number(i.get("cost")), False),
        "most_tool_calls": (lambda i: _number(i.get("tool_call_count")), True),
        "longest_duration": (_duration, True),
        "shortest_duration": (_duration, False),
    }[bucket]
    valued = [(key(i), i["id"]) for i in items if key(i) is not None]
    valued.sort(key=lambda pair: (-pair[0], pair[1]) if reverse else pair)
    return [session_id for _, session_id in valued]


def pick(items: list[dict[str, Any]], targeted: int, random_count: int, seed: int, exclude: set[str]) -> list[dict[str, Any]]:
    """Take failures up to half the targeted budget, fill the rest round-robin across extremes, then draw a random slice."""
    rng = random.Random(seed)
    if not exclude and len(items) <= targeted + random_count:
        return [{"session_id": i["id"], "reasons": ["all_in_scope"], "random": False} for i in sorted(items, key=lambda i: i["id"])]
    # Shuffle failures with the seed: session IDs sort by creation time, so ID order would always pick the oldest.
    failed = sorted(rank_bucket("failed", items))
    rng.shuffle(failed)
    reasons: dict[str, list[str]] = {session_id: ["failed"] for session_id in failed[: (targeted + 1) // 2]}
    queues = [(bucket, rank_bucket(bucket, items)) for bucket in EXTREME_BUCKETS]
    while len(reasons) < targeted and any(queue for _, queue in queues):
        for bucket, queue in queues:
            while queue and queue[0] in reasons:
                reasons[queue.pop(0)].append(bucket)
            if queue and len(reasons) < targeted:
                reasons[queue.pop(0)] = [bucket]
    eligible = sorted(i["id"] for i in items if i["id"] not in exclude)
    sampled = rng.sample(eligible, min(random_count, len(eligible)))
    for session_id in sampled:
        reasons.setdefault(session_id, []).append("random")
    return [
        {"session_id": sid, "reasons": rs, "random": "random" in rs}
        for sid, rs in sorted(reasons.items())
    ]


def build(items: list[dict[str, Any]], targeted: int, random_count: int, seed: int, include_in_progress: bool, exclude: set[str] | None = None) -> dict[str, Any]:
    """Pin the scope and return the sample document."""
    agents = {i.get("agent_id") for i in items}
    if len(agents) > 1:
        raise ValueError(f"scope spans {len(agents)} agents; cards attach to one agent")
    if not include_in_progress:
        items = [i for i in items if i.get("status") != "in_progress"]
    if not items:
        raise ValueError("scope has no finished sessions")
    population = sorted(i["id"] for i in items)
    return {
        "schema_version": 1,
        "agent_id": next(iter(agents)),
        "seed": seed,
        "population_count": len(population),
        "population_sha256": hashlib.sha256("\n".join(population).encode()).hexdigest(),
        "population_ids": population,
        "excluded": len(exclude or ()),
        "picks": pick(items, targeted, random_count, seed, exclude or set()),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", type=Path, help="session list JSON pages")
    parser.add_argument("--targeted", type=int, default=25)
    parser.add_argument("--random", type=int, default=15, dest="random_count")
    parser.add_argument("--seed", type=int, help="defaults to a fresh recorded seed")
    parser.add_argument("--include-in-progress", action="store_true")
    parser.add_argument("--out", type=Path, required=True, help="sample.json path")
    parser.add_argument("--ids-out", type=Path, help="write pinned IDs, one per line")
    parser.add_argument("--exclude", type=Path, help="earlier sample.json whose picks the random draw skips")
    args = parser.parse_args(argv)
    seed = args.seed if args.seed is not None else secrets.randbelow(2**31)
    try:
        exclude = {p["session_id"] for p in json.loads(args.exclude.read_text(encoding="utf-8"))["picks"]} if args.exclude else set()
        sample = build(load_items(args.pages), args.targeted, args.random_count, seed, args.include_in_progress, exclude)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    if args.ids_out:
        args.ids_out.write_text("\n".join(sample["population_ids"]) + "\n", encoding="utf-8")
    random_n = sum(p["random"] for p in sample["picks"])
    print(json.dumps({
        "population_count": sample["population_count"],
        "population_sha256": sample["population_sha256"],
        "seed": seed,
        "picked": len(sample["picks"]),
        "random": random_n,
        "targeted": sum(any(r not in {"random", "all_in_scope"} for r in p["reasons"]) for p in sample["picks"]),
        "all_in_scope": len(sample["picks"]) == sample["population_count"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
