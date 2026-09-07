# CLAUDE.md

Shared contributor guidance lives in [`AGENTS.md`](AGENTS.md). Follow it first
for contributor scope, validation, accuracy, distribution, and release rules.

## Claude Code invocation

Claude Code exposes the skills as `/kitaru-hosted-onboarding-tour`,
`/kitaru-guided-tour`, `/kitaru-investigation`, `/kitaru-replay-experiment`,
`/kitaru-importer-builder`, and `/kitaru-adapter-builder`, and may also select
them automatically from their frontmatter descriptions.

## Additional skill editing guidance

Preserve these details in the published skills when editing them; these are
not instructions to execute the workflows during repository maintenance.

- Keep investigation inspection, sampling, and synthesis detail in
  `skills/kitaru-investigation/references/investigation-method.md`, and exact
  CLI/MCP routing and product gaps in its `references/kitaru-operations.md`.
- Keep quickstart recognition and idempotent setup in each applicable skill's
  `references/starter-template.md`.
- Keep replay, importer, and adapter orchestration and approval gates in their
  respective `SKILL.md` files; keep detailed contracts and methods in their
  `references/` directories.
- Preserve custom evaluator authoring when no installed evaluator fits, or when
  the user declines a relevant match and requests custom authoring with
  equivalent reviewed evidence.
- Keep the hosted tour's prepared-environment contract and one bounded durable
  state read. Keep the public tour's complete replay run card and approval before
  experiment creation or execution.
- Narrate the public tour for someone who has read neither the sample agent nor
  Kitaru documentation. Explain each meaningful stage and next useful decision.
- Preserve generic first-run routing between a tour, specific-behavior debugging,
  and bounded discovery. Distinguish missing package support, host configuration,
  capability mode, and a pending host restart when choosing MCP or CLI.
- Route unsupported-provider setup to the importer builder, returning to
  investigation after usable sessions exist. A private script importer is a
  complete outcome; publication is optional.
- Check supported adapters, importer-backed adapters, importers, and OTLP before
  custom adapter development. A project-local adapter is a complete outcome.

## Local Claude Code testing

```bash
mkdir -p .claude/skills
cp -R skills/kitaru-hosted-onboarding-tour .claude/skills/
cp -R skills/kitaru-guided-tour .claude/skills/
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
