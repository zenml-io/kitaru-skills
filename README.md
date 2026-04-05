# Kitaru Skills for Claude Code

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for
discovering, designing, and building durable AI agent workflows with
[Kitaru](https://kitaru.ai).

## Skills

| Skill | Slash command | Purpose |
|---|---|---|
| **kitaru-quickstart** | `/kitaru-quickstart` | Interactive onboarding: scaffolds a personalized demo flow, demonstrates crash recovery with replay, human-in-the-loop with `wait()`, durable memory across executions, and optional MCP integration |
| **kitaru-scoping** | `/kitaru-scoping` | Structured interview to validate whether your workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, memory-vs-artifact strategy, memory scope design, operator surface, MVP scope) |
| **kitaru-authoring** | `/kitaru-authoring` | Guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, `kitaru.memory`, `KitaruClient.memories`, replay/resume/retry, CLI memory commands, MCP memory tools, and PydanticAI adapter integrations |

### Recommended workflow

1. **Quickstart** — use `/kitaru-quickstart` to see what Kitaru does and
   build intuition for crash recovery, replay, wait, and memory
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
You can also invoke them explicitly with `/kitaru-scoping` or
`/kitaru-authoring`.

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
mkdir -p .claude/skills/kitaru-scoping .claude/skills/kitaru-authoring

curl -fsSL https://raw.githubusercontent.com/zenml-io/kitaru-skills/main/skills/kitaru-scoping/SKILL.md \
  -o .claude/skills/kitaru-scoping/SKILL.md

curl -fsSL https://raw.githubusercontent.com/zenml-io/kitaru-skills/main/skills/kitaru-authoring/SKILL.md \
  -o .claude/skills/kitaru-authoring/SKILL.md
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
- "Should repo conventions live in memory or artifacts?"
- "I have a complex agent with 10 steps — help me scope it down."

**Authoring:**
- "Refactor this script into one `@flow` with explicit checkpoints."
- "Add a flow-level `kitaru.wait()` approval gate before publish."
- "Add `kitaru.memory` durable shared state to this flow."
- "How do I seed memory from a script and inspect it from the CLI or MCP?"
- "Wrap this PydanticAI call in a `@checkpoint` and preserve replay safety."

## Links

- [Kitaru documentation](https://kitaru.ai/docs)
- [Claude Code Skills docs](https://kitaru.ai/docs/agent-integrations/claude-code-skill)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)

## License

Apache 2.0 — see [LICENSE](LICENSE).
