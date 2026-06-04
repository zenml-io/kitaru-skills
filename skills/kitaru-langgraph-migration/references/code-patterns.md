# LangGraph Migration Code Patterns

These examples are intentionally import-complete. Copy the shape, then adapt
state schemas, graph names, thread IDs, prompts, and checkpoint choices to the
source project. They are static/signature-oriented examples, not provider-live
smoke tests.

## 1. Minimal `graph.invoke(...)` replacement

Source:

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    topic: str
    summary: str

def summarize(state: State) -> dict[str, str]:
    return {"summary": f"Summary for {state['topic']}"}

builder = StateGraph(State)
builder.add_node("summarize", summarize)
builder.add_edge(START, "summarize")
builder.add_edge("summarize", END)
graph = builder.compile()

result = graph.invoke({"topic": "durable agents", "summary": ""})
print(result["summary"])
```

Target:

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from kitaru.adapters.langgraph import KitaruGraphRunner, LangGraphRunRequest

class State(TypedDict):
    topic: str
    summary: str

def summarize(state: State) -> dict[str, str]:
    return {"summary": f"Summary for {state['topic']}"}

builder = StateGraph(State)
builder.add_node("summarize", summarize)
builder.add_edge(START, "summarize")
builder.add_edge("summarize", END)
graph = builder.compile()

runner = KitaruGraphRunner(graph, name="summary_graph")
request = LangGraphRunRequest.start(
    {"topic": "durable agents", "summary": ""},
    thread_id="summary-thread-001",
)
result = runner.invoke(request)
if result.status != "completed":
    raise RuntimeError(f"Expected completed graph, got {result.status!r}")
print(result.output)
```

Outside an explicit Kitaru flow, this is adapter API wiring. For a production
workflow, place the runner call in a Kitaru flow.

## 2. Explicit Kitaru flow with `graph_call`

Use this when the workflow needs one clear durable graph result.

```python
from typing import TypedDict

import kitaru
from langgraph.graph import END, START, StateGraph
from kitaru.adapters.langgraph import KitaruGraphRunner, LangGraphRunRequest

class State(TypedDict):
    topic: str
    summary: str

def summarize(state: State) -> dict[str, str]:
    return {"summary": f"Summary for {state['topic']}"}

builder = StateGraph(State)
builder.add_node("summarize", summarize)
builder.add_edge(START, "summarize")
builder.add_edge("summarize", END)
graph = builder.compile()
runner = KitaruGraphRunner(
    graph,
    name="summary_graph",
    checkpoint_strategy="graph_call",
)

@kitaru.flow
def summarize_topic(topic: str, thread_id: str) -> str:
    request = LangGraphRunRequest.start(
        {"topic": topic, "summary": ""},
        thread_id=thread_id,
    )
    result = runner.invoke(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed graph, got {result.status!r}")
    output = result.output
    if not isinstance(output, dict):
        raise TypeError("Expected dict output from summary graph")
    return str(output["summary"])

handle = summarize_topic.run("LangGraph adapters", "summary-thread-001")
print(handle.wait())
```

## 3. Async graph invocation

Use async runner methods in async application code.

```python
from typing import Any

from kitaru.adapters.langgraph import KitaruGraphRunner, LangGraphRunRequest

async def run_graph_async(graph: Any, message: str, thread_id: str) -> object:
    runner = KitaruGraphRunner(graph, name="async_agent_graph")
    request = LangGraphRunRequest.start(
        {"messages": [{"role": "user", "content": message}]},
        thread_id=thread_id,
    )
    result = await runner.ainvoke(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed graph, got {result.status!r}")
    return result.output
```

Do not convert async callers back to sync `invoke(...)` just to make migration
look smaller.

## 4. Interrupt and resume bridge

Source shape:

```python
from langgraph.types import Command

first = graph.invoke(input_state, config={"configurable": {"thread_id": thread_id}})
second = graph.invoke(Command(resume={"approved": True}), config={"configurable": {"thread_id": thread_id}})
```

Target shape:

```python
from typing import Any

from kitaru.adapters.langgraph import (
    KitaruGraphRunner,
    LangGraphRunRequest,
    build_resume_request,
)


def run_then_resume(
    graph: Any,
    input_state: dict[str, Any],
    thread_id: str,
    approval: bool,
) -> object:
    runner = KitaruGraphRunner(graph, name="approval_graph")
    first = runner.invoke(LangGraphRunRequest.start(input_state, thread_id=thread_id))
    if first.status == "completed":
        return first.output
    if first.status != "interrupted":
        raise RuntimeError(f"Unexpected LangGraph status: {first.status!r}")

    resume_request = build_resume_request(first, {"approved": approval})
    second = runner.invoke(resume_request)
    if second.status != "completed":
        raise RuntimeError(f"Expected completed resume, got {second.status!r}")
    return second.output
```

If the project needs a human wait, keep that wait in the surrounding Kitaru flow
and call `wait_for_interrupt(...)` from flow scope, not from a checkpoint.

## 5. LangChain `create_agent(...)` with middleware-backed `calls`

Use this only when the source is a LangChain agent and the relevant calls are
synchronous middleware-visible model/tool calls.

```python
from langchain.agents import create_agent
from langchain.tools import tool
from kitaru.adapters.langgraph import KitaruGraphRunner, LangGraphRunRequest
from kitaru.adapters.langgraph.langchain import KitaruLangGraphMiddleware

@tool
def lookup_order(order_id: str) -> str:
    """Return a deterministic order summary."""
    return f"Order {order_id} is processing."

agent_graph = create_agent(
    model="openai:gpt-5-nano",
    tools=[lookup_order],
    middleware=[KitaruLangGraphMiddleware()],
)
runner = KitaruGraphRunner(
    agent_graph,
    name="support_agent",
    checkpoint_strategy="calls",
)
request = LangGraphRunRequest.start(
    {"messages": [{"role": "user", "content": "Where is order ORD-1007?"}]},
    thread_id="support-thread-001",
)
result = runner.invoke(request)
if result.status != "completed":
    raise RuntimeError(f"Expected completed agent, got {result.status!r}")
print(result.output)
```

If `KitaruLangGraphMiddleware` is missing, `calls` mode should be reported as
metadata-only, not as per-call checkpointing.

## 6. Keep LangGraph checkpointers in place

Source:

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "conversation-1"}}
output = graph.invoke(input_state, config=config)
```

Target:

```python
from langgraph.checkpoint.memory import InMemorySaver
from kitaru.adapters.langgraph import KitaruGraphRunner, LangGraphRunRequest

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
runner = KitaruGraphRunner(graph, name="conversation_graph")
request = LangGraphRunRequest.start(input_state, thread_id="conversation-1")
result = runner.invoke(request)
```

Report caveat: `InMemorySaver` is local/demo/test storage. For production restart
resilience, switch to a durable LangGraph checkpointer; do not claim Kitaru makes
LangGraph's in-memory state durable.

## 7. Stream/event handling caveat

```python
from typing import Any

from kitaru.adapters.langgraph import KitaruGraphRunner, LangGraphRunRequest


def collect_final_output(graph: Any, input_state: dict[str, Any], thread_id: str) -> object:
    runner = KitaruGraphRunner(graph, name="streaming_graph")
    # Prefer one final invoke boundary when stream events are only UI progress.
    result = runner.invoke(LangGraphRunRequest.start(input_state, thread_id=thread_id))
    if result.status != "completed":
        raise RuntimeError(f"Expected completed graph, got {result.status!r}")
    return result.output
```

If the source stream handler writes progress to Slack or a database, flag it.
Replay may send the same progress twice, while cached replay may skip the handler
entirely.
