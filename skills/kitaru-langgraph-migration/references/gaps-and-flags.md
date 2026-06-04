# LangGraph Migration Gaps and Flags

Use this file when deciding whether a migration is safe to apply automatically.
The rule is: if replay, interrupt, stream, state, persistence, side effects, or
secret handling may change, make that visible in comments and in the migration
report.

## Upstream docs checked

Checked on 2026-06-04 against current official docs:

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- LangGraph streaming: https://docs.langchain.com/oss/python/langgraph/streaming
- LangChain agents: https://docs.langchain.com/oss/python/langchain/agents

Assumptions recorded here: LangGraph remains the stateful graph runtime;
checkpointers organize graph state by `thread_id`; interrupts resume through
LangGraph state and commands; LangChain `create_agent(...)` supports middleware;
Deep Agents/filesystem/memory middleware are LangChain/LangGraph-owned, not
Kitaru-owned.

## Severity levels

| Severity | Meaning | Required action |
|---|---|---|
| `LOW` | Cosmetic or documentation-only difference. | Migrate and mention in report. |
| `MEDIUM` | Behavior probably preserved, but settings or observability differ. | Migrate with caveat and verification step. |
| `HIGH` | Replay, interrupt, stream, state, side-effect, or persistence behavior may change. | Require human review before applying or mark partial migration. |
| `BLOCKER` | Migration would be unsafe or impossible without source redesign. | Do not auto-migrate; generate redesign note and report entry. |

## Must-flag patterns

### Missing or unstable `thread_id`

- **Severity:** `BLOCKER` for interrupt/resume or conversation memory flows;
  `HIGH` otherwise.
- **Pattern:** graph calls without stable `configurable.thread_id`, random IDs
  where resume is expected, or thread IDs derived from volatile trace IDs.
- **Why it matters:** LangGraph uses `thread_id` as the pointer to graph state.
  A new ID is a new thread, not a resume.
- **Action:** add a stable application-owned thread ID before migration.

### Replacing LangGraph persistence with Kitaru

- **Severity:** `BLOCKER`.
- **Pattern:** migration removes checkpointers/stores or claims Kitaru replaces
  LangGraph checkpoints.
- **Why it matters:** LangGraph interrupts, memory, and graph-local replay depend
  on LangGraph's own persistence layer.
- **Action:** keep or improve the LangGraph checkpointer/store. Use Kitaru only
  around adapter-visible boundaries.

### `InMemorySaver` used as production durability

- **Severity:** `HIGH` or `BLOCKER` for multi-process/remote deployment.
- **Pattern:** `InMemorySaver()` / `MemorySaver()` in code expected to survive a
  process restart or pod replacement.
- **Why it matters:** in-memory state disappears when the process dies.
- **Action:** keep for tests/demos only, or switch to a durable LangGraph
  checkpointer before claiming restart durability.

### `calls` mode without `KitaruLangGraphMiddleware`

- **Severity:** `HIGH`.
- **Pattern:** `KitaruGraphRunner(..., checkpoint_strategy="calls")` but no
  Kitaru middleware in the LangChain agent.
- **Why it matters:** Kitaru may collect run metadata, but it cannot open true
  per-model/per-tool checkpoints if calls never pass through the middleware.
- **Action:** install `KitaruLangGraphMiddleware()` or switch to `graph_call`.

### Async calls treated as true granular checkpoints

- **Severity:** `HIGH`.
- **Pattern:** migration claims async LangChain model/tool calls are separately
  durable Kitaru checkpoints.
- **Why it matters:** current Kitaru async middleware tracking is metadata-only.
- **Action:** describe async calls as metadata-only or use a coarser
  `graph_call` boundary.

### Interrupt results treated as completed

- **Severity:** `HIGH`.
- **Pattern:** code reads `result.output` without checking
  `result.status == "completed"` when interrupts are possible.
- **Why it matters:** an interrupted result is a paused graph pointer, not a final
  answer.
- **Action:** add explicit `completed` / `interrupted` status handling and resume
  through `build_resume_request(...)` or `LangGraphRunRequest.resume(...)`.

### `wait_for_interrupt(...)` inside a checkpoint

- **Severity:** `BLOCKER`.
- **Pattern:** Kitaru human wait bridge is called from inside a user checkpoint or
  graph-node checkpoint.
- **Why it matters:** waits must be created at Kitaru flow scope.
- **Action:** move the wait bridge to the surrounding `@kitaru.flow`.

### Stream/callback side effects

- **Severity:** `HIGH`; `BLOCKER` for destructive/customer-visible effects.
- **Pattern:** `stream`, `astream`, `stream_events`, callbacks, or LangSmith
  hooks write to Slack/files/databases or external APIs.
- **Why it matters:** replay may duplicate those writes, or cached results may
  skip them.
- **Action:** make handlers idempotent or move important side effects after a
  final checkpointed result.

### Deep Agents sandbox/filesystem assumed durable under Kitaru

- **Severity:** `HIGH`.
- **Pattern:** migration claims Kitaru snapshots Deep Agents filesystem,
  subagents, sandboxes, or backend state.
- **Why it matters:** those internals remain Deep Agents/LangChain-owned.
- **Action:** record only outer graph calls or visible sync middleware calls;
  store important file/state references explicitly.

### Non-serializable graph outputs

- **Severity:** `HIGH` to `BLOCKER`.
- **Pattern:** checkpoints return raw `StateSnapshot`, graph objects, clients,
  streams, callbacks, file handles, or stores.
- **Why it matters:** checkpoint outputs must be serializable.
- **Action:** return strings, dicts, Pydantic dumps, IDs, or explicit artifact
  references.

### Secrets in config, metadata, or state

- **Severity:** `BLOCKER`.
- **Pattern:** API keys or tokens in `config`, `configurable`, request metadata,
  graph state, or logs.
- **Why it matters:** these values may become durable records.
- **Action:** use environment variables or secret managers; keep secrets out of
  Kitaru request metadata and artifacts.

## Required report entry shape

```markdown
- Severity: HIGH
- Source location: path/to/graph.py:123
- Pattern: `checkpoint_strategy="calls"` but no `KitaruLangGraphMiddleware`
- Migration action: switched to `graph_call` / not auto-migrated
- Why it matters: without middleware, Kitaru cannot create granular call checkpoints
- Required human decision: install middleware or accept one outer graph checkpoint
```

## Code comment shape

```python
# TODO(migration): This graph uses InMemorySaver but is expected to resume after
# process restarts. Replace it with a durable LangGraph checkpointer before
# claiming production restart durability.
```
