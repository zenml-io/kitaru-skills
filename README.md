# Kitaru Agent Skills

This repository contains agent skills for connecting agent frameworks and trace
exports to [Kitaru](https://kitaru.ai), then turning recorded sessions into
human-reviewed evidence. They support custom adapter and importer development,
one-run review tours, specific-behavior debugging, recurring-problem discovery,
durable annotations, versioned cohorts, evaluator selection, and bounded replay
experiments.

Kitaru records agent runs as evidence-rich sessions. Model and tool activity is
recorded when the integration exposes it, and the skills make observability gaps
explicit. They help a coding agent record an unsupported framework, import an
unsupported trace format, and organize the resulting sessions into a bounded
investigation without replacing human judgment.

## Skills

| Skill | Purpose |
|---|---|
| [`kitaru-investigation`](skills/kitaru-investigation/SKILL.md) | Act as Kitaru's front door: verify setup, record or import sessions, guide human review, define one accepted behavior and cohort, select an evaluator, and offer a bounded replay experiment. |
| [`kitaru-replay-experiment`](skills/kitaru-replay-experiment/SKILL.md) | Safely test one candidate against an exact cohort and evaluator set, supervise the run, and report improved, regressed, trade-off, or inconclusive evidence without making the deployment decision. |
| [`kitaru-importer-builder`](skills/kitaru-importer-builder/SKILL.md) | Build and locally validate a private or packaged importer for an unsupported provider or export format, with conservative session joining, explicit fidelity reporting, and separately approved remote registration and smoke import. |
| [`kitaru-adapter-builder`](skills/kitaru-adapter-builder/SKILL.md) | Build a project-local Python or TypeScript adapter for an unsupported agent framework, with explicit recording and replay boundaries, partial-trace handling, side-effect controls, and separately approved upstream contribution. |

The workflow keeps human observations separate from agent suggestions. It uses
the Kitaru frontend for human review. If no returned or documented review URL
works, it preserves the investigation and reports the broken product handoff
rather than recreating the review UI in chat.

## Example prompts

- "Investigate why this Kitaru session gave a bad support answer."
- "I am new to Kitaru. Help me review one run before we investigate more."
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

These skills track the Kitaru 0.22 CLI, MCP, SDK, and adapter contracts developed
on [`kitaru/develop`](https://github.com/zenml-io/kitaru/tree/develop). The
currently verified Python range is `kitaru>=0.22.0rc4,<0.23`. Until a stable
0.22 release is available, enable prereleases explicitly:

```bash
uv add --prerelease allow "kitaru[cli,mcp]>=0.22.0rc4,<0.23"
```

This range accepts later 0.22 release candidates and the stable 0.22 release,
but not an unverified 0.23 release. An ordinary stable-only installation may
still resolve to Kitaru 0.21. Each skill verifies the installed version and
public schema before it acts, and stops when the required contract is
unavailable.

When the Kitaru product provides a skill handoff from frontend onboarding, the
investigation skill continues from its exact repository, working-directory,
agent, and trace context. The guided starter lives in
[`zenml-io/kitaru-template`](https://github.com/zenml-io/kitaru-template); the
skill verifies the checkout root and current README instead of guessing paths.
It asks a first-time user whether to learn the review flow on one run, debug a
specific behavior, or explore several runs for recurring problems. If an
unsupported provider prevents sessions from entering Kitaru, the
`kitaru-importer-builder` skill creates and validates the missing integration,
then hands usable sessions back. If no supported framework integration can
record the agent, the `kitaru-adapter-builder` skill verifies the installed SDK
and framework hooks before building a project-local adapter.

The front-door journey follows Kitaru's five-step method: Observe, Judge,
Define, Replay, and Compare. After investigation accepts a behavior and cohort,
it checks the installed evaluator catalog before proposing custom evaluator
code. It then offers to continue with the `kitaru-replay-experiment` skill,
carrying the exact accepted evidence forward without making the user copy IDs.

MCP is preferred, not required. For the most direct agent experience, configure
the native Kitaru MCP server in `standard` mode so the host can read
investigations and create review, cohort, evaluator, and workflow state.
Read-only mode supports orientation. CLI-only operation remains supported, and
the skill uses the structured `kitaru` CLI for local files, built-in waiting, or
operations MCP does not expose.

Review the official
[Kitaru MCP server guide](https://docs.zenml.io/kitaru/agent-native/mcp-server)
before enabling write or destructive capabilities.

## Installation and usage

Install the skills with the cross-host Agent Skills installer. This is the
recommended route for Codex, Cursor, Claude Code, and other compatible hosts:

```bash
npx skills add zenml-io/kitaru-skills
```

When the installer asks, select the host you actually use and include
`kitaru-investigation`. Your agent can then select it from context, or you can
ask for it by name: "Use `kitaru-investigation` to investigate why this Kitaru
session gave a bad support answer." Exact invocation syntax varies by host.

Configure Kitaru MCP separately according to your host and the official Kitaru
MCP server guide. Restart the coding-agent process after adding MCP
configuration so it can discover the server, then resume from the skill's
checkpoint. A missing MCP server does not block a path the CLI fully supports.

### Optional Claude Code plugin installation

Claude Code users who prefer its plugin marketplace can install the same skills
as a plugin:

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

You can then invoke
`/kitaru-investigation`, `/kitaru-replay-experiment`,
`/kitaru-importer-builder`, or `/kitaru-adapter-builder` explicitly.

### Manual installation

If your host does not support the installer, copy the relevant skill directory
into its skills location or load the skill's `SKILL.md` as explicit project
context.

## Links

- [Kitaru](https://kitaru.ai)
- [Kitaru documentation](https://docs.zenml.io/kitaru)
- [Kitaru SDK repository](https://github.com/zenml-io/kitaru)

## License

Apache 2.0. See [LICENSE](LICENSE).
