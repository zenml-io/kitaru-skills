# Repository Guidelines

## Project structure

This repository distributes public Kitaru agent skills plus Claude Code plugin
metadata. It is not a Python package.

- `skills/kitaru-investigation/SKILL.md` is the public routing playbook.
- `skills/kitaru-investigation/references/` contains method, transport, and
  evaluator details loaded only when needed.
- `skills/kitaru-importer-builder/SKILL.md` guides custom importer development.
- `skills/kitaru-importer-builder/references/` contains parser, normalization,
  validation, and recovery details loaded only when needed.
- `skills/kitaru-adapter-builder/SKILL.md` guides project-local adapter
  development for unsupported Python and TypeScript frameworks.
- `skills/kitaru-adapter-builder/references/` separates the shared method,
  Python and TypeScript SDK contracts, and validation and reporting rules.
- `.claude-plugin/plugin.json` defines the Claude Code plugin.
- `.claude-plugin/marketplace.json` defines its marketplace entry.
- `README.md` is the public installation and usage guide.
- `CLAUDE.md` contains Claude Code-specific contributor guidance.

Do not add process notes, plans, changelogs, or a second README inside the
skill directory. Keep reusable procedural material in `SKILL.md` and detailed
supporting material in `references/`.

## Validation commands

There is no build step or dedicated test suite. Validate Markdown, skill
frontmatter, and plugin JSON after edits.

```bash
rg --files
jq . .claude-plugin/plugin.json
jq . .claude-plugin/marketplace.json
git diff --check
```

Use the `skill-creator` `quick_validate.py` script when it is available in the
host environment.

## Style

- Use concise headings, short paragraphs, and readable line lengths.
- Use lowercase kebab-case for skill folders and frontmatter names.
- Use imperative instructions in skill bodies.
- Put all trigger conditions in the frontmatter description.
- Keep `SKILL.md` focused on routing, safety, state transitions, and resource
  discovery. Move detailed schemas, examples, and methods into `references/`.
- Keep references one level below `SKILL.md` and link each one directly from
  the playbook.
- Use Claude Code slash commands only as host-specific invocation examples.
- Preserve valid JSON with two-space indentation.

## Accuracy requirements

- Verify Kitaru CLI and MCP claims against the current Kitaru repository or
  installed schema before changing command guidance.
- Distinguish shipped Kitaru operations, planned frontend behavior, and
  unresolved product contracts.
- Preserve the human-review boundary. Agent suggestions are not human labels.
- Treat raw trace exports as sensitive, keep them out of version control, and
  use redacted fixtures for importer development.
- Treat installed Kitaru schemas as authoritative when importer commands or
  parser contracts differ from branch examples.
- Treat the user's installed framework and Kitaru SDK as authoritative when
  adapter contracts differ from draft reference branches.
- Keep adapter implementations user-project-first. Require separate approval
  before installing dependencies, creating remote sessions, allowing live tool
  passthrough, or preparing an upstream contribution.
- Distinguish application streaming, observation of the stream lifecycle, and
  replay of original chunks or timing.
- Do not recommend direct REST calls or local files to bypass missing Kitaru
  persistence contracts.
- Do not reintroduce removed Kitaru-owned durable memory APIs.

## Distribution consistency

When changing the public skill name, scope, or installation route, update all
of these in the same change:

- skill frontmatter;
- `README.md`;
- `AGENTS.md` and `CLAUDE.md`;
- `.claude-plugin/plugin.json`;
- `.claude-plugin/marketplace.json`.

Bump all three plugin version fields together when preparing a distribution
update.

## Commits and pull requests

Use short imperative commit subjects. Pull requests should explain what
changed, why it changed, and which files need careful review.
