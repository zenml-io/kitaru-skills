# Kitaru Agent Skills

Reusable Markdown agent skills for discovering, designing, migrating, and
building durable AI agent workflows with [Kitaru](https://kitaru.ai).

This repository contains nine shared skill directories plus Claude Code plugin
packaging. Claude Code can install the skills through its plugin flow. Codex,
Cursor, and other agent hosts can use the Markdown skill files and the
host-specific MCP setup guides where their local skill, rule, or context-loading
workflow supports that pattern.

## Skills

| Skill | Skill / invocation | Purpose |
|---|---|---|
| **kitaru-quickstart** | `kitaru-quickstart` (`/kitaru-quickstart` in Claude Code) | Interactive onboarding: scaffolds a personalized demo flow, demonstrates crash recovery with replay, human-in-the-loop with `wait()`, artifact capture, and optional MCP integration |
| **kitaru-scoping** | `kitaru-scoping` (`/kitaru-scoping` in Claude Code) | Structured interview to validate whether your workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, artifact strategy, operator surface, MVP scope) |
| **kitaru-authoring** | `kitaru-authoring` (`/kitaru-authoring` in Claude Code) | Guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `KitaruClient`, replay/resume/retry, deployments, secrets, CLI/MCP tools, and adapters for PydanticAI, OpenAI Agents, LangGraph, Claude Agent SDK, and Gemini Interactions |
| **kitaru-replay-lab** | `kitaru-replay-lab` (`/kitaru-replay-lab` in Claude Code) | Operational replay lab for existing executions: reproduce first, fork one change, inspect `ReplaySubmission`, diff results, replay cohorts, and diagnose waits, skipped rows, failures, and divergence |
| **kitaru-pydantic-ai-migration** | `kitaru-pydantic-ai-migration` (`/kitaru-pydantic-ai-migration` in Claude Code) | Migrate existing PydanticAI agent code to `KitaruAgent` with conservative boundary selection, direct/approximate/absent classification, HITL safety checks, capture policy guidance, and a migration report |
| **kitaru-openai-agents-migration** | `kitaru-openai-agents-migration` (`/kitaru-openai-agents-migration` in Claude Code) | Migrate existing OpenAI Agents SDK code to `KitaruRunner`, `OpenAIRunRequest`, and `OpenAIRunResult` with checkpoint strategy selection, approval/resume handling, context serialization checks, and a migration report |
| **kitaru-langgraph-migration** | `kitaru-langgraph-migration` (`/kitaru-langgraph-migration` in Claude Code) | Migrate existing LangGraph, LangChain `create_agent(...)`, or Deep Agents-style code to `KitaruGraphRunner` with honest `graph_call` vs middleware-backed `calls` boundary selection and a migration report |
| **kitaru-claude-agent-sdk-migration** | `kitaru-claude-agent-sdk-migration` (`/kitaru-claude-agent-sdk-migration` in Claude Code) | Migrate existing Claude Agent SDK code to `KitaruClaudeRunner` with one invocation checkpoint, Claude-owned tool/Bash/MCP/workspace caveats, capture policy review, and a migration report |
| **kitaru-gemini-interactions-migration** | `kitaru-gemini-interactions-migration` (`/kitaru-gemini-interactions-migration` in Claude Code) | Migrate existing Gemini Interactions, Google GenAI Interactions, or Antigravity managed-agent code to `KitaruGeminiInteractionsRunner` with `requires_action`, polling, function-result, Antigravity, and Google-owned internals caveats |

### Recommended workflow

For new Kitaru work:

1. **Quickstart** — use `kitaru-quickstart` to see what Kitaru does and build
   intuition for crash recovery, replay, waits, and artifacts
2. **Scope** — use `kitaru-scoping` to validate fit and define your flow
   architecture before writing code
3. **Author** — use `kitaru-authoring` to build the flows defined in your
   `flow_architecture.md`
4. **Replay Lab** — use `kitaru-replay-lab` when real executions exist and
   you want to recover, reproduce, fork, diff, or replay a cohort safely

For existing framework code:

1. **Inspect and classify** — use the migration skill that matches the source
   framework: PydanticAI, OpenAI Agents SDK, LangGraph/LangChain, Claude Agent
   SDK, or Gemini Interactions
