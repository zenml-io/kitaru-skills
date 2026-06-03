# OpenAI Agents SDK to Kitaru Concept Map

Use this map while classifying source code. The safe migration story is simple:
keep the OpenAI Agents SDK agent, replace the runner doorway, and flag anything
Kitaru cannot safely see or replay.

## Mapping labels

- `direct`: Kitaru has a close adapter surface for the same behavior.
- `approximate`: Migration is possible, but behavior, observability, replay, or
  configuration differs.
- `absent`: No safe automatic migration. The code needs redesign or explicit
  human review before migration.

## Core concepts

| OpenAI Agents source pattern | Kitaru target pattern | Mapping | Notes |
|---|---|---:|---|
| `agents.Agent(name=...)` | Same agent passed to `KitaruRunner(agent)` | `direct` | Keep the SDK agent definition. Kitaru changes execution entrypoint, not the agent internals. |
| `Runner.run_sync(agent, input)` | `runner.run_sync(OpenAIRunRequest.start(input))` | `direct` | Requires `runner = KitaruRunner(agent, ...)`. |
| `await Runner.run(agent, input)` | `await runner.run(OpenAIRunRequest.start(input))` | `direct` | Use async runner in async code. |
| `Runner.run_sync(...)` inside async code or active event loop | `await KitaruRunner.run(...)` | `absent` for sync call | Do not migrate by keeping sync execution. Convert caller to async or restructure. |
| `max_turns=` on raw runner call | `OpenAIRunRequest.start(input, max_turns=...)` | `direct` | Keep turn limit with the serializable request. |
| `metadata=` intended for run/checkpoint metadata | `OpenAIRunRequest.start(input, metadata=...)` | `direct` | Do not confuse this with SDK runtime `context=`. |
| `final_output` use | `OpenAIRunResult.final_output` after status check | `direct` | Check `result.status == "completed"` first if interruptions are possible. |
| `RunConfig(...)` passed to raw runner | `run_config_factory=lambda: RunConfig(...)` | `approximate` | Factory recreates config for Kitaru-managed runs. Avoid capturing volatile values. |
| `checkpoint_strategy="runner_call"` | One Kitaru checkpoint around outer runner call | `approximate` | Best when `.wait()` should return one clean result. Less inner observability. |
| `checkpoint_strategy="calls"` | Per supported model/local-tool checkpoints | `approximate` | Better replay granularity. `.wait()` can be ambiguous because there is no single terminal artifact. |
| Local `@function_tool` | Adapter-wrapped `FunctionTool` in calls mode | `direct` for supported tools | Still review side effects. Kitaru can replay a tool checkpoint; the external world may not be idempotent. |
| Tool guardrails on local tools | OpenAI Agents SDK-owned guardrail behavior, with only adapter-visible runner/model/local-tool events captured | `approximate` | Do not promise full guardrail internals. Verify current adapter behavior before claiming blocked-attempt observability. |
| Hosted/native tools | Provider-owned behavior | `approximate` or `absent` | Kitaru cannot see provider internals as local checkpoints. Treat as outer-run behavior unless redesigned. |
| Handoffs between SDK agents | Same SDK handoff behavior under `KitaruRunner` | `approximate` | The SDK still owns handoff decisions. Raw nested runner calls need separate Kitaru runners. |
| Raw nested `agents.Runner.run(...)` in guardrail/tool/helper | Separate `KitaruRunner` for nested agent, or leave raw and flag | `approximate` or `absent` | Raw nested calls are outside Kitaru unless explicitly wrapped. |
| SDK interruption for human approval | `OpenAIRunResult(status="interrupted")` | `approximate` | Requires explicit status branch. Do not treat as completed output. |
| Manual approval/resume | `wait_for_approval(...)` or `build_resume_request(...)` | `approximate` | Keep bridge at flow scope. Resume is SDK-version-sensitive. |
| `context=...` with simple JSON-like data | Same `context=` plus stable `context_cache_identity` | `approximate` | Context is SDK runtime state, not Kitaru metadata. |
| Object-heavy `context=...` | Add `context_serializer`, `context_deserializer`, and `context_cache_identity` | `absent` until configured | Needed for interrupted/resumed SDK state and safe cache separation. |
| Tenant/user/thread-sensitive context | `context_cache_identity=lambda ctx: {...}` | `approximate` | Include stable authorization and settings fields; exclude per-run trace/message cursors. |
| Missing stable agent or runner name | Add explicit stable `name=` or stable runner naming | `absent` until fixed | Generated or missing names make replay/debugging hard. |
| Non-serializable result/state returned from checkpoint | Return `OpenAIRunResult`, simple values, or external artifact references | `absent` until redesigned | Kitaru checkpoint outputs must be serializable. |
| Tool side effects without idempotency | Explicit side-effect boundary and idempotency key | `approximate` or `absent` | Example bad outcome: replay sends the Slack message twice. |
| API keys as flow parameters, metadata, or logs | Use environment variables or Kitaru secrets; keep out of artifacts | `absent` until fixed | Never persist secrets as user-visible flow input or metadata. |
| `runtime="isolated"` adapter request | Do not use isolated runtime for this adapter | `absent` | Adapter rejects isolated runtime. Use supported runtime path. |

## Boundary decision guide

Choose `runner_call` when:

- The user wants `flow.run(...).wait()` to return the agent result directly.
- One durable checkpoint around the whole agent turn is enough.
- Approval/resume handling should be straightforward at flow scope.

Choose `calls` when:

- The user values per-model/per-local-tool artifacts.
- The workflow can tolerate retrieving artifacts through Kitaru UI/client instead
  of relying on one `.wait()` return.
- Tool guardrail observability matters.

Do not choose `calls` when:

- The runner call is already inside a Kitaru checkpoint.
- The user expects a single clean `.wait()` value and does not want to handle
  `KitaruAmbiguousFlowResultError`.

## What Kitaru does not own

Kitaru does not own the provider's hosted tool internals, OpenAI's model-side
execution, SDK handoff internals, or arbitrary nested raw runner calls. If the
source code depends on those internals being replayed as separate Kitaru units,
mark the mapping `absent` or `approximate` and explain the boundary clearly.
