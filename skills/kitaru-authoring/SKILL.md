---
name: kitaru-authoring
description: >
  Guide for writing Kitaru durable workflows and operational control paths. Use
  when creating or refactoring Kitaru flows, checkpoints, waits, logging,
  artifacts, tracked LLM calls, replay/resume/retry flows, KitaruClient usage,
  CLI commands, MCP operations, or PydanticAI adapter integrations. Triggers on
  mentions of kitaru, @flow, @checkpoint, kitaru.wait, kitaru.log,
  kitaru.save, kitaru.load, kitaru.llm, KitaruClient, replay, resume, retry,
  `kitaru run`, `kitaru executions ...`, MCP tools, `wrap(...)`, or
  `hitl_tool(...)`.
---

# Kitaru Authoring Skill

Use this guide when writing or refactoring Kitaru workflows and when choosing
which Kitaru surface to use for running, observing, replaying, or controlling
those workflows.

> **Before building**: If the workflow shape is still fuzzy, suggest the
> `kitaru-scoping` skill first. It helps the user decide whether Kitaru is a
> fit, where checkpoints and waits belong, and which replay anchors should be
> stable before code gets written.

## Mental model

Think of a Kitaru flow like a long trip with named save points.

- `@flow` is the durable outer boundary.
- `@checkpoint` is a replay boundary inside that flow.
- `wait()` pauses at the flow level and resumes later with input.
- Replay reruns from the top, but checkpoints before the selected replay point
  return cached outputs instead of doing the work again.
- Flows are executed with `.run(...)`, not by calling the decorated function
  directly.

```python
from kitaru import checkpoint, flow, wait

@checkpoint
def draft(topic: str) -> str:
    return f"Draft for {topic}"

@flow
def review_flow(topic: str) -> str:
    text = draft(topic)
    approved = wait(name="approve_draft", question="Approve draft?", schema=bool)
    if not approved:
        return "Rejected"
    return text

handle = review_flow.run("Durable agents")
print(handle.exec_id)
```

A `FlowHandle` is the object you use after submission:

- `handle.exec_id` -> execution ID
- `handle.status` -> current execution status
- `handle.wait()` -> block until terminal state and return the result
- `handle.get()` -> fetch final result (or raise on failure)

## Authoring guardrails

Enforce these rules when writing or reviewing Kitaru code:

1. Do not nest flows.
2. Do not call one checkpoint from inside another checkpoint.
3. Do not call `wait()` inside a checkpoint.
4. `save()` and `load()` require checkpoint scope.
5. `log()` works in flow scope and checkpoint scope, but it attaches metadata to
   different targets depending on where it runs.
6. Checkpoint outputs must be serializable.
7. `.submit()`, `.map()`, and `.product()` are for work launched from inside a
   running flow.
8. `llm()` is valid only inside a `@flow`; outside a checkpoint it gets a
   synthetic `llm_call` checkpoint automatically.
9. Use stable, unique names for checkpoints, waits, and artifacts so replay and
   artifact lookup stay unambiguous.

## Primitive reference

### `@flow`

Use `@flow` for the durable orchestration boundary.

- Supported decorator overrides: `stack`, `image`, `cache`, `retries`
- Main entrypoints:
  - `.run(...)` — pass `stack="..."` to target a remote stack
  - `.replay(exec_id, from_=..., overrides=..., **flow_inputs)`

### `@checkpoint`

Use `@checkpoint` for meaningful replayable units of work.

- Supported decorator args: `retries`, `type`
- Supported call styles:
  - direct call inside a flow
  - `.submit(...)`
  - `.map(...)`
  - `.product(...)`
- Keep checkpoints coarse enough to matter and small enough to serialize.

### `wait(...)`

`wait(*, schema=bool, name=None, question=None, timeout=None, metadata=None)`
pauses the flow until input arrives.

- Valid only in the flow body
- Invalid inside checkpoints
- Use simple schemas and stable `name` values
- Default timeout is 600 seconds (runner polling window, not wait-record
  expiry); the execution stays waiting even after the timeout — the runner just
  stops polling and exits

### `log(...)`

`log(**kwargs)` records structured metadata.

- Inside a checkpoint: metadata is attached to the checkpoint
- Inside a flow but outside a checkpoint: metadata is attached to the execution
- Use this for breadcrumbs, decisions, IDs, and derived metrics

### `save(...)` / `load(...)`

Use explicit artifacts when a checkpoint should publish named outputs for later
inspection or reuse.

- `save(name, value, *, type="output", tags: list[str] | None = None)` requires
  checkpoint scope
- `load(exec_id, name)` requires checkpoint scope and an execution UUID string;
  it can retrieve both explicit `save(...)` artifacts and implicit checkpoint
  outputs by checkpoint/output name
