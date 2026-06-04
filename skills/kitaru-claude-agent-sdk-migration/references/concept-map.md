# Claude Agent SDK to Kitaru Concept Map

Use this map while classifying source code. The safe migration story is simple:
Claude Agent SDK owns the inner Claude Code-style loop; Kitaru records one outer
SDK invocation.

## Mapping labels

- `direct`: Kitaru has a close adapter surface for the same outer behavior.
- `approximate`: Migration is possible, but replay, workspace, session,
  transcript, option, or capture behavior differs.
- `absent`: No safe automatic migration. The code needs redesign or explicit
  human review before migration.

## Core concepts

| Claude Agent SDK source pattern | Kitaru target pattern | Mapping | Notes |
|---|---|---:|---|
| `claude_agent_sdk.query(prompt=..., options=...)` | `runner.run/run_sync(ClaudeRunRequest.start(prompt))` | `direct` for one invocation | Kitaru changes the outer doorway, not Claude's loop. |
| `ClaudeSDKClient(...).query(...)` | `KitaruClaudeRunner.run(...)` for one task | `approximate` | Client streaming/control surfaces may not map exactly; preserve only supportable invocation behavior. |
| `ClaudeAgentOptions(...)` fixed for all runs | `KitaruClaudeRunner(options=...)` | `direct` | Claude options pass through to the SDK invocation. |
| Options vary by request | `options_factory=lambda request: ClaudeAgentOptions(...)` | `approximate` | Factory runs per Kitaru request; avoid volatile captures. |
| `cwd=` in options or query | `ClaudeRunRequest.start(..., cwd=...)` or options | `direct` | Keep the path materialized. Do not pass checkpoint output handles. |
| `max_turns=` | `ClaudeRunRequest.start(..., max_turns=...)` | `direct` | Must be positive when provided. |
| Session ID captured from `SystemMessage`/`ResultMessage` | `ClaudeRunResult.session_id` | `direct` | Result envelope can expose the session ID. |
| `ClaudeAgentOptions(resume=session_id)` | `ClaudeRunRequest.resume(prompt, session_id=...)` plus options as needed | `approximate` | Claude session history remains SDK-owned and local/session-store dependent. |
| `ClaudeSDKClient` multi-turn chat | Separate Kitaru invocations with resume IDs, or leave client flow raw | `approximate` | Kitaru records invocation boundaries, not every streamed message. |
| Built-in tools: `Read`, `Write`, `Edit`, `Bash`, etc. | Same `allowed_tools` / permissions in Claude options | `approximate` | Claude executes the tools inside the invocation. Review side effects. |
| MCP servers | Same `mcp_servers` options | `approximate` | MCP calls remain Claude-owned inside the invocation. |
| Hooks | Same `hooks` options | `approximate` | Hooks can have side effects and are not separate Kitaru checkpoints. |
| Permissions / approval modes | Same Claude options | `approximate` | Kitaru does not replace Claude's permission system. |
| File checkpointing / `rewind_files(...)` | Leave Claude-owned; optionally capture IDs/paths as metadata/artifacts | `approximate` | It rewinds selected workspace files, not Kitaru execution state. |
| Transcripts / JSONL session files | Capture path or artifact only after privacy review | `approximate` | Transcripts can contain prompts, file paths, commands, and tool outputs. |
| `checkpoint_strategy="invocation"` | One Kitaru checkpoint around `query(...)` | `direct` | Only supported strategy. |
| `calls`, `runner_call`, `granular`, `model_call`, `tool_call`, `step`, `run` | No Kitaru mapping | `absent` | Kitaru intentionally rejects granular Claude-internal strategies. |
| Runner call inside existing Kitaru checkpoint | Move to flow scope, or explicit direct-execution opt-in | `absent` unless user accepts risk | Replay can duplicate the whole Claude invocation. |
| `runner.run_sync(...)` inside active event loop | `await runner.run(...)` | `absent` for sync shape | Do not preserve sync call in async code. |
| Workspace/file/API side effects | Application-owned idempotency or separate Kitaru flow steps | `approximate` or `absent` | Claude may repeat those effects if Kitaru replays the invocation. |
| Raw SDK messages returned from checkpoints | `ClaudeRunResult` or simple values | `absent until redesigned` | Raw message objects may not be serializable or privacy-safe. |
| Secrets in prompt/metadata | Use environment/secrets; keep out of durable metadata | `absent until fixed` | Kitaru artifacts and metadata may be retained. |

## Boundary decision guide

Use `invocation` when:

- one Claude task should be durable as a whole;
- the source uses `query(...)` or a single `ClaudeSDKClient.query(...)` task;
- tools/Bash/MCP/hooks are acceptable as Claude-owned internal behavior;
- the result envelope and optional captured artifacts are enough.

Do not use this adapter when:

- the user requires Kitaru to checkpoint every Claude tool/Bash/MCP step;
- replaying the whole invocation would repeat destructive file/API effects;
- session files or workspace changes cannot be made durable or idempotent enough
  for the target deployment.

## What Kitaru does not own

Kitaru does not own Claude's model calls, tool execution, Bash execution, MCP
calls, hooks, permissions, session JSONL files, workspace edits, or file
checkpointing/rewind mechanics. If the source depends on those internals being
replayed as separate Kitaru units, mark the mapping `absent` or `approximate` and
explain the boundary clearly.
