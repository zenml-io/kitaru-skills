# Migration Report: OpenAI Agents SDK to Kitaru Adapter

Use this template for OpenAI Agents SDK migrations. Keep the report concrete:
name the files inspected, the exact runner boundary chosen, and any behavior
that now depends on Kitaru replay semantics.

## Summary

- Source framework: OpenAI Agents SDK
- Target adapter: `kitaru.adapters.openai_agents`
- Source files reviewed:
  - `[path/to/source.py]`
- Files changed or proposed:
  - `[path/to/changed.py]`
- Migration status: `[complete | partial | proposed-only | blocked]`
- Classification totals:
  - Direct: `[count]`
  - Approximate: `[count]`
  - Absent: `[count]`
  - Flagged: `[count]`
  - Blocked: `[count]`

## Source Pattern Inventory

| Source location | Pattern found | Initial classification | Notes |
|---|---|---:|---|
| `[file.py:line]` | `Runner.run_sync(agent, input)` | `direct` | Replace with `KitaruRunner.run_sync(OpenAIRunRequest.start(...))`. |
| `[file.py:line]` | `[pattern]` | `[direct/approximate/absent]` | `[notes]` |

## Chosen Kitaru Boundaries

Describe the boundary in plain language.

Example:

> The source code used one raw `Runner.run_sync(...)` call for the whole support
> agent turn. The migration keeps the OpenAI `Agent` unchanged and replaces only
> the runner doorway with `KitaruRunner(..., checkpoint_strategy="runner_call")`.
> This gives Kitaru one durable checkpoint around the outer SDK run and keeps
> `.wait()` returning a single value.

- Main runner strategy: `[runner_call | calls]`
- Reason for this strategy: `[why this boundary is safest]`
- Flow scope used: `[yes/no/proposed]`
- Existing checkpoints touched: `[none/list]`
- Nested raw runner calls: `[none/list and decision]`

## Direct Translations

| Source pattern | Target pattern | Location | Verification |
|---|---|---|---|
| `Runner.run_sync(agent, input)` | `runner.run_sync(OpenAIRunRequest.start(input))` | `[file.py]` | `[static check / executed]` |
| `max_turns=` | `OpenAIRunRequest.start(..., max_turns=...)` | `[file.py]` | `[check]` |

## Approximate Translations

| Source pattern | Target pattern | What changes | Verification needed |
|---|---|---|---|
| `RunConfig(...)` | `run_config_factory=lambda: RunConfig(...)` | Config is recreated per Kitaru run. | Confirm factory does not capture volatile state. |
| `context=...` | same `context=` plus `context_cache_identity` | Context remains SDK runtime state; Kitaru uses identity for cache safety. | Test tenant/user/thread separation. |
| `[pattern]` | `[target]` | `[difference]` | `[verification]` |

## Flagged for Human Review

Use severity labels from `references/gaps-and-flags.md`.

| Severity | Source location | Pattern | Why it matters | Required action |
|---|---|---|---|---|
| `HIGH` | `[file.py:line]` | Side-effectful tool without idempotency | Replay may perform the external action twice. | Add idempotency key or keep outside replay. |
| `[LOW/MEDIUM/HIGH/BLOCKER]` | `[location]` | `[pattern]` | `[concrete bad outcome]` | `[action]` |

## Adapter-Specific Notes

### Runner name stability

- Agent names reviewed: `[yes/no]`
- Runner names reviewed: `[yes/no]`
- Volatile names found: `[none/list]`
- Decision: `[stable names added / user decision needed]`

### Checkpoint strategy

- Selected strategy: `[runner_call | calls]`
- Why not the other strategy: `[brief reason]`
- `.wait()` behavior: `[returns result cleanly | may raise KitaruAmbiguousFlowResultError]`
- Per-call artifact needs: `[none/list]`

### Result status handling

- `OpenAIRunResult.status` checked before reading `final_output`: `[yes/no]`
- Interruption branch present: `[yes/no/not applicable]`
- Remaining risk: `[none/description]`

### Approval and resume

- Approval-capable tools or interruptions found: `[yes/no]`
- Uses `wait_for_approval(...)`: `[yes/no/not applicable]`
- Uses `build_resume_request(...)`: `[yes/no/not applicable]`
- Resume SDK version tested/documented: `[yes/no]`
- Flow-scope wait confirmed: `[yes/no]`

### Context serialization

- `context=` used: `[yes/no]`
- Context type: `[simple data/object-heavy/external clients/etc.]`
- `context_cache_identity` configured: `[yes/no/not needed]`
- `context_serializer` configured for resumed state: `[yes/no/not needed]`
- `context_deserializer` configured for resumed state: `[yes/no/not needed]`
- Tenant/user/thread cache separation reviewed: `[yes/no]`