- Allowed artifact kinds are: `prompt`, `response`, `context`, `input`,
  `output`, `blob`
- Keep artifact names unique within an execution to avoid ambiguous loads

### `llm(...)`

`llm(prompt, *, model=None, system=None, temperature=None, max_tokens=None,
name=None) -> str`

- Valid only inside a `@flow`
- Accepts a plain string or chat-style message list
- Uses local model alias resolution when `model` names an alias
- Only `llm()` currently auto-resolves alias-linked secrets; other primitives do
  not have this behavior
- Inside a checkpoint: runs inline
- Inside a flow body outside a checkpoint: Kitaru wraps the call in a synthetic
  `llm_call` checkpoint so the call is still tracked and replayable

## Replay and control surfaces

Replay is one shared concept exposed through several surfaces.

### Replay entrypoints

- SDK: `flow.replay(exec_id, from_=..., overrides=..., **flow_inputs)`
- Client: `KitaruClient().executions.replay(exec_id, from_=..., overrides=...,
  **flow_inputs)`
- CLI: `kitaru executions replay <exec_id> --from <selector> [--override
  checkpoint.<name>=<value>]`
- MCP: `kitaru_executions_replay`

### Replay selector rules

`from_` targets a **checkpoint selector** — a checkpoint name, invocation ID, or
call ID. Wait selectors are not valid replay anchors.

Override keys must use the `checkpoint.<selector>` namespace:

- `checkpoint.<name>` — replace the cached output of that checkpoint
- `wait.*` overrides are **not supported**; if the replayed execution reaches a
  wait, resolve it via `client.executions.input(...)` or
  `kitaru executions input`

Do not invent alternate replay APIs or made-up override keys.

## Wait resolution lifecycle

When a flow hits `wait()`, the execution pauses. The resolution flow is:

1. **Provide input** — use `client.executions.input(exec_id, wait=...,
   value=...)`, CLI `kitaru executions input`, or MCP
   `kitaru_executions_input`
2. **Abort a wait** — use `client.executions.abort_wait(exec_id, wait=...)`
3. **Resume** — if the execution does not continue automatically after input is
   provided, use `client.executions.resume(exec_id)` or
   `kitaru executions resume` as a manual fallback

`input` resolves the wait; `resume` is a separate operation for paused
executions that didn't auto-continue.

## Operational surfaces: what exists where

Use the surface that matches the job instead of assuming everything is available
in every interface.

### SDK (flow objects + helpers)

- Author flows and checkpoints
- Use `wait`, `log`, `save`, `load`, `llm`
- Use `configure(...)`, `connect(server_url, ...)`, `list_stacks()`,
  `current_stack()`, `use_stack()`, `create_stack(...)` (**local stacks only**),
  `delete_stack(...)`
- Launch executions: `flow.run(...)`, `flow.replay(...)`

### KitaruClient (inspection and control of existing executions)

The client is for **managing existing executions**, not launching new ones.

- `executions.get / list / latest / logs / pending_waits / input / abort_wait /
  retry / resume / replay / cancel`
- `artifacts.list / get`

### CLI

- `login`, `logout`, `status`, `info`
- `log-store set / show / reset`
- `stack list / current / show / use / create / delete`
  - `stack create` supports `local`, `kubernetes`, `vertex`, `sagemaker`,
    `azureml` (remote stack creation is CLI/MCP only, not available in the
    Python SDK `create_stack()`)
  - Advanced: `--extra` for component overrides, `--async` for async
    provisioning
- `model register / list`
- `secrets set / show / list / delete`
- `executions get / list / logs / input / replay / retry / resume / cancel`
- JSON output contract: `--output json` / `-o json` emits
  `{command, item}` for single-item commands, `{command, items, count}` for
  lists, and JSONL event objects for `executions logs --follow --output json`

### MCP tools (exact names)

- `kitaru_executions_list`, `kitaru_executions_get`, `kitaru_executions_latest`
- `kitaru_executions_run` (target format: `<module_or_file>:<flow_name>`)
- `kitaru_executions_input`, `kitaru_executions_retry`,
  `kitaru_executions_replay`, `kitaru_executions_cancel`
- `get_execution_logs`
- `kitaru_artifacts_list`, `kitaru_artifacts_get`
- `kitaru_status`, `kitaru_stacks_list`
- `manage_stack` (create/delete; supports `local`, `kubernetes`, `vertex`,
  `sagemaker`, `azureml`, plus `extra` and `async_mode`)

### Key asymmetries

