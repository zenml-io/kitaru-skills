# OpenAI Agents SDK Migration Code Patterns

These examples are source-to-target patterns. Adapt names and domain details, but
preserve the boundary rule: keep `agents.Agent`; replace the raw runner doorway
with `KitaruRunner` and `OpenAIRunRequest`.

## 1. Minimal `Runner.run_sync` replacement

### Before

```python
from agents import Agent, Runner

agent = Agent(name="support_agent", model="gpt-5-nano")
result = Runner.run_sync(agent, "Where is order ORD-1007?")
print(result.final_output)
```

### After

```python
from agents import Agent
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

agent = Agent(name="support_agent", model="gpt-5-nano")
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")

result = runner.run_sync(OpenAIRunRequest.start("Where is order ORD-1007?"))
if result.status != "completed":
    raise RuntimeError(f"Expected completed run, got {result.status!r}")
print(result.final_output)
```

## 2. Async `Runner.run` replacement

### Before

```python
from agents import Agent, Runner

agent = Agent(name="researcher", model="gpt-5-nano")

async def answer(prompt: str) -> str:
    result = await Runner.run(agent, prompt)
    return str(result.final_output)
```

### After

```python
from agents import Agent
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

agent = Agent(name="researcher", model="gpt-5-nano")
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")

async def answer(prompt: str) -> str:
    result = await runner.run(OpenAIRunRequest.start(prompt))
    if result.status != "completed":
        raise RuntimeError(f"Expected completed run, got {result.status!r}")
    return str(result.final_output)
```

## 3. Explicit Kitaru flow with `runner_call`

Use this when the caller wants `flow.run(...).wait()` to return the agent result
cleanly.

```python
from agents import Agent
from kitaru import flow
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

agent = Agent(name="researcher", model="gpt-5-nano")
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")

@flow
def research_flow(topic: str) -> str:
    result = runner.run_sync(OpenAIRunRequest.start(f"Research {topic}"))
    if result.status != "completed":
        raise RuntimeError(f"Expected completed run, got {result.status!r}")
    return str(result.final_output)

answer = research_flow.run("durable agent workflows").wait()
```

## 4. `calls` strategy and `.wait()` ambiguity

Use `calls` when per-model/per-local-tool artifacts matter more than a single
terminal flow result. Do not wrap this runner call in another `@checkpoint`.

```python
from agents import Agent, function_tool
from kitaru import KitaruAmbiguousFlowResultError, flow
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

@function_tool
def lookup_order(order_id: str) -> str:
    return f"Order {order_id}: delayed by weather"

agent = Agent(
    name="support_agent",
    model="gpt-5-nano",
    tools=[lookup_order],
)
runner = KitaruRunner(agent, checkpoint_strategy="calls")

@flow
def support_flow(message: str) -> str:
    result = runner.run_sync(OpenAIRunRequest.start(message))
    if result.status != "completed":
        raise RuntimeError(f"Expected completed run, got {result.status!r}")
    return str(result.final_output)

try:
    output = support_flow.run("Check order ORD-1007").wait()
except KitaruAmbiguousFlowResultError as error:
    # In calls mode, Kitaru may have several sibling checkpoints and no single
    # terminal artifact. Inspect artifacts in the Kitaru UI or with KitaruClient.
    print(f"Per-call artifacts available; wait was ambiguous: {error}")
```

## 5. Result status handling

Do not read `final_output` as if every result completed. Approval flows can
return `status="interrupted"`.

```python
from kitaru.adapters.openai_agents import OpenAIRunResult

def require_completed(result: OpenAIRunResult) -> str:
    if result.status != "completed":
        raise RuntimeError(f"OpenAI agent run did not complete: {result.status!r}")
    return str(result.final_output)
```

## 6. `RunConfig` factory

### Before

```python
from agents import Agent, RunConfig, Runner

agent = Agent(name="support_agent", model="gpt-5-nano")
result = Runner.run_sync(
    agent,
    "Help the customer",
    run_config=RunConfig(tracing_disabled=True),
)
```

### After

```python
from agents import Agent, RunConfig
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

agent = Agent(name="support_agent", model="gpt-5-nano")
runner = KitaruRunner(
    agent,
    checkpoint_strategy="runner_call",
    run_config_factory=lambda: RunConfig(tracing_disabled=True),
)

result = runner.run_sync(OpenAIRunRequest.start("Help the customer"))
```

## 7. Local function tools

Local `@function_tool` tools can be observed in `calls` mode when the adapter can
wrap them. Still review side effects.

```python
from agents import Agent, function_tool
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

@function_tool
def shipping_policy(status: str) -> str:
    return f"Policy for {status}: escalate if unresolved after 48 hours."

agent = Agent(
    name="shipping_agent",
    model="gpt-5-nano",
    tools=[shipping_policy],
)
runner = KitaruRunner(agent, checkpoint_strategy="calls")

result = runner.run_sync(OpenAIRunRequest.start("What is the delayed policy?"))
```

## 8. Side-effectful tools need idempotency

Bad source story: the tool sends a Slack message. A replay happens. The tool
sends the same message again. The customer sees two messages and loses trust.

```python
from dataclasses import dataclass

from agents import Agent, RunContextWrapper, function_tool
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

@dataclass(frozen=True)
class RefundContext:
    operation_id: str

@function_tool
def send_refund_email(ctx: RunContextWrapper[RefundContext], order_id: str) -> str:
    # Application-owned side-effect boundary. The model supplies only the order_id.
    # The idempotency key is derived in code from stable application context.
    idempotency_key = f"refund-email:{ctx.context.operation_id}:{order_id}"
    # The mail service must deduplicate by idempotency_key so replay cannot send
    # a second customer-visible email.
    return f"Queued refund email for {order_id} with key {idempotency_key}"

agent = Agent(
    name="refund_agent",
    model="gpt-5-nano",
    tools=[send_refund_email],
)
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")

request = OpenAIRunRequest.start("Send refund email for ORD-1007")
result = runner.run_sync(
    request,
    context=RefundContext(operation_id="refund-ORD-1007-v1"),
)
```

