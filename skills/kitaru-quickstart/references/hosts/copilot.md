# GitHub Copilot — MCP Setup

## Detection markers

No reliable filesystem markers for Copilot. Ask the user to confirm their
host if Copilot is suspected.

## Configuration

GitHub Copilot MCP configuration is not yet authoritatively documented in
the Kitaru repository. The Kitaru MCP server executable is:

```
kitaru-mcp
```

Suggest the user consult GitHub Copilot documentation for MCP server
registration, then use `kitaru-mcp` as the server command.

## Fallback

If MCP configuration is not straightforward, skip MCP setup and refer the
user to `references/mcp-config-guide.md` for manual guidance.
