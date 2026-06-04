# Migration Report: Gemini Interactions to Kitaru Adapter

Use this template for `MIGRATION_REPORT.md` or for a report section in the final
answer when the user does not want a file written.

## Summary

- Source framework/API: Gemini Interactions / Google GenAI / Antigravity managed agents
- Target adapter: `kitaru.adapters.gemini.KitaruGeminiInteractionsRunner`
- Source files reviewed:
  - `[path]`
- Files changed or proposed:
  - `[path]`
- Migration status: `[complete / partial / plan only / blocked]`
- Classification totals:
  - Direct: `[n]`
  - Approximate: `[n]`
  - Absent: `[n]`
  - Flagged: `[n]`
  - Blocked: `[n]`

## Source Pattern Inventory

| Source location | Pattern found | Classification | Severity | Notes |
|---|---|---|---|---|
| `[file:line]` | `client.interactions.create(...)` | `direct` | `LOW` | Replaced with `KitaruGeminiInteractionsRunner` interaction boundary. |
| `[file:line]` | `[pattern]` | `[direct / approximate / absent]` | `[LOW / MEDIUM / HIGH / BLOCKER]` | `[concrete note]` |

## Chosen Kitaru Boundaries

Describe the save points in plain language.

Example:

- Gemini Interactions remains the hosted runtime.
- `KitaruGeminiInteractionsRunner` is constructed once with a stable name.
- The adapter uses `checkpoint_strategy="interaction"`, so one stable
  `client.interactions.create(...)` or `.get(...)` response becomes one Kitaru
  checkpoint.
- Stable statuses are `completed` and `requires_action`.
- Google-hosted tools, MCP, web/code execution, Antigravity sandbox state,
  server-side history, and background job internals remain Google-owned.

## Direct Translations

| Source | Target | Why direct |
|---|---|---|
| `client.interactions.create(input=prompt, model=model)` | `runner.run_sync(GeminiInteractionRequest.start(prompt, model=model))` | Same one-turn interaction; Kitaru changes the outer doorway. |
| `client.interactions.get(interaction_id=...)` | `runner.run_sync(GeminiInteractionRequest.poll(interaction_id=...))` | Same existing interaction ID; no duplicate provider job. |
| `[source]` | `[target]` | `[reason]` |

## Approximate Translations

| Source | Target | Behavior difference | Verification step |
|---|---|---|---|
| Hosted tools / Antigravity work | Same request through Kitaru adapter | Google-owned internal steps are not separate Kitaru checkpoints. | Inspect result IDs/summaries and confirm important state is persisted outside hosted sandbox. |
| `previous_interaction_id` resume | `GeminiInteractionRequest.resume(...)` | Server-side history remains Google-owned and retention-bound. | Resume a known stored interaction in the target environment. |
| `[source]` | `[target]` | `[difference]` | `[step]` |

## Flagged for Human Review

| Severity | Source location | Issue | What could break | Required action |
|---|---|---|---|---|
| `HIGH` | `[file:line]` | `[issue]` | `[duplicate provider job / lost server-side history / unsafe raw capture / etc.]` | `[review or redesign step]` |

## Adapter-Specific Notes

### Runner identity and strategy

- Runner name: `[name]`
- Chosen strategy: `interaction`
- Unsupported strategies found: `[none/list]`
- Runner call inside an existing checkpoint: `[none / blocked and moved to flow scope]`

### Target and client configuration

- Uses `model=`: `[yes/no/list]`
- Uses `agent=`: `[yes/no/list]`
- Uses Antigravity preset: `[yes/no]`
- Client construction: `[default / client= / client_factory=]`
- Project/region/credential/source of truth: `[known/unknown]`
- `cache_identity`: `[configured / missing / not needed]`
- Risk note:
  - `[what would happen if cache_identity is wrong or missing]`

### Stable statuses and polling

- Stable statuses handled: `[completed / requires_action / both]`
- Background jobs found: `[yes/no/list]`
- Polling uses existing `interaction_id`: `[yes/no/not applicable]`
- Non-stable status behavior:
  - `[poll again / blocked / needs redesign]`

### `requires_action` and function results

