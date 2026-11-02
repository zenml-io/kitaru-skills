"""Turn saved TypeSafe Noul evaluation rows into judgment lines for tally_notes.py.

Reads `kitaru evaluation list --output json` pages already saved locally. This
offline helper never contacts Kitaru or TypeSafe.
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from pick_sample import load_items

UNAVAILABLE = "unavailable"


def verdict(row: dict[str, Any], decisive_at: float) -> str:
    """Map p(yes) to yes, no, or unclear, keeping oversize sessions apart."""
    if row.get("value") == UNAVAILABLE:
        return UNAVAILABLE
    score = row.get("score")
    if isinstance(score, bool) or not isinstance(score, int | float) or not math.isfinite(score):
        raise ValueError(f"evaluation {row.get('id')}: expected a numeric p(yes) score")
    if score >= decisive_at:
        return "yes"
    if score <= 1 - decisive_at:
        return "no"
    return "unclear"


def convert(rows: list[dict[str, Any]], prefix: str, decisive_at: float) -> list[dict[str, Any]]:
    """Build one judgment per session and pattern from rows whose name carries the prefix."""
    if not 0.5 < decisive_at <= 1:
        raise ValueError("--decisive-at must be above 0.5 and at most 1")
    judgments: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("name") or "")
        if not name.startswith(prefix):
            continue
        key = (str(row.get("session_id")), name.removeprefix(prefix))
        if key in judgments:
            raise ValueError(f"session {key[0]} has two {name} rows; keep each evaluation run's pages in its own folder")
        judgments[key] = {
            "session_id": key[0],
            "pattern_id": key[1],
            "verdict": verdict(row, decisive_at),
            "evaluation_id": row.get("id"),
            "score": row.get("score"),
            "reason": row.get("explanation"),
        }
    if not judgments:
        raise ValueError(f"no evaluation rows named {prefix}PATTERN_ID")
    return [judgments[key] for key in sorted(judgments)]


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", type=Path, help="evaluation list JSON pages")
    parser.add_argument("--prefix", default="insights.", help="question-name prefix before the pattern ID")
    parser.add_argument("--decisive-at", type=float, default=0.8)
    parser.add_argument("--out", type=Path, required=True, help="judgments .jsonl path")
    args = parser.parse_args(argv)
    try:
        judgments = convert(load_items(args.pages), args.prefix, args.decisive_at)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(j) + "\n" for j in judgments), encoding="utf-8")
    counts: dict[str, int] = {}
    for judgment in judgments:
        counts[judgment["verdict"]] = counts.get(judgment["verdict"], 0) + 1
    print(json.dumps({"judgments": len(judgments), **counts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
