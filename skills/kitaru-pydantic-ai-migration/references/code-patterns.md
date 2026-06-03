# PydanticAI Migration Code Patterns

These examples are intentionally import-complete. Copy the shape, then adapt
names, prompts, schemas, and checkpoint choices to the source project.

## 1. Minimal wrapping

Source:

```python
from pydantic_ai import Agent

agent = Agent("openai:gpt-5-nano", name="researcher")
result = agent.run_sync("Summarize quantum error correction.")
print(result.output)
```

Target:

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = KitaruAgent(agent)

result = durable_agent.run_sync("Summarize quantum error correction.")
print(result.output)
```

## 2. Explicit flow for production or remote stacks

Use this when the code must run on a remote stack or when the workflow has more
than one durable step.

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = KitaruAgent(agent, checkpoint_strategy="turn")

@kitaru.flow
def research(topic: str) -> str:
    result = durable_agent.run_sync(f"Research {topic}.")
    return result.output

handle = research.run("Kitaru adapters")
print(handle.wait())
```

## 3. Existing checkpoint passthrough

Inside an explicit `@checkpoint`, the adapter does not open nested Kitaru
checkpoints. The user-written checkpoint is the replay boundary.

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = KitaruAgent(agent)

@kitaru.checkpoint(type="llm_call")
def ask_agent(prompt: str) -> str:
    return durable_agent.run_sync(prompt).output

@kitaru.flow
def two_step_research(topic: str) -> str:
    overview = ask_agent(f"Give an overview of {topic}.")
    return ask_agent(f"List open questions, given this overview:\n{overview}")
```

## 4. Structured output

Source:

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class Brief(BaseModel):
    title: str
    summary: str

agent = Agent("openai:gpt-5-nano", name="brief_writer", output_type=Brief)
brief = agent.run_sync("Write a short brief about durable agents.").output
```

Target:

```python
from pydantic import BaseModel
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

class Brief(BaseModel):
    title: str
    summary: str

agent = Agent("openai:gpt-5-nano", name="brief_writer", output_type=Brief)
durable_agent = KitaruAgent(agent)

brief = durable_agent.run_sync("Write a short brief about durable agents.").output
```

If `Brief` is returned from a Kitaru checkpoint, confirm that it serializes
cleanly. If not, return `brief.model_dump()` or save an explicit artifact.

## 5. No-key `TestModel` validation

Use this pattern for migration dry-runs that should not call a provider.

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent(TestModel(call_tools=[]), name="dry_run_agent", output_type=str)
durable_agent = KitaruAgent(agent)

result = durable_agent.run_sync("Check that migration wiring works.")
print(result.output)
```

## 6. `calls` vs `turn`

Per-call checkpoints:

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="granular_researcher")
durable_agent = KitaruAgent(
    agent,
    checkpoint_strategy="calls",
    model_checkpoint_config={"retries": 2, "cache": True},
    tool_checkpoint_config={"retries": 1},
)
```

One checkpoint for the whole agent turn:

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="turn_researcher")
durable_agent = KitaruAgent(
    agent,
    checkpoint_strategy="turn",
    turn_checkpoint_config={"retries": 2, "type": "llm_call"},
)
```

Compatibility migration:

```python
# Old compatibility option:
# KitaruAgent(agent, granular_checkpoints=False)

# New preferred spelling:
KitaruAgent(agent, checkpoint_strategy="turn")
```

## 7. Capture policy

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import CapturePolicy, KitaruAgent

agent = Agent("openai:gpt-5-nano", name="private_researcher")
durable_agent = KitaruAgent(
    agent,
    capture=CapturePolicy(
        save_prompts=False,
        save_responses=True,
        save_stream_transcripts=False,
        tool_capture="metadata",
        tool_capture_overrides={"fetch_secret": None},
    ),
)
```

Capture policy is observability-only. It controls what Kitaru stores; it does not
make a side-effectful tool replay-safe.

