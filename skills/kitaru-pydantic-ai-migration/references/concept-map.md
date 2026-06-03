# PydanticAI to Kitaru Concept Map

Use this map when classifying source code before migration. The rule is simple:
PydanticAI still owns the agent runtime; Kitaru records only the safe boundary it
can actually see.

## Mapping labels

- `direct` — Kitaru has a clear adapter equivalent and behavior should mostly
  stay the same.
- `approximate` — the migration is possible, but replay, capture, wait, state,
  or operational behavior changes.
- `absent` — there is no safe adapter equivalent until the source is redesigned.

## Core source-to-target map

| PydanticAI source pattern | Kitaru target pattern | Mapping | Notes |
|---|---|---|---|
| `Agent(...)` with concrete model and stable name | Same `Agent`, wrapped by `KitaruAgent(agent)` | `direct` | Keep PydanticAI in charge. Add Kitaru around the agent. |
| `agent.run(...)` / `agent.run_sync(...)` | `durable_agent.run(...)` / `durable_agent.run_sync(...)` | `direct` | Result remains a PydanticAI-style result; use `.output` as before. |
| `Agent(..., output_type=...)` | Same agent wrapped by `KitaruAgent` | `direct` | Structured output remains PydanticAI-owned. Ensure checkpoint outputs are serializable. |
| `TestModel` no-key example | Same `TestModel`, wrapped by `KitaruAgent` | `direct` | Good for static or local dry-runs without provider credentials. |
| Existing `@kitaru.flow` around agent call | Keep explicit `@flow` | `direct` | Best for production and remote stacks. |
| Existing `@kitaru.checkpoint` around agent call | Keep checkpoint; adapter passthrough inside | `direct` | The explicit checkpoint is the replay boundary. |
| `checkpoint_strategy="calls"` | Per supported model/tool/MCP checkpoints | `approximate` | More granular replay, but only for adapter-visible calls. Tool waits need care. |
| `checkpoint_strategy="turn"` | One checkpoint per agent run | `approximate` | Coarser replay. Easier to reason about a whole turn as one save point. |
| `granular_checkpoints=True` | `checkpoint_strategy="calls"` | `approximate` | Compatibility alias. Prefer `checkpoint_strategy` in new code. |
| `granular_checkpoints=False` | `checkpoint_strategy="turn"` | `approximate` | Compatibility alias. Prefer `checkpoint_strategy` in new code. |
| `CapturePolicy(...)` | Same `CapturePolicy(...)` on `KitaruAgent` | `approximate` | Observability only; it changes what is saved, not how tools execute. |
| `persist_message_history=True` | Same flag, with caveat | `approximate` | Instance-local history only. Not durable across process restarts or separate instances. |
| `message_history=...` per run | Pass explicit `message_history=...` per run | `direct` | Prefer explicit persisted history for durable conversations. |
| `event_stream_handler` | Same argument, with streaming caveat | `approximate` | Calls mode can fall back to turn behavior for streamed calls. |
| `run_stream()` / `iter()` | Explicit `@kitaru.checkpoint` required | `approximate` or `absent` | Approximate if an explicit checkpoint can safely contain the stream. Absent until redesigned if stream side effects must replay exactly. |
| `@hitl_tool` | `kitaru.adapters.pydantic_ai.hitl_tool` | `direct` for pure waits | Safe because the adapter creates the wait at flow scope and skips the synthetic tool checkpoint. |
| Tool body `wait_for_input(...)` | Tool checkpoint opt-out plus `allow_sync_tool_body_waits=True` | `approximate` | `HIGH` flag. Changes sync tool execution threading for that run. Prefer explicit flow waits if possible. |
| PydanticAI `requires_approval=True`, `ApprovalRequired`, or `CallDeferred` | Adapter-routed Kitaru wait when the deferred tool reaches flow scope | `approximate` | Supported, but use the same caveats as tool-body waits: if `checkpoint_strategy="calls"` would put the tool inside a synthetic checkpoint, prefer `@hitl_tool` for pure waits or opt that tool out of checkpointing. Flag rather than auto-rewrite when flow-scope safety is unclear. |
| MCP server/toolset attached to agent | Adapter wraps supported toolsets/MCP servers automatically | `approximate` | Kitaru sees top-level MCP calls, not arbitrary provider internals. |
| `kp.wrap(...)` / `wrap(...)` | `KitaruAgent(...)` | `approximate` | Deprecated source style. Preserve behavior, but migrate target code to `KitaruAgent`. |
| Per-run `model=` override | Separate `Agent` / `KitaruAgent` per model | `absent` | The adapter requires a concrete model at construction time. |
| Agent without stable `name=` | Add stable `name=` before wrapping | `absent until fixed` | Stable names are needed for artifact keys and generated flow/checkpoint names. |
| Agent without concrete model at construction | Bind model in `Agent(...)` constructor | `absent until fixed` | Late binding is not supported by the adapter. |
| Non-serializable checkpoint output | Return serializable value or explicit artifact reference | `absent until redesigned` | Raw framework/client objects should not be checkpoint outputs. |
| Hidden mutable module state | Explicit artifact, flow input, or external store | `absent` | Replay may see different state unless the value is explicit. |
| Provider/native tool hidden internals | Leave provider-owned and flag replay limits | `approximate` or `absent` | Kitaru cannot promise granular replay for work it cannot see. |
| `runtime="isolated"` in adapter checkpoint config | Use inline adapter-managed checkpoints | `absent` | Isolated runtime is rejected for adapter-managed checkpoints. |
| Auto-flow intended for remote stacks | Add explicit `@kitaru.flow` | `absent until fixed` | Auto-flow depends on in-process registration and is local-only. |

## Boundary choice guide

Choose boundaries by asking what should happen after a crash:

1. If the whole agent turn can safely repeat, use an explicit checkpoint or
   `checkpoint_strategy="turn"`.
2. If expensive model calls or flaky tools should be skipped individually on
   replay, use `checkpoint_strategy="calls"`.
3. If a human wait is involved, make sure the wait is created at flow scope.
4. If the workflow will run on a remote stack, use explicit `@kitaru.flow`.
5. If source behavior depends on hidden mutable state, do not claim a full
   migration until that state is made explicit.

## Kitaru authoring guardrails inherited by this skill

- Do not nest flows.
- Do not call one checkpoint from inside another checkpoint.
- Do not call `wait()` inside a checkpoint.
- Keep checkpoint outputs serializable.
- Use stable names.
- Make cross-execution state explicit through artifacts or external storage.
