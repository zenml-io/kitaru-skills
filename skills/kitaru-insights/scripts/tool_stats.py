"""Count how each tool was used across exported sessions: calls, failures, retries, loops, and cycles.

Reads the same export folder as `condense_sessions.py`: `NAME.read.json` files
from `kitaru session read --output json`, or `ID.session.json` plus
`ID.nodes.json` pages. Optionally splits the sessions into named time windows
by their start time. Identical-argument repeats compare the exported text, so
two long inputs that differ only after a `--max-chars` cut count as identical.
This offline helper never contacts Kitaru.
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from condense_sessions import load_export
from pick_sample import parse_time, parse_windows

# `kitaru session read` replaces a repeated payload with a pointer to where it first appeared.
SAME_AS = re.compile(r"^\(same as \[(\d+)\]\)$")
EXAMPLES = 5
TABLE_ROWS = 10


def _seconds(start: Any, end: Any) -> float | None:
    started, ended = parse_time(start), parse_time(end)
    return None if started is None or ended is None else (ended - started).total_seconds()


def _text(value: Any) -> str | None:
    if value is None or value in ("", [], {}):
        return None
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return " ".join(text.split())


def tool_calls(entry: dict[str, Any]) -> tuple[str, datetime | None, list[dict[str, Any]]]:
    """Return a session's ID, start time, and tool calls in recorded order."""
    if "transcript" in entry:
        transcript = entry["transcript"]
        inputs = {s.get("index"): s.get("input") for s in transcript["steps"] if isinstance(s.get("input"), str)}
        calls = []
        for step in transcript["steps"]:
            if step.get("node_type") != "tool_call":
                continue
            raw = step.get("input")
            pointer = SAME_AS.match(raw) if isinstance(raw, str) else None
            # Repeats of one payload all point at its first appearance, so the pointed-at step's
            # input stands in for the text. A pointer to that step's output instead is rare for
            # consecutive calls to one tool, and is the one case this can misjudge.
            key = (inputs.get(int(pointer[1])) or f"same-as-{pointer[1]}") if pointer else _text(raw)
            calls.append({"node_id": str(step.get("node_id")), "tool": str(step.get("name")), "failed": step.get("status") == "failed", "input": key, "seconds": step.get("duration_seconds")})
        return str(transcript["session_id"]), parse_time(transcript.get("started_at")), calls
    session = entry["session"]
    nodes = [n for _, page in sorted(entry["pages"], key=lambda p: p[0]) for n in page]
    calls = [
        {"node_id": str(n.get("id")), "tool": str(n.get("tool_name") or n.get("name")), "failed": n.get("status") == "failed", "input": _text(n.get("inputs")), "seconds": _seconds(n.get("started_at"), n.get("ended_at"))}
        for n in nodes
        if n.get("node_type") == "tool_call"
    ]
    return str(session["id"]), parse_time(session.get("started_at")), calls


def _percentiles(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)

    def rank(q: float) -> float:
        return round(ordered[max(0, math.ceil(q * len(ordered)) - 1)], 3)

    return {"p50": rank(0.5), "p90": rank(0.9), "max": round(ordered[-1], 3)}


def _cycles(tools: list[str], min_repeats: int) -> list[tuple[str, int, int]]:
    """Find runs where a sequence of two or three different tools repeats back to back."""
    found, index = [], 0
    while index < len(tools):
        best = None
        for period in (2, 3):
            unit = tools[index : index + period]
            if len(unit) < period or len(set(unit)) < 2:
                continue
            repeats = 1
            while tools[index + repeats * period : index + (repeats + 1) * period] == unit:
                repeats += 1
            if repeats >= min_repeats and (best is None or repeats * period > best[1] * best[2]):
                best = (" → ".join(unit), repeats, period)
        if best:
            found.append((best[0], best[1], index))
            index += best[1] * best[2]
        else:
            index += 1
    return found


