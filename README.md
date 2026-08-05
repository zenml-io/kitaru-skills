# Kitaru Agent Skill

This repository contains `kitaru-investigation`, an agent skill for turning
recorded [Kitaru](https://kitaru.ai) sessions into human-reviewed evidence.
It supports trace-first debugging, cold-start error discovery, durable
annotations, versioned cohorts, and optional evaluator authoring.

Kitaru records agent runs as full traces, including model calls, tool calls,
and decisions. This skill helps a coding agent organize those traces into a
bounded investigation without replacing human judgment.

## Skill

| Skill | Claude Code invocation | Purpose |
|---|---|---|
| [`kitaru-investigation`](skills/kitaru-investigation/SKILL.md) | `/kitaru-investigation` | Map the registered agent and its operating context, review a known bad session or discover candidate failure modes, persist human annotations, create an accepted cohort, and optionally author one narrow evaluator. |

The workflow keeps human observations separate from agent suggestions. It
uses a Kitaru frontend review block when that route is available and falls
back to the same durable investigation through Kitaru MCP or structured CLI
operations in the meantime.

## Example prompts

- "Investigate why this Kitaru session gave a bad support answer."
- "Help me discover recurring failure modes in last week's agent sessions."
- "Resume investigation `INVESTIGATION_ID` and show me what remains."
- "Turn this accepted behavior and cohort into a narrow evaluator."

## Requirements

Kitaru's light frontend onboarding directs users into this skill. The skill
then drives the journey according to one simple choice: start from a session
the user wants to understand, or explore a bounded session population for
recurring problems and unexpectedly good behavior. If sessions are not ready,
the skill helps the user record the current agent or import existing traces,
then continues without restarting intake.

For the most direct agent experience, configure the native Kitaru MCP server
in `standard` mode so the host can read investigations and create review,
cohort, evaluator, and workflow state. Read-only mode still supports
orientation. The skill uses the structured `kitaru` CLI when a local file
upload or built-in wait behavior is required.

Review the official
[Kitaru MCP server guide](https://docs.zenml.io/kitaru/agent-native/mcp-server)
before enabling write or destructive capabilities.

## Installation and usage

### Claude Code plugin

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Claude Code selects the skill from context. You can also invoke it explicitly
with `/kitaru-investigation`.

For project or team installation, add the plugin to
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

For manual local testing:

```bash
mkdir -p .claude/skills
cp -R skills/kitaru-investigation .claude/skills/
```

### Codex, Cursor, and other hosts

Copy `skills/kitaru-investigation` into the host's supported skills location,
or load its `SKILL.md` as explicit project context. Configure Kitaru MCP
separately according to the host and the official Kitaru MCP server guide.

## Repository structure

```text
skills/kitaru-investigation/
  SKILL.md
  references/
    evaluator-authoring.md
    investigation-method.md
    kitaru-operations.md
```

`SKILL.md` is the routing playbook. The reference files are loaded only for
the relevant stage so ordinary invocations do not carry the full method and
command catalog.

## Links

- [Kitaru](https://kitaru.ai)
- [Kitaru documentation](https://docs.zenml.io/kitaru)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)
- [Kitaru MCP server guide](https://docs.zenml.io/kitaru/agent-native/mcp-server)

## License

Apache 2.0. See [LICENSE](LICENSE).
