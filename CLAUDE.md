# CLAUDE.md

Shared contributor guidance lives in [`AGENTS.md`](AGENTS.md). Follow it first.

## What this repository distributes

The repository contains one public skill, `kitaru-investigation`, plus Claude
Code plugin packaging. The skill conducts evidence-grounded review of Kitaru
agent sessions and can turn an accepted behavior into a versioned cohort and
optional evaluator.

```text
.claude-plugin/
  plugin.json
  marketplace.json
skills/
  kitaru-investigation/
    SKILL.md
    references/
      evaluator-authoring.md
      investigation-method.md
      kitaru-operations.md
```

Claude Code exposes the skill as `/kitaru-investigation` and may also select
it automatically from the frontmatter description.

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

## Local Claude Code testing

```bash
mkdir -p .claude/skills
cp -R skills/kitaru-investigation .claude/skills/
```

For marketplace testing:

```bash
/plugin marketplace add zenml-io/kitaru-skills
/plugin install kitaru@kitaru
```

Validate both plugin JSON files and keep all plugin version fields in sync.
