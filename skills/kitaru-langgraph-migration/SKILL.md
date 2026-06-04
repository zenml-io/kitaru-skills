---
name: kitaru-langgraph-migration
description: >
  Migrate existing LangGraph and LangChain agent code to Kitaru's LangGraph
  adapter. Use when code mentions LangGraph, StateGraph, CompiledStateGraph,
  graph.invoke, graph.ainvoke, stream, astream, interrupt, Command, thread_id,
  checkpointer, InMemorySaver, MemorySaver, create_agent,
  KitaruGraphRunner, LangGraphRunRequest, LangGraphRunResult,
  KitaruLangGraphMiddleware, build_resume_request, wait_for_interrupt,
  checkpoint_strategy, graph_call, calls, callbacks, event streams, Deep Agents,
  or checkpointers. Helps classify direct, approximate, and absent mappings,
  choose graph_call vs middleware-backed calls boundaries, preserve LangGraph
  ownership of graph state, and produce a migration report.
---

# Migrate LangGraph to Kitaru

## What this skill does

Use this skill to inspect LangGraph, LangChain `create_agent(...)`, or Deep
Agents code and move only the supportable durability boundary to Kitaru's
`kitaru.adapters.langgraph` surfaces.

The output should be conservative:

1. A source pattern inventory.
2. A migration plan that classifies each important pattern as `direct`,
   `approximate`, or `absent`.
3. Migrated or proposed code using `KitaruGraphRunner`, `LangGraphRunRequest`,
   `LangGraphRunResult`, and, when safe, `KitaruLangGraphMiddleware`.
4. A `MIGRATION_REPORT.md` section or file that names replay, interrupt,
   checkpointer, state, stream, and side-effect risks.

Do not promise that Kitaru replaces LangGraph persistence or checkpoints every
node inside the graph.

## Mental model: LangGraph owns the graph; Kitaru records the doorway

LangGraph still owns graph state, checkpointers, stores, interrupts,
`thread_id`, graph-local replay, and any Deep Agents sandbox or filesystem
backend.

Kitaru can record either:

- one outer graph invocation with `checkpoint_strategy="graph_call"`; or
- synchronous LangChain model/tool calls that physically pass through
  `KitaruLangGraphMiddleware` while a `KitaruGraphRunner` is active with
  `checkpoint_strategy="calls"`.

A useful picture: LangGraph is the house. Kitaru can put a camera at the front
door and, if LangChain middleware is installed, at a few visible interior
doorways. It cannot see through walls into checkpointers, stores, hosted tools,
or async model/tool internals that do not pass through a true Kitaru checkpoint.

## When to use this skill

Use it when the user asks to:

- replace raw `graph.invoke(...)` / `graph.ainvoke(...)` entrypoints with
  `KitaruGraphRunner.invoke(...)` / `ainvoke(...)`;
- add Kitaru around a `StateGraph` / `CompiledStateGraph`;
- choose between `checkpoint_strategy="graph_call"` and `"calls"`;
- migrate LangGraph interrupts and `Command(resume=...)` handling;
- review LangGraph checkpointers, stores, `thread_id`, `InMemorySaver`, or
  `MemorySaver` assumptions;
- add `KitaruLangGraphMiddleware` to a LangChain `create_agent(...)` agent;
- reason about callbacks, events, `stream`, `astream`, `stream_events`, or Deep
  Agents under Kitaru;
- produce a migration report for LangGraph code.

## When not to use this skill

Do not use it to:

- replace LangGraph's checkpointer or store with Kitaru;
- promise Kitaru can replay every LangGraph node, edge, interrupt, event, or
  Deep Agents filesystem operation;
- migrate PydanticAI, OpenAI Agents SDK, Claude Agent SDK, Gemini Interactions,
  or raw provider SDK code;
- put Kitaru waits inside graph nodes or checkpoints without a flow-scope
  redesign;
- invent unsupported Kitaru strategies beyond `graph_call` and `calls`.

## The three mapping types

Classify each source pattern before editing:

- `direct`: Kitaru has a clear adapter surface for the same outer behavior.
  Example: `graph.invoke(input, config)` becomes
  `runner.invoke(LangGraphRunRequest.start(input, thread_id=...))`.
- `approximate`: The migration is possible, but replay, observability,
  interrupt, streaming, state, or persistence behavior differs. Example:
  callbacks remain observability, not replay boundaries.
- `absent`: There is no safe automatic migration until the source is redesigned.
  Example: a claim that Kitaru will replace a production LangGraph checkpointer.

Unsupported patterns must not be silently approximated. Add a concrete
`# TODO(migration): ...` comment near proposed code, list it in the report, and
explain the redesign needed.

## Migration workflow

1. **Inspect source first.** Find graph construction, compile-time checkpointers
   and stores, `thread_id` handling, raw invoke/ainvoke/stream calls, interrupts,
   `Command(resume=...)`, callbacks, middleware, Deep Agents usage, and existing
   Kitaru flows/checkpoints.
2. **Classify every pattern.** Use `references/concept-map.md` and
   `references/gaps-and-flags.md`. Count direct, approximate, flagged, and
   blocked items.
3. **Choose Kitaru boundaries.** Prefer `checkpoint_strategy="graph_call"` unless
   the source clearly uses synchronous LangChain model/tool handlers that can be
   wrapped by `KitaruLangGraphMiddleware`.
4. **Present the plan before generating code** when the migration is more than a
   tiny entrypoint replacement. Name high-risk seams before editing.
