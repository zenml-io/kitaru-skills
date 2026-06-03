# PydanticAI Migration Gaps and Flags

Use this file when source behavior is not a clean direct mapping. The report
should name the concrete risk, not just say "needs review".

## Severity levels

| Severity | Meaning | Required action |
|---|---|---|
| `LOW` | Cosmetic or documentation-only difference. | Migrate and mention in report. |
| `MEDIUM` | Behavior probably preserved, but settings or observability differ. | Migrate with caveat and verification step. |
| `HIGH` | Replay, wait, state, side-effect, or runtime behavior may change. | Require human review before applying or mark partial migration. |
| `BLOCKER` | Migration would be unsafe or impossible without source redesign. | Do not auto-migrate; generate redesign note and report entry. |

## Must-flag patterns

| Source pattern | Severity | Why it matters | Safer action |
|---|---:|---|---|
| Regular sync tool body calls `wait_for_input(...)` without tool checkpoint opt-out | `BLOCKER` | A wait would be created from inside a synthetic tool checkpoint, which Kitaru rejects because waits must be flow-scope. | Add `tool_checkpoint_config_by_name={"tool": False}` plus `allow_sync_tool_body_waits=True`, or move the wait into flow code. |
| Regular sync tool body waits with opt-out and `allow_sync_tool_body_waits=True` | `HIGH` | Supported, but sync tool execution may run inline instead of PydanticAI's normal worker-thread path. | Migrate only with report caveat and verify concurrency/blocking behavior. |
| Native deferred tool behavior inside checkpointed tool bodies | `HIGH` | Deferred approval/call behavior must reach flow scope to resume cleanly. | Use `hitl_tool` for pure waits or opt that tool out of adapter tool checkpoints. |
| Missing stable `Agent(..., name=...)` | `BLOCKER` | Adapter-generated artifact, flow, and checkpoint names need stable names. Changing names later orphans old executions. | Add an explicit stable name before wrapping. |
| No concrete model at `Agent(...)` construction time | `BLOCKER` | `KitaruAgent` requires a bound model when it is constructed. | Bind the model in `Agent(...)`; create separate agents for separate models. |
| Per-run `model=` override | `BLOCKER` | The adapter does not support late model binding or per-run model swaps. | Create one named `Agent` / `KitaruAgent` pair per model. |
| `runtime="isolated"` in adapter checkpoint config | `BLOCKER` | Adapter-managed checkpoints currently reject isolated runtime. | Use inline runtime or move work to a user-authored checkpoint that supports the needed runtime. |
| Non-serializable checkpoint output | `BLOCKER` | Replay needs checkpoint outputs it can store and load. Raw clients, streams, file handles, or framework objects can fail serialization. | Return strings, dicts, Pydantic dumps, IDs, or explicit artifact references. |
| Hidden mutable module state | `HIGH` | Replay may see today's state, not the original run's state. | Pass state as flow input, save an artifact, or use an application-owned external store. |
| Provider/native side effects | `HIGH` | Kitaru cannot rewind hidden provider internals. Replay can duplicate emails, charges, file writes, or external API calls. | Move side effects into idempotent Kitaru checkpoints or add idempotency keys. |
| Auto-flow intended for remote stacks | `BLOCKER` | Auto-flow depends on in-process registration and is local-only. Remote workers cannot see that registration. | Add explicit `@kitaru.flow`. |
| `run_stream()` / `iter()` without explicit checkpoint | `BLOCKER` | Context-manager streaming cannot auto-open the needed checkpoint boundary. | Wrap stream collection in an explicit checkpoint or redesign stream side effects. |
| `event_stream_handler` with important external side effects | `HIGH` | Stream progress handlers may run again on replay or be skipped when cached. | Keep handlers idempotent or move important side effects after the final result. |
| `persist_message_history=True` used as durable memory | `HIGH` | History is stored on the Python `KitaruAgent` instance only. Restart, replay, or another process starts without it. | Persist `result.all_messages()` explicitly and pass `message_history=`. |
| Concurrent runs on one `persist_message_history=True` instance | `HIGH` | Instance-local history can race between conversations. | Use one `KitaruAgent` instance per conversation or explicit message histories. |
| Capture policy saves sensitive prompts/tool outputs by default | `MEDIUM` | Full observability can persist user content or tool payloads. | Set `CapturePolicy(save_prompts=False, tool_capture="metadata" or None, overrides=...)`. |
| `granular_checkpoints=True/False` legacy wording | `LOW` | Compatibility alias still works, but new docs use `checkpoint_strategy`. | Rewrite to `checkpoint_strategy="calls"` or `"turn"`. |
| Deprecated `kp.wrap(...)` / `wrap(...)` | `MEDIUM` | The shim still exists but emits deprecation guidance. | Replace with `KitaruAgent(...)` and map old options explicitly. |
| Provider-owned/native tools treated as granularly replayable | `HIGH` | Adapter may not see the real side effects inside provider-native behavior. | Report replay limits; keep provider-owned work outside durability claims. |
| Tool/MCP cache assumptions | `MEDIUM` | Kitaru checkpoint cache and MCP `cache_tools=True` solve different problems. | Explain which cache is being used and verify replay behavior. |

## Human wait safety rules

Human waits are safe only when the wait reaches Kitaru flow scope.

Safe patterns:

- `@hitl_tool` for pure wait tools.
- `kitaru.wait(...)` directly in a `@kitaru.flow` before or after the agent
  turn.
- Regular tool `wait_for_input(...)` only when the tool is opted out of
  per-tool checkpoints and `allow_sync_tool_body_waits=True` is explicitly set.

Unsafe patterns:

- `wait_for_input(...)` in a normal tool body with default calls checkpointing.
- `kitaru.wait(...)` inside any `@kitaru.checkpoint`.
- Hidden approval/deferred behavior that cannot be seen in source and is not
  covered by adapter configuration.

## Replay and side-effect questions to ask

For every tool, MCP call, stream handler, and provider-native feature, ask:

1. If this line runs twice, what external thing changes twice?
2. If Kitaru serves a cached checkpoint output, what side effect will not happen
   the second time?
3. Is there an idempotency key, stable request ID, or external record that makes
   replay safe?
4. Is the value needed after restart stored as a checkpoint output, artifact,
   flow input, or external-store reference?

If the answer is unclear, mark the item `HIGH` or `BLOCKER` instead of guessing.

## Standard report phrases

Use concrete language like:

- "The source calls `wait_for_input()` from inside a regular sync tool. With
  Kitaru's default calls strategy, that tool would normally be inside a
  synthetic tool checkpoint, but waits must be created at flow scope. This needs
  a tool checkpoint opt-out or a redesign."
- "The migrated code uses `persist_message_history=True`, but that history lives
  on one Python object. It is convenient for a local conversation but not a
  durable conversation store."
- "This provider-native tool remains provider-owned. Kitaru can record the
  surrounding agent turn or supported calls, but it cannot replay hidden provider
  internals as separate Kitaru checkpoints."
- "Auto-flow is fine for local prototyping. For remote stacks, this migration
  adds an explicit `@kitaru.flow` because the auto-flow registry is in-process."
