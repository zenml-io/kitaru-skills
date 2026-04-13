# Claude Code — MCP Setup

## Detection markers

- `.claude/` directory exists
- `.claude/settings.json` exists

## Option A: CLI registration

Use the demo project's uv environment instead of a bare `kitaru-mcp` binary:

```bash
claude mcp add kitaru uv run --directory <ABSOLUTE_DEMO_DIR> kitaru-mcp
```

If your Claude Code version rejects command arguments in this form, use
Option B instead. The important part is the server argv:
`uv run --directory <ABSOLUTE_DEMO_DIR> kitaru-mcp`.

## Option B: Project `.mcp.json` file

Create or merge into `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "uv",
      "args": ["run", "--directory", "<ABSOLUTE_DEMO_DIR>", "kitaru-mcp"]
    }
  }
}
```

If `.mcp.json` already exists, merge the `kitaru` key into the existing
`mcpServers` object. Do not overwrite other servers.

## After setup

Claude Code picks up MCP changes on the next message. No restart is usually
needed.

## Scopes

Claude Code supports three configuration scopes:

- **Project** (`.mcp.json` in project root) — recommended for quickstart
- **User** (`~/.claude/settings.json`)
- **Organization** (managed by team admin)

The CLI `claude mcp add` command normally defaults to project scope.