If the source tool performs side effects without idempotency, mark it `HIGH` or
`BLOCKER` in the migration report.

## 9. Context serialization and cache identity

`context=` is OpenAI Agents SDK runtime state. It is not Kitaru metadata. For
production replay, give Kitaru a stable identity for cache separation.

```python
from dataclasses import dataclass
from typing import Any

from agents import Agent, RunContextWrapper, function_tool
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

@dataclass(frozen=True)
class WorkerContext:
    team_id: str
    user_id: str
    thread_id: str
    message_id: str
    tool_settings: dict[str, Any]

@function_tool
def lookup_customer(ctx: RunContextWrapper[WorkerContext], customer_id: str) -> str:
    return f"team={ctx.context.team_id}, customer={customer_id}"

agent = Agent(
    name="customer_agent",
    model="gpt-5-nano",
    tools=[lookup_customer],
)
runner = KitaruRunner(
    agent,
    checkpoint_strategy="calls",
    context_cache_identity=lambda ctx: {
        "team_id": ctx.team_id,
        "user_id": ctx.user_id,
        "thread_id": ctx.thread_id,
        "tool_settings": ctx.tool_settings,
    },
)

result = runner.run_sync(
    OpenAIRunRequest.start("Look up customer 123"),
    context=WorkerContext(
        team_id="team_abc",
        user_id="user_123",
        thread_id="thread_456",
        message_id="msg_this_run_only",
        tool_settings={"include_private_notes": False},
    ),
)
```

For interrupted/resumed runs with object-heavy context, add
`context_serializer=` and `context_deserializer=` to the runner as required by
the application. If those are missing, flag the migration.

## 10. Approval and resume

Keep approval waits at flow scope.

```python
from agents import Agent
from kitaru import flow
from kitaru.adapters.openai_agents import (
    KitaruRunner,
    OpenAIRunRequest,
    OpenAIRunResult,
    build_resume_request,
    wait_for_approval,
)

agent = Agent(name="publisher", model="gpt-5-nano")
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")

@flow
def publish_flow(prompt: str) -> str:
    result = runner.run_sync(OpenAIRunRequest.start(prompt))

    if result.status == "interrupted":
        resume_request = wait_for_approval(
            result,
            name="approve_openai_tool",
            timeout=600,
        )
        result = runner.run_sync(resume_request)

    if result.status != "completed":
        raise RuntimeError(f"Expected completed run, got {result.status!r}")
    return str(result.final_output)

def resume_after_external_approval(
    interrupted_result: OpenAIRunResult,
) -> OpenAIRunRequest:
    """Build a resume request when approval was collected outside Kitaru wait."""
    return build_resume_request(interrupted_result, approve=True)
```

If the source code implies approval behavior but never checks `status`, mark the
migration `HIGH`.

## 11. Fan-out research workflow shape

For multi-step research bots, wrap each OpenAI agent through its own stable
runner. Keep cross-step state serializable.

```python
from agents import Agent
from kitaru import flow
from kitaru.adapters.openai_agents import KitaruRunner, OpenAIRunRequest

planner = Agent(name="planner", model="gpt-5-nano")
writer = Agent(name="writer", model="gpt-5-nano")
planner_runner = KitaruRunner(planner, checkpoint_strategy="runner_call")
writer_runner = KitaruRunner(writer, checkpoint_strategy="runner_call")

@flow
def research_report(topic: str) -> str:
    plan = planner_runner.run_sync(OpenAIRunRequest.start(f"Plan report: {topic}"))
    if plan.status != "completed":
        raise RuntimeError(f"Planner interrupted: {plan.status!r}")

    draft = writer_runner.run_sync(
        OpenAIRunRequest.start(f"Write report for {topic} using plan: {plan.final_output}")
    )
    if draft.status != "completed":
        raise RuntimeError(f"Writer interrupted: {draft.status!r}")
    return str(draft.final_output)
```

## 12. Remote API key and secret handling

Prefer environment variables or Kitaru secret configuration. Do not pass API keys
as visible flow parameters, request metadata, or log messages.

```python
import os

from agents import Agent
from kitaru.adapters.openai_agents import KitaruRunner

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Set OPENAI_API_KEY before running this workflow.")

agent = Agent(name="secure_agent", model="gpt-5-nano")
runner = KitaruRunner(agent, checkpoint_strategy="runner_call")
```

## 13. `KitaruAmbiguousFlowResultError` handling

If the migration keeps `calls`, prepare callers for ambiguous terminal flow
results.

```python
from typing import Protocol

from kitaru import KitaruAmbiguousFlowResultError

class RunnableFlow(Protocol):
    def run(self, value: str) -> object: ...


def wait_for_calls_mode_flow(flow_obj: RunnableFlow, value: str) -> object | None:
    try:
        handle = flow_obj.run(value)
        return handle.wait()  # type: ignore[attr-defined]
    except KitaruAmbiguousFlowResultError as error:
        print("The flow produced per-call artifacts instead of one terminal value.")
        print(error)
        return None
```

When the user wants a simple value from `.wait()`, switch to
`checkpoint_strategy="runner_call"` instead of wrapping calls mode inside a
checkpoint.
