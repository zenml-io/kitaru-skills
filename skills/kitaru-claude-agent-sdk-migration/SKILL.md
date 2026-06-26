---
name: kitaru-claude-agent-sdk-migration
description: >
  Migrate existing Claude Agent SDK code to Kitaru's Claude Agent SDK adapter.
  Use when code mentions claude_agent_sdk, claude_agent_sdk.query, query,
  ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, SystemMessage, session_id,
  resume, cwd, allowed_tools, Bash, Read, Write, Edit, MCP, hooks, permissions,
  file checkpointing, transcript, workspace, KitaruClaudeRunner,
  ClaudeRunRequest, ClaudeRunResult, ClaudeCapturePolicy, checkpoint_strategy,
  or invocation. Helps classify direct, approximate, and absent mappings, keep
  Claude-owned internals inside one invocation boundary, and produce a migration
  report with replay, workspace, session, tool, Bash, MCP, hook, and privacy
  risks called out.
---

# Migrate Claude Agent SDK to Kitaru

## What this skill does

Use this skill to inspect existing Claude Agent SDK code and move the safe outer
execution boundary to Kitaru's `KitaruClaudeRunner`, `ClaudeRunRequest`, and
`ClaudeRunResult` surfaces.

The output should be conservative:

1. A pattern inventory of the source code.
2. A migration plan that classifies every important pattern as `direct`,
   `approximate`, or `absent`.
3. Migrated or proposed code.
4. A `MIGRATION_REPORT.md` section or file that names behavior changes and
   review risks.

Do not promise that Kitaru can see or replay Claude-internal model calls, tool
calls, Bash commands, MCP calls, hooks, permissions, workspace edits, or file
checkpointing steps.

## Mental model: Claude runs the loop; Kitaru records one invocation

Claude Agent SDK owns the inner Claude Code-style loop. It decides which files to
read, which Bash commands to run, which tools or MCP servers to call, which hooks
fire, how permissions work, and how sessions/files are recorded.

Kitaru changes the doorway you use to enter that loop:

```python
import kitaru
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner, ClaudeRunRequest

runner = KitaruClaudeRunner(
    name="read_only_reviewer",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
)

@kitaru.flow
def review(prompt: str) -> str:
    result = runner.run_sync(ClaudeRunRequest.start(prompt))
    return result.final_text or ""
```

Concrete story: Claude starts, reads files, maybe runs tools or Bash, maybe uses
MCP or hooks, and eventually returns a final result message. Claude owns that
story. Kitaru records one completed invocation around it.

## When to use this skill

Use it when the user asks to:

- replace `claude_agent_sdk.query(...)` with `KitaruClaudeRunner`;
- wrap one Claude Agent SDK task in a Kitaru flow;
- preserve `ClaudeAgentOptions`, `cwd`, `max_turns`, `allowed_tools`, MCP,
  hooks, permissions, or sessions;
- handle `session_id` / `resume` through `ClaudeRunRequest.resume(...)`;
- review file checkpointing, transcripts, workspace file changes, Bash, or MCP
  under Kitaru replay;
- choose the only supported strategy: `checkpoint_strategy="invocation"`;
- produce a migration report for Claude Agent SDK code.

## When not to use this skill

Do not use it to:

- claim Kitaru can checkpoint Claude's internal model/tool/Bash/MCP/hook steps;
- rewrite the user's code into LangGraph, OpenAI Agents, Gemini Interactions, or
  PydanticAI;
- convert Claude file checkpointing into Kitaru workspace snapshots;
- hide replay, workspace, permission, privacy, or side-effect risks just to
  produce cleaner code;
- call `KitaruClaudeRunner` from inside an existing Kitaru checkpoint unless the
  user explicitly opts into direct execution and accepts replay risk.

## The three mapping types

Classify each source pattern before editing:

- `direct`: Kitaru has a close adapter surface for the same outer behavior.
  Example: one `query(prompt=...)` task becomes
  `runner.run_sync(ClaudeRunRequest.start(prompt))`.
- `approximate`: The code can move, but replay, session, transcript, workspace,
  capture, or option behavior differs. Example: `ClaudeAgentOptions` becomes
  fixed `options=` or per-request `options_factory=`.
- `absent`: There is no safe automatic migration. Example: a plan to checkpoint
  each Claude Bash command as a Kitaru checkpoint.

Unsupported patterns must not be silently approximated. Add a concrete
`# TODO(migration): ...` comment near proposed code, list it in the report, and
explain the redesign needed.

## Migration workflow

1. **Inspect source first.** Find `query(...)`, `ClaudeSDKClient`, options,
   `allowed_tools`, `cwd`, `max_turns`, sessions, transcripts, MCP servers,
   hooks, permissions, file checkpointing, Bash, workspace writes, and existing
   Kitaru decorators.
2. **Classify every pattern.** Use `references/concept-map.md` and
   `references/gaps-and-flags.md`. Count direct, approximate, high-risk, and
   blocked items.
3. **Choose Kitaru boundaries.** Use only `checkpoint_strategy="invocation"`.
   One completed Claude SDK invocation becomes one Kitaru checkpoint.
4. **Present the plan before generating code** when the migration is more than a
   tiny entrypoint replacement. Name risky tools, workspace writes, and privacy
   capture decisions before editing.
5. **Draft migrated code.** Replace raw `query(...)` entrypoints with
   `KitaruClaudeRunner` plus `ClaudeRunRequest`. Keep Claude options Claude-owned
   and add explicit capture-policy review.
6. **Produce `MIGRATION_REPORT.md`.** Include the inventory, chosen boundary,
   classifications, flags, behavior differences, and verification plan.
