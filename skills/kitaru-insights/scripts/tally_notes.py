"""Count pattern members by how sessions were picked, with ranges only for random samples.

Reads sample.json, patterns.json, and optional reader notes and measurement
judgments already written to the run folder. This offline helper never
contacts Kitaru.
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from pick_sample import load_items

Z_95 = 1.959964
VERDICTS = ("yes", "no", "unclear", "unavailable")


def wilson(successes: int, trials: int) -> tuple[float, float] | None:
    """Return the 95% Wilson score interval, or None without trials."""
    if trials == 0:
        return None
    p = successes / trials
    denominator = 1 + Z_95**2 / trials
    centre = (p + Z_95**2 / (2 * trials)) / denominator
    half = Z_95 * math.sqrt(p * (1 - p) / trials + Z_95**2 / (4 * trials**2)) / denominator
    return round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)


def read_lines(directory: Path) -> list[dict[str, Any]]:
    """Read every JSON line from the .jsonl files in a directory."""
    rows = []
    paths = sorted(directory.glob("*.jsonl"))
    if not paths:
        raise ValueError(f"{directory}: no .jsonl files; subagents must write NAME.jsonl")
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path.name}:{number}: {error.msg}") from error
    return rows


def check_notes(picks: dict[str, dict[str, Any]], notes: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Report picked sessions with no note, several notes, or notes for unpicked sessions."""
    counts: dict[str, int] = {}
    for note in notes:
        counts[str(note.get("session_id"))] = counts.get(str(note.get("session_id")), 0) + 1
    return {
        "missing": sorted(set(picks) - set(counts)),
        "duplicated": sorted(s for s, n in counts.items() if n > 1),
        "unexpected": sorted(set(counts) - set(picks)),
    }


def measure(pattern_id: str, judgments: list[dict[str, Any]], measured_ids: set[str]) -> tuple[dict[str, Any], dict[str, str]]:
    """Count one pattern's judgments over the measurement sample and return each session's verdict."""
    counts = dict.fromkeys(VERDICTS, 0)
    verdicts: dict[str, str] = {}
    sources: set[str] = set()
    for row in judgments:
        if row.get("pattern_id") != pattern_id or row.get("session_id") not in measured_ids:
            continue
        if row.get("verdict") not in VERDICTS:
            raise ValueError(f"pattern {pattern_id}: bad verdict {row.get('verdict')!r}")
        if row["session_id"] in verdicts:
            raise ValueError(f"pattern {pattern_id}: {row['session_id']} judged twice")
        if row["verdict"] == "yes" and not (row.get("node_id") or row.get("evaluation_id")):
            raise ValueError(f"pattern {pattern_id}: yes for {row['session_id']} has no node_id or evaluation_id")
        sources.add("jev" if row.get("evaluation_id") else "subagents")
        verdicts[row["session_id"]] = row["verdict"]
        counts[row["verdict"]] += 1
    counts["missing"] = sorted(measured_ids - set(verdicts))
    counts["method"] = sources.pop() if len(sources) == 1 else ("mixed" if sources else None)
    return counts, verdicts


def agreement(members: set[str], verdicts: dict[str, str], read_ids: set[str]) -> dict[str, int] | None:
    """Compare judged verdicts with reader-based membership on sessions both covered."""
    overlap = [s for s in read_ids if verdicts.get(s) in {"yes", "no"}]
    if not overlap:
        return None
    table = {"both_yes": 0, "judged_only": 0, "readers_only": 0, "both_no": 0}
    for session_id in overlap:
        judged, member = verdicts[session_id] == "yes", session_id in members
        table["both_yes" if judged and member else "judged_only" if judged else "readers_only" if member else "both_no"] += 1
    return table


