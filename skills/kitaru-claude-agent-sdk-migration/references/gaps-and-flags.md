# Claude Agent SDK Migration Gaps and Flags

Use this file when deciding whether a migration is safe to apply automatically.
The rule is: if replay, workspace, session, transcript, permission, side effect,
secret, or SDK resume behavior may change, make that visible in code comments
and in the migration report.

## Upstream docs checked

Checked on 2026-06-04 against current official docs:

- Agent SDK overview: https://platform.claude.com/docs/en/agent-sdk/overview
- Python SDK reference: https://platform.claude.com/docs/en/agent-sdk/python
- Sessions: https://platform.claude.com/docs/en/agent-sdk/sessions
- Hooks: https://platform.claude.com/docs/en/agent-sdk/hooks
- MCP: https://platform.claude.com/docs/en/agent-sdk/mcp
- File checkpointing: https://platform.claude.com/docs/en/agent-sdk/file-checkpointing

Assumptions recorded here: `query(...)`, `ClaudeAgentOptions`, and
`ClaudeSDKClient` remain the main Python surfaces; sessions are Claude-owned and
resume by ID; file checkpointing rewinds selected file changes, not conversation
or Kitaru execution state; tools, Bash, MCP, hooks, and permissions execute
inside the Claude invocation.

## Severity levels

| Severity | Meaning | Required action |
|---|---|---|
| `LOW` | Cosmetic or documentation-only difference. | Migrate and mention in report. |
| `MEDIUM` | Behavior probably preserved, but settings or observability differ. | Migrate with caveat and verification step. |
| `HIGH` | Replay, workspace, session, side-effect, privacy, or runtime behavior may change. | Require human review before applying or mark partial migration. |
| `BLOCKER` | Migration would be unsafe or impossible without source redesign. | Do not auto-migrate; generate redesign note and report entry. |

## Must-flag patterns

### Unsupported granular checkpoint strategies

- **Severity:** `BLOCKER`.
- **Pattern:** `checkpoint_strategy="calls"`, `"runner_call"`, `"granular"`,
  `"model_call"`, `"tool_call"`, `"step"`, or `"run"`.
- **Why it matters:** Kitaru's Claude adapter only supports one invocation
  boundary. Claude-internal steps are not Kitaru checkpoints.
- **Action:** use `checkpoint_strategy="invocation"` or redesign.

### Runner call inside existing Kitaru checkpoint

- **Severity:** `BLOCKER` unless the user explicitly accepts direct execution
  risk.
- **Pattern:** `KitaruClaudeRunner.run/run_sync(...)` called from a
  `@kitaru.checkpoint` body.
- **Why it matters:** replaying the outer checkpoint may run the whole Claude
  invocation again: files changed twice, Bash run twice, API called twice.
- **Action:** move the runner call to flow scope, or set
  `allow_direct_execution_inside_checkpoint=True` only with an explicit report
  warning.

### Bash or write tools without idempotency

- **Severity:** `HIGH`; `BLOCKER` for destructive/customer-visible effects.
- **Pattern:** `allowed_tools` includes `Bash`, `Write`, `Edit`, or tools/MCP
  servers that mutate external systems.
- **Why it matters:** Kitaru replays the invocation as one unit. Claude may run
  the same command or edit again.
- **Action:** restrict tools, add idempotency/safety checks, or move critical
  side effects into reviewed Kitaru-owned flow steps after Claude returns.

### File checkpointing treated as Kitaru checkpointing

- **Severity:** `HIGH`.
- **Pattern:** migration claims `enable_file_checkpointing=True` gives Kitaru
  durable workspace snapshots.
- **Why it matters:** Claude file checkpointing tracks selected file edits for
  rewind; it does not rewind the Claude conversation or Kitaru execution state,
  and Bash file writes are not covered by Claude's file checkpointing limits.
- **Action:** describe file checkpointing as Claude-owned. Capture IDs/paths only
  if useful and privacy-safe.

### Session resume without stable `cwd` / session storage

- **Severity:** `HIGH`.
- **Pattern:** `resume=session_id` or `ClaudeRunRequest.resume(...)` without
  checking that the session exists under the same working directory or shared
  session store.
- **Why it matters:** Claude session lookup can miss the old transcript and start
  without expected context.
- **Action:** preserve `cwd`, mirror session files/shared storage if needed, or
  pass needed state explicitly into a fresh prompt.

### Transcript or message capture without privacy review

- **Severity:** `MEDIUM`, or `HIGH` for customer data, source code, secrets,
  incident data, or regulated workflows.
- **Pattern:** migration enables broad transcript/message/output capture by
  default.
- **Why it matters:** transcripts can contain prompts, tool arguments, command
  output, file paths, and user data.
- **Action:** choose an explicit `ClaudeCapturePolicy(...)` and record what is
  saved.

### Hooks with side effects

- **Severity:** `HIGH`.
- **Pattern:** hooks write audit files, send webhooks, update databases, or block
 /modify tool calls in ways the migration does not inspect.
- **Why it matters:** hooks run inside the Claude invocation and may run again on
  replay.
- **Action:** make hooks idempotent, move durable side effects outside the
  invocation, or keep the migration plan-only.

### `ClaudeSDKClient` streaming/control flow mapped as if identical

- **Severity:** `MEDIUM` to `HIGH`.
- **Pattern:** source depends on streamed intermediate messages,
  `receive_response()`, progress monitoring, or interactive client lifecycle.
- **Why it matters:** Kitaru runner records one invocation result envelope, not
  arbitrary client streaming behavior.
- **Action:** migrate only the one-task invocation, or leave complex streaming
  client code raw and report the difference.

### `run_sync` inside an active event loop

- **Severity:** `BLOCKER` for preserving sync shape.
- **Pattern:** async application code calls sync query/runner methods.
- **Why it matters:** keeping sync execution preserves the event-loop bug.
- **Action:** convert caller to `await runner.run(...)`.

### Secrets in prompt, metadata, logs, or transcripts

- **Severity:** `BLOCKER`.
- **Pattern:** API keys/tokens are passed as prompts, request metadata, or logged
  outputs.
- **Why it matters:** Kitaru may store request metadata and artifacts durably.
- **Action:** use environment variables or a secret manager; remove secrets from
  prompts, metadata, and logs.

## Required report entry shape

```markdown
- Severity: HIGH
- Source location: path/to/agent.py:123
- Pattern: `allowed_tools=["Bash", "Edit"]` inside one Kitaru invocation
- Migration action: migrated outer invocation only
- Why it matters: replay may run the same Bash command or edit again
- Required human decision: restrict tools or add idempotent workspace checks
```

## Code comment shape

```python
# TODO(migration): Claude can run Bash inside this invocation. If Kitaru replays
# the invocation, the command may run again. Add idempotency or restrict tools
# before relying on this boundary for production replay.
```
