---
name: kitaru-gemini-interactions-migration
description: >
  Migrate existing Gemini Interactions, Google GenAI, and Antigravity managed
  agent code to Kitaru's Gemini Interactions adapter. Use when code mentions
  google.genai, genai.Client, client.interactions.create, client.interactions.get,
  Interaction, interaction_id, previous_interaction_id, requires_action,
  function_call, function_result, background, store, poll, steps, output_text,
  Antigravity, managed agents, environment, Vertex, API key,
  KitaruGeminiInteractionsRunner, GeminiInteractionRequest,
  GeminiInteractionResult, GeminiInteractionCapturePolicy, or cache_identity.
  Helps classify direct, approximate, and absent mappings, preserve Google-owned
  hosted interaction internals, handle requires_action and polling safely, and
  produce a migration report.
---

# Migrate Gemini Interactions to Kitaru

## What this skill does

Use this skill to inspect existing Gemini Interactions / Google GenAI code and
move the safe outer interaction boundary to Kitaru's `kitaru.adapters.gemini`
surfaces.

The output should be conservative:

1. A source pattern inventory.
2. A migration plan that classifies each important pattern as `direct`,
   `approximate`, or `absent`.
3. Migrated or proposed code using `KitaruGeminiInteractionsRunner`,
   `GeminiInteractionRequest`, `GeminiInteractionResult`, and capture policy.
4. A `MIGRATION_REPORT.md` section or file that names replay, polling,
   `requires_action`, hosted-tool, Antigravity, environment, region, credential,
   and privacy risks.

Use the user-facing name **Gemini Interactions**. Treat Antigravity as an
important managed-agent/preset use case, not as the primary adapter identity.

## Mental model: Google owns the hosted runtime; Kitaru records one stable response

Google owns the hosted interaction runtime: model/agent execution, hosted tools,
MCP, web/code execution, Antigravity sandbox/environment internals, background
jobs, and server-side interaction history.

Kitaru records one stable Gemini Interactions response with
`checkpoint_strategy="interaction"`. Stable means `completed` or
`requires_action`.

Concrete story: the app sends an interaction request. Google may think, browse,
call hosted tools, use an Antigravity environment, or ask for a local function
result. Kitaru cannot see all of that internal work. Kitaru records the stable
response that comes back. If the response says `requires_action`, the work
returns to your Kitaru flow: run the local tool or ask a human, then send a later
`function_result` request.

## When to use this skill

Use it when the user asks to:

- replace `client.interactions.create(...)` with
  `KitaruGeminiInteractionsRunner.run/run_sync(...)`;
- migrate `client.interactions.get(...)` polling to `GeminiInteractionRequest.poll(...)`;
- preserve `previous_interaction_id` with `GeminiInteractionRequest.resume(...)`;
- migrate function-result turns with `GeminiInteractionRequest.function_result(...)`;
- handle `requires_action` at Kitaru flow scope;
- review `background`, `store`, `steps`, `output_text`, hosted tools, MCP,
  Google Search, code execution, web tools, Antigravity, managed agents, Vertex,
  API keys, regions, environments, or `cache_identity`;
- produce a migration report for Gemini Interactions code.

## When not to use this skill

Do not use it to:

- migrate classic `generateContent` code unless the user is explicitly moving it
  to Gemini Interactions first;
- claim Kitaru can checkpoint Google-owned hosted tools, MCP, web/code
  execution, background internals, or Antigravity sandbox steps;
- hide `requires_action` work inside the provider-owned interaction instead of
  returning it to Kitaru flow scope;
- treat in-progress/background jobs as successful checkpoint outputs;
- make Antigravity look like the core adapter identity.

## The three mapping types

Classify each source pattern before editing:

- `direct`: Kitaru has a close adapter surface for the same outer behavior.
  Example: `client.interactions.create(model=..., input=...)` becomes
  `runner.run_sync(GeminiInteractionRequest.start(input, model=...))`.
- `approximate`: The migration is possible, but replay, polling, state,
  environment, capture, or hosted-tool behavior differs. Example: hosted tool
  steps remain Google-owned and are captured only as response summaries/artifacts.
- `absent`: There is no safe automatic migration. Example: a plan to replay each
  Antigravity file operation as a Kitaru checkpoint.

Unsupported patterns must not be silently approximated. Add a concrete
`# TODO(migration): ...` comment near proposed code, list it in the report, and
explain the redesign needed.

## Migration workflow

1. **Inspect source first.** Find `genai.Client`, `client.interactions.create`,
   `get`, `previous_interaction_id`, `background`, `store`, function calls,
   function results, status checks, Antigravity/managed agents, environments,
   Vertex/API-key configuration, and existing Kitaru decorators.
2. **Classify every pattern.** Use `references/concept-map.md` and
   `references/gaps-and-flags.md`. Count direct, approximate, high-risk, and
   blocked items.
3. **Choose Kitaru boundaries.** Use only `checkpoint_strategy="interaction"`.
   One stable Gemini Interactions response becomes one Kitaru checkpoint.
4. **Present the plan before generating code** when the migration is more than a
   tiny entrypoint replacement. Name hosted runtime limits, polling behavior,
   and privacy capture decisions before editing.
5. **Draft migrated code.** Replace raw interactions entrypoints with
   `KitaruGeminiInteractionsRunner` plus `GeminiInteractionRequest`. Add status
   handling for `completed`, `requires_action`, and non-stable statuses.
