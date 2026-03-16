# Kitaru Skills for Claude Code

Two [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for
designing and building durable AI agent workflows with
[Kitaru](https://kitaru.ai).

## Skills

| Skill | Slash command | Purpose |
|---|---|---|
| **kitaru-scoping** | `/kitaru-scoping` | Structured interview to validate whether your workflow benefits from durable execution, then designs the flow architecture (checkpoint boundaries, wait points, replay anchors, artifact strategy, MVP scope) |
| **kitaru-authoring** | `/kitaru-authoring` | Guide for writing Kitaru flows, checkpoints, waits, logging, artifacts, tracked LLM calls, replay/resume/retry, KitaruClient usage, CLI commands, MCP operations, and PydanticAI adapter integrations |

### Recommended workflow

1. **Scope first** — use `/kitaru-scoping` to validate fit and define your flow
   architecture before writing code
2. **Author second** — use `/kitaru-authoring` to build the flows defined in
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

**Scoping:**
- "I want to build a research agent — is Kitaru right for this?"
- "Help me figure out where to put checkpoints in my coding agent workflow."
- "I have a complex agent with 10 steps — help me scope it down."

**Authoring:**
- "Refactor this script into one `@flow` with explicit checkpoints."
- "Add a flow-level `kitaru.wait()` approval gate before publish."
- "Wrap this PydanticAI call in a `@checkpoint` and preserve replay safety."

## Links

- [Kitaru documentation](https://kitaru.ai/docs)
- [Claude Code Skills docs](https://kitaru.ai/docs/agent-integrations/claude-code-skill)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)

## License

Apache 2.0 — see [LICENSE](LICENSE).
