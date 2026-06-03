# Migration Report: PydanticAI to Kitaru Adapter

Use this template for `MIGRATION_REPORT.md` or for a report section in the final
answer when the user does not want a file written.

## Summary

- Source framework: PydanticAI
- Target adapter: `kitaru.adapters.pydantic_ai.KitaruAgent`
- Source files reviewed:
  - `[path]`
- Files changed or proposed:
  - `[path]`
- Migration status: `[complete / partial / plan only / blocked]`
- Classification totals:
  - Direct: `[n]`
  - Approximate: `[n]`
  - Flagged: `[n]`
  - Blocked: `[n]`

## Source Pattern Inventory

| Source location | Pattern found | Classification | Severity | Notes |
|---|---|---|---|---|
| `[file:line]` | `Agent(..., name=...)` | `direct` | `LOW` | Wrapped with `KitaruAgent`. |
| `[file:line]` | `[pattern]` | `[direct / approximate / absent]` | `[LOW / MEDIUM / HIGH / BLOCKER]` | `[concrete note]` |

## Chosen Kitaru Boundaries

Describe the save points in plain language.

Example:

- The existing PydanticAI agent remains the agent runtime.
- `KitaruAgent` is constructed once at module scope.
- The workflow uses explicit `@kitaru.flow` because this code may run on remote
  stacks.
- The adapter uses `checkpoint_strategy="turn"`, so one whole agent run becomes
  one Kitaru checkpoint.

## Direct Translations

List mappings that should preserve behavior.

| Source | Target | Why direct |
|---|---|---|
| `agent.run_sync(prompt)` | `durable_agent.run_sync(prompt)` | Same PydanticAI run path; Kitaru adds durability around it. |
| `[source]` | `[target]` | `[reason]` |

## Approximate Translations

List mappings where behavior is close but not identical.

| Source | Target | Behavior difference | Verification step |
|---|---|---|---|
| `granular_checkpoints=False` | `checkpoint_strategy="turn"` | New spelling for the same coarse-boundary intent. | Run one dry-run and confirm one turn checkpoint appears. |
| `[source]` | `[target]` | `[difference]` | `[step]` |

## Flagged for Human Review

| Severity | Source location | Issue | What could break | Required action |
|---|---|---|---|---|
| `HIGH` | `[file:line]` | `[issue]` | `[duplicate side effect / wait cannot resume / state lost / etc.]` | `[review or redesign step]` |

## Adapter-Specific Notes

### Stable names

- Agent names found: `[names]`
- Names added or changed: `[names]`
- Risk: changing names later can orphan existing Kitaru execution history.

### Concrete model construction

- Model is bound at `Agent(...)` construction: `[yes/no]`
- Per-run `model=` overrides found: `[yes/no]`
- Required action if no: create separate named `Agent` / `KitaruAgent` pairs per
  model.

### Checkpoint strategy

- Chosen strategy: `[calls / turn / explicit checkpoint passthrough]`
- Reason:
  - `[why this boundary is safe for this workflow]`
- Replay consequence:
  - `[what re-runs after a crash and what is served from checkpoint cache]`

### Tool waits and HITL

- `hitl_tool` used: `[yes/no]`
- `wait_for_input(...)` in regular tool body: `[yes/no]`
- Tool checkpoint opt-outs required:
  - `[tool_name]`
- `allow_sync_tool_body_waits=True` required: `[yes/no]`
- Human review required: `[yes/no and why]`

### Message history

- Uses `message_history=` explicitly: `[yes/no]`
- Uses `persist_message_history=True`: `[yes/no]`
- Durability caveat:
  - `[instance-local history / persisted external history / no conversation state]`

### Streaming

- Uses `event_stream_handler`: `[yes/no]`
- Uses `run_stream()` / `iter()`: `[yes/no]`
- Explicit checkpoint added for context-manager streaming: `[yes/no/not needed]`
- Stream side effects reviewed: `[yes/no]`

### Capture policy

- Capture policy configured: `[yes/no]`
- Prompts saved: `[yes/no/default]`
- Responses saved: `[yes/no/default]`
- Tool capture: `[full / metadata / none / overrides]`
- Sensitive data risk: `[none known / needs review]`

### MCP and toolset handling

- MCP servers found: `[yes/no/list]`
- Toolsets found: `[yes/no/list]`
- Provider/native tools found: `[yes/no/list]`
- Replay limit note:
  - `[what Kitaru can see and what remains provider-owned]`

## Behavioral Differences

Explain concrete differences introduced by the migration.

Examples:

- "The source previously ran the PydanticAI agent directly. The migrated code
  runs the same agent through `KitaruAgent`, so Kitaru can record checkpoints and
  artifacts around supported calls."
- "Message history remains instance-local. A process restart loses it unless the
  application persists `result.all_messages()` explicitly."
- "Provider-native tool internals remain provider-owned and are not replayed as
  separate Kitaru checkpoints."

## What Is Not Migrated

List anything deliberately left unchanged or blocked.

| Item | Reason | Recommended redesign |
|---|---|---|
| `[item]` | `[why absent or unsafe]` | `[redesign]` |

## Verification Plan

- Static checks:
  - `[imports resolve / no deprecated wrap target / stable names present]`
- No-key dry-run:
  - `[TestModel snippet or command]`
- Provider-backed run:
  - `[command or not run because credentials unavailable]`
- Kitaru behavior checks:
  - Confirm execution appears in dashboard or `kitaru executions list`.
  - Confirm checkpoint strategy produces expected boundaries.
  - Confirm waits can be resolved with `kitaru executions input` when applicable.
  - Confirm replay does not duplicate unsafe side effects.

## Docs and Reference Links

- Kitaru PydanticAI adapter docs:
  `kitaru/docs/content/docs/adapters/pydantic-ai.mdx`
- Kitaru PydanticAI adapter exports:
  `kitaru/src/kitaru/adapters/pydantic_ai/__init__.py`
- Runnable example:
  `kitaru/examples/integrations/pydantic_ai_agent/pydantic_ai_adapter.py`
- Skill references:
  - `skills/kitaru-pydantic-ai-migration/references/concept-map.md`
  - `skills/kitaru-pydantic-ai-migration/references/code-patterns.md`
  - `skills/kitaru-pydantic-ai-migration/references/gaps-and-flags.md`

## Deferred Adapter Migration Work

This report covers only PydanticAI to Kitaru's PydanticAI adapter. LangGraph,
Claude Agent SDK, Gemini Interactions, and other adapter migration skills are
separate work tracked in https://github.com/zenml-io/kitaru-skills/issues/9.

## Recommended Next Steps

1. `[Run the no-key TestModel dry-run / provider-backed smoke test]`
2. `[Review HIGH/BLOCKER items]`
3. `[Decide whether calls or turn strategy is the long-term default]`
4. `[Add project-specific tests for replay, waits, and side effects]`
5. `[Update user-facing docs or examples if this migration changes public behavior]`