5. **Draft migrated code.** Keep the source graph. Add `KitaruGraphRunner` and
   serializable `LangGraphRunRequest` objects. Add explicit result status
   handling for `completed` vs `interrupted`.
6. **Produce `MIGRATION_REPORT.md`.** Include the pattern inventory,
   classifications, chosen boundary, flags, behavior differences, and
   verification plan.
7. **Verify behavior.** Prefer static/import checks and a small local graph. If
   provider keys or production checkpointers are unavailable, say so.

## Pattern detection checklist

Look for:

- `StateGraph(...)`, `.compile(...)`, `CompiledStateGraph`, `graph.invoke(...)`,
  `graph.ainvoke(...)`, `stream(...)`, `astream(...)`, or `stream_events(...)`.
- `config={"configurable": {"thread_id": ...}}`, `checkpoint_id`, or
  `checkpoint_ns`.
- `interrupt(...)`, `Command(resume=...)`, `wait_for_interrupt(...)`, and
  result status branches.
- `InMemorySaver`, `MemorySaver`, Postgres/Redis/custom checkpointers, stores,
  or memory APIs.
- `create_agent(...)`, `middleware=[...]`, and whether
  `KitaruLangGraphMiddleware()` is installed.
- callbacks, LangSmith tracing, event streams, or stream handlers with external
  side effects.
- Deep Agents middleware/backends, filesystem tools, subagents, sandboxes, or
  state backends.
- Existing `@kitaru.flow` or `@kitaru.checkpoint` wrappers.
- Non-serializable graph outputs, state snapshots, clients, file handles, or raw
  framework objects returned from checkpoints.

## Boundary decision rules

- Keep LangGraph as the graph runtime.
- Default to `KitaruGraphRunner(graph, checkpoint_strategy="graph_call")` for a
  clean outer checkpoint around one completed or interrupted invocation.
- Use `checkpoint_strategy="calls"` only when synchronous LangChain model/tool
  calls pass through `KitaruLangGraphMiddleware` while the runner is active.
- Treat async calls mode as metadata-only today; do not promise true async
  granular checkpoints.
- Keep LangGraph checkpointers/stores in place. Kitaru records its own boundary;
  it does not replace LangGraph's persistence layer.
- Preserve stable `thread_id` handling. If the source has no stable thread ID,
  flag it before migration.
- Treat callbacks, events, and streams as observability unless a concrete Kitaru
  checkpoint boundary stores a final serializable value.
- Do not put Kitaru `wait()` calls inside graph nodes or checkpoints. Bridge
  LangGraph interrupts at flow scope when human input is needed.

## LangGraph migration quick guide

Minimal outer graph call:

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
    thread_id="thread-001",
)
result = runner.invoke(request)
if result.status != "completed":
    raise RuntimeError(f"Expected completed graph, got {result.status!r}")
print(result.output)
```

For full examples, load `references/code-patterns.md`.

## Gap handling rules

When a pattern is unsafe or unsupported:

1. Do not silently approximate it.
2. Add a concrete `# TODO(migration): ...` comment near proposed code.
3. Add a report entry with severity `LOW`, `MEDIUM`, `HIGH`, or `BLOCKER`.
4. Explain the bad outcome the flag prevents. Example: "the graph resumes from a
   LangGraph interrupt, so code before `interrupt()` in that node may run again."
5. Propose the smallest safe redesign.

## Report requirements

Every non-trivial migration must include or draft `MIGRATION_REPORT.md` with:

- source files reviewed and changed/proposed;
- classification totals;
- source pattern inventory with `file:line` locations;
- chosen Kitaru graph boundary and checkpoint strategy;
- direct translations;
- approximate translations and caveats;
- flagged items with severity and required action;
- LangGraph-specific notes for `thread_id`, checkpointers/stores,
  interrupts/resume, middleware/calls mode, streams/events, Deep Agents, capture
  policy, and side effects;
- verification plan and whether execution was actually run.

Use `references/report-template.md` when a full report is needed.

## Anti-patterns

Avoid these:

- Replacing a LangGraph checkpointer/store with Kitaru.
- Claiming Kitaru replays every node, edge, stream event, or Deep Agents action.
- Using `calls` without `KitaruLangGraphMiddleware` and calling it granular
  Kitaru checkpointing.
- Treating async `awrap_model_call` / `awrap_tool_call` metadata as true
  checkpoints.
- Using `InMemorySaver` as production restart-durable storage.
- Ignoring `result.status == "interrupted"`.
- Returning raw graph state snapshots or non-serializable framework objects from
  checkpoints.
- Hiding durable side effects in stream/callback handlers without idempotency.

## References

Load only the reference file needed for the current task:

- `references/concept-map.md` — source-to-target mapping table and
  classification guidance.
- `references/code-patterns.md` — import-complete migration examples.
- `references/gaps-and-flags.md` — severity definitions, upstream assumptions,
  and must-flag patterns.
- `references/report-template.md` — LangGraph-specific migration report template.

Kitaru source references:

- Kitaru LangGraph adapter docs:
  `kitaru/docs/content/docs/adapters/langgraph.mdx`
- Adapter exports:
  `kitaru/src/kitaru/adapters/langgraph/__init__.py`
- LangChain middleware:
  `kitaru/src/kitaru/adapters/langgraph/langchain.py`
- Adapter example:
  `kitaru/examples/integrations/langgraph_agent/README.md`
