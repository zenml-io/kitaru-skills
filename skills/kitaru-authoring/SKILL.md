---
name: kitaru-authoring
description: >
  Guide for writing Kitaru durable workflows and operational control paths. Use
  when creating or refactoring Kitaru flows, checkpoints, waits, logging,
  artifacts, tracked LLM calls, replay/resume/retry flows, KitaruClient usage,
  CLI commands, MCP operations, deployments, secrets, or adapter integrations
  for PydanticAI, OpenAI Agents, LangGraph, Claude Agent SDK, and Gemini
  Interactions. Triggers on mentions of kitaru, @flow, @checkpoint,
  kitaru.wait, kitaru.log, kitaru.save, kitaru.load, KitaruClient, replay,
  resume, retry, `kitaru executions ...`, MCP tools, `KitaruAgent`,
  `KitaruRunner`, `KitaruGraphRunner`, `KitaruClaudeRunner`,
  `KitaruGeminiInteractionsRunner`, `GeminiInteractionRequest`,
  `wait_for_input`, `wait_for_approval`, `wait_for_interrupt`,
  `requires_action`, Antigravity, or migration from deprecated `wrap(...)`.
---

# Kitaru Authoring Skill

Use this guide when writing or refactoring Kitaru workflows and when choosing
which Kitaru surface to use for running, observing, replaying, controlling,
deploying, or inspecting durable artifacts and external state references for
those workflows.

> **Before building**: If the workflow shape is still fuzzy, suggest the
> `kitaru-scoping` skill first. It helps the user decide whether Kitaru is a
> fit, where checkpoints and waits belong, which values should become explicit
> artifacts, and which replay anchors should be stable before code gets written.

## Mental model

Think of a Kitaru flow like a long trip with named save points and labeled boxes for durable outputs.

- `@flow` is the durable outer boundary.
- `@checkpoint` is a replay boundary inside that flow.
- `wait()` pauses at the flow level and resumes later with input.
- Replay reruns from the top, but checkpoints before the selected replay point
  return cached outputs instead of doing the work again.
- Artifacts are labeled boxes tied to a specific execution or checkpoint.
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
   operations stay unambiguous.
10. Use artifacts for execution-linked values and external/application-owned
    stores for mutable cross-execution state.

## Primitive reference

### `@flow`

Use `@flow` for the durable orchestration boundary.

- Supported decorator overrides: `stack`, `image`, `cache`, `retries`
- Main entrypoints:
  - `.run(...)` — pass `stack="..."` to target a remote stack
  - `.replay(exec_id, at=..., flow_overrides=..., checkpoint_overrides=..., invocation_overrides=..., skip=..., tag=..., wait=..., on_error=...)`
- Use `current_execution_id()` inside a running flow/checkpoint when code needs
  to record or pass along the active execution ID. It returns `None` outside a
  Kitaru execution.

### `@checkpoint`

Use `@checkpoint` for meaningful replayable units of work.

- Supported decorator args: `retries`, `type`, `cache`
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

### Durable state beyond one execution

Kitaru's current shipped public surface does not include a native key-value
state API. If a workflow needs information to survive across executions, choose
one of these explicit patterns instead:

- Save execution-linked values with `save(...)` inside checkpoints and inspect
  them later through `KitaruClient.artifacts` or MCP artifact tools.
- Pass upstream execution IDs into downstream flows when one flow needs to load
  another flow's artifacts.
- Store global preferences, configuration, or mutable application data in an
  external system such as a database, object store, repository file, or service
  API.
- Use Kitaru secrets for sensitive configuration and `llm(...)` aliases, not for
  arbitrary workflow state.

Do not invent SDK helpers, CLI commands, or MCP tools for native durable
key-value state. When replay correctness matters, make the critical value an
explicit checkpoint output or saved artifact so the exact value from the source
execution remains inspectable.

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

All replay entrypoints return the shared `ReplaySubmission` model.