- Uses `requires_action`: `[yes/no]`
- Function call ID source: `[where found]`
- Local function/human work happens at flow scope: `[yes/no/needs redesign]`
- `GeminiInteractionRequest.function_result(...)` used: `[yes/no/not applicable]`
- Replay consequence:
  - `[what local work can be replayed or skipped]`

### Server-side state and retention

- Uses `previous_interaction_id`: `[yes/no]`
- Uses `store`: `[true/false/default/unknown]`
- Stored interaction ID persistence: `[where/how]`
- Retention caveat:
  - `[server-side history remains Google-owned and retention-bound]`

### Antigravity and environments

- Agent ID/preset: `[antigravity-preview-05-2026 / custom / not applicable]`
- Environment: `[remote / env id / config / not applicable]`
- Background mode requested: `[no / yes BLOCKER]`
- Hosted files/sandbox note:
  - `[what remains Google-owned]`

### Hosted tools and steps

- Hosted tools found: `[web / code_execution / MCP / Google Search / URL context / list]`
- Step summaries captured: `[yes/no/default]`
- Raw step/provider payload capture: `[yes/no]`
- Granular replay note:
  - `[hosted tool and step internals are not Kitaru checkpoints]`

### Capture and privacy policy

- Capture policy configured: `[yes/no]`
- Input saved: `[yes/no/default]`
- Request manifest saved: `[yes/no/default]`
- Raw interaction saved: `[yes/no/default]`
- Steps saved: `[yes/no/default]`
- Output saved: `[yes/no/default]`
- Usage saved: `[yes/no/default]`
- Sensitive data risk: `[none known / needs review]`

## Behavioral Differences

Explain concrete differences introduced by the migration.

Examples:

- "The source previously called `client.interactions.create(...)` directly. The
  migrated code calls the same hosted API through `KitaruGeminiInteractionsRunner`,
  so Kitaru can record one stable interaction response."
- "A `requires_action` response is saved as a durable handoff point. Local tool
  work happens in the Kitaru flow, then the flow sends a later function-result
  interaction."
- "Antigravity filesystem and sandbox state remain Google-owned. Kitaru does not
  snapshot the remote environment."
- "Polling uses `GeminiInteractionRequest.poll(interaction_id=...)`, so replay
  does not accidentally start a second background job."

## What Is Not Migrated

| Item | Reason | Recommended redesign |
|---|---|---|
| `[item]` | `[why absent or unsafe]` | `[redesign]` |

## Verification Plan

- Static checks:
  - `[imports resolve / strategy is interaction / exactly one of model or agent / cache_identity reviewed]`
- Local dry-run:
  - `[not applicable / signature-only check]`
- Provider-backed run:
  - `[command or not run because API key/Vertex access unavailable]`
- Kitaru behavior checks:
  - Confirm execution appears in dashboard or `kitaru executions list`.
  - Confirm one interaction checkpoint appears for stable responses.
  - Confirm `requires_action` returns work to flow scope.
  - Confirm polling uses the same `interaction_id` instead of creating a new job.
  - Confirm replay does not duplicate unsafe provider work or local side effects.

## Docs and Reference Links

- Kitaru Gemini Interactions adapter docs:
  `kitaru/docs/content/docs/adapters/gemini-interactions.mdx`
- Kitaru Gemini adapter exports:
  `kitaru/src/kitaru/adapters/gemini/__init__.py`
- Skill references:
  - `skills/kitaru-gemini-interactions-migration/references/concept-map.md`
  - `skills/kitaru-gemini-interactions-migration/references/code-patterns.md`
  - `skills/kitaru-gemini-interactions-migration/references/gaps-and-flags.md`
- Official docs checked:
  - https://ai.google.dev/gemini-api/docs/interactions
  - https://ai.google.dev/api/interactions-api
  - https://ai.google.dev/gemini-api/docs/antigravity-agent

## Recommended Next Steps

1. `[Run provider-backed model or Antigravity smoke test if credentials are available]`
2. `[Review HIGH/BLOCKER polling, cache_identity, Antigravity, and privacy items]`
3. `[Decide whether client construction should use client= or client_factory=]`
4. `[Add project-specific tests for replay, requires_action, and duplicate-job prevention]`
5. `[Update user-facing docs or examples if this migration changes public behavior]`
