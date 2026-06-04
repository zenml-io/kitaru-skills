---
name: kitaru-pydantic-ai-migration
description: >
  Migrate existing PydanticAI agent code to Kitaru's PydanticAI adapter. Use
  when code mentions pydantic_ai.Agent, KitaruAgent, CapturePolicy, hitl_tool,
  wait_for_input, kp.wrap, tools, toolsets, MCP servers, streaming,
  run_stream, iter, event_stream_handler, message_history, TestModel,
  granular_checkpoints, or checkpoint_strategy. Helps classify direct,
  approximate, and absent mappings, choose safe Kitaru boundaries, update
  deprecated wrap(...) usage, and produce a migration report.
---

# Migrate PydanticAI to Kitaru

## What this skill does

Use this skill to migrate existing PydanticAI code onto Kitaru's
`kitaru.adapters.pydantic_ai` adapter without pretending Kitaru controls the
parts of PydanticAI or the model provider that it cannot see.

The output should be one of these:

- migrated code using `KitaruAgent`, `CapturePolicy`, `hitl_tool`, or
  `wait_for_input` where safe;
- a conservative migration plan when direct edits are not safe yet;
- a `MIGRATION_REPORT.md` or report section that explains what changed, what is
  approximate, and what still needs human review.

## Mental model: keep PydanticAI in charge, add Kitaru save points

PydanticAI still drives the agent turn. It chooses prompts, runs tools, talks to
models, handles MCP toolsets, and returns PydanticAI result objects.

Kitaru is added around safe seams:

- around each supported model/tool/MCP call with `checkpoint_strategy="calls"`;
- around the whole agent turn with `checkpoint_strategy="turn"`;
- around a user-written `@kitaru.checkpoint`, where `KitaruAgent` becomes a
  passthrough inside that explicit boundary;
- around flow-scope human waits created by adapter helpers such as
  `hitl_tool(...)` or `wait_for_input(...)`.

A useful picture: PydanticAI is still driving the car. Kitaru installs dashcams
and safe pull-over points. It can replay from the pull-over points it created;
it cannot rewind hidden provider internals or arbitrary side effects inside a
provider-owned tool.

## When to use this skill

Use it when the user has PydanticAI code and wants to:

- wrap an existing `pydantic_ai.Agent` with `KitaruAgent`;
- replace deprecated `kp.wrap(...)` / `wrap(...)` adapter usage;
- choose between `checkpoint_strategy="calls"` and
  `checkpoint_strategy="turn"`;
- migrate `granular_checkpoints=True/False` to `checkpoint_strategy` wording;
- add capture policy controls for prompts, responses, tools, or streams;
- make PydanticAI tool waits safe with `hitl_tool` or explicit flow waits;
- migrate examples that use `TestModel` and should not require provider keys;
- reason about streaming, `message_history`, MCP servers, toolsets, or
  structured output under Kitaru.

## When not to use this skill

Do not use this skill for:

- OpenAI Agents SDK code using `agents.Agent` or `Runner.run(...)`; use the
  OpenAI Agents migration skill instead.
- LangGraph, Claude Agent SDK, Gemini Interactions, or raw LangChain migrations;
  use the matching sibling migration skill instead.
- Rewriting PydanticAI internals or provider-owned native tool behavior.
- Promising exact replay of side effects that happen outside a Kitaru checkpoint
  boundary.
- Inventing Kitaru APIs that are not in the adapter docs.

## The three mapping types

Classify every important source pattern before writing migrated code:

- `direct` — Kitaru has a clear equivalent and behavior should be preserved.
  Example: `Agent("openai:gpt-5-nano", name="researcher")` wrapped with
  `KitaruAgent(agent)`.
- `approximate` — Kitaru can preserve the broad shape, but replay,
  observability, capture, wait, or state behavior changes. Example:
  `persist_message_history=True`, because history is instance-local and not
  durable across restarts.
- `absent` — there is no safe adapter mapping until the source is redesigned.
  Example: per-run `model=` overrides; create separate named agents instead.

Unsupported patterns must not be silently approximated. Add a concrete
`# TODO(migration): ...` comment near proposed code, list it in the report, and
explain the redesign needed.

## Migration workflow

1. **Inspect the source first.** Find `Agent(...)` construction, model binding,
   names, tools, MCP servers, run calls, streaming calls, waits, message history,
   capture settings, and existing Kitaru decorators.
2. **Classify every pattern.** Use `direct`, `approximate`, or `absent`. Load
   `references/concept-map.md` when the mapping is not obvious.
3. **Choose Kitaru boundaries.** Decide whether the migration should rely on
   auto-flow, an explicit `@kitaru.flow`, an explicit `@kitaru.checkpoint`,
   `checkpoint_strategy="calls"`, or `checkpoint_strategy="turn"`.
4. **Present the plan before editing.** For non-trivial migrations, explain the
   boundary choice and list high-risk seams before generating code.
5. **Draft migrated code.** Use import-complete examples from
   `references/code-patterns.md`. Keep the original PydanticAI agent where
   possible and add `KitaruAgent` around it.
6. **Write or include `MIGRATION_REPORT.md`.** The report must list direct,
   approximate, flagged, and blocked items. Use
   `references/report-template.md`.
7. **Verify behavior.** Prefer a no-key `TestModel` dry-run when credentials are
   unavailable. For provider-backed agents, include local checks and explain any
   provider execution that was not run.

## Pattern detection checklist

