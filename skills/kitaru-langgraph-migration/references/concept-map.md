# LangGraph to Kitaru Concept Map

Use this map while classifying source code. The safe migration story is simple:
LangGraph owns graph execution and graph state; Kitaru records only the boundary
it can honestly see.

## Mapping labels

- `direct`: Kitaru has a close adapter surface for the same outer behavior.
- `approximate`: Migration is possible, but replay, observability, interrupt,
  stream, state, or persistence behavior differs.
- `absent`: No safe automatic migration. The code needs redesign or explicit
  human review before migration.

## Core concepts

| LangGraph source pattern | Kitaru target pattern | Mapping | Notes |
|---|---|---:|---|
| `graph.invoke(input, config=...)` | `runner.invoke(LangGraphRunRequest.start(input, thread_id=...))` | `direct` | Keep the same graph. Kitaru changes the entrypoint. |
| `await graph.ainvoke(input, config=...)` | `await runner.ainvoke(LangGraphRunRequest.start(...))` | `direct` | Use async runner in async code. |
| `thread_id` in `configurable` | `LangGraphRunRequest.start(..., thread_id=...)` | `direct` | Stable thread IDs remain required for LangGraph persistence/resume. |
| `checkpoint_id` / `checkpoint_ns` | Matching request fields | `direct` | Preserve when the source intentionally targets a checkpoint namespace. |
| `config={"configurable": {...}}` | `config=` / `configurable=` request fields | `direct` | Keep serializable values. Do not put secrets in metadata. |
| `context=...` on graph call | `context=` or `context_factory` | `approximate` | Review serialization and tenant/user/cache identity needs. |
| Raw `CompiledStateGraph` | Same graph passed to `KitaruGraphRunner` | `direct` | Kitaru does not rewrite graph nodes or edges. |
| `checkpoint_strategy="graph_call"` | One Kitaru checkpoint around completed/interrupted invocation | `approximate` | Default recommendation. LangGraph still creates its own graph checkpoints if configured. |
| `checkpoint_strategy="calls"` with `KitaruLangGraphMiddleware` | True sync model/tool call checkpoints plus event metadata | `approximate` | Only for synchronous LangChain model/tool handlers that pass through middleware. |
| `checkpoint_strategy="calls"` without middleware | Trace metadata only, not granular Kitaru checkpoints | `approximate` or `absent` | Use only if metadata is enough. Do not claim per-call replay. |
| Async LangChain model/tool middleware calls | Metadata-only async tracking | `approximate` | Current Kitaru calls mode does not open true async granular checkpoints. |
| `create_agent(...)` from LangChain | Same agent/graph plus optional `KitaruLangGraphMiddleware()` | `direct` for outer call, `approximate` for calls | Middleware must be installed for granular sync call checkpoints. |
| `interrupt(...)` | `LangGraphRunResult(status="interrupted")` | `approximate` | The paused graph is LangGraph-owned; Kitaru returns a serializable pending-state summary. |
| `Command(resume=...)` | `build_resume_request(...)` or `LangGraphRunRequest.resume(...)` | `approximate` | Resume at flow scope and check status again after resume. |
| `wait_for_interrupt(...)` | Kitaru flow-scope wait bridge | `approximate` | Good for human input; do not call inside checkpoints. |
| LangGraph checkpointer | Keep graph checkpointer | `direct` for preserving source | Kitaru does not replace it. |
| `InMemorySaver` / `MemorySaver` | Keep only for local/demo/test or replace with durable LangGraph store | `approximate` | Not restart-durable across processes or pods. |
| LangGraph store/memory | Keep LangGraph-owned | `approximate` | Kitaru records adapter outputs/artifacts, not graph memory internals. |
| `stream(...)`, `astream(...)`, `stream_events(...)` | Prefer final `invoke`/`ainvoke` boundary, or explicit stream collection | `approximate` | Events are observability. Stream handlers with side effects need idempotency. |
| callbacks / LangSmith tracing | Leave as observability | `approximate` | Useful for debugging, not Kitaru replay boundaries. |
| Deep Agents middleware/backends/filesystem | Outer graph call only, unless visible sync LangChain calls are wrapped | `approximate` or `absent` | Sandbox/filesystem/backend remain Deep Agents-owned. |
| Side-effectful graph nodes | Application-owned idempotency or explicit Kitaru checkpoint outside graph | `approximate` or `absent` | Kitaru cannot make hidden graph-node side effects safe automatically. |
| Non-serializable graph output/state | Return serializable value or artifact reference | `absent until redesigned` | Raw clients, state snapshots, streams, and file handles are unsafe checkpoint outputs. |
| Missing stable graph name | Add `name=` to `KitaruGraphRunner` | `absent until fixed` | Stable names are needed for readable checkpoints/artifacts. |
| Missing stable thread ID | Add stable `thread_id` generation/storage | `BLOCKER` for resume workflows | New thread IDs create new LangGraph threads instead of resuming. |

## Boundary decision guide

Choose `graph_call` when:

- one durable record around the graph invocation is enough;
- the graph may interrupt and resume through LangGraph state;
- the project has async graph calls, streams, callbacks, Deep Agents, or opaque
  graph internals;
- the user wants `flow.run(...).wait()` to return one result envelope.

Choose `calls` only when:

- the graph is a LangChain `create_agent(...)`-style graph;
- `KitaruLangGraphMiddleware()` is installed in the agent middleware list;
- the source uses synchronous model/tool handlers;
- per-model/per-tool Kitaru artifacts are worth the extra complexity.

Do not choose `calls` when:

- there is no Kitaru middleware;
- the desired granular calls are async-only;
- the call runs inside an existing Kitaru checkpoint;
- the user expects Kitaru to replace LangGraph checkpointers.

## What Kitaru does not own

Kitaru does not own LangGraph's checkpointer, store, state snapshots, interrupt
mechanics, node replay, event stream, or Deep Agents sandbox/filesystem. If the
source depends on those internals being replayed as separate Kitaru units, mark
the mapping `approximate` or `absent` and explain the boundary clearly.
