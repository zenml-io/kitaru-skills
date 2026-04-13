# Codex CLI — MCP Setup

## Detection markers

- `.codex/` directory exists

## Configuration

Codex CLI MCP configuration may vary by installation. The Kitaru MCP server
should still be launched through the demo project's uv environment:

```bash
uv run --directory <ABSOLUTE_DEMO_DIR> kitaru-mcp
```

Suggest the user consult the Codex CLI documentation for the correct MCP
configuration path and format, then use the command/args form below rather
than a bare `kitaru-mcp` executable.

If the user knows their Codex MCP config location, the general pattern is:

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

## Fallback

If MCP configuration is not straightforward, skip MCP setup and refer the
user to `references/mcp-config-guide.md` for manual guidance.