Look for these source patterns:

- `from pydantic_ai import Agent`, `Agent(...)`, `agent.run(...)`,
  `agent.run_sync(...)`, `run_stream(...)`, or `iter(...)`.
- Agent construction without a stable `name=`.
- Agents without a concrete model at construction time.
- Per-run `model=` arguments.
- `output_type=...` or structured result models.
- `TestModel` examples.
- `tool_plain`, `tool`, external toolsets, MCP servers, or provider-native
  tools.
- `requires_approval=True`, deferred calls, `hitl_tool`, or
  `wait_for_input(...)`.
- Existing `@kitaru.flow` or `@kitaru.checkpoint` wrappers.
- `granular_checkpoints`, `checkpoint_strategy`, checkpoint config dictionaries,
  or `runtime="isolated"`.
- `CapturePolicy(...)`, tool capture overrides, or stream transcript settings.
- `message_history=` and `persist_message_history=True`.
- Hidden mutable module state, global conversation lists, open file handles,
  client objects, or other non-serializable checkpoint outputs.

## Boundary decision rules

Use the smallest safe Kitaru boundary that makes replay behavior clear:

1. If the source already has a meaningful `@kitaru.flow`, keep it.
2. If the source already has a meaningful `@kitaru.checkpoint` around the agent
   turn, keep it; `KitaruAgent` will pass through inside that checkpoint.
3. For production or remote stacks, prefer explicit `@kitaru.flow`; auto-flow is
   local-only.
4. Use `checkpoint_strategy="calls"` when per-model/tool/MCP replay boundaries
   are useful and tool waits are safe.
5. Use `checkpoint_strategy="turn"` when one clean agent-turn checkpoint is more
   useful than many sibling call checkpoints, or when streaming fallback makes a
   turn-level boundary easier to explain.
6. Use `hitl_tool` for pure human-input tools. For regular sync tool bodies that
   call `wait_for_input(...)`, require both a tool checkpoint opt-out and
   `allow_sync_tool_body_waits=True`, or move the wait into flow code.
7. Do not put `wait()` inside checkpoints. Do not call one checkpoint from
   another checkpoint. Keep checkpoint outputs serializable.
8. Use stable names for agents, flows, checkpoints, waits, and artifacts.

## PydanticAI migration quick guide

The common migration is intentionally small:

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = KitaruAgent(agent)

result = durable_agent.run_sync("Summarize quantum error correction.")
print(result.output)
```

For explicit production boundaries:

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = KitaruAgent(agent, checkpoint_strategy="turn")

@kitaru.checkpoint
def ask_agent(prompt: str) -> str:
    return durable_agent.run_sync(prompt).output

@kitaru.flow
def research(topic: str) -> str:
    return ask_agent(f"Research {topic}")
```

Replace deprecated `kp.wrap(agent, ...)` with `KitaruAgent(agent, ...)`. Preserve
legacy behavior only when needed, and report the compatibility change.

## Gap handling rules

When the source contains a risky or unsupported pattern:

1. Stop and classify it.
2. Use severity labels from `references/gaps-and-flags.md`:
   `LOW`, `MEDIUM`, `HIGH`, or `BLOCKER`.
3. Prefer a safe partial migration over a false full migration.
4. Add a `# TODO(migration): ...` comment for code that needs redesign.
5. Explain the concrete failure mode in the report: duplicate side effect,
   missing wait resume point, lost message history, non-serializable output,
   changed replay boundary, or unsupported runtime.

## Report requirements

Every migration report must include:

- source files reviewed and files changed or proposed;
- classification totals for direct, approximate, flagged, and blocked patterns;
- chosen Kitaru boundaries and why they were chosen;
- direct translations;
- approximate translations and behavior differences;
- high-risk and blocker items with severity and required action;
- adapter-specific notes for stable names, concrete model construction, tool
  waits, message history, streaming, capture policy, and MCP/toolset handling;
- verification steps and any tests or dry-runs not performed.

Use `references/report-template.md` for the exact structure.

## Anti-patterns

Do not:

- claim that Kitaru replays all PydanticAI or provider internals;
- use deprecated `wrap(...)` as the normal target style;
- add per-run `model=` overrides to a wrapped agent;
- leave an adapter-wrapped agent without a stable name;
- use `runtime="isolated"` in adapter-managed checkpoint config;
- call `wait()` inside a checkpoint or inside a checkpointed regular tool body;
- return raw, non-serializable framework objects from checkpoints;
- hide mutable conversation state in module globals;
- treat instance-local `persist_message_history=True` as durable conversation
  memory across processes;
- rely on auto-flow for remote-stack execution;
- migrate streaming context managers without an explicit checkpoint boundary.

## References

Load these only when needed:

- `references/concept-map.md` — source-to-target mapping table with
  classifications.
- `references/code-patterns.md` — import-complete source and target examples.
- `references/gaps-and-flags.md` — severity labels and must-flag patterns.
- `references/report-template.md` — PydanticAI-specific `MIGRATION_REPORT.md`
  template.

Kitaru source-of-truth docs and examples:

- Kitaru PydanticAI adapter docs:
  `kitaru/docs/content/docs/adapters/pydantic-ai.mdx`
- Kitaru adapter exports:
  `kitaru/src/kitaru/adapters/pydantic_ai/__init__.py`
- Runnable example:
  `kitaru/examples/integrations/pydantic_ai_agent/pydantic_ai_adapter.py`
