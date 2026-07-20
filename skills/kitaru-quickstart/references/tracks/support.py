"""Support/triage flow — Kitaru quickstart demo.

Demonstrates: @flow, @checkpoint, wait(), log(), save()
Flow shape: classify ticket → draft response → approve → escalate
"""

import time

from kitaru import checkpoint, flow, log, save, wait


@checkpoint
def classify_ticket(ticket: str) -> dict:
    """Simulate classifying an incoming support ticket."""
    log(step="classify", ticket=ticket)
    time.sleep(1)
    return {
        "ticket": ticket,
        "category": "billing",
        "priority": "high",
        "sentiment": "frustrated",
    }


@checkpoint
def draft_response(classification: dict) -> str:
    """Simulate drafting a response to the classified ticket."""
    log(step="draft_response", category=classification["category"])
    # --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
    raise Exception("Simulated timeout calling response generation model")
    # --- end crash ---
    time.sleep(2)
    return (
        f"Dear customer,\n\n"
        f"Thank you for reaching out about your {classification['category']} issue. "
        f"We understand this is urgent (priority: {classification['priority']}). "
        f"We're looking into this and will follow up within 24 hours.\n\n"
        f"Best regards,\nSupport Team"
    )


@checkpoint
def escalate(ticket: str, response: str) -> str:
    """Simulate escalating the ticket with the approved response."""
    log(step="escalate", ticket=ticket, response_length=len(response))
    time.sleep(1)
    result = f"Ticket escalated to senior support. Response sent ({len(response)} chars)"
    save("escalation_result", result, type="output")
    return result


@flow
def support_flow(ticket: str) -> str:
    """Classify a ticket, draft a response, approve, and escalate."""
    classification = classify_ticket(ticket)
    response = draft_response(classification)

    approved = wait(
        name="approve_escalation",
        question=f"Approve escalation for '{ticket}'? (true/false)",
        schema=bool,
    )

    if not approved:
        return f"Escalation for '{ticket}' was rejected"

    return escalate(ticket, response)


REPLAY_AT = "draft_response"
DEFAULT_TICKET = "billing charge incorrect on invoice #1234"


def _usage() -> None:
    print("Usage: uv run python demo_flow.py [ticket]")
    print("       uv run python demo_flow.py --replay <EXEC_ID>")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--replay":
        if len(sys.argv) < 3:
            _usage()
            raise SystemExit(2)
        submission = support_flow.replay(sys.argv[2], at=REPLAY_AT, wait=False)
        row = submission.results[0]
        handle = row.handle
        if handle is None:
            raise RuntimeError(
                f"Replay did not return a live handle: {row.replay_exec_id}"
            )
    else:
        ticket = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TICKET
        handle = support_flow.run(ticket)

    print(f"Execution ID: {handle.exec_id}")
    print(f"Status: {handle.status}")
    result = handle.wait()
    print(f"Result: {result}")
