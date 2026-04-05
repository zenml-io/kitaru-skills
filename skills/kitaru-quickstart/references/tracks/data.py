"""Data pipeline flow — Kitaru quickstart demo.

Demonstrates: @flow, @checkpoint, wait(), log(), memory
Flow shape: ingest → validate → transform → approve → load
"""

import time

from kitaru import checkpoint, flow, log, memory, wait


@checkpoint
def ingest(source: str) -> list[dict]:
    """Simulate ingesting raw data from a source."""
    log(step="ingest", source=source)
    time.sleep(1)
    return [
        {"id": 1, "value": 100, "status": "active"},
        {"id": 2, "value": -5, "status": "active"},
        {"id": 3, "value": 200, "status": "inactive"},
    ]


@checkpoint
def validate(records: list[dict]) -> dict:
    """Simulate validating ingested records."""
    log(step="validate", record_count=len(records))
    time.sleep(1)
    issues = [r for r in records if r["value"] < 0]
    return {
        "valid_count": len(records) - len(issues),
        "issue_count": len(issues),
        "issues": issues,
        "records": records,
    }


@checkpoint
def transform(validation: dict) -> list[dict]:
    """Simulate transforming validated data."""
    log(step="transform", valid_count=validation["valid_count"])
    # --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
    raise Exception("Simulated schema mismatch during transformation")
    # --- end crash ---
    time.sleep(2)
    transformed = []
    for r in validation["records"]:
        if r["value"] >= 0:
            transformed.append({
                "id": r["id"],
                "value_normalized": r["value"] / 100.0,
                "is_active": r["status"] == "active",
            })
    return transformed


@checkpoint
def load_data(records: list[dict]) -> str:
    """Simulate loading transformed data into a destination."""
    log(step="load", record_count=len(records))
    time.sleep(1)
    return f"Loaded {len(records)} records into warehouse"


@flow
def data_flow(source: str) -> str:
    """Ingest, validate, transform, approve, and load data."""
    previous_source = memory.get("last_source")
    if previous_source:
        log(returning_user=True, previous_source=previous_source)

    raw = ingest(source)
    validation = validate(raw)

    if validation["issue_count"] > 0:
        log(data_quality_warning=True, issues=validation["issues"])

    transformed = transform(validation)

    approved = wait(
        name="approve_load",
        question=f"Approve loading {len(transformed)} records? (true/false)",
        schema=bool,
    )

    if not approved:
        return "Data load was rejected"

    result = load_data(transformed)
    memory.set("last_source", source)
    return result


if __name__ == "__main__":
    import sys

    source = sys.argv[1] if len(sys.argv) > 1 else "sales_data_2026_q1.csv"
    handle = data_flow.run(source)
    print(f"Execution ID: {handle.exec_id}")
    print(f"Status: {handle.status}")
    result = handle.wait()
    print(f"Result: {result}")
