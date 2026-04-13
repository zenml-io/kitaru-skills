---
name: kitaru-authoring
description: >
  Guide for writing Kitaru durable workflows, durable shared memory, and
  operational control paths. Use when creating or refactoring Kitaru flows,
  checkpoints, waits, logging, artifacts, `kitaru.memory`,
  `KitaruClient.memories`, tracked LLM calls, replay/resume/retry flows,
  KitaruClient usage, CLI commands, MCP operations, or PydanticAI adapter
  integrations. Triggers on mentions of kitaru, @flow, @checkpoint,
  kitaru.wait, kitaru.log, kitaru.save, kitaru.load, kitaru.memory,
  memory.configure, memory.get, memory.set, memory.list, memory.history,
  memory.delete, KitaruClient, KitaruClient.memories, replay, resume, retry,
  `kitaru executions ...`, `kitaru memory ...`, MCP tools,
  `kitaru_memory_*`, `wrap(...)`, or `hitl_tool(...)`.
---

# Kitaru Authoring Skill

Use this guide when writing or refactoring Kitaru workflows and when choosing
which Kitaru surface to use for running, observing, replaying, controlling, or
persisting durable state for those workflows.

> **Before building**: If the workflow shape is still fuzzy, suggest the
> `kitaru-scoping` skill first. It helps the user decide whether Kitaru is a
> fit, where checkpoints and waits belong, whether memory or artifacts should
> hold shared state, and which replay anchors should be stable before code gets
> written.

## Mental model

Think of a Kitaru flow like a long trip with named save points and a shared
cabinet of durable facts.

- `@flow` is the durable outer boundary.
- `@checkpoint` is a replay boundary inside that flow.
- `wait()` pauses at the flow level and resumes later with input.
- Replay reruns from the top, but checkpoints before the selected replay point
  return cached outputs instead of doing the work again.
- Artifacts are boxes tied to a specific execution or checkpoint.
- Memory is the shared cabinet: durable values stored under stable
  `scope_type + scope + key` names.
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
5. `kitaru.memory.*` is allowed in the flow body but forbidden inside a
   checkpoint.
6. Outside a flow, configure an active scope before using `memory.get()`,
   `memory.set()`, `memory.list()`, `memory.history()`, or `memory.delete()`;
   `memory.configure(scope=...)` defaults to `scope_type="namespace"`.
7. The module-level `kitaru.memory` API uses the active configured typed scope;
   it does not take per-call `scope=` or `scope_type=` arguments.
8. `log()` works in flow scope and checkpoint scope, but it attaches metadata to
   different targets depending on where it runs.
9. Checkpoint outputs must be serializable.
10. `.submit()`, `.map()`, and `.product()` are for work launched from inside a
    running flow.
11. `llm()` is valid only inside a `@flow`; outside a checkpoint it gets a
    synthetic `llm_call` checkpoint automatically.
12. Use stable, unique names for checkpoints, waits, artifacts, memory scopes,
    and important memory keys so replay and operations stay unambiguous.

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

### `memory`

Use `kitaru.memory` for durable shared state addressed by stable keys within one
active configured typed scope (`scope_type` + `scope`).

Public module-level API:

- `memory.configure(scope: str | None = None, *, scope_type: "namespace" | "flow" | "execution" | None = None)`
- `memory.set(key, value)`
- `memory.get(key, *, version=None)`
- `memory.list()`
- `memory.history(key)`
- `memory.delete(key)`

Key behavior to teach correctly:

- Valid in the flow body
- Invalid inside checkpoints
- Inside a flow, the default scope is the active flow identity unless you
  configured a different active scope. Operator surfaces may expose that flow
  identity as a flow ID, so use execution details or `memory scopes` to find
  the exact external scope value.
- Outside a flow, configure an active scope first; `memory.configure(scope=...)`
  defaults to `scope_type="namespace"`
- `memory.configure(scope_type="namespace")` still requires an explicit
  `scope=...`, while `scope_type="flow"` and `scope_type="execution"` can only
  be inferred inside a `@flow`
- The module API uses the active typed scope; do not invent per-call `scope=` or
  `scope_type=` support
