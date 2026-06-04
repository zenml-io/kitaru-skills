# Claude Agent SDK Migration Code Patterns

These examples are intentionally import-complete. Copy the shape, then adapt
names, prompts, `cwd`, options, permissions, and capture settings to the source
project. They are not provider-live smoke tests.

## 1. Minimal `query(...)` replacement

Source:

```python
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

async def main() -> None:
    async for message in query(
        prompt="Summarize this repository.",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
    ):
        if isinstance(message, ResultMessage):
            print(message.result)

asyncio.run(main())
```

Target:

```python
import kitaru
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner, ClaudeRunRequest

runner = KitaruClaudeRunner(
    name="repo_summarizer",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
)

@kitaru.flow
def summarize_repo(prompt: str) -> str:
    result = runner.run_sync(ClaudeRunRequest.start(prompt))
    return result.final_text or ""

handle = summarize_repo.run("Summarize this repository.")
print(handle.wait())
```

## 2. Async Kitaru runner

Use this when the caller is already async.

```python
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner, ClaudeRunRequest

runner = KitaruClaudeRunner(
    name="async_reviewer",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
)

async def review_async(prompt: str) -> str:
    result = await runner.run(ClaudeRunRequest.start(prompt))
    return result.final_text or ""
```

Do not keep `run_sync(...)` inside an active event loop.

## 3. Request-specific options with `options_factory`

Use a factory when fields vary per request. Keep the factory deterministic and
avoid capturing secrets or live clients.

```python
import kitaru
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import (
    ClaudeRunRequest,
    KitaruClaudeRunner,
)


def options_for_request(request: ClaudeRunRequest) -> ClaudeAgentOptions:
    allowed_tools = ["Read", "Glob", "Grep"]
    if request.metadata.get("allow_edits") is True:
        allowed_tools = ["Read", "Glob", "Grep", "Edit"]
    return ClaudeAgentOptions(
        allowed_tools=allowed_tools,
        cwd=request.cwd,
    )

runner = KitaruClaudeRunner(
    name="request_sensitive_claude",
    options_factory=options_for_request,
)

@kitaru.flow
def run_task(prompt: str, cwd: str, allow_edits: bool) -> str:
    request = ClaudeRunRequest.start(
        prompt,
        cwd=cwd,
        metadata={"allow_edits": allow_edits},
    )
    result = runner.run_sync(request)
    return result.final_text or ""
```

If `allow_edits=True`, flag workspace side effects for human review.

## 4. Resume a Claude session

Source shape:

```python
from claude_agent_sdk import ClaudeAgentOptions, query

async for message in query(
    prompt="Continue the refactor.",
    options=ClaudeAgentOptions(resume=session_id),
):
    ...
```

Target shape:

```python
import kitaru
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner, ClaudeRunRequest

def options_for_resume(request: ClaudeRunRequest) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        cwd=request.cwd,
        resume=request.resume_session_id,
        max_turns=request.max_turns,
    )


runner = KitaruClaudeRunner(
    name="claude_session_runner",
    options_factory=options_for_resume,
)

@kitaru.flow
def continue_session(
    prompt: str,
    session_id: str,
    cwd: str,
    max_turns: int,
) -> str:
    request = ClaudeRunRequest.resume(
        prompt,
        session_id=session_id,
        cwd=cwd,
        max_turns=max_turns,
    )
    result = runner.run_sync(request)
    return result.final_text or ""
```

Report caveat: Claude session files/history remain Claude-owned. Session
resume migrations should generally use `options_factory`, because request-scoped
fields such as `cwd`, `resume_session_id`, and `max_turns` must be copied into
`ClaudeAgentOptions` for each request. Preserve `cwd` and session storage, or
pass needed state explicitly into a fresh prompt.

## 5. Capture policy review

```python
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import (
    ClaudeCapturePolicy,
    KitaruClaudeRunner,
)

runner = KitaruClaudeRunner(
    name="privacy_reviewed_claude",
    options=ClaudeAgentOptions(allowed_tools=[]),
    capture=ClaudeCapturePolicy(
        emit_events=True,
        save_prompt=False,
        save_messages=False,
        save_transcript_file=False,
        save_options_manifest=True,
        save_final_output=True,
        save_usage=True,
        redact_options_manifest=True,
    ),
)
```

Adjust field names against the current Kitaru adapter if the capture policy has
changed. The migration report should say exactly what is saved.

## 6. Workspace side-effect warning

This is a possible migration shape, but it must be flagged when tools can write.

```python
import kitaru
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner, ClaudeRunRequest

runner = KitaruClaudeRunner(
    name="editing_claude",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Write", "Bash"],
        permission_mode="acceptEdits",
    ),
)

@kitaru.flow
def edit_code(prompt: str, cwd: str) -> str:
    # TODO(migration): Claude can edit files and run Bash inside this single
    # invocation. If Kitaru replays it, those effects may happen again. Add
    # idempotency, validation, or narrower tools before production use.
    result = runner.run_sync(ClaudeRunRequest.start(prompt, cwd=cwd))
    return result.final_text or ""
```

## 7. Keep file checkpointing Claude-owned

```python
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner

runner = KitaruClaudeRunner(
    name="file_checkpointing_claude",
    options=ClaudeAgentOptions(
        enable_file_checkpointing=True,
        permission_mode="acceptEdits",
        extra_args={"replay-user-messages": None},
    ),
)
```

Report caveat: Claude file checkpointing can rewind selected file changes, but
it is not Kitaru checkpointing. It does not make Bash writes or arbitrary
workspace state Kitaru-durable.