2. **Migrate only recorded work** — choose the framework call Kitaru can
   record honestly: a wrapped PydanticAI run, an OpenAI Agents runner call or
   observed call, a LangGraph graph call or middleware-observed sync call, one Claude SDK
   invocation, or one stable Gemini Interactions response
3. **Review the report** — use the generated `MIGRATION_REPORT.md` to check
   replay, wait, state, approval/resume, interrupt, polling, context, privacy,
   and side-effect risks
4. **Author follow-up Kitaru code** — use `kitaru-authoring` for any additional
   flows, checkpoints, artifacts, CLI/MCP usage, or deployment work
5. **Operate real executions** — use `kitaru-replay-lab` to reproduce, fork,
   diff, or diagnose existing executions without inventing replay behavior

In Claude Code, those skills are exposed as slash commands:
`/kitaru-quickstart`, `/kitaru-scoping`, `/kitaru-authoring`,
`/kitaru-replay-lab`, `/kitaru-pydantic-ai-migration`, `/kitaru-openai-agents-migration`,
`/kitaru-langgraph-migration`, `/kitaru-claude-agent-sdk-migration`, and
`/kitaru-gemini-interactions-migration`.

## Installation and usage

### Claude Code plugin distribution

Claude Code users can install the packaged skills from the Claude Code plugin
marketplace:

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Once installed, Claude Code will automatically use the skills based on context.
You can also invoke them explicitly with `/kitaru-quickstart`,
`/kitaru-scoping`, `/kitaru-authoring`, `/kitaru-replay-lab`,
`/kitaru-pydantic-ai-migration`, `/kitaru-openai-agents-migration`, `/kitaru-langgraph-migration`,
`/kitaru-claude-agent-sdk-migration`, or
`/kitaru-gemini-interactions-migration`.

For project/team installation, add this to your project's
`.claude/settings.json`:

```json
{
  "plugins": {
    "kitaru": {
      "source": "zenml-io/kitaru-skills",
      "name": "kitaru"
    }
  }
}
```

For manual Claude Code installation during local development:

```bash
tmpdir=$(mktemp -d)
git clone --depth 1 https://github.com/zenml-io/kitaru-skills.git "$tmpdir/kitaru-skills"
mkdir -p .claude/skills
cp -R "$tmpdir/kitaru-skills/skills/kitaru-quickstart" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-scoping" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-authoring" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-replay-lab" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-pydantic-ai-migration" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-openai-agents-migration" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-langgraph-migration" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-claude-agent-sdk-migration" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-gemini-interactions-migration" .claude/skills/
rm -rf "$tmpdir"
```

See the [Claude Code host guide](skills/kitaru-quickstart/references/hosts/claude-code.md)
for MCP setup details.

### Codex usage

Codex setup depends on the Codex version and local configuration style you use.
If your Codex environment supports local skills, copy the nine
`skills/kitaru-*` directories into the supported Codex skills location or load
the relevant `SKILL.md` files as explicit project context.

For Kitaru MCP setup, follow the cautious host notes in the
[Codex host guide](skills/kitaru-quickstart/references/hosts/codex.md). Codex
MCP configuration can vary by installation, so use that guide as a starting
point and confirm against your current Codex documentation.

### Cursor usage

Cursor does not install this Claude Code plugin automatically. Use the Markdown
skill files as project rules or agent context according to the Cursor workflow
you already use.

For Kitaru MCP setup, see the
[Cursor host guide](skills/kitaru-quickstart/references/hosts/cursor.md), which
shows the `.cursor/mcp.json` stdio configuration pattern.

### Manual Markdown use

For any other capable agent host, open the relevant `skills/*/SKILL.md` file and
ask the agent to follow it. This is the portable fallback path when the host does
not have a formal skill or plugin system.

## Example prompts

**Quickstart:**
- "I want to try Kitaru — show me what it does."
- "Give me a five-minute tour of Kitaru's crash recovery."
- "Set up a Kitaru demo for my data pipeline workflow."
- "Walk me through Kitaru with MCP integration."

**Scoping:**
- "I want to build a research agent — is Kitaru right for this?"
- "Help me figure out where to put checkpoints in my coding agent workflow."
- "Should repo conventions be stored as explicit artifacts or outside the flow?"
- "I have a complex agent with 10 steps — help me scope it down."