- In flow code, reads like `memory.get()` behave like runtime step outputs, so
  keep memory calls in the flow body and pass their results into checkpoints
  when you need normal Python logic
- Deletes are soft deletes, so `history(...)` includes tombstones
- Maintenance operations are **not** module-level APIs: do not invent
  `memory.compact()`, `memory.purge()`, `memory.purge_scope()`,
  `memory.compaction_log()`, or `memory.reindex()`
- Replay is not fully memory-frozen: replays may observe newer values, and
  replayed writes create new versions

A good pattern is to keep the memory calls in the flow body, then pass the
result into a checkpoint when you want normal Python logic:

```python
from kitaru import checkpoint, flow, memory

@checkpoint
def increment_runs(previous_runs: int | None) -> int:
    return (previous_runs or 0) + 1

@flow
def research_agent(topic: str) -> None:
    previous_runs = memory.get("stats/run_count")
    updated_runs = increment_runs(previous_runs)
    memory.set("stats/run_count", updated_runs)
    memory.set("last_topic", topic)
```

Outside a flow, configure first:

```python
from kitaru import memory

memory.configure(scope="repo_docs", scope_type="namespace")
memory.set("style/release_notes", {"tone": "concise"})
```

Switch to `KitaruClient.memories` when you need explicit typed-scope
administration, prefix filtering, scope listing, maintenance operations, or
memory inspection outside the active-scope module model.

Maintenance lives on `KitaruClient`, CLI, and MCP surfaces:

- `compact` sends selected memory values to an LLM and writes the summary as a
  new memory version; it does not delete source entries. Single-key compaction
  defaults to `source_mode="current"`, can use `source_mode="history"`, and
  multi-key compaction summarizes current values into a required target key.
- `purge` / `purge_scope` physically delete old versions; delete is only a
  tombstone.
- `compaction_log` reads compact/purge audit records.
- `reindex` is project-scoped, dry-run by default, additive tag backfill for
  historical memory discovery; it does not rewrite memory values.
- `compact` uses an LLM, so make sure a default model or explicit `model=` /
  `--model` is available.

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
- Use `wait`, `log`, `save`, `load`, `llm`, `memory.configure`, `memory.set`,
  `memory.get`, `memory.list`, `memory.history`, `memory.delete`
- Use `configure(...)`, `connect(server_url, ...)`, `list_stacks()`,
  `current_stack()`, `use_stack()`, `create_stack(...)` (**local stacks only**),
  `delete_stack(...)`
- Launch executions: `flow.run(...)`, `flow.replay(...)`

### KitaruClient (execution control + explicit memory/artifact inspection)

The client is for **managing existing executions** and for **explicit typed-scope
memory/artifact administration**, not for launching new executions.

- `executions.get / list / latest / logs / pending_waits / input / abort_wait /
  retry / resume / replay / cancel`
- `artifacts.list / get`
- `memories.get / list(prefix=...) / history / set / delete / scopes / purge /
  purge_scope / compact / compaction_log / reindex`
  - Scoped memory calls require explicit `scope=` and `scope_type=`.
  - `get(..., version=...)` supports versioned reads.
  - `compact`, `purge`, `purge_scope`, and `compaction_log` are typed-scope
    maintenance operations.
  - `reindex(apply=False)` is project-scoped, dry-run by default, and backfills
    missing memory discovery tags for historical data.
  - `memories.get(...)`, `list(...)`, and `history(...)` return memory-entry
    metadata; load values with
    `client.artifacts.get(entry.artifact_id).load()`. Module-level
    `memory.get(...)` returns the stored value directly.

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
- `memory scopes`; `memory list/get/set/delete/history`; `memory compact`;
  `memory purge`; `memory purge-scope`; `memory compaction-log`;
  `memory reindex`
  - All scoped memory commands require both `--scope` and `--scope-type`.
  - `memory scopes` and `memory reindex` are unscoped/project-scoped commands.
  - `memory set` parses JSON when possible; otherwise it stores the raw string.
  - CLI memory does not expose versioned `get` or prefix-filtered `list`.
  - `memory compact` summarizes selected memory values with an LLM and writes a
    new memory version; it may need a configured default model or `--model`.
  - `memory purge` physically deletes old versions of one key.
  - `memory purge-scope` physically deletes old versions across a scope;
    `--include-deleted` also removes tombstoned keys.
  - `memory compaction-log` reads compact/purge audit records.
  - `memory reindex` is dry-run by default; use `--apply` to persist missing
    discovery tags.
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
- `kitaru_memory_list`, `kitaru_memory_get`, `kitaru_memory_set`,
  `kitaru_memory_delete`, `kitaru_memory_history`
