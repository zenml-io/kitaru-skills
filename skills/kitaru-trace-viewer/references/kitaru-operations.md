# Kitaru operations for viewers

Verify these against the installed Kitaru when a call fails: `kitaru-mcp --help` lists the server flags, and the MCP tool schemas are authoritative.

## Tools

| Tool | Visible to | Mode | Use |
| --- | --- | --- | --- |
| `kitaru_session_view` | assistant | read-only | Open a viewer: `{"request": {"session_id": ID, "viewer": NAME}}` or `{"request": {"investigation_id": ID, "position": N, "viewer": NAME}}`. Pass exactly one of `session_id` and `investigation_id`; `position` is zero-based and needs `investigation_id`. The result names the session and its questions without the session's payloads; the viewer page reads the full session itself. |
| `kitaru_viewer_read` | viewer only | read-only | The page reads the session, the viewer's HTML, and further node pages. Do not call it. |
| `kitaru_viewer_write` | viewer only | standard | The page saves notes, answers, edits, and verdicts. Never call it. |
| `kitaru_review_read` | assistant | read-only | Read saved work back: `{"operation": "list", "kind": "annotation", "filter": {"field": "investigation_id", "op": "eq", "value": ID}}` for an investigation's answers, `{"field": "session_id", …}` for a session's notes, and `list_sessions` with the investigation id for verdicts. |

A `not_found` error from `kitaru_session_view` naming a viewer lists the viewers that exist and the folder they were read from.

## The viewers folder

The MCP server reads `<folder>/<name>.html` on every open, so edits need no restart. The folder is, in order:

1. `--viewers-dir PATH` on `kitaru-mcp`;
2. `KITARU_MCP_VIEWERS_DIR`;
3. `~/.config/kitaru/viewers` (more exactly `$KITARU_CONFIG_DIR/viewers`, else `$XDG_CONFIG_HOME/kitaru/viewers`).

Changing the folder means changing the host's MCP configuration and restarting the MCP server. A JSON `mcpServers` entry looks like this; hosts with a form, such as the ChatGPT desktop app's STDIO option, take the same command and arguments:

```json
{"command": "/absolute/path/to/uv", "args": ["run", "--directory", "/absolute/path/to/project", "kitaru-mcp", "--server", "http://localhost:8000", "--mode", "standard", "--viewers-dir", "/absolute/path/to/viewers"]}
```

## Starting points

- The built-in default viewer, which lists any session's steps: print its path with `python -c "import kitaru.mcp, pathlib; print(pathlib.Path(kitaru.mcp.__file__).parent / 'ui' / 'viewers' / 'default.html')"` and copy it into the viewers folder under a new name.
- The finished examples in [examples/](examples/): `gene-map.html`, a plasmid map for a biologist, with span notes on the DNA sequence and field notes on a feature table; and `line-schedule.html`, a Gantt chart for a production planner, with field notes on plan assignments and checks of the agent's claims against its own plan. Each expects one agent's session shape, so read them for technique and copy the parts that fit, rather than opening them on other sessions.

## Preview and check

Run these where the Kitaru MCP extra is installed, against the same server and viewers folder as the host:

```bash
python -m kitaru.mcp.viewer_preview --server URL --viewers-dir FOLDER
```

It prints a local address; the page plays the MCP host's part, runs the real `kitaru-mcp`, and shows every tool call the viewer makes. Writes in the preview are real: they save to the server.

```bash
uv run --with playwright python -m kitaru.mcp.viewer_preview --server URL \
  --viewers-dir FOLDER --investigation ID --viewer NAME --check
```

`--check` opens the viewer headless, prints the anchor report and any page errors as JSON, and exits non-zero on a problem. It needs a Chromium for Playwright (`playwright install chromium`, or `KITARU_PREVIEW_CHROMIUM=/path/to/chromium`). It only reads.