### Capture and privacy policy

- Explicit `OpenAICapturePolicy` reviewed: `[yes/no]`
- Saves input: `[yes/no]`
- Saves final output: `[yes/no]`
- Saves run state: `[yes/no]`
- Saves interruption payloads: `[yes/no]`
- Saves response items: `[yes/no]`
- Saves usage: `[yes/no]`
- Sensitive prompts, approval payloads, or customer data retained durably:
  `[none/list]`
- Required cleanup or retention decision: `[none/list]`

### Tool side effects

- Local `@function_tool` tools found: `[count/list]`
- Hosted/native tools found: `[count/list]`
- External side effects found: `[none/list]`
- Idempotency strategy: `[none/list/required]`
- Provider-owned internals clearly marked as outside Kitaru granular replay:
  `[yes/no]`

### SDK version compatibility

- OpenAI Agents SDK version observed: `[version/unknown]`
- Resume/interruption behavior tested on this version: `[yes/no/not applicable]`
- Version drift risk: `[none/LOW/MEDIUM/HIGH]`

### API key handling

- API keys passed as flow args: `[yes/no]`
- API keys in metadata/logs: `[yes/no]`
- Recommended handling: `[environment/Kitaru secrets/other]`
- Required cleanup: `[none/list]`

## Behavioral Differences

Explain what actually changes after migration.

Examples:

- With `runner_call`, Kitaru saves one durable checkpoint around the whole agent
  turn. It does not show every SDK-internal hosted tool step as a Kitaru
  checkpoint.
- With `calls`, supported local tool/model calls become peer checkpoints. The
  flow may not have one obvious final artifact for `.wait()`.
- `context=` remains local OpenAI Agents SDK runtime context. Kitaru does not
  turn it into visible request metadata.

## What Is Not Migrated

List anything intentionally left unchanged or blocked.

| Source location | Not migrated | Reason | Follow-up |
|---|---|---|---|
| `[file.py:line]` | Raw hosted tool internals | Provider-owned; Kitaru cannot checkpoint internals. | Accept outer runner checkpoint or redesign. |
| `[file.py:line]` | `[item]` | `[reason]` | `[follow-up]` |

## Verification Plan

### Static checks

- [ ] Imports updated to include `KitaruRunner` and `OpenAIRunRequest`.
- [ ] Raw top-level `Runner.run` / `Runner.run_sync` calls replaced or reported.
- [ ] `OpenAIRunResult.status` handled before `final_output` in risky flows.
- [ ] `calls` mode is not inside an existing Kitaru checkpoint.
- [ ] Context identity/serialization reviewed.
- [ ] Side-effectful tools reviewed for idempotency.
- [ ] API keys are not flow parameters, request metadata, or logs.

### Runtime checks

- [ ] Tiny provider-backed run executed, if `OPENAI_API_KEY` is available.
- [ ] If no credentials are available, report explicitly says static-only.
- [ ] Approval/interruption path tested, if relevant.
- [ ] `runner_call` `.wait()` behavior tested, if relevant.
- [ ] `calls` artifact retrieval / ambiguity behavior tested, if relevant.

## Docs and Reference Links

- Kitaru OpenAI Agents adapter docs:
  `kitaru/docs/content/docs/adapters/openai-agents.mdx`
- Adapter exports:
  `kitaru/src/kitaru/adapters/openai_agents/__init__.py`
- Integration example:
  `kitaru/examples/integrations/openai_agents_agent/openai_agents_adapter.py`
- End-to-end research bot example:
  `kitaru/examples/end_to_end/openai_research_bot/research_bot.py`
- Skill concept map:
  `skills/kitaru-openai-agents-migration/references/concept-map.md`
- Skill gaps and flags:
  `skills/kitaru-openai-agents-migration/references/gaps-and-flags.md`

## Other Adapter Migration Skills

LangGraph, Claude Agent SDK, Gemini Interactions, and PydanticAI migrations are
not part of this OpenAI Agents SDK migration. Use the matching sibling skill:
`kitaru-langgraph-migration`, `kitaru-claude-agent-sdk-migration`,
`kitaru-gemini-interactions-migration`, or `kitaru-pydantic-ai-migration`.

## Recommended Next Steps

1. `[Run static checks / apply migrated code / ask human about BLOCKER]`.
2. `[Run a small OpenAI-backed smoke test, or record static-only status]`.
3. `[Review HIGH/BLOCKER items before relying on replay in production]`.
4. `[Update application docs or PR notes with chosen checkpoint strategy]`.