- `kitaru_memory_compact`, `kitaru_memory_purge`,
  `kitaru_memory_purge_scope`, `kitaru_memory_compaction_log`
  - MCP memory tools use explicit typed scopes: every scoped memory tool takes
    `scope` and `scope_type`.
  - `kitaru_memory_get` supports `version`; `kitaru_memory_list` supports
    `prefix`.
  - MCP does not expose memory scope listing or memory reindexing.
- `kitaru_status`, `kitaru_stacks_list`
- `manage_stack` (create/delete; supports `local`, `kubernetes`, `vertex`,
  `sagemaker`, `azureml`, plus `extra` and `async_mode`)

### Key asymmetries

| Capability | SDK | KitaruClient | CLI | MCP |
|---|---|---|---|---|
| Launch new execution | Yes (flow object / Python entrypoint) | No | No top-level run command | Yes (`kitaru_executions_run`) |
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

### Memory-specific asymmetries

| Memory capability | SDK `kitaru.memory` | KitaruClient | CLI | MCP |
|---|---|---|---|---|
| In-flow memory reads/writes | Yes | No | No | No |
| Outside-flow seed/update | Yes, after `memory.configure(...)` | Yes | Yes | Yes |
| Active-scope Python API | Yes | No | No | No |
| Explicit typed-scope admin (`scope` + `scope_type`) | No | Yes | Yes | Yes |
| List memory scopes | No | Yes (`memories.scopes()`) | Yes (`kitaru memory scopes`) | No |
| Read a specific version | Yes (`memory.get(version=...)`) | Yes | No | Yes |
| Prefix-filter a list | No | Yes (`memories.list(..., prefix=...)`) | No | Yes |
| Compact memory | No | Yes | Yes | Yes |
| Purge one key | No | Yes | Yes | Yes |
| Purge a whole scope | No | Yes | Yes | Yes |
| Read compaction/purge audit log | No | Yes | Yes | Yes |
| Reindex historical memory tags | No | Yes (`reindex(apply=False)`) | Yes (`kitaru memory reindex`) | No |

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
- Calling `memory.*` inside a checkpoint
- Passing `scope=` or `scope_type=` to module-level `kitaru.memory` calls even
  though the module API uses the active configured typed scope
- Forgetting to configure an active scope before module-level memory use outside
  flows; `memory.configure(scope=...)` defaults to `scope_type="namespace"`
- Describing memory identity as only a `scope` when the operation requires
  `scope_type + scope + key`
- Forgetting `--scope-type` on CLI memory commands
- Assuming CLI or MCP memory commands infer a default scope
- Assuming MCP can list memory scopes or run memory reindexing
- Trying to call maintenance operations on module-level `kitaru.memory`
- Assuming `compact` deletes source entries; it writes a summary, then `purge`
  is a separate hard-delete step
- Treating `delete` and `purge` as interchangeable: delete writes a tombstone;
  purge physically removes versions
- Treating `KitaruClient.memories.get(...)` as the raw stored value rather than
  entry metadata
- Using invalid memory keys/scopes; use letters, numbers, `.`, `_`, `-`, and
  `/`, and avoid `:`
- Using memory for execution-linked outputs that should be explicit artifacts
- Assuming memory is replay-deterministic across replays
- Nesting checkpoint calls
- Returning non-serializable values from checkpoints
- Calling `llm()` outside a `@flow`
- Using vague or duplicate checkpoint / wait names that make replay selectors
  hard to target
- Reusing artifact names so `load()` becomes ambiguous
- Reusing unstable memory scope or key names so operators cannot inspect state
  later
- Using `wait.*` override keys in replay (they are not supported)
- Assuming CLI, client, and MCP expose the same operation set
- Using `KitaruClient` to launch new executions (it's for
  inspection/control/memory admin only)
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
