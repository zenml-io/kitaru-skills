# Codex CLI — MCP Setup

## Detection markers

- `.codex/` directory exists

## Configuration

Codex CLI MCP configuration is not yet authoritatively documented in the
Kitaru repository. The Kitaru MCP server executable is:

```
kitaru-mcp
```

Suggest the user consult the Codex CLI documentation for the correct MCP
configuration path and format, then use `kitaru-mcp` as the server command.

If the user knows their Codex MCP config location, the general pattern is:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "kitaru-mcp"
    }
  }
}
```

## Fallback

If MCP configuration is not straightforward, skip MCP setup and refer the
user to `references/mcp-config-guide.md` for manual guidance.
