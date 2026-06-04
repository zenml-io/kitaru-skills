---
name: kitaru-openai-agents-migration
description: >
  Migrate existing OpenAI Agents SDK code to Kitaru's OpenAI Agents adapter.
  Use when code mentions agents.Agent, Runner.run, Runner.run_sync,
  KitaruRunner, OpenAIRunRequest, OpenAIRunResult, wait_for_approval,
  build_resume_request, function_tool, RunConfig, handoffs, context,
  approval/resume flows, or checkpoint_strategy. Helps classify direct,
  approximate, and absent mappings, choose runner_call vs calls boundaries,
  preserve OpenAI Agents SDK ownership of the agent turn, and produce a
  MIGRATION_REPORT.md with replay, context, approval, tool, and side-effect
  risks called out.
---

# Migrate OpenAI Agents SDK to Kitaru

## What this skill does

Use this skill to inspect existing OpenAI Agents SDK code and move the safe
execution boundary to Kitaru's `KitaruRunner`, `OpenAIRunRequest`, and
`OpenAIRunResult` surfaces.

The output should be conservative:

1. A pattern inventory of the source code.
2. A migration plan that classifies every important pattern as `direct`,
   `approximate`, or `absent`.
3. Migrated or proposed code.
4. A `MIGRATION_REPORT.md` section or file that names behavior changes and
   review risks.

Do not promise that Kitaru can see or replay OpenAI/provider internals that stay
inside the OpenAI Agents SDK.

## Mental model: Runner stays OpenAI-owned, Kitaru records safe seams

Think of the OpenAI Agents SDK as the driver of the agent turn. It decides how
handoffs, guardrails, model calls, hosted tools, and approvals work.

Kitaru changes the doorway you use to enter that turn:

```python
from agents import Agent, Runner
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

agent = Agent(name="researcher", model="gpt-5-nano")

# Before: enter through the raw OpenAI SDK runner.
raw_result = Runner.run_sync(agent, "Research durable workflows")

# After: enter through Kitaru's runner doorway.
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")
result = runner.run_sync(OpenAIRunRequest.start("Research durable workflows"))
```

Concrete story: the agent starts, calls a model, maybe calls tools, maybe pauses
for approval, and then returns a final answer. OpenAI still runs that story.
Kitaru records either one durable checkpoint around the whole runner call or
supported model/local-tool calls that the adapter can safely see.

## When to use this skill

Use it when the user asks to:

- Migrate `agents.Agent` workflows to Kitaru.
- Replace `Runner.run(...)` or `Runner.run_sync(...)` with `KitaruRunner`.
- Choose `checkpoint_strategy="runner_call"` versus `"calls"`.
- Add durable behavior to OpenAI Agents SDK tools, handoffs, guardrails,
  approvals, or resume flows.
- Review whether `context=...`, `RunConfig`, hosted tools, function tools, API
  keys, or raw nested runner calls are safe under Kitaru replay.
- Produce a migration report for OpenAI Agents SDK code.

## When not to use this skill

Do not use it to:

- Rewrite the user's agent into a different framework.
- Claim Kitaru owns OpenAI Agents SDK internals.
- Add LangGraph, Claude Agent SDK, Gemini Interactions, or PydanticAI migration
  behavior; use the matching sibling migration skill instead.
- Hide replay, state, privacy, or side-effect risks just to produce cleaner
  code.
- Put Kitaru `wait()` calls inside checkpoints.

## The three mapping types

Classify each source pattern before editing:

- `direct`: Kitaru has a close adapter surface for the same behavior. Example:
  `Runner.run_sync(agent, input)` becomes
  `runner.run_sync(OpenAIRunRequest.start(input))`.
- `approximate`: The code can move, but semantics, observability, cache keys,
  or replay behavior differ. Example: `RunConfig(...)` becomes a
  `run_config_factory`, which recreates config per Kitaru run.
- `absent`: There is no safe automatic migration. Add a `# TODO(migration)`
  comment, do not pretend it is solved, and explain the redesign needed in the
  report.

## Migration workflow

1. **Inspect source first.** Find imports, `Agent(...)` construction,
   `Runner.run` / `Runner.run_sync`, `RunConfig`, `context=...`, tools,
   approvals, handoffs, guardrails, nested runner calls, and API-key handling.
2. **Classify every pattern.** Use `references/concept-map.md` and
   `references/gaps-and-flags.md`. Count direct, approximate, high-risk, and
   blocked items.
3. **Choose Kitaru boundaries.** Decide whether the main runner should use
   `checkpoint_strategy="runner_call"` or `"calls"`. Prefer `runner_call` when
   the surrounding flow needs a clean `.wait()` result.
4. **Present the plan before generating code** when the migration is more than a
   tiny local replacement. Name risky patterns before editing.
5. **Draft migrated code.** Keep the vanilla `agents.Agent`. Replace raw runner
   entrypoints with `KitaruRunner` plus `OpenAIRunRequest`. Add status handling
   for `OpenAIRunResult`.
6. **Produce `MIGRATION_REPORT.md`.** Include the pattern inventory, chosen
   boundary, classifications, flags, behavior differences, and verification
   plan.
7. **Verify behavior.** Prefer small representative snippets. If no API key or
   runtime is available, say the check was static only.

## Pattern detection checklist

Look for:

- `from agents import Agent, Runner`, `agents.Agent`, or `Runner.run*`.
- Raw nested `agents.Runner.run(...)` calls inside tools, guardrails, or helper
  agents.
- `RunConfig(...)`, tracing configuration, hooks, guardrails, and handoffs.
- `@function_tool`, `FunctionTool`, hosted tools, web search/file search/code
  interpreter tools, or custom tool wrappers.
- Tool functions that write to databases, send messages, charge cards, create
  tickets, upload files, or call external APIs.
- `context=...`, `RunContextWrapper`, context objects, serializers, and cache
  identity needs.
- Existing privacy, logging, tracing, retention, or capture expectations; decide
  whether `OpenAICapturePolicy` should save inputs, outputs, run state,
  interruption payloads, response items, and usage.
- Approval interruptions, `result.status`, `interrupted`, resume state, and
  manual approval decisions.
- `final_output` use without checking status.
- `Runner.run_sync(...)` inside async code or an active event loop.
- API keys passed as ordinary function parameters or logged.
- Raw SDK result objects returned directly from Kitaru checkpoints.

## Boundary decision rules

- Keep `agents.Agent(...)` as the OpenAI-owned agent definition.
- Use `KitaruRunner(agent, checkpoint_strategy="runner_call")` when the flow
  needs one durable result and ergonomic `.wait()` behavior.
- Use `checkpoint_strategy="calls"` when per-model/per-local-tool visibility is
  more important than a single terminal flow result.
- Do not put `calls` mode inside an existing Kitaru checkpoint.
- Keep `wait_for_approval(...)` at flow scope, not checkpoint scope.
- Treat `context=` as OpenAI Agents SDK runtime context, not Kitaru metadata.
- Use `context_cache_identity=` for production context objects so replay does
  not mix tenants, users, threads, or tool settings.
- Keep checkpoint outputs serializable. Return Kitaru adapter result envelopes or
  simple values, not arbitrary live SDK objects.
- Use stable agent and runner names. If names are missing or generated from
  volatile values, flag the migration.

## OpenAI Agents migration quick guide

Minimal durable sync replacement:

```python
from agents import Agent
from kitaru import flow
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

agent = Agent(name="support_agent", model="gpt-5-nano")
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")

@flow
def support_flow(message: str) -> str:
    result = runner.run_sync(OpenAIRunRequest.start(message))
    if result.status != "completed":
        raise RuntimeError(f"Expected completed run, got {result.status!r}")
    return str(result.final_output)

print(support_flow.run("Where is order ORD-1007?").wait())
```

Outside an explicit Kitaru flow, this is only adapter API wiring; it does not
establish a durable Kitaru checkpoint.

For full examples, load `references/code-patterns.md`.

## Gap handling rules

When a pattern is unsafe or unsupported:

1. Do not silently approximate it.
2. Add a concrete `# TODO(migration): ...` comment near the code if you are
   producing code.
3. Add a report entry with severity `LOW`, `MEDIUM`, `HIGH`, or `BLOCKER`.
4. Explain the bad outcome the flag prevents. Example: "the tool charges a card;
   replay may call it again unless the tool uses an idempotency key."
5. Propose the smallest safe redesign.

Use `references/gaps-and-flags.md` for severity definitions and required
actions.

## Report requirements

Every non-trivial migration must include or draft `MIGRATION_REPORT.md` with:

- Source files reviewed and changed/proposed.
- Classification totals.
- Source pattern inventory.
- Chosen Kitaru runner boundary and checkpoint strategy.
- Direct translations.
- Approximate translations and caveats.
- Flagged items with severity and required action.
- OpenAI-specific notes for result status, approval/resume, context,
  capture/privacy policy, side-effectful tools, SDK version compatibility, and
  API-key handling.
- Verification plan and whether execution was actually run.

Use `references/report-template.md` when a full report is needed.

## Anti-patterns

Avoid these:

- Replacing `agents.Agent` internals instead of changing the runner doorway.
- Using `Runner.run_sync(...)` from inside an active event loop.
- Returning `result.final_output` without checking `result.status` when approval
  interruptions are possible.
- Treating hosted/native tools as granularly replayable by Kitaru.
- Running `checkpoint_strategy="calls"` inside a Kitaru `@checkpoint`.
- Calling `wait_for_approval(...)` or `kitaru.wait(...)` inside a checkpoint.
- Passing API keys, tokens, prompts, or user secrets as Kitaru flow metadata.
- Saving raw non-serializable SDK objects as checkpoint outputs.
- Ignoring context cache identity for tenant/user/thread-sensitive tools.

## References

Load only the reference file needed for the current task:

- `references/concept-map.md` — source-to-target mapping table and
  classification guidance.
- `references/code-patterns.md` — import-complete migration examples.
- `references/gaps-and-flags.md` — severity definitions and must-flag patterns.
- `references/report-template.md` — OpenAI-specific migration report template.

Kitaru source references:

- Kitaru OpenAI Agents adapter docs:
  `kitaru/docs/content/docs/adapters/openai-agents.mdx`
- Adapter exports:
  `kitaru/src/kitaru/adapters/openai_agents/__init__.py`
- Adapter examples:
  `kitaru/examples/integrations/openai_agents_agent/openai_agents_adapter.py`
  and `kitaru/examples/end_to_end/openai_research_bot/research_bot.py`
