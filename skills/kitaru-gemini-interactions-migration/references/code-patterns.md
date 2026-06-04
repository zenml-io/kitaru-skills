# Gemini Interactions Migration Code Patterns

These examples are intentionally import-complete. Copy the shape, then adapt
models, agents, environments, client factories, cache identities, capture policy,
and local tool bodies to the source project. They are static/signature-oriented
examples, not provider-live smoke tests.

## 1. Minimal `client.interactions.create(...)` model replacement

Source:

```python
from google import genai

client = genai.Client()
interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="Write a short summary of durable AI workflows.",
)
print(interaction.output_text)
```

Target:

```python
import kitaru
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(name="gemini_summary")

@kitaru.flow
def summarize(topic: str) -> str:
    request = GeminiInteractionRequest.start(
        f"Write a short summary of {topic}.",
        model="gemini-3.5-flash",
    )
    result = runner.run_sync(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed interaction, got {result.status!r}")
    return result.output_text or ""

handle = summarize.run("durable AI workflows")
print(handle.wait())
```

Outside an explicit Kitaru flow, this is adapter API wiring. For production
replay, place the runner call in a Kitaru flow.

## 2. Async interaction runner

Use this when the caller is already async.

```python
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(name="async_gemini_summary")

async def summarize_async(topic: str) -> str:
    request = GeminiInteractionRequest.start(
        f"Explain {topic} in three bullets.",
        model="gemini-3.5-flash",
    )
    result = await runner.run(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed interaction, got {result.status!r}")
    return result.output_text or ""
```

Do not keep `run_sync(...)` inside an active event loop.

## 3. Client factory and `cache_identity`

Use `cache_identity` when the same runner name and request can point at different
projects, regions, credential aliases, endpoints, or client configuration.

```python
from google import genai
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)


def build_client() -> genai.Client:
    return genai.Client()

runner = KitaruGeminiInteractionsRunner(
    name="regional_gemini_summary",
    client_factory=build_client,
    cache_identity="dev-project/global",
)


def summarize_for_region(topic: str) -> str:
    request = GeminiInteractionRequest.start(
        f"Summarize {topic}.",
        model="gemini-3.5-flash",
    )
    result = runner.run_sync(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed interaction, got {result.status!r}")
    return result.output_text or ""
```

Report caveat: `cache_identity` must be stable and non-secret. It should describe
the client world, not contain API keys or live object representations.

## 4. Resume with `previous_interaction_id`

Source shape:

```python
follow_up = client.interactions.create(
    model="gemini-3.5-flash",
    input="Turn that into a checklist.",
    previous_interaction_id=interaction.id,
)
```

Target shape:

```python
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(name="gemini_followups")


def continue_interaction(previous_interaction_id: str) -> str:
    request = GeminiInteractionRequest.resume(
        "Turn that into a checklist.",
        previous_interaction_id=previous_interaction_id,
        model="gemini-3.5-flash",
    )
    result = runner.run_sync(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed interaction, got {result.status!r}")
    return result.output_text or ""
```

Report caveat: server-side history remains Google-owned. Confirm the source uses
`store=True` and that the previous interaction is still retained.

## 5. `requires_action` and function-result handoff

When Gemini asks for a local function result, bring that work back into the
Kitaru flow. Do not hide it inside a provider-owned loop.

```python
import kitaru
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    GeminiInteractionResult,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(name="tool_call_gemini")


def run_local_lookup(city: str) -> dict[str, str]:
    return {"city": city, "forecast": "sunny"}


@kitaru.flow
def continue_after_requires_action(first: GeminiInteractionResult, city: str) -> str:
    if first.status != "requires_action":
        raise RuntimeError(f"Expected requires_action, got {first.status!r}")
    if first.interaction_id is None:
        raise RuntimeError("requires_action result did not include interaction_id")

    call = next((step for step in first.steps if step.call_id), None)
    if call is None or call.call_id is None:
        raise RuntimeError("requires_action result did not include a function call")

    local_result = run_local_lookup(city)
    second_request = GeminiInteractionRequest.function_result(
        previous_interaction_id=first.interaction_id,
        function_call_id=call.call_id,
        function_name=call.tool_name,
        function_result=local_result,
        model="gemini-3.5-flash",
    )
    second = runner.run_sync(second_request)
    if second.status != "completed":
        raise RuntimeError(f"Expected completed interaction, got {second.status!r}")
    return second.output_text or ""
```

The first `requires_action` response may come from source code that already
configured Gemini tools. Keep that provider-specific tool declaration from the
source project; this example focuses on the Kitaru handoff after Gemini has
already asked for a function result.

If a human must approve the local work, call `kitaru.wait()` from flow scope
between the `requires_action` result and the later `function_result` request.

## 6. Poll an existing background interaction

Source shape:

```python
interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="Run a long analysis.",
    background=True,
    store=True,
)
latest = client.interactions.get(interaction_id=interaction.id)
```

Target shape:

```python
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(name="background_gemini")


def start_background_job(topic: str):
    request = GeminiInteractionRequest.start(
        f"Run a long analysis of {topic}.",
        model="gemini-3.5-flash",
        background=True,
        store=True,
    )
    return runner.run_sync(request)


def poll_background_job(interaction_id: str):
    return runner.run_sync(GeminiInteractionRequest.poll(interaction_id=interaction_id))
```

Report caveat: if the job is not yet `completed` or `requires_action`, Kitaru
raises instead of saving an unfinished response as successful work. Poll the same
`interaction_id`; do not start a duplicate background job unless that is
intentional.

## 7. Antigravity managed-agent preset

Use Antigravity intentionally as a managed-agent use case, not as the adapter's
primary identity.

```python
import kitaru
from kitaru.adapters.gemini import (
    GeminiInteractionRequest,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(
    name="antigravity_repo_review",
    cache_identity="dev-project/global",
)

@kitaru.flow
def review_repo() -> str:
    request = GeminiInteractionRequest.antigravity(
        "Inspect this repository and summarize the test strategy. Do not edit files.",
        environment="remote",
        timeout_s=300,
    )
    result = runner.run_sync(request)
    if result.status != "completed":
        raise RuntimeError(f"Expected completed Antigravity run, got {result.status!r}")
    return result.output_text or ""
```

Report caveat: Antigravity sandbox files, web/code execution, managed-agent
planning, and environment reuse remain Google-owned. The Kitaru checkpoint is the
stable interaction response, not a filesystem snapshot.

## 8. Capture policy review

```python
from kitaru.adapters.gemini import (
    GeminiInteractionCapturePolicy,
    KitaruGeminiInteractionsRunner,
)

runner = KitaruGeminiInteractionsRunner(
    name="privacy_reviewed_gemini",
    capture=GeminiInteractionCapturePolicy(
        emit_events=True,
        save_input=False,
        save_request_manifest=True,
        save_raw_interaction=False,
        save_steps=False,
        save_output=True,
        save_usage=True,
        redact_request_manifest=True,
    ),
)
```

Raw prompts, tool arguments, provider payloads, step contents, generated files,
and user data may be sensitive. The migration report should say exactly what is
saved and why.
