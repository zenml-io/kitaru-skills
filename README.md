# Kitaru Skills for Claude Code

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for
discovering, designing, and building durable AI agent workflows with
[Kitaru](https://kitaru.ai).

## Skills

| Skill | Slash command | Purpose |
|---|---|---|
| **kitaru-quickstart** | `/kitaru-quickstart` | Interactive onboarding: scaffolds a personalized demo flow, demonstrates crash recovery with replay, human-in-the-loop with `wait()`, artifact capture, and optional MCP integration |
| **kitaru-scoping** | `/kitaru-scoping` | Structured interview to validate whether your workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, artifact strategy, operator surface, MVP scope) |
| **kitaru-authoring** | `/kitaru-authoring` | Guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `KitaruClient`, replay/resume/retry, deployments, secrets, CLI/MCP tools, and adapters for PydanticAI, OpenAI Agents, LangGraph, and Claude Agent SDK |

### Recommended workflow

1. **Quickstart** — use `/kitaru-quickstart` to see what Kitaru does and
   build intuition for crash recovery, replay, waits, and artifacts
2. **Scope** — use `/kitaru-scoping` to validate fit and define your flow
   architecture before writing code
3. **Author** — use `/kitaru-authoring` to build the flows defined in
   your `flow_architecture.md`

## Installation

### Marketplace (recommended)

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Once installed, Claude Code will automatically use the skills based on context.
You can also invoke them explicitly with `/kitaru-quickstart`,
`/kitaru-scoping`, or `/kitaru-authoring`.

### Team installation

Add to your project's `.claude/settings.json`:

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

### Manual installation

```bash
tmpdir=$(mktemp -d)
git clone --depth 1 https://github.com/zenml-io/kitaru-skills.git "$tmpdir/kitaru-skills"
mkdir -p .claude/skills
cp -R "$tmpdir/kitaru-skills/skills/kitaru-quickstart" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-scoping" .claude/skills/
cp -R "$tmpdir/kitaru-skills/skills/kitaru-authoring" .claude/skills/
rm -rf "$tmpdir"
```

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
- [Claude Code Skills docs](https://kitaru.ai/docs/agent-native/claude-code-skill)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)

## License

Apache 2.0 — see [LICENSE](LICENSE).