- SDK flow object: `flow.replay(exec_id, at=..., flow_overrides=..., checkpoint_overrides=..., invocation_overrides=..., skip=..., tag=..., wait=..., on_error=...)`
- Client: `KitaruClient().executions.replay(exec_id_or_ids, at=..., flow_overrides=..., checkpoint_overrides=..., invocation_overrides=..., skip=..., tag=..., wait=..., on_error=...)`
- CLI: `kitaru executions replay <exec_id> --at <selector> --flow-overrides '{...}' --checkpoint-overrides '{...}' --invocation-overrides '{...}'`
- MCP: `kitaru_executions_replay`

### Replay selector and override rules

`at` targets one recorded checkpoint invocation, tool call, model call, or an
unambiguous checkpoint name. Wait selectors are not valid replay anchors.

Replay overrides are grouped by target:

- `flow_overrides` / `--flow-overrides` — top-level flow parameters for the
  replay run.
- `checkpoint_overrides` / `--checkpoint-overrides` — every invocation of a
  checkpoint name.
- `invocation_overrides` / `--invocation-overrides` — one recorded invocation ID
  or call ID.

Checkpoint and invocation overrides can use these fields:

- `input` — replace the target inputs, then rerun that target and downstream
  checkpoints.
- `output` — inject a value as the target output; the target checkpoint does not
  run.
- `code` — import a replacement callable for the target when it reruns.
- `model` — change the model for supported LLM checkpoint calls only.

`skip` can force a recorded invocation or call to reuse its saved output even
though it is at or after `at`. Do not both skip and override the same target.

`wait.*` overrides are **not supported**. If the replayed execution reaches a
wait, resolve it via `client.executions.input(...)`,
`kitaru executions input`, or `kitaru_executions_input`.

Do not invent alternate replay APIs, flat `overrides=...`, old `from_` / `--from`
selectors, or `checkpoint.<selector>` override namespaces.

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
- Use `wait`, `log`, `save`, `load`, and `llm`
- Use `configure(...)`, `connect(server_url, ...)`, `list_stacks()`,
  `current_stack()`, `use_stack()`, `create_stack(...)` (**local stacks only**),
  `delete_stack(...)`
- Use `create_secret(...)`, `delete_secret(...)`, and `get_secret(...)` for
  Kitaru-native secret writes/reads
- Use `current_execution_id()` inside active runs when code needs the execution
  ID for downstream references
- Launch executions: `flow.run(...)`, `flow.replay(...)`

### KitaruClient (execution control + artifact inspection)

The client is for **managing existing executions** and for **artifact
inspection**, not for launching new executions.

- `executions.get / list / latest / logs / pending_waits / input / abort_wait /
  retry / resume / replay / cancel`
- `artifacts.list / get`
- Deployment inspection/invocation helpers where supported by the active server
- Auth management namespaces for service accounts and API keys

### CLI

- `login`, `logout`, `status`, `info` (`--all`, `--file`, JSON/YAML export)
- `clean project / global / all` for safe local-state reset (`--dry-run` first)
- `analytics opt-in / opt-out / status`
- `auth token` for a short-lived bearer token from the active connection
- `log-store set / show / reset`
- `stack list / current / show / use / create / delete`
  - `stack create` supports `local`, `kubernetes`, `vertex`, `sagemaker`,
    `azureml` (remote stack creation is CLI/MCP only, not available in the
    Python SDK `create_stack()`)
  - Advanced: `--extra` for component overrides, `--async` for async
    provisioning
- `model register / list`
- `secrets set / show / list / delete`
- `build`, `deploy`, `invoke`, `flow deployments list/show/delete/logs/curl`, and `flow tag` / `flow untag`
- `executions get / list / latest / statistics / logs / input / replay / cohort`
  (dry-run replay selection) / `diff / diff-matrix / retry / resume / cancel`
