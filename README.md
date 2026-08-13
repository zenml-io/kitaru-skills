# Kitaru Agent Skills

This repository contains agent skills for connecting agent frameworks and trace
exports to [Kitaru](https://kitaru.ai), then turning recorded sessions into
human-reviewed evidence. They support custom adapter and importer development,
trace-first debugging, cold-start error discovery, durable annotations,
versioned cohorts, built-in or custom evaluator selection, and bounded replay
experiments.

Kitaru records agent runs as evidence-rich sessions. Model and tool activity is
recorded when the integration exposes it, and the skills make observability gaps
explicit. They help a coding agent record an unsupported framework, import an
unsupported trace format, and organize the resulting sessions into a bounded
investigation without replacing human judgment.

## Skills

| Skill | Claude Code invocation | Purpose |
|---|---|---|
| [`kitaru-investigation`](skills/kitaru-investigation/SKILL.md) | `/kitaru-investigation` | Map the registered agent and its operating context, review a known bad session or discover candidate failure modes, persist human annotations, create an accepted cohort, and select a built-in evaluator or author one narrow custom evaluator. |
| [`kitaru-replay-experiment`](skills/kitaru-replay-experiment/SKILL.md) | `/kitaru-replay-experiment` | Safely test one candidate against an exact cohort and evaluator set, supervise the run, and report improved, regressed, trade-off, or inconclusive evidence without making the deployment decision. |
| [`kitaru-importer-builder`](skills/kitaru-importer-builder/SKILL.md) | `/kitaru-importer-builder` | Build and locally validate a private or packaged importer for an unsupported provider or export format, with conservative session joining, explicit fidelity reporting, and separately approved remote registration and smoke import. |
| [`kitaru-adapter-builder`](skills/kitaru-adapter-builder/SKILL.md) | `/kitaru-adapter-builder` | Build a project-local Python or TypeScript adapter for an unsupported agent framework, with explicit recording and replay boundaries, partial-trace handling, side-effect controls, and separately approved upstream contribution. |

The workflow keeps human observations separate from agent suggestions. It
uses a Kitaru frontend review block when that route is available and falls
back to the same durable investigation through Kitaru MCP or structured CLI
operations in the meantime.

## Example prompts

- "Investigate why this Kitaru session gave a bad support answer."
- "Help me discover recurring failure modes in last week's agent sessions."
- "Resume investigation `INVESTIGATION_ID` and show me what remains."
- "Turn this accepted behavior and cohort into a narrow evaluator."
- "Replay this cohort with the new prompt and tell me whether it helped."
- "Run a safe experiment with history-backed tools and no live passthrough."
- "Build a private Kitaru importer for this provider's JSONL trace export."
- "These traces store each conversation turn separately. Join them safely when importing into Kitaru."
- "Help me understand whether this partial import is safe to retry."
- "Build a Kitaru adapter for this Python agent framework."
- "Add Kitaru recording and safe replay to this TypeScript agent without changing its public API."
- "Can this framework support a Kitaru adapter, including streaming and tool replay?"

## Requirements

Kitaru's light frontend onboarding directs users into the investigation skill.
It then drives the journey according to one simple choice: start from a session
the user wants to understand, or explore a bounded session population for
recurring problems and unexpectedly good behavior. If an unsupported provider
prevents sessions from entering Kitaru, the importer-builder skill creates and
validates the missing integration, then hands usable sessions back to the
investigation flow. If the application needs in-process recording or replay and
no supported framework integration exists, the adapter-builder skill verifies
the installed SDK and public framework hooks before building a project-local
adapter.

After investigation accepts a behavior and cohort, it checks the installed
evaluator catalog before proposing custom evaluator code. If the user wants to
test one change, the replay-experiment skill preflights adapter support and tool
effects, shows one run card, supervises the bounded run, and explains the exact
case-level evidence.

For the most direct agent experience, configure the native Kitaru MCP server
in `standard` mode so the host can read investigations and create review,
cohort, evaluator, and workflow state. Read-only mode still supports
orientation. The skill uses the structured `kitaru` CLI when a local file
upload or built-in wait behavior is required.

Review the official
[Kitaru MCP server guide](https://docs.zenml.io/kitaru/agent-native/mcp-server)
before enabling write or destructive capabilities.

## Installation and usage

Use the cross-host installer when the agent host supports the Agent Skills
standard:

```bash
npx skills add zenml-io/kitaru-skills
```

### Claude Code plugin

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Claude Code selects a skill from context. You can also invoke
`/kitaru-investigation`, `/kitaru-replay-experiment`,
`/kitaru-importer-builder`, or `/kitaru-adapter-builder` explicitly.

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
cp -R skills/kitaru-importer-builder .claude/skills/
cp -R skills/kitaru-adapter-builder .claude/skills/
cp -R skills/kitaru-investigation .claude/skills/
cp -R skills/kitaru-replay-experiment .claude/skills/
```

### Codex, Cursor, and other hosts

Copy the relevant skill directory into the host's supported skills location, or
load its `SKILL.md` as explicit project context. Configure Kitaru MCP separately
according to the host and the official Kitaru MCP server guide.

## Repository structure

```text
skills/kitaru-importer-builder/
  SKILL.md
  references/
    failure-and-validation.md
    importer-contract.md
    normalization-patterns.md

skills/kitaru-adapter-builder/
  SKILL.md
  references/
    adapter-method.md
    python-adapters.md
    typescript-adapters.md
    validation-and-reporting.md

skills/kitaru-investigation/
  SKILL.md
  references/
    deterministic-evaluators.md
    evaluator-authoring.md
    investigation-method.md
    kitaru-operations.md

skills/kitaru-replay-experiment/
  SKILL.md
  agents/
    openai.yaml
  references/
    experiment-contract.md
    experiment-method.md
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
