# Migration Report: LangGraph to Kitaru Adapter

Use this template for `MIGRATION_REPORT.md` or for a report section in the final
answer when the user does not want a file written.

## Summary

- Source framework: LangGraph / LangChain / Deep Agents
- Target adapter: `kitaru.adapters.langgraph.KitaruGraphRunner`
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
| `[file:line]` | `graph.invoke(...)` | `direct` | `LOW` | Replaced with `KitaruGraphRunner.invoke(...)`. |
| `[file:line]` | `[pattern]` | `[direct / approximate / absent]` | `[LOW / MEDIUM / HIGH / BLOCKER]` | `[concrete note]` |

## Chosen Kitaru Boundaries

Describe the save points in plain language.

Example:

- The existing LangGraph graph remains the graph runtime.
- `KitaruGraphRunner` is constructed once with a stable name.
- The workflow uses `checkpoint_strategy="graph_call"`, so one completed or
  interrupted `graph.invoke(...)` becomes one Kitaru checkpoint.
- LangGraph checkpointers and `thread_id` remain responsible for graph-local
  state and resume.

## Direct Translations

| Source | Target | Why direct |
|---|---|---|
| `graph.invoke(input, config=config)` | `runner.invoke(LangGraphRunRequest.start(input, thread_id=...))` | Same graph invocation; Kitaru changes the outer doorway. |
| `[source]` | `[target]` | `[reason]` |

## Approximate Translations

| Source | Target | Behavior difference | Verification step |
|---|---|---|---|
| `create_agent(..., middleware=[...])` | Add `KitaruLangGraphMiddleware()` and use `calls` | Only synchronous middleware-visible model/tool calls become true Kitaru checkpoints. | Run a small sync model/tool call and inspect artifacts/events. |
| `[source]` | `[target]` | `[difference]` | `[step]` |

## Flagged for Human Review

| Severity | Source location | Issue | What could break | Required action |
|---|---|---|---|---|
| `HIGH` | `[file:line]` | `[issue]` | `[duplicate side effect / lost resume / metadata-only boundary / etc.]` | `[review or redesign step]` |

## Adapter-Specific Notes

### Graph identity and names

- Graph runner name: `[name]`
- Names added or changed: `[names]`
- Risk: changing names later can make old Kitaru execution history harder to
  find.

### `thread_id` and LangGraph persistence

- Stable `thread_id` source: `[how generated/stored]`
- Checkpointer found: `[yes/no/type]`
- Store/memory found: `[yes/no/type]`
- In-memory persistence caveat: `[not applicable / local-only / needs durable replacement]`

### Checkpoint strategy

- Chosen strategy: `[graph_call / calls]`
- Reason:
  - `[why this boundary is safe for this workflow]`
- Replay consequence:
  - `[what re-runs after a crash and what is served from Kitaru cache]`

### Interrupts and resume

- Uses `interrupt(...)`: `[yes/no]`
- Resume mechanism found: `[Command(resume=...) / build_resume_request / other]`
- Result status handling added: `[yes/no]`
- Human wait bridge required: `[yes/no]`

### Middleware and calls mode

- Uses LangChain `create_agent(...)`: `[yes/no]`
- `KitaruLangGraphMiddleware` installed: `[yes/no/not applicable]`
- Sync model/tool call checkpoints expected: `[yes/no]`
- Async calls caveat: `[metadata-only / not applicable]`

### Streams, callbacks, and observability

- Uses `stream` / `astream` / `stream_events`: `[yes/no/list]`
- External stream/callback side effects: `[none known / needs review]`
- Replay note:
  - `[events are observability, not Kitaru replay boundaries]`

### Deep Agents

- Deep Agents features found: `[yes/no/list]`
- Filesystem/sandbox/backend state note:
  - `[what remains Deep Agents-owned]`

## Behavioral Differences

Explain concrete differences introduced by the migration.

Examples:

- "The source previously entered LangGraph directly. The migrated code enters the
  same graph through `KitaruGraphRunner`, so Kitaru can record one outer graph
  invocation result."
- "LangGraph checkpointers still hold graph-local state. Kitaru does not replace
  them."
- "Callbacks and event streams remain observability paths. They are not replayed
  as separate Kitaru checkpoints."

## What Is Not Migrated

| Item | Reason | Recommended redesign |
|---|---|---|
| `[item]` | `[why absent or unsafe]` | `[redesign]` |

## Verification Plan

- Static checks:
  - `[imports resolve / stable runner name / stable thread_id / status checks]`
- Local dry-run:
  - `[small graph command or not run]`
- Provider-backed run:
  - `[command or not run because credentials unavailable]`
- Kitaru behavior checks:
  - Confirm execution appears in dashboard or `kitaru executions list`.
  - Confirm expected `graph_call` or middleware-visible `calls` boundaries.
  - Confirm interrupted runs resume through LangGraph state.
  - Confirm replay does not duplicate unsafe side effects.

## Docs and Reference Links

- Kitaru LangGraph adapter docs:
  `kitaru/docs/content/docs/adapters/langgraph.mdx`
- Kitaru LangGraph adapter exports:
  `kitaru/src/kitaru/adapters/langgraph/__init__.py`
- Kitaru LangChain middleware:
  `kitaru/src/kitaru/adapters/langgraph/langchain.py`
- Skill references:
  - `skills/kitaru-langgraph-migration/references/concept-map.md`
  - `skills/kitaru-langgraph-migration/references/code-patterns.md`
  - `skills/kitaru-langgraph-migration/references/gaps-and-flags.md`

## Recommended Next Steps

1. `[Run local graph dry-run / provider-backed smoke test]`
2. `[Review HIGH/BLOCKER items]`
3. `[Decide whether graph_call or calls is the long-term default]`
4. `[Add project-specific tests for interrupts, replay, and side effects]`
5. `[Update user-facing docs or examples if this migration changes public behavior]`