7. **Verify behavior.** Prefer read-only examples with `allowed_tools=[]` or safe
   read-only tools. If provider execution is not run, say the check was static.

## Pattern detection checklist

Look for:

- `from claude_agent_sdk import query`, `query(...)`, `ClaudeSDKClient`,
  `client.query(...)`, or `client.receive_response()`.
- `ClaudeAgentOptions(...)`, `cwd=`, `max_turns=`, `allowed_tools=`,
  `permission_mode=`, `setting_sources=`, `mcp_servers=`, `hooks=`, or custom
  agents/skills/plugins.
- `SystemMessage`, `ResultMessage`, `session_id`, `resume=`,
  `continue_conversation`, `fork_session`, transcripts, or session stores.
- `enable_file_checkpointing=True`, `rewind_files(...)`, or checkpoint UUIDs.
- Built-in tools such as `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`,
  `WebSearch`, `WebFetch`, or `AskUserQuestion`.
- Bash commands, filesystem edits, external API calls, database writes, ticket
  creation, emails, Slack messages, or other side effects triggered by Claude.
- Existing `@kitaru.flow` or `@kitaru.checkpoint` wrappers.
- Attempts to configure `calls`, `runner_call`, `model_call`, `tool_call`,
  `step`, `run`, or granular checkpoints.

## Boundary decision rules

- Keep `claude_agent_sdk` as the agent runtime.
- Use `KitaruClaudeRunner(name=..., checkpoint_strategy="invocation")`.
- Use `options=` for fixed `ClaudeAgentOptions` and `options_factory=` when
  options depend on the `ClaudeRunRequest`.
- Use `ClaudeRunRequest.start(prompt, cwd=..., max_turns=...)` for fresh tasks.
- Use `ClaudeRunRequest.resume(prompt, session_id=..., cwd=...)` when the source
  resumes a specific Claude session.
- Keep session files/transcripts/file checkpointing Claude-owned. Capture paths
  or artifacts only when the privacy policy allows it.
- Move durable file/tool/API side effects into Kitaru-owned flow steps after
  Claude returns when exact replay matters.
- For replay planning, there is one invocation checkpoint and one coarse `at`
  target. Do not promise granular overrides for Claude-internal Bash, tool, MCP,
  hook, permission, or file-workspace steps.
- Do not run this adapter inside an existing Kitaru checkpoint unless the user
  explicitly chooses `allow_direct_execution_inside_checkpoint=True` and accepts
  duplicate-invocation risk.

## Claude Agent SDK migration quick guide

Minimal read-only migration:

```python
import kitaru
from claude_agent_sdk import ClaudeAgentOptions
from kitaru.adapters.claude_agent_sdk import KitaruClaudeRunner, ClaudeRunRequest

runner = KitaruClaudeRunner(
    name="read_only_reviewer",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
)

@kitaru.flow
def review_code(prompt: str) -> str:
    result = runner.run_sync(ClaudeRunRequest.start(prompt))
    return result.final_text or ""

print(review_code.run("Summarize the repository structure.").wait())
```

For full examples, load `references/code-patterns.md`.

## Gap handling rules

When a pattern is unsafe or unsupported:

1. Do not silently approximate it.
2. Add a concrete `# TODO(migration): ...` comment near the code if producing
   code.
3. Add a report entry with severity `LOW`, `MEDIUM`, `HIGH`, or `BLOCKER`.
4. Explain the bad outcome the flag prevents. Example: "Claude runs Bash inside
   the invocation; if Kitaru replays the invocation, the Bash command may run
   again."
5. Propose the smallest safe redesign.

## Report requirements

Every non-trivial migration must include or draft `MIGRATION_REPORT.md` with:

- source files reviewed and changed/proposed;
- classification totals;
- source pattern inventory;
- chosen Kitaru invocation boundary;
- direct translations;
- approximate translations and caveats;
- flagged items with severity and required action;
- Claude-specific notes for the one invocation replay target, options,
  sessions/resume, workspace effects, file checkpointing, transcripts, MCP,
  hooks, permissions, Bash/tools, capture policy, and direct execution inside
  checkpoints;
- verification plan and whether execution was actually run.

Use `references/report-template.md` when a full report is needed.

## Anti-patterns

Avoid these:

- Using any checkpoint strategy except `"invocation"`.
- Claiming Kitaru replays Claude-internal model/tool/Bash/MCP/hook steps.
- Treating Claude file checkpointing as Kitaru checkpointing.
- Ignoring workspace edits or Bash side effects.
- Returning raw SDK message objects from Kitaru checkpoints.
- Passing API keys, prompts, transcripts, file paths, or user data as Kitaru
  metadata without a privacy review.
- Calling `runner.run_sync(...)` from inside an active event loop.
- Calling the runner inside another Kitaru checkpoint without explicit opt-in.

## References

Load only the reference file needed for the current task:

- `references/concept-map.md` — source-to-target mapping table and
  classification guidance.
- `references/code-patterns.md` — import-complete migration examples.
- `references/gaps-and-flags.md` — severity definitions, upstream assumptions,
  and must-flag patterns.
- `references/report-template.md` — Claude Agent SDK-specific migration report
  template.

Kitaru source references:

- Kitaru Claude Agent SDK adapter docs:
  `kitaru/docs/content/docs/adapters/claude-agent-sdk.mdx`
- Adapter exports:
  `kitaru/src/kitaru/adapters/claude_agent_sdk/__init__.py`
- Adapter example:
  `kitaru/examples/integrations/claude_agent_sdk_agent/README.md`
