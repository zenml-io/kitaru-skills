"""Check drafted insight cards against Kitaru's limits and this skill's contract.

Besides the server's limits, it checks what the dashboard can show: a short
plain-text description, readable text and chart payloads, rank order, and,
with `--dashboard-url`, links to the sessions behind each text card.
Optionally prints a safely quoted `kitaru insight create --insight-file`
command for the checked file. This offline helper never contacts Kitaru.
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
CARD_KINDS = {"finding", "bright_spot", "opportunity", "coverage_gap"}
RATE_METHODS = {None, "readers", "subagents", "jev", "mixed"}
RATE_BASES = {"census", "exact_proxy", "measurement", "random_slice", "targeted_only"}
MAX_CARDS = 8
SERVER_MAX_CARDS = 100
# The dashboard prints the description as plain text under the title, so Markdown shows as
# literal symbols there. Only a text card's content is rendered as Markdown.
DESCRIPTION_MAX = 240
MARKDOWN_IN_PLAIN_TEXT = re.compile(r"`|\*\*|__|\]\(|^\s*(?:#|[-*+] |\d+\. )", re.MULTILINE)
CONTENT_MAX = 2500
# The donut chart cycles eight colors, and the bar chart is 112 pixels tall.
MAX_SLICES = 8
MAX_BINS = 12
IMPACT_UNITS = {"tokens", "usd", "seconds", "sessions", "calls"}
UUID_TEXT = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


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


def _reject_constant(name: str) -> None:
    # The file is sent to Kitaru as written, so NaN and Infinity must fail here, not on the server.
    raise ValueError(f"{name} is not valid JSON")


def check_data(data: Any) -> list[str]:
    """Check one card's typed data payload."""
    if not isinstance(data, dict):
        return ["data: expected an object"]
    kind = data.get("type")
    if kind == "text":
        if not _text(data.get("content")) or set(data) != {"type", "content"}:
            return ["data: text needs exactly type and non-empty content"]
        return [] if len(data["content"]) <= CONTENT_MAX else [f"data: text content is {len(data['content'])} characters; keep it to {CONTENT_MAX}"]
    if kind == "categorical":
        values = data.get("values")
        if not isinstance(values, list) or not values:
            return ["data: categorical needs a non-empty values array"]
        labels = [v.get("label") if isinstance(v, dict) else None for v in values]
        errors = [] if set(data) <= {"type", "unit", "values"} else ["data: categorical allows only type, unit, and values"]
        if len(values) > MAX_SLICES:
            errors.append(f"data: categorical has {len(values)} values; keep at most {MAX_SLICES} and fold the rest into one \"Other\" label")
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
        if len(bins) > MAX_BINS:
            errors.append(f"data: binned has {len(bins)} bins; keep at most {MAX_BINS}")
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
    pattern = skill.get("pattern") if isinstance(skill.get("pattern"), dict) else {}
    if pattern.get("kind") not in CARD_KINDS:
        errors.append(f"metadata.{SKILL_KEY}.pattern.kind: expected one of {', '.join(sorted(CARD_KINDS))}")
    rate = skill.get("rate") if isinstance(skill.get("rate"), dict) else {}
    if rate.get("method") not in RATE_METHODS:
        errors.append(f"metadata.{SKILL_KEY}.rate.method: expected readers, subagents, jev, mixed, or null")
    if rate.get("basis") not in RATE_BASES:
        errors.append(f"metadata.{SKILL_KEY}.rate.basis: expected one of {', '.join(sorted(RATE_BASES))}")
    elif rate["basis"] != "measurement" and (rate.get("low") is not None or rate.get("high") is not None):
        errors.append(f"metadata.{SKILL_KEY}.rate: {rate['basis']} must not carry an interval")
    rank = skill.get("rank")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        errors.append(f"metadata.{SKILL_KEY}.rank: expected a positive integer, 1 for the most important card")
    errors += check_impact(skill.get("impact"))
    return errors


def check_impact(impact: Any) -> list[str]:
    """Check the impact estimate that ranks a card."""
    where = f"metadata.{SKILL_KEY}.impact"
    if not isinstance(impact, dict) or set(impact) - {"summary", "sessions", "amount", "unit"}:
        return [f"{where}: expected an object with summary, sessions, amount, and unit"]
    errors = []
    if not _text(impact.get("summary"), 160):
        errors.append(f"{where}.summary: required, at most 160 characters")
    sessions = impact.get("sessions")
    if sessions is not None and (not isinstance(sessions, int) or isinstance(sessions, bool) or sessions < 0):
        errors.append(f"{where}.sessions: a non-negative integer or null")
    amount, unit = impact.get("amount"), impact.get("unit")
    if (amount is None) != (unit is None):
        errors.append(f"{where}: amount and unit are set together or both null")
    elif amount is not None and (not _finite(amount) or amount < 0 or unit not in IMPACT_UNITS):
        errors.append(f"{where}: amount must be a non-negative number and unit one of {', '.join(sorted(IMPACT_UNITS))}")
    return errors


