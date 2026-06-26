"""Research/content approval flow — Kitaru quickstart demo.

Demonstrates: @flow, @checkpoint, wait(), log(), save()
Flow shape: gather sources → draft content → approve → publish
"""

import time

from kitaru import checkpoint, flow, log, save, wait


@checkpoint
def gather_sources(topic: str) -> list[str]:
    """Simulate gathering research sources."""
    log(step="gather", topic=topic)
    time.sleep(1)
    return [
        f"Academic paper on {topic}",
        f"Industry report: {topic} trends 2026",
        f"Expert interview transcript about {topic}",
    ]


@checkpoint
def draft_content(topic: str, sources: list[str]) -> str:
    """Draft content from gathered sources."""
    log(step="draft", source_count=len(sources))
    # --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
    raise Exception("Simulated network timeout during content generation")
    # --- end crash ---
    time.sleep(2)
    lines = [f"# {topic}", "", "## Key Findings", ""]
    lines.extend(f"- Finding from: {s}" for s in sources)
    return "\n".join(lines)


@checkpoint
def publish(draft: str) -> str:
    """Simulate publishing the approved content."""
    log(step="publish", draft_length=len(draft))
    time.sleep(1)
    url = f"Published at https://example.com/articles/{abs(hash(draft)) % 10000}"
    save("published_url", url, type="output")
    return url


@flow
def research_flow(topic: str) -> str:
    """Research, draft, approve, and publish content about a topic."""
    sources = gather_sources(topic)
    draft = draft_content(topic, sources)

    approved = wait(
        name="approve_draft",
        question=f"Approve draft about '{topic}'? (true/false)",
        schema=bool,
    )

    if not approved:
        return f"Draft about '{topic}' was rejected"

    return publish(draft)


REPLAY_AT = "draft_content"
DEFAULT_TOPIC = "durable AI agents"


def _usage() -> None:
    print("Usage: uv run python demo_flow.py [topic]")
    print("       uv run python demo_flow.py --replay <EXEC_ID>")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--replay":
        if len(sys.argv) < 3:
            _usage()
            raise SystemExit(2)
        handle = research_flow.replay(sys.argv[2], at=REPLAY_AT)
    else:
        topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TOPIC
        handle = research_flow.run(topic)

    print(f"Execution ID: {handle.exec_id}")
    print(f"Status: {handle.status}")
    result = handle.wait()
    print(f"Result: {result}")
