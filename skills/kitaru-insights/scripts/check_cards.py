"""Check drafted insight cards against Kitaru's limits and this skill's contract.

Optionally prints a safely quoted `kitaru insight create` command. This offline
helper never contacts Kitaru.
"""

import argparse
import json
import math
import re
import shlex
import sys
import uuid
from pathlib import Path
from typing import Any

NAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?$")
SHARED_KEY = "kitaru.insights/v1"
SKILL_KEY = "kitaru.insights.skill/v1"
CARD_FIELDS = {"name", "title", "description", "data", "metadata"}
SHARED_FIELDS = {"investigation_prompt", "cta_label", "contributing_session_ids", "evidence", "check_first"}
LEVELS = {"standard", "deep"}
RATE_BASES = {"census", "exact_proxy", "measurement", "random_slice", "targeted_only"}
MAX_CARDS = 8
SERVER_MAX_CARDS = 100


def _is_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
    except ValueError:
        return False
    return isinstance(value, str)


def _finite(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def _text(value: Any, limit: int | None = None) -> bool:
    return isinstance(value, str) and bool(value.strip()) and (limit is None or len(value) <= limit)


def check_data(data: Any) -> list[str]:
    """Check one card's typed data payload."""
    if not isinstance(data, dict):
        return ["data: expected an object"]
    kind = data.get("type")
    if kind == "text":
        return [] if _text(data.get("content")) and set(data) == {"type", "content"} else ["data: text needs exactly type and non-empty content"]
    if kind == "categorical":
        values = data.get("values")
        if not isinstance(values, list) or not values:
            return ["data: categorical needs a non-empty values array"]
        labels = [v.get("label") if isinstance(v, dict) else None for v in values]
        errors = [] if set(data) <= {"type", "unit", "values"} else ["data: categorical allows only type, unit, and values"]
        if any(isinstance(v, dict) and set(v) - {"label", "value"} for v in values):
            errors.append("data: categorical values allow only label and value")
        if not all(_text(label) for label in labels) or len(set(labels)) != len(labels):
            errors.append("data: categorical labels must be unique non-empty text")
        if not all(isinstance(v, dict) and _finite(v.get("value")) and v["value"] >= 0 for v in values):
            errors.append("data: categorical values must be non-negative numbers")
        return errors
    if kind == "binned":
        bins = data.get("bins")
        if not isinstance(bins, list) or not bins or not all(isinstance(b, dict) for b in bins):
            return ["data: binned needs a non-empty bins array"]
        errors = [] if set(data) <= {"type", "unit", "bins"} else ["data: binned allows only type, unit, and bins"]
        for index, item in enumerate(bins):
            lower, upper = item.get("lower_bound"), item.get("upper_bound")
            if set(item) - {"lower_bound", "upper_bound", "count"}:
                errors.append(f"data: bin {index} allows only lower_bound, upper_bound, and count")
            if any(bound is not None and not _finite(bound) for bound in (lower, upper)):
                errors.append(f"data: bin {index} bounds must be finite numbers or null")
                continue
            if lower is None and index != 0 or upper is None and index != len(bins) - 1:
                errors.append(f"data: bin {index} has an open bound in the middle")
            if lower is not None and upper is not None and lower >= upper:
                errors.append(f"data: bin {index} lower_bound must be below upper_bound")
            if index and bins[index - 1].get("upper_bound") != lower:
                errors.append(f"data: bin {index} does not start where bin {index - 1} ends")
            if not isinstance(item.get("count"), int) or isinstance(item.get("count"), bool) or item["count"] < 0:
                errors.append(f"data: bin {index} count must be a non-negative integer")
        return errors
    return [f"data: unknown type {kind!r}"]


def check_shared(shared: Any) -> list[str]:
    """Check the dashboard-facing context fields."""
    if not isinstance(shared, dict):
        return [f"metadata.{SHARED_KEY}: expected an object"]
    errors = [f"metadata.{SHARED_KEY}.{k}: not part of the skill contract" for k in sorted(set(shared) - SHARED_FIELDS)]
    if not _text(shared.get("investigation_prompt"), 16_000):
        errors.append(f"metadata.{SHARED_KEY}.investigation_prompt: required, at most 16000 characters")
    if not _text(shared.get("cta_label"), 40):
        errors.append(f"metadata.{SHARED_KEY}.cta_label: required, at most 40 characters")
    ids = shared.get("contributing_session_ids")
    if not isinstance(ids, list) or not 1 <= len(ids) <= 1000 or not all(_is_uuid(i) for i in ids) or len(set(ids)) != len(ids):
        errors.append(f"metadata.{SHARED_KEY}.contributing_session_ids: 1 to 1000 unique UUIDs")
    evidence = shared.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) > 20:
        errors.append(f"metadata.{SHARED_KEY}.evidence: at most 20 locators")
    else:
        for index, item in enumerate(evidence):
            ok = isinstance(item, dict) and set(item) <= {"session_id", "node_id", "signal"} and _is_uuid(item.get("session_id")) and (item.get("node_id") is None or _is_uuid(item.get("node_id"))) and _text(item.get("signal"), 80)
            if not ok:
                errors.append(f"metadata.{SHARED_KEY}.evidence[{index}]: needs session_id UUID, node_id UUID or null, signal up to 80 characters")
    if isinstance(ids, list) and isinstance(evidence, list):
        stray = [e.get("session_id") for e in evidence if isinstance(e, dict) and e.get("session_id") not in ids]
        if stray:
            errors.append(f"metadata.{SHARED_KEY}.evidence: sessions not in contributing_session_ids: {', '.join(map(str, stray))}")
    if "check_first" in shared and not _text(shared["check_first"], 1000):
        errors.append(f"metadata.{SHARED_KEY}.check_first: at most 1000 characters")
    return errors


