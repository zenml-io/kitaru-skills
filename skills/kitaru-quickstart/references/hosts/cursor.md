# Cursor — MCP Setup

## Detection markers

- `.cursor/` directory exists
- `.cursorignore` file exists
- `.cursorindexingignore` file exists

## Configuration

Create or merge into `.cursor/mcp.json`. Use the demo project's uv
environment instead of a bare `kitaru-mcp` executable:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "uv",
      "args": ["run", "--directory", "<ABSOLUTE_DEMO_DIR>", "kitaru-mcp"],
      "transport": "stdio"
    }
  }
}
```

If `.cursor/mcp.json` already exists, merge the `kitaru` key into the
existing `mcpServers` object. Do not overwrite other servers.

## After setup

Cursor may need a reload to pick up MCP configuration changes. Suggest the
user reload the window or restart Cursor if tools are not immediately
available.