- List commands use `--page` / `--size` pagination where documented; `--limit`
  is a first-page shortcut for compatible lists
- JSON output contract: `--output json` / `-o json` emits
  `{command, item}` for single-item commands, `{command, items, count}` for
  lists, and JSONL event objects for `executions logs --follow --output json`

### MCP tools (exact names)

- `kitaru_executions_list`, `kitaru_executions_get`, `kitaru_executions_latest`,
  `kitaru_executions_statistics`
- `get_execution_logs`
- `kitaru_executions_run` (target format: `<module_or_file>:<flow_name>`)
- `kitaru_executions_input`, `kitaru_executions_retry`,
  `kitaru_executions_replay`, `kitaru_executions_cohort`,
  `kitaru_executions_diff`, `kitaru_executions_diff_matrix`,
  `kitaru_executions_cancel`
- `kitaru_deployments_deploy`, `kitaru_deployments_invoke`,
  `kitaru_deployments_list`, `kitaru_deployments_get`,
  `kitaru_deployments_delete`, `kitaru_deployments_tag`,
  `kitaru_deployments_untag`
- `kitaru_artifacts_list`, `kitaru_artifacts_get`
- `kitaru_secrets_create` (metadata-only secret creation; no MCP delete tool)
- `kitaru_start_local_server`, `kitaru_stop_local_server`, `kitaru_status`,
  `kitaru_stacks_list`
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
| Deploy flow version | No (use CLI/server APIs) | Limited deployment namespace | Yes | Yes |
| Invoke deployment | No (use deployment endpoint/client) | Yes | Yes | Yes |
| Create secret | Yes | No | Yes | Yes (metadata only) |
| Delete secret | Yes | No | Yes | No |
| Print auth token / curl command | No | No | Yes | No |
| Clean/reset local state | No | No | Yes | No |

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
- `create_secret(...)` / `delete_secret(...)` are the Python SDK write helpers;
  `kitaru_secrets_create` is the MCP metadata-only create path
- `kitaru auth token` prints a short-lived bearer token for raw HTTP calls
- `kitaru flow deployments curl FLOW` generates a copy-pasteable curl command
  that starts a deployment execution without inlining real token values

## Adapter reference

Use adapters when the agent framework already owns an inner runtime. Kitaru then
needs a clear seam where it can put durable checkpoints without pretending to
control side effects it cannot see.

### PydanticAI / `KitaruAgent`

Public surface to reach for in new code:

- `KitaruAgent(agent, *, name=None, capture=CapturePolicy(...), granular_checkpoints=True, ...)`
- `CapturePolicy(tool_capture="full" | "metadata" | None, tool_capture_overrides={...})`
- `wait_for_input(...)` and `hitl_tool(...)` for human input from tool context
- `KitaruToolset`, `KitaruFunctionToolset`, `KitaruMCPServer`,
  `kitaruify_toolset(...)`, and `kitaruify_mcp_server(...)` for lower-level
  durable tool surfaces

`wrap(...)` is still exported only as a deprecated compatibility shim. Do not
show it as the normal path for new code.

Key implementation rules:

- The wrapped PydanticAI agent must have a concrete model at construction time.
- Default granular mode creates separate model/tool/MCP checkpoints.
- `granular_checkpoints=False` switches to one turn checkpoint per agent run.
- Inside your own `@checkpoint`, `KitaruAgent` runs as a passthrough so the
  explicit checkpoint is the replay boundary.
- `wait_for_input(...)` is a wrapper around `kitaru.wait(...)`; it still has to
  create the wait at flow scope. In granular mode, opt regular waiting tools out
  with `tool_checkpoint_config_by_name={"tool_name": False}` or use
  `@hitl_tool` for pure wait tools.
- Capture policy is observability-only. Current tool capture values are
  `"full"`, `"metadata"`, or `None`.
- `run_stream()` and `iter()` return context managers and need explicit
  checkpointing; streamed turns can fall back from granular to turn behavior.

