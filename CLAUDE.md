# CLAUDE.md

Shared contributor guidance lives in [`AGENTS.md`](AGENTS.md). Follow it first.

## What this repository distributes

The repository contains public Kitaru skills plus Claude Code plugin packaging.
`kitaru-investigation` conducts evidence-grounded review of Kitaru agent
sessions and can turn an accepted behavior into a versioned cohort and optional
installed or custom evaluator. `kitaru-replay-experiment` safely compares one
candidate against an exact cohort and evaluator set. `kitaru-importer-builder`
builds and validates a private or packaged importer when a trace provider has
no suitable built-in integration.
`kitaru-adapter-builder` builds a project-local Python or TypeScript adapter
when an agent framework has no suitable supported integration.

```text
.claude-plugin/
  plugin.json
  marketplace.json
skills/
  kitaru-importer-builder/
    SKILL.md
    references/
      failure-and-validation.md
      importer-contract.md
      normalization-patterns.md
  kitaru-adapter-builder/
    SKILL.md
    references/
      adapter-method.md
      python-adapters.md
      typescript-adapters.md
      validation-and-reporting.md
  kitaru-investigation/
    SKILL.md
    references/
      deterministic-evaluators.md
      evaluator-authoring.md
      investigation-method.md
      kitaru-operations.md
  kitaru-replay-experiment/
    SKILL.md
    agents/
      openai.yaml
    references/
      experiment-contract.md
      experiment-method.md
```

Claude Code exposes the skills as `/kitaru-investigation`,
`/kitaru-replay-experiment`, `/kitaru-importer-builder`, and
`/kitaru-adapter-builder`, and may also select them automatically from their
frontmatter descriptions.

## Editing the skill

- Keep `SKILL.md` as the resumable orchestration playbook.
- Keep repository inspection, sampling, review, and synthesis detail in
  `references/investigation-method.md`.
- Keep exact CLI/MCP routing and current product gaps in
  `references/kitaru-operations.md`.
- Check installed evaluators after the user accepts a behavior and cohort. Load
  custom evaluator guidance only after checking that catalog. Continue when no
  installed evaluator fits, or when the user explicitly declines a relevant
  match and requests custom authoring with equivalent reviewed evidence.
- Keep replay state resolution, approvals, supervision, and handoffs in
  `kitaru-replay-experiment/SKILL.md`. Keep current Kitaru contracts and bounded
  comparison method in its two references.
- Require an explicit tool policy for tool-using replays and verify adapter
  support before approval or paid execution.
- Report directional replay evidence without making a deployment decision.
- Verify command and tool claims against the current Kitaru source or
  installed schema before editing them.
- Preserve the distinction between human annotations and agent suggestions.
- Treat the frontend review as the intended human interaction. If no returned
  or documented URL reaches it, preserve the investigation and report the
  broken product handoff; do not recreate review in chat automatically.
- Treat the skill as Kitaru's front door. Orient new users once with Observe,
  Judge, Define, Replay, and Compare, then reveal only the current step and next
  useful decision.
- Treat frontend onboarding as the doorway into the skill, not a separate
  workflow owner. Require its exact repository and working-directory context.
  For generic first runs, ask whether the user wants a one-run tour,
  specific-behavior debugging, or bounded discovery.
- Treat MCP as preferred and CLI-only operation as supported. Distinguish
  missing package support, host configuration, capability mode, and a pending
  coding-agent restart before choosing the transport.
- Route unsupported-provider setup to `kitaru-importer-builder`, then return to
  `kitaru-investigation` only after usable sessions exist.
- Keep importer orchestration and approval gates in its `SKILL.md`; keep parser
  contracts, normalization, validation, and recovery detail in its references.
- Preserve a private script importer as a complete outcome. Do not require
  package publication or an upstream contribution.
- Keep raw trace exports out of version control and require redacted fixtures.
- Route unsupported in-process framework integration to
  `kitaru-adapter-builder`. Check supported adapters, importers, and OTLP first.
- Keep adapter routing and approval gates in its `SKILL.md`; keep the shared
  method, language-specific SDK contracts, and validation detail in its four
  references.
- Preserve project-local adapter success as the ordinary outcome. Treat an OSS
  contribution as a separately approved final step.

## Local Claude Code testing

```bash
mkdir -p .claude/skills
cp -R skills/kitaru-importer-builder .claude/skills/
cp -R skills/kitaru-adapter-builder .claude/skills/
cp -R skills/kitaru-investigation .claude/skills/
cp -R skills/kitaru-replay-experiment .claude/skills/
```

For marketplace testing:

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Validate both plugin JSON files and keep all plugin version fields in sync.