| Capability | SDK | KitaruClient | CLI | MCP |
|---|---|---|---|---|
| Launch new execution | Yes (flow object) | No | Yes (`kitaru run`) | Yes (`kitaru_executions_run`) |
| Inspect execution | Limited (FlowHandle) | Yes | Yes | Yes |
| Resolve wait input | No | Yes | Yes | Yes |
| Abort wait | No | Yes (`abort_wait`) | No | No |
| Resume paused execution | No | Yes | Yes | No |
| Replay execution | Yes (flow object) | Yes | Yes | Yes |
| Browse artifacts | No | Yes | No | Yes |
| List pending waits | No | Yes (`pending_waits`) | No | No |
| Create local stack | Yes | No | Yes | Yes |
| Create remote stack | No | No | Yes | Yes |
| Switch active stack | Yes | No | Yes | No |

## Connection and runtime context

Use Kitaru configuration helpers instead of inventing custom runtime wiring.

- `configure(...)` sets local execution defaults
- `connect(server_url, ...)` connects to a server via URL (Python SDK surface)
- `kitaru login` connects to a server URL **or** a managed workspace by name/ID
  (CLI surface — broader than `connect()`)
- `list_stacks()`, `current_stack()`, `use_stack()` and `kitaru stack ...` help
  choose the active execution stack
- `create_stack(...)` in the SDK creates **local stacks only**; use CLI
  (`kitaru stack create`) or MCP (`manage_stack`) for remote stacks
  (`kubernetes`, `vertex`, `sagemaker`, `azureml`)
- `model register / list` manage local model aliases used by `llm(...)`; alias
  registries are transported into submitted/replayed runs via
  `KITARU_MODEL_REGISTRY`
- `secrets set / show / list / delete` manage secret values used by aliases

## PydanticAI adapter

Public adapter surface:

- `kitaru.adapters.pydantic_ai.wrap(agent, *, name=None,
  tool_capture_config=None, tool_capture_config_by_name=None)`
- `kitaru.adapters.pydantic_ai.hitl_tool(*, question=None, name=None,
  schema=bool)`

What the adapter really does:

- Wrapped agents must already have a model bound at construction time
- Wraps agent/model/tool activity so it is tracked under Kitaru execution
  metadata
- Inside a checkpoint, child model/tool events become part of that checkpoint's
  trace
- At flow scope outside a checkpoint, `run()` and `run_sync()` use a synthetic
  `llm_call` checkpoint
- `hitl_tool(...)` is a tool marker/decorator that bridges tool-time approvals
  back to flow-level `wait(...)` — it is not the wait primitive itself
- Tool capture modes are `full`, `metadata_only`, and `off`
- Per-tool capture overrides are supported
- MCP toolsets are supported and wrapped (via `KitaruMCPToolset`)
- Deferred tool flows (`ApprovalRequired`, `CallDeferred`) are not supported;
  prefer `hitl_tool(...)` or an explicit flow-level `wait(...)` instead
- Only `run()` and `run_sync()` are explicitly synthetic-checkpointed at flow
  scope; do not assume `iter()` behaves identically

Safe default pattern: wrap the agent once at module scope, then call it inside
an explicit outer checkpoint with `type="llm_call"`. This gives you the clearest
replay boundary.

```python
from kitaru import checkpoint, flow
from kitaru.adapters import pydantic_ai as kp

agent = kp.wrap(
    Agent(model, tools=[...]),
    tool_capture_config={"mode": "full"},
)

@checkpoint(type="llm_call")
def run_agent(prompt: str) -> str:
    return agent.run_sync(prompt).output

@flow
def my_flow(topic: str) -> str:
    return run_agent(f"Research {topic}")
```

## Common mistakes checklist

- Calling `my_flow(...)` directly instead of `my_flow.run(...)`
- Putting `wait()` inside a checkpoint
- Nesting checkpoint calls
- Returning non-serializable values from checkpoints
- Calling `llm()` outside a `@flow`
- Using vague or duplicate checkpoint / wait names that make replay selectors
  hard to target
- Reusing artifact names so `load()` becomes ambiguous
- Using `wait.*` override keys in replay (they are not supported)
- Assuming CLI, client, and MCP expose the same operation set
- Using `KitaruClient` to launch new executions (it's for
  inspection/control only)
- Using `connect(...)` and expecting managed workspace support (use
  `kitaru login` for that)
- Using SDK `create_stack(...)` for remote stacks (it's local-only; use
  CLI/MCP)
- Reaching for deferred PydanticAI tools even though they are unsupported here
- Wrapping every tiny helper in a checkpoint instead of using meaningful replay
  boundaries
- Wrapping the PydanticAI agent inside the checkpoint function instead of at
  module scope
- Using `type="agent_turn"` on a PydanticAI checkpoint instead of
  `type="llm_call"` (the shipped example pattern)
