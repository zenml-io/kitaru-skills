# Repository Guidelines

## Project Structure & Module Organization
This repository is a Claude Code plugin, not a Python package. Keep contributor work focused on the plugin metadata and skill documents:

- `skills/kitaru-scoping/SKILL.md` defines the workflow-scoping skill.
- `skills/kitaru-authoring/SKILL.md` defines the implementation-authoring skill.
- `.claude-plugin/plugin.json` contains plugin metadata such as name, version, and repository URL.
- `.claude-plugin/marketplace.json` defines the marketplace entry used for local/plugin testing.
- `README.md` is the public-facing usage and installation guide.

When adding a new skill, follow the existing pattern: `skills/<skill-name>/SKILL.md`.

## Build, Test, and Development Commands
There is no build step in this repo. Most contributor work is editing Markdown and JSON, then doing a quick manual validation.

- `rg --files` lists the complete tracked file set.
- `sed -n '1,160p' skills/kitaru-authoring/SKILL.md` previews a skill without opening an editor.
- `git diff --stat` gives a compact review of changed files.
- `jq . .claude-plugin/plugin.json` validates plugin JSON formatting if `jq` is installed.

For manual smoke testing, follow the install commands in [`README.md`](README.md) and verify the plugin exposes `/kitaru-scoping` and `/kitaru-authoring`.

## Coding Style & Naming Conventions
Use Markdown for prose and JSON for plugin metadata. Match the existing style:

- Use concise headings and short paragraphs.
- Wrap lines at a readable width similar to the current files.
- Keep examples concrete and technically accurate.
- Use kebab-case for skill directory names and slash commands, for example `kitaru-scoping`.
- Preserve valid JSON with two-space indentation in `.claude-plugin/*.json`.

## Testing Guidelines
There is currently no dedicated automated test suite. Treat testing as documentation validation:

- Check that examples match the current Kitaru API surface.
- Confirm new trigger phrases and command names are consistent across `SKILL.md`, `README.md`, and plugin metadata.
- Re-read edited Markdown in rendered form when possible to catch broken lists, code fences, or tables.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit messages such as `Update skills for Kitaru memory support` and `Align skills with current Kitaru SDK surface`. Follow that pattern.

Pull requests should explain what changed, why it changed, and which files were updated. If you alter behavior or installation steps, update `README.md` in the same PR.
