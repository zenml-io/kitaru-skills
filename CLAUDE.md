# CLAUDE.md

Shared contributor guidance lives in [`AGENTS.md`](AGENTS.md). Follow it first.

## What this repository distributes

The repository contains public Kitaru skills plus Claude Code plugin packaging.
`kitaru-investigation` conducts evidence-grounded review of Kitaru agent
sessions and can turn an accepted behavior into a versioned cohort and optional
evaluator. `build-kitaru-importer` builds and validates a private or packaged
importer when a trace provider has no suitable built-in integration.
`kitaru-adapter-builder` builds a project-local Python or TypeScript adapter
when an agent framework has no suitable supported integration.

```text
.claude-plugin/
  plugin.json
  marketplace.json
skills/
  build-kitaru-importer/
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
      evaluator-authoring.md
      investigation-method.md
      kitaru-operations.md
```

Claude Code exposes the skills as `/kitaru-investigation` and
`/build-kitaru-importer` and `/kitaru-adapter-builder`, and may also select them
automatically from their frontmatter descriptions.

## Editing the skill

- Keep `SKILL.md` as the resumable orchestration playbook.
- Keep repository inspection, sampling, review, and synthesis detail in
  `references/investigation-method.md`.
- Keep exact CLI/MCP routing and current product gaps in
  `references/kitaru-operations.md`.
- Load evaluator guidance only after the user accepts a behavior or supplies
  equivalent reviewed evidence.
- Verify command and tool claims against the current Kitaru source or
  installed schema before editing them.
- Preserve the distinction between human annotations and agent suggestions.
- Treat the frontend review as a handoff when available and retain the
  MCP/structured-CLI fallback until it is available.
- Treat the skill as Kitaru's front door. Orient new users briefly, preserve
  technical depth for experienced users, and reveal only the next useful
  decision instead of dumping the complete workflow.
- Treat frontend onboarding as the doorway into the skill, not a separate
  workflow owner. Drive either the seed-session or bounded-discovery flow and
  do not bounce the user back into a circular handoff.
- Route unsupported-provider setup to `build-kitaru-importer`, then return to
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
cp -R skills/build-kitaru-importer .claude/skills/
cp -R skills/kitaru-adapter-builder .claude/skills/
cp -R skills/kitaru-investigation .claude/skills/
```

For marketplace testing:

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Validate both plugin JSON files and keep all plugin version fields in sync.
