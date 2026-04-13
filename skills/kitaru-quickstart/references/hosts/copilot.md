# GitHub Copilot — MCP Setup

## Detection markers

No reliable filesystem markers for Copilot. Ask the user to confirm their
host if Copilot is suspected.

## Configuration

GitHub Copilot MCP configuration may vary by editor/version. The Kitaru MCP
server should still be launched through the demo project's uv environment:

```bash
uv run --directory <ABSOLUTE_DEMO_DIR> kitaru-mcp
```

Suggest the user consult GitHub Copilot documentation for MCP server
registration, then use this command/args shape rather than a bare
`kitaru-mcp` executable:

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