def count(entries: list[tuple[str, list[dict[str, Any]]]], loop_run: int, cycle_repeats: int) -> dict[str, Any]:
    """Count tool use over one group of sessions."""
    tools: dict[str, dict[str, Any]] = {}
    cycles: dict[str, dict[str, Any]] = {}
    for session_id, calls in entries:
        run_start = 0
        for position, call in enumerate(calls):
            stats = tools.setdefault(call["tool"], {"calls": 0, "failed": 0, "sessions": set(), "failed_sessions": set(), "repeats": 0, "retries_after_failure": 0, "loop_sessions": set(), "longest_run": 0, "seconds": [], "examples": {"failed": [], "repeat": [], "loop": []}})
            stats["calls"] += 1
            stats["sessions"].add(session_id)
            if isinstance(call["seconds"], int | float) and math.isfinite(call["seconds"]):
                stats["seconds"].append(float(call["seconds"]))
            if call["failed"]:
                stats["failed"] += 1
                stats["failed_sessions"].add(session_id)
                _example(stats, "failed", session_id, call)
            previous = calls[position - 1] if position else None
            if previous and previous["tool"] == call["tool"]:
                if previous["failed"]:
                    stats["retries_after_failure"] += 1
                if call["input"] is not None and call["input"] == previous["input"]:
                    stats["repeats"] += 1
                    _example(stats, "repeat", session_id, call)
            else:
                run_start = position
            run = position - run_start + 1
            stats["longest_run"] = max(stats["longest_run"], run)
            if run == loop_run:
                stats["loop_sessions"].add(session_id)
                _example(stats, "loop", session_id, calls[run_start])
        for label, repeats, start in _cycles([c["tool"] for c in calls], cycle_repeats):
            cycle = cycles.setdefault(label, {"sessions": set(), "longest_repeats": 0, "examples": []})
            cycle["sessions"].add(session_id)
            cycle["longest_repeats"] = max(cycle["longest_repeats"], repeats)
            if len(cycle["examples"]) < EXAMPLES:
                cycle["examples"].append({"session_id": session_id, "node_id": calls[start]["node_id"]})
    sessions = len(entries)
    rows = []
    for name, stats in tools.items():
        rows.append({
            "tool": name,
            "calls": stats["calls"],
            "sessions": len(stats["sessions"]),
            "failed": stats["failed"],
            "failure_rate": round(stats["failed"] / stats["calls"], 4),
            "sessions_with_failure": len(stats["failed_sessions"]),
            "identical_repeats": stats["repeats"],
            "retries_after_failure": stats["retries_after_failure"],
            "loop_sessions": len(stats["loop_sessions"]),
            "longest_run": stats["longest_run"],
            "seconds": _percentiles(stats["seconds"]),
            "seconds_total": round(sum(stats["seconds"]), 3) if stats["seconds"] else None,
            "examples": stats["examples"],
        })
    rows.sort(key=lambda r: (-r["calls"], r["tool"]))
    cycle_rows = sorted(({"cycle": label, "sessions": len(c["sessions"]), "longest_repeats": c["longest_repeats"], "examples": c["examples"]} for label, c in cycles.items()), key=lambda r: (-r["sessions"], r["cycle"]))
    return {"sessions": sessions, "sessions_with_tool_calls": sum(bool(calls) for _, calls in entries), "tool_calls": sum(r["calls"] for r in rows), "tools": rows, "cycles": cycle_rows}


def _example(stats: dict[str, Any], kind: str, session_id: str, call: dict[str, Any]) -> None:
    examples = stats["examples"][kind]
    if len(examples) < EXAMPLES and all(e["session_id"] != session_id for e in examples):
        examples.append({"session_id": session_id, "node_id": call["node_id"]})


def table(rows: list[dict[str, Any]], limit: int = TABLE_ROWS) -> str:
    """Render the busiest tools as a GitHub-flavored Markdown table for a text card."""
    lines = ["| Tool | Calls | Sessions | Failed | Retries after failure | Identical repeats | Sessions with a loop |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in rows[:limit]:
        failed = f"{row['failed']} ({row['failure_rate']:.1%})"
        lines.append(f"| `{row['tool']}` | {row['calls']:,} | {row['sessions']:,} | {failed} | {row['retries_after_failure']:,} | {row['identical_repeats']:,} | {row['loop_sessions']:,} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--table-out", type=Path, help="write a Markdown table of the busiest tools")
    parser.add_argument("--window", action="append", default=[], metavar="NAME=START/END", help="also count sessions that started in this window; repeat for each window")
    parser.add_argument("--loop-run", type=int, default=3, help="consecutive calls to one tool that count as a loop")
    parser.add_argument("--cycle-repeats", type=int, default=3, help="back-to-back repeats of a 2- or 3-tool sequence that count as a cycle")
    args = parser.parse_args(argv)
    try:
        windows = parse_windows(args.window)
        if args.loop_run < 2 or args.cycle_repeats < 2:
            raise ValueError("--loop-run and --cycle-repeats must be at least 2")
        exported = load_export(args.export_dir)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if not exported:
        print(f"error: no *.read.json or *.session.json files in {args.export_dir}", file=sys.stderr)
        return 1
    if any("pages" in entry and not entry["pages"] for entry in exported.values()):
        missing = sorted(sid for sid, entry in exported.items() if "pages" in entry and not entry["pages"])
        print(f"error: sessions without node pages: {', '.join(missing)}", file=sys.stderr)
        return 1
    sessions = [tool_calls(entry) for _, entry in sorted(exported.items())]
    document: dict[str, Any] = {"schema_version": 1, "loop_run": args.loop_run, "cycle_repeats": args.cycle_repeats, "scope": count([(sid, calls) for sid, _, calls in sessions], args.loop_run, args.cycle_repeats)}
    if windows:
        document["by_window"] = {name: count([(sid, calls) for sid, started, calls in sessions if started is not None and start <= started < end], args.loop_run, args.cycle_repeats) for name, start, end in windows}
        document["sessions_without_start"] = sum(started is None for _, started, _ in sessions)
    args.out.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.table_out:
        args.table_out.write_text(table(document["scope"]["tools"]), encoding="utf-8")
    scope = document["scope"]
    print(json.dumps({"sessions": scope["sessions"], "tool_calls": scope["tool_calls"], "tools": len(scope["tools"]), "cycles": len(scope["cycles"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