**Authoring:**
- "Refactor this script into one `@flow` with explicit checkpoints."
- "Add a flow-level `kitaru.wait()` approval gate before publish."
- "Add explicit artifact saving to this flow."
- "How do I inspect executions, waits, logs, and artifacts from the CLI or MCP?"
- "Show me how to use `--at`, `--flow-overrides`, `--checkpoint-overrides`, and `--invocation-overrides` safely from the CLI."
- "Add stable checkpoint names so future replays have clear `at` selectors."

**Replay Lab:**
- "Replay execution `kr-a8f3c2` at `write_draft` with a top-level
  `prompt_profile` flow override, then diff the replay against the original."
- "Replay this failed execution safely and tell me where to restart from."
- "Run a no-change replay first, then fork with a different model and diff the outputs with CLI or MCP."
- "Use CLI or MCP to resolve a cohort of recent failed executions, then replay
  the explicit IDs with one checkpoint override and summarize every `ReplaySubmission` row."
- "This replay diverged — help me diagnose whether the code, selector, or external data changed."
- "This replay would rerun a side-effectful checkpoint — help me decide whether
  to use `kitaru.is_replay()`, idempotency, or a different checkpoint design."

**Adapter authoring:**
- "Help me add Kitaru durability around a LangGraph graph."
- "Make this Claude Agent SDK invocation durable without promising granular tool replay."
- "Add Kitaru durability around this Gemini Interactions flow without treating Antigravity internals as replayable."

**PydanticAI migration:**
- "Migrate this `pydantic_ai.Agent` to `KitaruAgent` and tell me what is direct vs risky."
- "This code uses `kp.wrap(...)`; update it to the current `KitaruAgent` style."
- "Choose `calls` vs `turn` checkpointing for this PydanticAI workflow."
- "Add Kitaru durability around this PydanticAI HITL tool without hiding wait risks."

**OpenAI Agents SDK migration:**
- "Migrate this `Runner.run_sync` OpenAI Agents workflow to `KitaruRunner`."
- "Choose `runner_call` vs `calls` for this OpenAI Agents SDK workflow and explain the tradeoff."
- "Add Kitaru durability around this OpenAI Agents approval flow without hiding resume risks."
- "Update this OpenAI Agents workflow to use `OpenAIRunRequest` and status-aware `OpenAIRunResult` handling."

**LangGraph migration:**
- "Migrate this `graph.invoke(...)` LangGraph workflow to `KitaruGraphRunner`."
- "Choose `graph_call` vs middleware-backed `calls` for this LangGraph app and explain what Kitaru can actually replay."
- "Add Kitaru durability around this LangGraph interrupt flow without replacing the LangGraph checkpointer."
- "Review this LangChain `create_agent(...)` code and tell me whether `KitaruLangGraphMiddleware` can give safe call-level checkpoints."

**Claude Agent SDK migration:**
- "Migrate this `claude_agent_sdk.query(...)` workflow to `KitaruClaudeRunner`."
- "Make this Claude Agent SDK session durable as one invocation checkpoint and flag workspace/file risks."
- "Review this Claude Agent SDK tool/Bash/MCP setup and tell me what must stay Claude-owned."
- "Move durable file or API side effects out of the Claude loop and into Kitaru checkpoints."

**Gemini Interactions migration:**
- "Migrate this `client.interactions.create(...)` code to `KitaruGeminiInteractionsRunner`."
- "Handle this Gemini Interactions `requires_action` turn at Kitaru flow scope."
- "Poll an existing Gemini interaction ID with Kitaru instead of creating duplicate background jobs."
- "Review this Antigravity managed-agent workflow and flag which Google-owned internals are not replayable."

## Links

- [Kitaru documentation](https://kitaru.ai/docs)
- [Claude Code skill distribution guide](https://kitaru.ai/docs/agent-native/claude-code-skill)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)
- [Claude Code MCP host guide](skills/kitaru-quickstart/references/hosts/claude-code.md)
- [Codex MCP host guide](skills/kitaru-quickstart/references/hosts/codex.md)
- [Cursor MCP host guide](skills/kitaru-quickstart/references/hosts/cursor.md)

## License

Apache 2.0 — see [LICENSE](LICENSE).