def tally_pattern(pattern: dict[str, Any], picks: dict[str, dict[str, Any]], population: int, judgments: list[dict[str, Any]] | None, measured_ids: set[str], census: bool, whole_scope: bool, versions: dict[str, str] | None) -> dict[str, Any]:
    """Count one pattern and choose the strongest supported rate basis."""
    members = set(pattern.get("members") or [])
    unread = sorted(members - set(picks))
    if unread:
        raise ValueError(f"pattern {pattern['id']}: members were not read: {', '.join(unread)}")
    random_ids = {s for s, p in picks.items() if p["random"]}
    targeted_ids = {s for s, p in picks.items() if any(r != "random" for r in p["reasons"])}
    result: dict[str, Any] = {
        "id": pattern["id"],
        "members": len(members),
        "targeted": {"hits": len(members & targeted_ids), "read": len(targeted_ids)},
        "random_slice": {"hits": len(members & random_ids), "read": len(random_ids)},
        "population_count": population,
    }
    if pattern.get("proxy_count") is not None and pattern.get("proxy_total"):
        result["rate"] = {"basis": "exact_proxy", "method": None, "numerator": pattern["proxy_count"], "denominator": pattern["proxy_total"], "low": None, "high": None}
        return result
    # A judged measurement outranks reader notes, which record only what readers noticed.
    if judgments is not None:
        counts, verdicts = measure(pattern["id"], judgments, measured_ids)
        decided = counts["yes"] + counts["no"]
        # Judging every session in scope leaves model error but no sampling error.
        bounds = None if whole_scope else wilson(counts["yes"], decided)
        result["measurement"] = {**counts, "whole_scope": whole_scope, "interval_95": bounds}
        result["agreement"] = agreement(members, verdicts, set(picks))
        if versions is not None:
            by_version: dict[str, dict[str, int]] = {}
            for session_id, verdict in verdicts.items():
                bucket = by_version.setdefault(versions.get(session_id, "None"), dict.fromkeys(VERDICTS, 0))
                bucket[verdict] += 1
            result["by_version"] = dict(sorted(by_version.items()))
        result["rate"] = {"basis": "measurement", "method": counts["method"], "numerator": counts["yes"], "denominator": decided, "low": bounds and bounds[0], "high": bounds and bounds[1], "unclear": counts["unclear"], "unavailable": counts["unavailable"]}
        return result
    # Reading every session in scope is a full count of what readers noticed, so a sampling interval would misstate it.
    if census:
        result["rate"] = {"basis": "census", "method": "readers", "numerator": len(members), "denominator": population, "low": None, "high": None}
        return result
    # Readers note what they happen to see rather than judging every session against the final
    # definition, so a random-slice count is a floor without a sampling interval.
    if random_ids:
        result["rate"] = {"basis": "random_slice", "method": "readers", "numerator": len(members & random_ids), "denominator": len(random_ids), "low": None, "high": None}
    else:
        result["rate"] = {"basis": "targeted_only", "method": "readers", "numerator": len(members & targeted_ids), "denominator": len(targeted_ids), "low": None, "high": None}
    return result


def tally(sample: dict[str, Any], patterns: dict[str, Any], notes: list[dict[str, Any]] | None, measure_sample: dict[str, Any] | None, judgments: list[dict[str, Any]] | None, versions: dict[str, str] | None = None) -> dict[str, Any]:
    """Build the tally document."""
    picks = {p["session_id"]: p for p in sample["picks"]}
    ids = [p.get("id") for p in patterns.get("patterns", [])]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise ValueError("patterns need unique, non-empty ids")
    if (measure_sample is None) != (judgments is None):
        raise ValueError("pass --measure-sample and --judgments together")
    measured_ids = {p["session_id"] for p in measure_sample["picks"]} if measure_sample else set()
    population_ids = set(sample.get("population_ids") or ())
    census = population_ids <= set(picks) and len(picks) == sample["population_count"]
    whole_scope = bool(measure_sample) and len(measured_ids) == sample["population_count"] and population_ids <= measured_ids
    if measure_sample and not whole_scope and not all(p["random"] for p in measure_sample["picks"]):
        raise ValueError("measurement sample must be purely random (use --targeted 0) or cover the whole scope")
    if measure_sample and measure_sample.get("population_sha256") != sample["population_sha256"]:
        raise ValueError("measurement sample was drawn from a different scope than the read sample")
    if judgments is not None and not judgments:
        raise ValueError("no judgments found; the measurement wave wrote nothing")
    document: dict[str, Any] = {
        "schema_version": 1,
        "population_count": sample["population_count"],
        "population_sha256": sample["population_sha256"],
        "census": census,
        "patterns": [tally_pattern(p, picks, sample["population_count"], judgments, measured_ids, census, whole_scope, versions) for p in patterns.get("patterns", [])],
    }
    if notes is not None:
        document["notes"] = check_notes(picks, notes)
    if measure_sample:
        document["measurement_seed"] = measure_sample["seed"]
        document["measured"] = len(measured_ids)
        document["measured_whole_scope"] = whole_scope
    return document


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True)
    parser.add_argument("--notes", type=Path, help="directory of reader .jsonl files")
    parser.add_argument("--measure-sample", type=Path)
    parser.add_argument("--judgments", type=Path, help="directory of judgment .jsonl files")
    parser.add_argument("--by-version", type=Path, help="directory of session list pages, to split measurements by agent version")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        def load(path: Path | None) -> Any:
            return None if path is None else json.loads(path.read_text(encoding="utf-8"))

        document = tally(
            load(args.sample),
            load(args.patterns),
            read_lines(args.notes) if args.notes else None,
            load(args.measure_sample),
            read_lines(args.judgments) if args.judgments else None,
            {i["id"]: str(i.get("agent_version_id")) for i in load_items(sorted(args.by_version.glob("*.json")))} if args.by_version else None,
        )
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    problems = document.get("notes", {})
    if any(problems.values()):
        print(f"warning: note coverage problems: {json.dumps(problems)}", file=sys.stderr)
    for pattern in document["patterns"]:
        print(json.dumps({"id": pattern["id"], "rate": pattern["rate"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
