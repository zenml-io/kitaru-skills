# Gemini CLI — MCP Setup

## Detection markers

No reliable filesystem markers for Gemini CLI. Ask the user to confirm
their host if Gemini is suspected.

## Configuration

Gemini CLI MCP configuration may vary by installation. The Kitaru MCP server
should still be launched through the demo project's uv environment:

```bash
uv run --directory <ABSOLUTE_DEMO_DIR> kitaru-mcp
```

Suggest the user consult Gemini CLI documentation for MCP server
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