Safe default pattern for explicit flows:

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import CapturePolicy, KitaruAgent

agent = Agent("openai:gpt-4o", name="researcher")
durable_agent = KitaruAgent(
    agent,
    capture=CapturePolicy(tool_capture="full"),
)

@kitaru.checkpoint
def run_agent(prompt: str) -> str:
    return durable_agent.run_sync(prompt).output

@kitaru.flow
def my_flow(topic: str) -> str:
    return run_agent(f"Research {topic}")
```

### OpenAI Agents / `KitaruRunner`

Use `KitaruRunner` for OpenAI Agents SDK agents.

- `checkpoint_strategy="runner_call"` places one checkpoint around the outer
  runner call. Prefer it when the flow needs a clean `.wait()` return value.
- `checkpoint_strategy="calls"` is the default granular mode: supported
  model/tool calls become separate checkpoints. This is useful for fine replay,
  but it can create multiple terminal checkpoints, so `flow.run(...).wait()` may
  raise the ambiguous-result error. Inspect artifacts/UI/client output instead,
  or choose `runner_call`.
- `OpenAIRunRequest.start(...)` and `OpenAIRunRequest.resume(...)` carry start
  and resume state.
- `wait_for_approval(...)` bridges an interrupted OpenAI run into a normal
  flow-scope Kitaru wait and returns a resume request.
- `OpenAICapturePolicy` controls saved input/output/run-state/interruption/usage
  details. Use tool checkpoint overrides for side-effectful tools.
- `calls` mode must run at flow scope, not inside another checkpoint.

### LangGraph / `KitaruGraphRunner`

Use `KitaruGraphRunner` for LangGraph graphs and LangChain/Deep Agents objects
that behave like LangGraph runnables.

- `checkpoint_strategy="graph_call"` is the default coarse boundary: one Kitaru
  checkpoint per outer `invoke(...)` / `ainvoke(...)` call.
- `checkpoint_strategy="calls"` creates true sync model/tool checkpoints only
  when `KitaruLangGraphMiddleware` wraps the LangChain handler call. Callbacks
  and event streams are trace-only; they are not replay boundaries.
- Async calls mode is metadata-only today. `async_checkpoint_policy` is not a
  hidden switch for true async checkpoints.
- LangGraph checkpointers and stores remain LangGraph-owned. If examples use
  `InMemorySaver`, treat it as a local LangGraph checkpointer, not durable
  Kitaru state.
- `wait_for_interrupt(...)` bridges LangGraph interrupts to flow-scope
  `kitaru.wait(...)` and returns a resume request.
- `LangGraphCapturePolicy` defaults to metadata-first summaries; saving full
  state values can persist prompts, tool outputs, or customer data.

### Claude Agent SDK / `KitaruClaudeRunner`

Use `KitaruClaudeRunner` when one Claude SDK invocation should be durable.

- `checkpoint_strategy="invocation"` is the only supported strategy and is the
  default. `"calls"`, `"runner_call"`, `"model_call"`, and `"tool_call"` are
  rejected because the adapter does not provide granular Claude-internal replay.
- Put `runner.run(...)` / `runner.run_sync(...)` directly in the flow body so the
  adapter can create its invocation checkpoint. Calling from inside an existing
  checkpoint is rejected unless you explicitly opt into direct execution and
  accept replay risk.
- `ClaudeRunRequest` carries prompt/options such as cwd, session resume ID, and
  max turns. `ClaudeCapturePolicy` controls saved messages/transcripts/usage and
  manifest details.
- Claude session resume and Claude file checkpointing are Claude SDK concepts.
  Kitaru replay can skip a completed Claude invocation, but it does not recreate
  arbitrary workspace files, Bash side effects, MCP side effects, hooks, or
  custom-tool side effects made inside Claude's loop.
- If a side effect must be durable, make it a separate Kitaru checkpoint after
  Claude returns.

### Gemini Interactions / `KitaruGeminiInteractionsRunner`

Use `KitaruGeminiInteractionsRunner` when one stable Gemini Interactions
response should be durable. Use the public module `kitaru.adapters.gemini` and
keep the user-facing adapter name as Gemini Interactions. Treat Antigravity as a
managed-agent/preset use case, not as the core adapter identity.

- `checkpoint_strategy="interaction"` is the supported boundary: one stable
  Gemini interaction response becomes one Kitaru checkpoint. Stable statuses are
  `completed` and `requires_action`.
- `GeminiInteractionRequest.start(...)`, `.resume(...)`, `.function_result(...)`,
  `.poll(...)`, and `.antigravity(...)` describe the interaction turn. Poll an
  existing unfinished interaction by ID instead of creating a duplicate job.
- Treat `requires_action` as a handoff back to the Kitaru flow. Run local tool
  work or `kitaru.wait(...)` at flow scope, then send a later
  `function_result` request.
- Google-owned hosted tools, MCP, web/code execution, managed-agent steps, and
  Antigravity sandbox/environment/filesystem internals are not granular Kitaru
  checkpoints.
- Use `cache_identity` when project, region, credentials, or client
  configuration can change what the same logical request means.
- Review `GeminiInteractionCapturePolicy` before saving raw prompts, provider
  payloads, steps, or outputs, because those values can contain user data.

## Common mistakes checklist

- Calling `my_flow(...)` directly instead of `my_flow.run(...)`
- Putting `wait()` inside a checkpoint
- Nesting checkpoint calls
- Returning non-serializable values from checkpoints
- Calling `llm()` outside a `@flow`
- Using vague or duplicate checkpoint / wait names that make replay selectors
  hard to target
- Reusing artifact names so `load()` becomes ambiguous
- Treating Kitaru as a durable key-value store instead of using artifacts or an
  external store
- Using old replay APIs: `from_=...`, `--from`, flat `overrides=...`, or
  `--override checkpoint.*` examples
- Using `wait.*` override keys in replay (they are not supported)
- Assuming CLI, client, and MCP expose the same operation set
- Using `KitaruClient` to launch new executions (it's for
  inspection/control only)
- Using `connect(...)` and expecting managed workspace support (use
  `kitaru login` for that)
- Using SDK `create_stack(...)` for remote stacks (it's local-only; use
  CLI/MCP)
- Recommending deprecated PydanticAI `wrap(...)` for new code instead of
  `KitaruAgent(...)`
- Using legacy PydanticAI capture modes `metadata_only` or `off` instead of
  `"metadata"` or `None`
- Putting adapter wait helpers inside checkpoint-contained tool bodies without a
  flow-scope bridge or tool-checkpoint opt-out
- Expecting OpenAI Agents `checkpoint_strategy="calls"` to produce one clean
  `.wait()` result
- Wrapping an OpenAI `calls` runner call inside your own checkpoint
- Treating LangGraph callbacks or event streams as Kitaru replay boundaries
- Treating LangGraph `InMemorySaver` as durable cross-process storage
- Expecting Claude Agent SDK `KitaruClaudeRunner` to replay Claude-internal Bash,
  MCP, custom-tool, hook, permission, or workspace side effects granularly
- Treating Gemini hosted tools, MCP, web/code execution, managed-agent steps, or
  Antigravity sandbox/filesystem internals as granular Kitaru checkpoints
- Hiding Gemini `requires_action` work inside the provider-owned interaction
  instead of returning local tool or human work to Kitaru flow scope
- Assuming Antigravity remote environments provide Kitaru-owned filesystem
  durability or replayable sandbox state
- Wrapping every tiny helper in a checkpoint instead of using meaningful replay
  boundaries
- Constructing adapter wrappers inside hot checkpoint functions when module-scope
  construction is clearer and stable
