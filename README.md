# Kitaru Agent Skills

This repository contains agent skills for bringing traces into
[Kitaru](https://kitaru.ai) and turning recorded sessions into human-reviewed
evidence. They support custom importer development, trace-first debugging,
cold-start error discovery, durable annotations, versioned cohorts, and
optional evaluator authoring.

Kitaru records agent runs as full traces, including model calls, tool calls,
and decisions. The skills help a coding agent import unsupported trace formats
and organize the resulting sessions into a bounded investigation without
replacing human judgment.

## Skill

| Skill | Claude Code invocation | Purpose |
|---|---|---|
| [`kitaru-investigation`](skills/kitaru-investigation/SKILL.md) | `/kitaru-investigation` | Map the registered agent and its operating context, review a known bad session or discover candidate failure modes, persist human annotations, create an accepted cohort, and optionally author one narrow evaluator. |
| [`build-kitaru-importer`](skills/build-kitaru-importer/SKILL.md) | `/build-kitaru-importer` | Build and locally validate a private or packaged importer for an unsupported provider or export format, with conservative session joining, explicit fidelity reporting, and separately approved remote registration and smoke import. |

The workflow keeps human observations separate from agent suggestions. It
uses a Kitaru frontend review block when that route is available and falls
back to the same durable investigation through Kitaru MCP or structured CLI
operations in the meantime.

## Example prompts

- "Investigate why this Kitaru session gave a bad support answer."
- "Help me discover recurring failure modes in last week's agent sessions."
- "Resume investigation `INVESTIGATION_ID` and show me what remains."
- "Turn this accepted behavior and cohort into a narrow evaluator."
- "Build a private Kitaru importer for this provider's JSONL trace export."
- "These traces store each conversation turn separately. Join them safely when importing into Kitaru."
- "Help me understand whether this partial import is safe to retry."

## Requirements

Kitaru's light frontend onboarding directs users into the investigation skill.
It then drives the journey according to one simple choice: start from a session
the user wants to understand, or explore a bounded session population for
recurring problems and unexpectedly good behavior. If an unsupported provider
prevents sessions from entering Kitaru, the importer-builder skill creates and
validates the missing integration, then hands usable sessions back to the
investigation flow.

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

Claude Code selects a skill from context. You can also invoke
`/kitaru-investigation` or `/build-kitaru-importer` explicitly.

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
cp -R skills/build-kitaru-importer .claude/skills/
cp -R skills/kitaru-investigation .claude/skills/
```

### Codex, Cursor, and other hosts

Copy either skill directory into the host's supported skills location, or load
its `SKILL.md` as explicit project context. Configure Kitaru MCP separately
according to the host and the official Kitaru MCP server guide.

## Repository structure

```text
skills/build-kitaru-importer/
  SKILL.md
  references/
    failure-and-validation.md
    importer-contract.md
    normalization-patterns.md

skills/kitaru-investigation/
  SKILL.md
  references/
    evaluator-authoring.md
    investigation-method.md
    kitaru-operations.md
```

Each `SKILL.md` is a routing playbook. Reference files are loaded only for the
relevant stage so ordinary invocations do not carry the full method and command
catalog.

## Links

- [Kitaru](https://kitaru.ai)
- [Kitaru documentation](https://docs.zenml.io/kitaru)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)
- [Kitaru MCP server guide](https://docs.zenml.io/kitaru/agent-native/mcp-server)

## License

Apache 2.0. See [LICENSE](LICENSE).