6. **Produce `MIGRATION_REPORT.md`.** Include the inventory, chosen boundary,
   classifications, flags, behavior differences, and verification plan.
7. **Verify behavior.** Prefer static/import checks. If API-key/Vertex access is
   unavailable, say the check was static only.

## Pattern detection checklist

Look for:

- `from google import genai`, `genai.Client(...)`, `client.interactions.create`,
  `client.interactions.get`, or `Interaction` objects.
- `model=...`, `agent=...`, `environment=...`, `tools=...`,
  `system_instruction=...`, `generation_config=...`, `agent_config=...`,
  `response_format=...`, or `response_mime_type=...`.
- `previous_interaction_id`, `interaction.id`, `interaction_id`, `background`,
  `store`, `poll`, webhooks, or retry loops.
- `status`, `requires_action`, `function_call`, `function_result`, `call_id`,
  `steps`, `output_text`, and manual local tool execution.
- Antigravity agent IDs/presets, managed agents, remote environments, sandbox
  files, and environment IDs.
- API-key vs Vertex/ADC setup, project, region/location, and client factories.
- Raw interaction payload capture, request manifests, logs, prompts, tool args,
  generated files, or user data.
- Existing `@kitaru.flow` or `@kitaru.checkpoint` wrappers.

## Boundary decision rules

- Keep Gemini Interactions as the hosted runtime.
- Use `KitaruGeminiInteractionsRunner(name=..., checkpoint_strategy="interaction")`.
- Use `GeminiInteractionRequest.start(...)` for new interactions.
- Use `GeminiInteractionRequest.resume(...)` for `previous_interaction_id` turns.
- Use `GeminiInteractionRequest.function_result(...)` to answer a prior
  `requires_action` function call.
- Use `GeminiInteractionRequest.poll(interaction_id=...)` to fetch an existing
  background interaction. Do not create duplicate jobs to check progress.
- Preserve the `model=` vs `agent=` distinction. Set exactly one.
- Use `.antigravity(...)` for Antigravity managed-agent requests when that preset
  fits, but report that Antigravity internals remain Google-owned.
- Add `cache_identity` when the same logical request might run under different
  projects, regions, credentials, clients, or environment configuration.
- Treat statuses other than `completed` and `requires_action` as not safely
  checkpointable final outputs.

## Gemini Interactions migration quick guide

Minimal model interaction:

```python
import kitaru
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(name="gemini_writer")

@kitaru.flow
def write_summary(topic: str) -> str:
    result = runner.run_sync(
        GeminiInteractionRequest.start(
            f"Write a short summary of {topic}.",
            model="gemini-3.5-flash",
        )
    )
    if result.status != "completed":
        raise RuntimeError(f"Expected completed interaction, got {result.status!r}")
    return result.output_text or ""
```

For full examples, load `references/code-patterns.md`.

## Gap handling rules

When a pattern is unsafe or unsupported:

1. Do not silently approximate it.
2. Add a concrete `# TODO(migration): ...` comment near the code if producing
   code.
3. Add a report entry with severity `LOW`, `MEDIUM`, `HIGH`, or `BLOCKER`.
4. Explain the bad outcome the flag prevents. Example: "creating a new
   background interaction while polling would start duplicate provider work."
5. Propose the smallest safe redesign.

## Report requirements

Every non-trivial migration must include or draft `MIGRATION_REPORT.md` with:

- source files reviewed and changed/proposed;
- classification totals;
- source pattern inventory;
- chosen Kitaru interaction boundary;
- direct translations;
- approximate translations and caveats;
- flagged items with severity and required action;
- Gemini-specific notes for stable statuses, `requires_action`, function
  results, polling/background jobs, model vs agent targets, Antigravity,
  environments, Vertex/API-key/region/client configuration, `cache_identity`,
  capture/privacy policy, and hosted tools;
- verification plan and whether execution was actually run.

Use `references/report-template.md` when a full report is needed.

## Anti-patterns

Avoid these:

- Using any checkpoint strategy except `"interaction"`.
- Treating `in_progress`, `failed`, `cancelled`, `incomplete`, or
  `budget_exceeded` as successful checkpoint outputs.
- Creating a new background interaction when the source meant to poll an
  existing `interaction_id`.
- Claiming Kitaru can replay hosted tools, MCP, web/code execution, or
  Antigravity sandbox internals as granular checkpoints.
- Hiding local function-result work inside provider-owned flow instead of
  returning it to Kitaru flow scope.
- Mixing `model=` and `agent=` in one request.
- Omitting `cache_identity` when project/region/credential/client differences
  change the meaning of the cached request.
- Saving raw prompts/provider payloads without an explicit privacy decision.

## References

Load only the reference file needed for the current task:

- `references/concept-map.md` — source-to-target mapping table and
  classification guidance.
- `references/code-patterns.md` — import-complete migration examples.
- `references/gaps-and-flags.md` — severity definitions, upstream assumptions,
  and must-flag patterns.
- `references/report-template.md` — Gemini Interactions-specific migration
  report template.

Kitaru source references:

- Kitaru Gemini Interactions adapter docs:
  `kitaru/docs/content/docs/adapters/gemini-interactions.mdx`
- Adapter exports:
  `kitaru/src/kitaru/adapters/gemini/__init__.py`
- Adapter example:
  `kitaru/examples/integrations/gemini_interactions_agent/README.md`