def check_visible_text(card: dict[str, Any], dashboard_url: str | None) -> list[str]:
    """Check what the dashboard shows: a plain description, no run metadata, and session links."""
    errors = []
    description = card.get("description")
    if not _text(description, DESCRIPTION_MAX) or "\n" in description:
        errors.append(f"description: required, one line of at most {DESCRIPTION_MAX} characters")
    elif MARKDOWN_IN_PLAIN_TEXT.search(description):
        errors.append("description: plain text only; the dashboard shows Markdown symbols literally here, so put formatting in a text card's content")
    data = card.get("data") if isinstance(card.get("data"), dict) else {}
    content = data.get("content") if data.get("type") == "text" and isinstance(data.get("content"), str) else ""
    metadata = card.get("metadata") if isinstance(card.get("metadata"), dict) else {}
    skill = metadata.get(SKILL_KEY) if isinstance(metadata.get(SKILL_KEY), dict) else {}
    scope = skill.get("scope") if isinstance(skill.get("scope"), dict) else {}
    visible = " ".join(t for t in (card.get("title"), description, content) if isinstance(t, str))
    for label, value in (("run_id", skill.get("run_id")), ("population_sha256", scope.get("population_sha256"))):
        if isinstance(value, str) and value and value in visible:
            errors.append(f"visible text: contains the {label}; keep run details in metadata")
    if dashboard_url and data.get("type") == "text":
        shared = metadata.get(SHARED_KEY) if isinstance(metadata.get(SHARED_KEY), dict) else {}
        ids = {str(i).lower() for i in shared.get("contributing_session_ids", []) if isinstance(i, str)}
        pattern = re.compile(r"\]\(" + re.escape(dashboard_url.rstrip("/")) + r"/sessions/(" + UUID_TEXT + r")\)")
        if not {m.lower() for m in pattern.findall(content)} & ids:
            errors.append(f"data: text content needs a Markdown link to at least one contributing session, as [label]({dashboard_url.rstrip('/')}/sessions/SESSION_ID)")
    return errors


def check_cards(cards: Any, max_cards: int = MAX_CARDS, dashboard_url: str | None = None) -> list[str]:
    """Return every contract violation across a batch of cards."""
    if not isinstance(cards, list) or not cards:
        return ["cards: expected a non-empty array"]
    errors = []
    if len(cards) > min(max_cards, SERVER_MAX_CARDS):
        errors.append(f"cards: {len(cards)} cards; this skill writes at most {min(max_cards, SERVER_MAX_CARDS)} per run")
    names, runs, ranks = [], set(), []
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
        errors += [f"{where}: {e}" for e in check_data(card.get("data"))]
        errors += [f"{where}: {e}" for e in check_visible_text(card, dashboard_url)]
        metadata = card.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{where}: metadata must be an object")
            continue
        errors += [f"{where}: {e}" for e in check_shared(metadata.get(SHARED_KEY))]
        errors += [f"{where}: {e}" for e in check_provenance(metadata.get(SKILL_KEY))]
        if isinstance(metadata.get(SKILL_KEY), dict):
            runs.add(metadata[SKILL_KEY].get("run_id"))
            ranks.append(metadata[SKILL_KEY].get("rank"))
    # The dashboard lists cards without an import newest first, so the most important card is
    # written last: ranks must run from len(cards) down to 1.
    if all(isinstance(r, int) and not isinstance(r, bool) for r in ranks) and len(ranks) == len(cards) and ranks != list(range(len(cards), 0, -1)):
        errors.append(f"cards: ranks must be {len(cards)} down to 1 in file order, so rank 1 is written last and shows first; got {ranks}")
    if len(set(names)) != len(names):
        errors.append("cards: names must be unique within a run")
    if len(runs) > 1:
        errors.append("cards: every card in one batch must share one run_id")
    return errors


def build_command(cards_path: Path, agent: str, idempotency_key: str) -> str:
    """Return a shell-quoted insight create command that writes the checked cards file."""
    parts = ["env", "KITARU_ACTIVE_SKILL=kitaru-insights", "kitaru", "insight", "create", "--agent", agent, "--insight-file", str(cards_path.resolve())]
    parts += ["--idempotency-key", idempotency_key, "--output", "json", "--machine", "--non-interactive", "--no-browser"]
    return shlex.join(parts)


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cards", type=Path, help="JSON array of drafted cards")
    parser.add_argument("--max-cards", type=int, default=MAX_CARDS)
    parser.add_argument("--dashboard-url", help="dashboard base URL from kitaru info; require session links in text cards")
    parser.add_argument("--emit-command", metavar="AGENT", help="print the create command for AGENT")
    parser.add_argument("--idempotency-key", help="required with --emit-command")
    args = parser.parse_args(argv)
    try:
        cards = json.loads(args.cards.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    errors = check_cards(cards, args.max_cards, args.dashboard_url)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    if args.emit_command:
        if not args.idempotency_key:
            print("error: --emit-command needs --idempotency-key", file=sys.stderr)
            return 1
        print(build_command(args.cards, args.emit_command, args.idempotency_key))
    else:
        print(json.dumps({"cards": len(cards), "ok": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
