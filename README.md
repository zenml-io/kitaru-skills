# Kitaru Agent Skills

Reusable Markdown agent skills for discovering, designing, and building durable
AI agent workflows with [Kitaru](https://kitaru.ai).

This repository contains the shared skill content plus Claude Code plugin
packaging. Claude Code can install the skills through its plugin flow. Codex,
Cursor, and other agent hosts can use the Markdown skill files and the
host-specific MCP setup guides where their local skill, rule, or context-loading
workflow supports that pattern.

## Skills

| Skill | Skill / invocation | Purpose |
|---|---|---|
| **kitaru-quickstart** | `kitaru-quickstart` (`/kitaru-quickstart` in Claude Code) | Interactive onboarding: scaffolds a personalized demo flow, demonstrates crash recovery with replay, human-in-the-loop with `wait()`, artifact capture, and optional MCP integration |
| **kitaru-scoping** | `kitaru-scoping` (`/kitaru-scoping` in Claude Code) | Structured interview to validate whether your workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, artifact strategy, operator surface, MVP scope) |
| **kitaru-authoring** | `kitaru-authoring` (`/kitaru-authoring` in Claude Code) | Guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `KitaruClient`, replay/resume/retry, deployments, secrets, CLI/MCP tools, and adapters for PydanticAI, OpenAI Agents, LangGraph, and Claude Agent SDK |

### Recommended workflow

1. **Quickstart** — use `kitaru-quickstart` to see what Kitaru does and build
   intuition for crash recovery, replay, waits, and artifacts
2. **Scope** — use `kitaru-scoping` to validate fit and define your flow
   architecture before writing code
3. **Author** — use `kitaru-authoring` to build the flows defined in your
   `flow_architecture.md`

In Claude Code, those skills are exposed as slash commands:
`/kitaru-quickstart`, `/kitaru-scoping`, and `/kitaru-authoring`.

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
`/kitaru-scoping`, or `/kitaru-authoring`.

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
rm -rf "$tmpdir"
```

See the [Claude Code host guide](skills/kitaru-quickstart/references/hosts/claude-code.md)
for MCP setup details.

### Codex usage

Codex setup depends on the Codex version and local configuration style you use.
If your Codex environment supports local skills, copy the three
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
- "Convert this PydanticAI agent to `KitaruAgent` and preserve replay safety."
- "Use `KitaruRunner` for this OpenAI Agents workflow and choose the checkpoint strategy."
- "Help me add Kitaru durability around a LangGraph graph."
- "Make this Claude Agent SDK invocation durable without promising granular tool replay."

## Links

- [Kitaru documentation](https://kitaru.ai/docs)
- [Claude Code skill distribution guide](https://kitaru.ai/docs/agent-native/claude-code-skill)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)
- [Claude Code MCP host guide](skills/kitaru-quickstart/references/hosts/claude-code.md)
- [Codex MCP host guide](skills/kitaru-quickstart/references/hosts/codex.md)
- [Cursor MCP host guide](skills/kitaru-quickstart/references/hosts/cursor.md)

## License

Apache 2.0 — see [LICENSE](LICENSE).