## 8. Durable message history caveat

Instance-local history:

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="chat_agent")
chat = KitaruAgent(agent, persist_message_history=True)

first = chat.run_sync("Hi, I am Alice.").output
second = chat.run_sync("What's my name?").output
```

More durable shape with explicit history storage:

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="chat_agent")
chat = KitaruAgent(agent)

@kitaru.checkpoint
def chat_turn(prompt: str, message_history: list[object]) -> tuple[str, list[object]]:
    result = chat.run_sync(prompt, message_history=message_history)
    return result.output, result.all_messages()
```

Before accepting this pattern, verify that `result.all_messages()` is serializable
in the project environment. If not, convert it to a serializable representation
or store it in an application-owned database.

## 9. Pure human wait with `@hitl_tool`

Use `hitl_tool` when the tool is only a human wait.

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent, hitl_tool

@hitl_tool(question="Approve publishing this summary?", schema=bool)
def approve_publish(summary: str) -> bool:
    ...

agent = Agent(
    "openai:gpt-5-nano",
    name="publisher",
    tools=[approve_publish],
)
durable_agent = KitaruAgent(agent)
```

The function body is skipped. The adapter creates the wait at flow scope, which
avoids checkpoint-contained waits. Keep the tool attached to the source agent the
same way other PydanticAI tools are attached in the project.

## 10. Regular sync tool waits with opt-out

Use this only when the tool body really must compute the wait question or schema.
Flag it as `HIGH` in the migration report.

```python
from pydantic_ai import Agent
from kitaru.adapters import pydantic_ai as kp

agent = Agent("openai:gpt-5-nano", name="support_agent")

def ask_user(question: str) -> str:
    return kp.wait_for_input(schema=str, question=question)

agent.tool_plain(ask_user)

durable_agent = kp.KitaruAgent(
    agent,
    tool_checkpoint_config_by_name={"ask_user": False},
    allow_sync_tool_body_waits=True,
)
```

Safer redesign when possible:

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="support_agent")
durable_agent = KitaruAgent(agent)

@kitaru.flow
def support_flow(issue: str) -> str:
    clarification = kitaru.wait(
        name="clarify_issue",
        question="What extra detail should the agent consider?",
        schema=str,
    )
    return durable_agent.run_sync(f"Issue: {issue}\nExtra: {clarification}").output
```

## 11. Deprecated `kp.wrap(...)` replacement

Source:

```python
from pydantic_ai import Agent
from kitaru.adapters import pydantic_ai as kp

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = kp.wrap(agent, granular_checkpoints=False)
```

Target:

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="researcher")
durable_agent = KitaruAgent(agent, checkpoint_strategy="turn")
```

## 12. Streaming

`event_stream_handler` can stay on the run call, but document the fallback: calls
mode may use a turn-level checkpoint for streamed turns.

```python
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="streaming_agent")
durable_agent = KitaruAgent(agent, checkpoint_strategy="calls")

def on_event(event: object) -> None:
    print(event)

result = durable_agent.run_sync(
    "Stream progress while answering.",
    event_stream_handler=on_event,
)
print(result.output)
```

For context-manager streaming APIs, use an explicit checkpoint and review side
effects from incremental stream handling.

```python
import kitaru
from pydantic_ai import Agent
from kitaru.adapters.pydantic_ai import KitaruAgent

agent = Agent("openai:gpt-5-nano", name="stream_context_agent")
durable_agent = KitaruAgent(agent)

@kitaru.checkpoint
def collect_stream(prompt: str) -> str:
    chunks: list[str] = []
    with durable_agent.run_stream(prompt) as stream:
        for chunk in stream.stream_text():
            chunks.append(chunk)
    return "".join(chunks)
```

If the stream handler writes to Slack, a file, or another external system while
chunks arrive, flag it. Replay may duplicate those writes unless the side effect
is moved behind an idempotent boundary.
