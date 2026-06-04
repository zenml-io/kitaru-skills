# Migration Report: Claude Agent SDK to Kitaru Adapter

Use this template for `MIGRATION_REPORT.md` or for a report section in the final
answer when the user does not want a file written.

## Summary

- Source framework: Claude Agent SDK
- Target adapter: `kitaru.adapters.claude_agent_sdk.KitaruClaudeRunner`
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
| `[file:line]` | `query(prompt=...)` | `direct` | `LOW` | Replaced with `KitaruClaudeRunner` invocation. |
| `[file:line]` | `[pattern]` | `[direct / approximate / absent]` | `[LOW / MEDIUM / HIGH / BLOCKER]` | `[concrete note]` |

## Chosen Kitaru Boundaries

Describe the save points in plain language.

Example:

- The Claude Agent SDK remains the agent runtime.
- `KitaruClaudeRunner` is constructed once with a stable name.
- The adapter uses `checkpoint_strategy="invocation"`, so one completed
  `claude_agent_sdk.query(...)` invocation becomes one Kitaru checkpoint.
- Claude tools, Bash, MCP, hooks, permissions, sessions, transcripts, and file
  checkpointing remain Claude-owned inside that invocation.

## Direct Translations

| Source | Target | Why direct |
|---|---|---|
| `query(prompt=prompt, options=options)` | `runner.run_sync(ClaudeRunRequest.start(prompt))` | Same one-task SDK invocation; Kitaru changes the outer doorway. |
| `[source]` | `[target]` | `[reason]` |

## Approximate Translations

| Source | Target | Behavior difference | Verification step |
|---|---|---|---|
| `ClaudeAgentOptions(resume=session_id)` | `ClaudeRunRequest.resume(prompt, session_id=...)` | Session history remains Claude-owned and depends on cwd/session storage. | Resume a known session from the target environment. |
| `[source]` | `[target]` | `[difference]` | `[step]` |

## Flagged for Human Review

| Severity | Source location | Issue | What could break | Required action |
|---|---|---|---|---|
| `HIGH` | `[file:line]` | `[issue]` | `[duplicate Bash/file/API side effect / lost session / sensitive transcript / etc.]` | `[review or redesign step]` |

## Adapter-Specific Notes

### Runner identity and strategy

- Runner name: `[name]`
- Chosen strategy: `invocation`
- Unsupported strategies found: `[none/list]`

### Options and permissions

- Fixed `options=` used: `[yes/no]`
- `options_factory=` used: `[yes/no]`
- `allowed_tools`: `[list]`
- Permission mode: `[mode/default]`
- Risk note: `[what Claude can do inside the invocation]`

### Sessions and resume

- Captures `session_id`: `[yes/no]`
- Uses resume: `[yes/no]`
- `cwd` stable across resume: `[yes/no/unknown]`
- Session storage caveat:
  - `[local session file / shared store / explicitly passed state]`

### Workspace, Bash, and file checkpointing

- File-writing tools enabled: `[yes/no/list]`
- Bash enabled: `[yes/no]`
- File checkpointing enabled: `[yes/no]`
- Rewind IDs captured: `[yes/no/not needed]`
- Replay consequence:
  - `[what may run again if Kitaru replays the whole invocation]`

### MCP, hooks, and custom tools

- MCP servers found: `[yes/no/list]`
- Hooks found: `[yes/no/list]`
- Custom tools/subagents/skills/plugins found: `[yes/no/list]`
- Side effects reviewed: `[yes/no]`

### Capture and privacy policy

- Capture policy configured: `[yes/no]`
- Messages saved: `[yes/no/default]`
- Transcript saved: `[yes/no/default]`
- Output saved: `[yes/no/default]`
- Options manifest saved: `[yes/no/default]`
- Sensitive data risk: `[none known / needs review]`

## Behavioral Differences

Explain concrete differences introduced by the migration.

Examples:

- "The source previously called `claude_agent_sdk.query(...)` directly. The
  migrated code calls the same SDK through `KitaruClaudeRunner`, so Kitaru can
  record one completed invocation result."
- "Claude file checkpointing remains Claude-owned. Kitaru does not snapshot the
  workspace or rewind files."
- "Bash and MCP calls happen inside the invocation. If Kitaru replays the
  invocation, those effects may happen again unless the project makes them safe."

## What Is Not Migrated

| Item | Reason | Recommended redesign |
|---|---|---|
| `[item]` | `[why absent or unsafe]` | `[redesign]` |

## Verification Plan

- Static checks:
  - `[imports resolve / strategy is invocation / no runner call inside checkpoint]`
- Read-only dry-run:
  - `[allowed_tools=[] or Read/Glob/Grep command]`
- Provider-backed run:
  - `[command or not run because credentials unavailable]`
- Kitaru behavior checks:
  - Confirm execution appears in dashboard or `kitaru executions list`.
  - Confirm one invocation checkpoint appears.
  - Confirm resume works if sessions are migrated.
  - Confirm replay does not duplicate unsafe workspace or external side effects.

## Docs and Reference Links

- Kitaru Claude Agent SDK adapter docs:
  `kitaru/docs/content/docs/adapters/claude-agent-sdk.mdx`
- Kitaru Claude adapter exports:
  `kitaru/src/kitaru/adapters/claude_agent_sdk/__init__.py`
- Skill references:
  - `skills/kitaru-claude-agent-sdk-migration/references/concept-map.md`
  - `skills/kitaru-claude-agent-sdk-migration/references/code-patterns.md`
  - `skills/kitaru-claude-agent-sdk-migration/references/gaps-and-flags.md`

## Recommended Next Steps

1. `[Run read-only SDK smoke test / provider-backed smoke test]`
2. `[Review HIGH/BLOCKER workspace, Bash, MCP, hook, and transcript items]`
3. `[Decide whether options should be fixed or request-specific]`
4. `[Add project-specific tests for replay and side effects]`
5. `[Update user-facing docs or examples if this migration changes public behavior]`
