# Claude Code — MCP Setup

## Detection markers

- `.claude/` directory exists
- `.claude/settings.json` exists

## Option A: CLI registration (recommended)

```bash
claude mcp add kitaru kitaru-mcp
```

This registers the Kitaru MCP server in Claude Code's project-scoped
configuration. No file edits needed.

## Option B: Project `.mcp.json` file

Create or merge into `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "kitaru-mcp"
    }
  }
}
```

If `.mcp.json` already exists, merge the `kitaru` key into the existing
`mcpServers` object. Do not overwrite other servers.

## After setup

Claude Code picks up MCP changes on the next message. No restart is needed.

## Scopes

Claude Code supports three configuration scopes:

- **Project** (`.mcp.json` in project root) — recommended for quickstart
- **User** (`~/.claude/settings.json`)
- **Organization** (managed by team admin)

The CLI `claude mcp add` command defaults to project scope.