def check_provenance(skill: Any) -> list[str]:
    """Check the skill provenance block."""
    if not isinstance(skill, dict):
        return [f"metadata.{SKILL_KEY}: expected an object"]
    errors = []
    if skill.get("schema_version") != 1:
        errors.append(f"metadata.{SKILL_KEY}.schema_version: expected 1")
    if not _is_uuid(skill.get("run_id")):
        errors.append(f"metadata.{SKILL_KEY}.run_id: expected a UUID")
    if skill.get("level") not in LEVELS:
        errors.append(f"metadata.{SKILL_KEY}.level: expected standard or deep")
    for key in ("scope", "sample", "pattern", "rate"):
        if not isinstance(skill.get(key), dict):
            errors.append(f"metadata.{SKILL_KEY}.{key}: expected an object")
    scope = skill.get("scope") if isinstance(skill.get("scope"), dict) else {}
    if not isinstance(scope.get("population_count"), int) or not re.fullmatch(r"[0-9a-f]{64}", str(scope.get("population_sha256"))):
        errors.append(f"metadata.{SKILL_KEY}.scope: needs population_count and population_sha256")
    rate = skill.get("rate") if isinstance(skill.get("rate"), dict) else {}
    if rate.get("basis") not in RATE_BASES:
        errors.append(f"metadata.{SKILL_KEY}.rate.basis: expected one of {', '.join(sorted(RATE_BASES))}")
    elif rate["basis"] != "measurement" and (rate.get("low") is not None or rate.get("high") is not None):
        errors.append(f"metadata.{SKILL_KEY}.rate: {rate['basis']} must not carry an interval")
    return errors


def check_cards(cards: Any, max_cards: int = MAX_CARDS) -> list[str]:
    """Return every contract violation across a batch of cards."""
    if not isinstance(cards, list) or not cards:
        return ["cards: expected a non-empty array"]
    errors = []
    if len(cards) > min(max_cards, SERVER_MAX_CARDS):
        errors.append(f"cards: {len(cards)} cards; this skill writes at most {min(max_cards, SERVER_MAX_CARDS)} per run")
    names, runs = [], set()
    for index, card in enumerate(cards):
        where = f"card {index}"
        if not isinstance(card, dict):
            errors.append(f"{where}: expected an object")
            continue
        errors += [f"{where}: unknown field {k}" for k in sorted(set(card) - CARD_FIELDS)]
        name = card.get("name")
        if not isinstance(name, str) or len(name) > 255 or not NAME.match(name):
            errors.append(f"{where}: name must be 1-255 letters, digits, - or _, starting and ending alphanumeric")
        names.append(name)
        if not _text(card.get("title"), 255):
            errors.append(f"{where}: title must be non-empty, at most 255 characters")
        if "description" in card and card["description"] is not None and not isinstance(card["description"], str):
            errors.append(f"{where}: description must be text")
        errors += [f"{where}: {e}" for e in check_data(card.get("data"))]
        metadata = card.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{where}: metadata must be an object")
            continue
        errors += [f"{where}: {e}" for e in check_shared(metadata.get(SHARED_KEY))]
        errors += [f"{where}: {e}" for e in check_provenance(metadata.get(SKILL_KEY))]
        if isinstance(metadata.get(SKILL_KEY), dict):
            runs.add(metadata[SKILL_KEY].get("run_id"))
    if len(set(names)) != len(names):
        errors.append("cards: names must be unique within a run")
    if len(runs) > 1:
        errors.append("cards: every card in one batch must share one run_id")
    return errors


def build_command(cards: list[dict[str, Any]], agent: str, idempotency_key: str) -> str:
    """Return a shell-quoted insight create command for the batch."""
    parts = ["env", "KITARU_ACTIVE_SKILL=kitaru-insights", "kitaru", "insight", "create", "--agent", agent]
    for card in cards:
        parts += ["--insight", json.dumps(card, ensure_ascii=False, separators=(",", ":"), allow_nan=False)]
    parts += ["--idempotency-key", idempotency_key, "--output", "json", "--machine", "--non-interactive", "--no-browser"]
    return shlex.join(parts)


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cards", type=Path, help="JSON array of drafted cards")
    parser.add_argument("--max-cards", type=int, default=MAX_CARDS)
    parser.add_argument("--emit-command", metavar="AGENT", help="print the create command for AGENT")
    parser.add_argument("--idempotency-key", help="required with --emit-command")
    args = parser.parse_args(argv)
    try:
        cards = json.loads(args.cards.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    errors = check_cards(cards, args.max_cards)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    if args.emit_command:
        if not args.idempotency_key:
            print("error: --emit-command needs --idempotency-key", file=sys.stderr)
            return 1
        print(build_command(cards, args.emit_command, args.idempotency_key))
    else:
        print(json.dumps({"cards": len(cards), "ok": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
