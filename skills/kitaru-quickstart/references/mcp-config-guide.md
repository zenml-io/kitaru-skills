# Kitaru MCP Server — Manual Setup Guide

Use this guide when automatic host detection fails or when the user's host
is not directly supported.

## Install the MCP extra

With uv:

```bash
uv add 'kitaru[mcp]>=0.4.0'
```

Or with pip:

```bash
pip install 'kitaru[mcp]>=0.4.0'
```

## Verify installation from the project environment

Prefer the uv directory form so the MCP host uses the same virtual
environment where Kitaru was installed:

```bash
uv run --directory <ABSOLUTE_PROJECT_PATH> kitaru-mcp --help
```

If you are not using uv, configure the MCP host with the absolute path to the
`kitaru-mcp` executable inside the Python environment. Do not rely on shell
activation; many MCP hosts do not inherit the active terminal environment.

## Server executable

The environment-safe server invocation is:

```bash
uv run --directory <ABSOLUTE_PROJECT_PATH> kitaru-mcp
```

It uses stdio transport by default.

## Generic MCP configuration

Most hosts use a JSON configuration file with this schema:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "<ABSOLUTE_PROJECT_PATH>",
        "kitaru-mcp"
      ]
    }
  }
}
```

Some hosts require an explicit transport field:

```json
{
  "mcpServers": {
    "kitaru": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "<ABSOLUTE_PROJECT_PATH>",
        "kitaru-mcp"
      ],
      "transport": "stdio"
    }
  }
}
```

Replace `<ABSOLUTE_PROJECT_PATH>` with the full path to the project that has
Kitaru installed, for example `/Users/alex/kitaru-quickstart-demo`.

## Available MCP tools

Once configured, the Kitaru MCP server exposes these tools:

- `kitaru_executions_list` — list recent executions
- `kitaru_executions_get` — inspect an execution
- `kitaru_executions_latest` — get the most recent execution
- `kitaru_executions_run` — run a flow
- `kitaru_executions_input` — provide input to a waiting execution
- `kitaru_executions_retry` — retry a failed execution
- `kitaru_executions_replay` — replay from a checkpoint
- `kitaru_executions_cancel` — cancel a running execution
- `get_execution_logs` — read execution logs when the active log backend has entries
- `kitaru_artifacts_list` — list artifacts for an execution
- `kitaru_artifacts_get` — read an artifact
- `kitaru_status` — check Kitaru connection status
- `kitaru_stacks_list` — list available stacks
- `manage_stack` — create or delete stacks


## Authentication

The MCP server uses the same authentication context as the Kitaru CLI. If
you are logged in via `kitaru login`, the MCP server will use those
credentials.

For local-only usage, run `kitaru login` only if you want the local server and
dashboard. The MCP server can still inspect local project state through the
same Kitaru environment.
