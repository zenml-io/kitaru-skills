"""Validate a local evaluator-comparison snapshot and report exact counts.

This offline helper never retrieves evidence or verifies server provenance.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

OUTCOMES = ("pass", "fail", "held", "unavailable", "error", "missing")
SPLITS = ("examples", "development", "test")
LABELS = ("pass", "fail", "uncertain", "unreviewed")


def _object(value: Any, keys: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{where}: expected exactly {', '.join(sorted(keys))}")
    return value


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: expected nonempty text")
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def validate(snapshot: Any) -> dict[str, Any]:
    """Reject incomplete accounting, ambiguous identity, and split leakage."""
    data = _object(
        snapshot,
        {"schema_version", "criterion", "evaluator", "selected_session_ids", "records"},
        "snapshot",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("schema_version: expected 1")
    criterion = _object(data["criterion"], {"id", "revision", "text"}, "criterion")
    for key, value in criterion.items():
        _text(value, f"criterion.{key}")
    evaluator = _object(
        data["evaluator"], {"version_id", "result_name", "params"}, "evaluator"
    )
    for key in ("version_id", "result_name"):
        _text(evaluator[key], f"evaluator.{key}")
    if not isinstance(evaluator["params"], dict):
        raise TypeError("evaluator.params: expected object")
    _canonical(evaluator["params"])
    selected = data["selected_session_ids"]
    if not isinstance(selected, list):
        raise TypeError("selected_session_ids: expected array")
    for value in selected:
        _text(value, "selected_session_ids item")
    if len(set(selected)) != len(selected):
        raise ValueError("selected_session_ids: duplicate session")
    if not isinstance(data["records"], list):
        raise TypeError("records: expected array")
    seen: set[str] = set()
    links: set[str] = set()
    result_ids: set[str] = set()
    task_ids: set[str] = set()
    groups: dict[str, str] = {}
    for index, record in enumerate(data["records"]):
        where = f"records[{index}]"
        row = _object(
            record,
            {
                "session_id",
                "group_id",
                "split",
                "investigation_id",
                "investigation_session_id",
                "human_label",
                "label_updated_at",
                "exclusion_reason",
                "evaluation",
            },
            where,
        )
        for key in (
            "session_id",
            "group_id",
            "investigation_id",
            "investigation_session_id",
            "label_updated_at",
        ):
            _text(row[key], f"{where}.{key}")
        if row["session_id"] in seen or row["investigation_session_id"] in links:
            raise ValueError(f"{where}: duplicate session or investigation link")
        seen.add(row["session_id"])
        links.add(row["investigation_session_id"])
        if row["split"] not in SPLITS or row["human_label"] not in LABELS:
            raise ValueError(f"{where}: invalid split or human label")
        prior = groups.setdefault(row["group_id"], row["split"])
        if prior != row["split"]:
            raise ValueError(f"{where}: group_id crosses splits")
        if row["exclusion_reason"] is not None:
            _text(row["exclusion_reason"], f"{where}.exclusion_reason")
        evaluation = row["evaluation"]
        if evaluation is None:
            if (
                row["human_label"] in ("pass", "fail")
                and row["exclusion_reason"] is None
            ):
                raise ValueError(
                    f"{where}: eligible binary label needs an evaluation outcome"
                )
            continue
        ev = _object(
            evaluation,
            {
                "job_id",
                "task_id",
                "evaluator_version_id",
                "result_name",
                "params",
                "outcome",
                "result_id",
            },
            f"{where}.evaluation",
        )
        for key in ("job_id", "task_id", "evaluator_version_id", "result_name"):
            _text(ev[key], f"{where}.evaluation.{key}")
        if ev["task_id"] in task_ids:
            raise ValueError(f"{where}: duplicate task identity")
        task_ids.add(ev["task_id"])
        if (
            ev["evaluator_version_id"] != evaluator["version_id"]
            or ev["result_name"] != evaluator["result_name"]
            or _canonical(ev["params"]) != _canonical(evaluator["params"])
        ):
            raise ValueError(f"{where}: evaluator identity or params mismatch")
        if ev["outcome"] not in OUTCOMES:
            raise ValueError(f"{where}: invalid evaluation outcome")
        if ev["outcome"] in ("error", "missing"):
            if ev["result_id"] is not None:
                raise ValueError(f"{where}: error/missing must not name a result")
        else:
            result_id = _text(ev["result_id"], f"{where}.result_id")
            if result_id in result_ids:
                raise ValueError(f"{where}: duplicate result identity")
            result_ids.add(result_id)
    if seen != set(selected):
        raise ValueError("records: must cover exactly selected_session_ids")
    return data


def _fraction(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def summarize(snapshot: Any) -> dict[str, Any]:
    """Count every selected case without treating abstention as a label."""
    data = validate(snapshot)
    splits: dict[str, Any] = {}
    for split in SPLITS:
        rows = [row for row in data["records"] if row["split"] == split]
        counts = {label: dict.fromkeys(OUTCOMES, 0) for label in ("pass", "fail")}
        separate: dict[str, list[str]] = {
            key: [] for key in ("excluded", "uncertain", "unreviewed")
        }
        for row in rows:
            label = row["human_label"]
            category = "excluded" if row["exclusion_reason"] is not None else label
            if category in separate:
                separate[category].append(row["session_id"])
            else:
                counts[label][row["evaluation"]["outcome"]] += 1
        metrics = {}
        for label, outcomes in counts.items():
            total = sum(outcomes.values())
            decided = outcomes["pass"] + outcomes["fail"]
            metrics[label] = {
                "coverage": _fraction(decided, total),
                "decided_agreement": _fraction(outcomes[label], decided),
                "all_labeled_correct_decisions": _fraction(outcomes[label], total),
            }
        splits[split] = {
            "selected": len(rows),
            "outcomes_by_human_label": counts,
            "separate": {key: sorted(ids) for key, ids in separate.items()},
            "metrics_by_human_label": metrics,
        }
    return {
        "schema_version": 1,
        "criterion": data["criterion"],
        "evaluator": data["evaluator"],
        "selected": len(data["records"]),
        "splits": splits,
    }


def compare_snapshots(current: Any, baseline: Any) -> list[str]:
    """Identify changed snapshot fields, ignoring record and selection order."""
    current, baseline = validate(current), validate(baseline)
    changes = [
        key
        for key in ("criterion", "evaluator")
        if _canonical(current[key]) != _canonical(baseline[key])
    ]
    if set(current["selected_session_ids"]) != set(baseline["selected_session_ids"]):
        changes.append("selected_session_ids")
    old = {row["session_id"]: row for row in baseline["records"]}
    new = {row["session_id"]: row for row in current["records"]}
    for session_id in sorted(old.keys() | new.keys()):
        if session_id not in old or session_id not in new:
            changes.append(f"records.{session_id}")
            continue
        for key in sorted(new[session_id]):
            if _canonical(new[session_id][key]) != _canonical(old[session_id][key]):
                changes.append(f"records.{session_id}.{key}")
    return changes


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _read(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError("nonfinite JSON number")

    return json.loads(
        path.read_text(), object_pairs_hook=_pairs, parse_constant=reject_constant
    )


def main() -> int:
    """Print a report, or reject malformed or changed evidence with exit 2."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    try:
        snapshot = _read(args.snapshot)
        if args.baseline:
            changes = compare_snapshots(snapshot, _read(args.baseline))
            if changes:
                print(json.dumps({"status": "changed", "changed_fields": changes}))
                return 2
        print(json.dumps(summarize(snapshot), indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, OSError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
