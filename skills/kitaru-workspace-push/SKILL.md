---
name: kitaru-workspace-push
description: Move a local open-source Kitaru workspace to a managed cloud workspace with `kitaru workspace push`. Use when a user who has been running Kitaru against a local server wants to sign up for the managed cloud and bring their agents, agent versions, provider connections, sessions, and insights with them, or asks to copy a workspace from one Kitaru server to another.
---

# Push a local Kitaru workspace to the managed cloud

`kitaru workspace push --to <destination-url>` copies agents, agent versions, provider connections, settled sessions with their nodes, and insights from one Kitaru server to another. This skill walks the user from a local server to a managed workspace: sign up, preview, copy, verify, and finish what the command cannot do.

## Rules

- Inside a project, run the CLI as `uv run kitaru`. Use plain `kitaru` only for an isolated install. The commands below write `kitaru` for brevity.
- The push creates remote state. Do not run it without `--dry-run` until the user has seen the preview and said yes.
- Tell the user before the push that connection secret values are not copied, so they know they will re-enter them on the destination.
- Never ask the user to paste a secret value, API key, or password into the chat, and never put one in a command you run. Give the user the command and have them run it in their own terminal.
- Never delete local data (`kitaru logout --volumes`) as part of this procedure. The local server stays the source of truth until the user decides otherwise.
- The user makes the judgment calls: which agents to move, whether to copy connections, and when to switch production traffic.

## 1. Check prerequisites

1. **The CLI has the command.** Run `kitaru schema workspace push`. It works offline and prints the command's parameters. If it fails with `invalid_arguments`, the installed version predates the command: upgrade Kitaru by rerunning the installer (`curl -fsSL https://kitaru.ai/install | bash`), then check again.
2. **Record the local URL before logging in to the cloud.** Run `kitaru status --output json` and read `item.server_url` and `item.server_source`. For a local server this is `http://localhost:8000` unless the user chose another port with `kitaru login --local --port`. `kitaru config` holds only CLI preferences and does not report server URLs. If the managed login already happened, confirm the local URL with `kitaru --server http://localhost:8000 status` (substitute the user's port).
3. **The local server is reachable.** `kitaru --server <local-url> status` must succeed. If it reports `network_error`, the containers are stopped: `kitaru login --local` starts them again and keeps the database. It also makes the local server the selected one, which is why every command below passes `--server` explicitly.
4. **The user is logged in to the managed cloud and a Kitaru workspace exists.** Have the user run `kitaru login` themselves. It opens a browser device flow where they select or create a Kitaru workspace (14-day trial, no credit card required), waits for the workspace, and stores a credential for its URL. For an existing workspace, `kitaru login <workspace-url>` does the same. Read the managed URL from the login result (`item.server_url`) or from `kitaru status` afterwards.
5. **Know which server is selected.** `kitaru login` makes the managed workspace the selected server. From here on, `kitaru` without `--server` talks to the managed workspace, so every push command must name the local server with the global `--server <local-url>` option. `--server` takes precedence over `KITARU_API_URL` and the stored selection.

Credentials: the destination is authenticated only with the credential `kitaru login` stored for the exact `--to` URL. `KITARU_API_KEY` in the environment applies to the source and is ignored for the destination. If `KITARU_API_KEY` holds a key for a different server than the source, unset it for these commands.

## 2. Preview with a dry run

```bash
kitaru --server <local-url> workspace push --to <managed-url> --dry-run \
  --output json --machine --non-interactive --no-browser
```

A dry run writes nothing. `item.counts` has one entry per kind (`agents`, `agent_versions`, `connections`, `sessions`, `insights`), each with `copied`, `already_present`, `skipped`, and `failed`. In a dry run, `copied` means "would be copied". Show the user the counts as a small table, then list what `item.skipped` says and why.

Tell the user what the preview does not show:

- Connections that hold secret values are copied without them and listed under `incomplete_connections` with the names of the missing keys.
- A destination agent with the same name is reused, and the source agent's sessions land under it.
- To move only some agents, repeat `--agent <name>`. Their sessions and insights follow them. Connections are always considered because they belong to the workspace.

## 3. Get confirmation

Ask two separate questions and wait for each answer:

1. "Copy these records from `<local-url>` to `<managed-url>`?" State the counts again.
2. If `incomplete_connections` is not empty: "These connections will arrive without their secret values, because the server never returns them. You will re-enter them on the destination afterwards. OK?"

## 4. Run the push

```bash
kitaru --server <local-url> workspace push --to <managed-url> \
  --output json --machine --non-interactive --no-browser
```

Add `--agent` options only as confirmed. Capture stdout and stderr, and keep the output: a later rerun reports copied records as `already_present` and no longer repeats `unmapped_references` for them. `incomplete_connections` is reported on every run until the keys are set.

## 5. Read the report

On success (exit code 0) the report is the JSON document on stdout. `warnings` and `next_actions` are top-level fields. The rest is under `item`:

| Field | Meaning | What to tell the user |
|---|---|---|
| `counts` | Per-kind totals of `copied`, `already_present`, `skipped`, `failed` | The headline result. |
| `skipped` | `kind`, `record`, `reason` for each skipped record | Sessions still in progress and replay result sessions are never copied. An agent version is skipped when the destination agent's version numbers differ from the source. |
| `failed` | `kind`, `record`, `error` | Empty on success. See `partial_failure` below. |
| `incomplete_connections` | `connection`, `missing_keys`, and the `command` that sets them | These connections exist on the destination without their secret values. They do not work until the user sets every listed key. |
| `unmapped_references` | `insight`, `source_insight_id`, and `references` (`id`, `kind`) | These copied insights still mention records that exist only on the source, such as a skipped session, the import that created the sessions, or an analyzer version. Those links lead nowhere on the destination. The same list is stored in each insight's `kitaru.push/v1` metadata. |
| `not_copied` | Kinds a push never copies | Recreate the ones the user needs. |
| `details_truncated` | `true` when a detail list hit its limit of 200 entries | The counts are still complete. |

Explain each non-empty list in plain language, and read every entry in `warnings` to the user. Two warnings need action: agent versions whose run spec named secrets were copied without them, and sessions copied without an agent version because that version was not copied.

Insight references to copied sessions, nodes, and agents are rewritten to the destination IDs, and the local server URL inside insights is replaced with the managed URL. Sessions get new IDs on the destination.

## 6. Verify on the destination

The list commands return one page with `count` (items in this page) and `page.truncated`. There is no total, so use a large page and follow `page.next_cursor` with `--cursor` while `page.truncated` is true.

```bash
kitaru --server <managed-url> agent list --size 1000 --output json
kitaru --server <managed-url> session list --agent <agent-name> --size 1000 --output json
kitaru --server <managed-url> insight list --agent <agent-name> --size 1000 --output json
kitaru --server <managed-url> connection list --output json
```

For each pushed agent, the destination should hold at least `copied + already_present` records of each kind. A destination that had data before the push holds more. Give the user the dashboard link from `kitaru --server <managed-url> status` (`item.dashboard_url`) and ask them to open one copied session and one copied insight.

Rerunning the push is safe. Records are matched before they are written, so a second run reports everything as `already_present` and creates no duplicates. Rerun it later to bring over sessions recorded since the first push.

## 7. Next steps for the user

1. **Re-enter connection secrets.** For each entry under `incomplete_connections`, give the user this command to run in their own terminal, with the real names filled in and the values left for them to type:

   ```bash
   kitaru --server <managed-url> connection update <connection-name> \
     --set-secret KEY_ONE=... --set-secret KEY_TWO=...
   ```

   `--set-secret` replaces all stored secret values of the connection, so every missing key must go in one command. Do not run this command yourself.
2. **Reattach run-spec secrets** on agent versions if the report warned about them.
3. **Point the SDK and workers at the managed workspace.** Set `KITARU_API_URL` to the managed URL and `KITARU_API_KEY` to an API key the user creates for that workspace, wherever the agent, CI, and workers run. Restart workers so they register with the new server. If the MCP server was registered against the local URL, rerun `kitaru --server <managed-url> setup`.
4. **Recreate what was not copied**, if the user needs it: cohorts, evaluators, evaluations, investigations, annotations, experiments, replays, tags, importers, and analyzers. Sessions that were in progress can be pushed with a rerun once they settle.
5. **Leave the local server alone** until the user is satisfied. `kitaru logout --volumes` deletes its database and is the user's decision.

## Troubleshooting

Failures are JSON on stderr under `error`, with `kind`, `message`, and often `hint`.

| `error.kind` | Exit code | Cause and fix |
|---|---|---|
| `invalid_arguments` | 2 | `--to` is not an absolute HTTP(S) URL, or it is the same server as the source. After `kitaru login`, the selected server is the managed workspace: add `--server <local-url>`. |
| `invalid_configuration` | 2 | No source server could be resolved. Pass `--server <local-url>`. |
| `authentication_failed` | 3 | No stored credential for the `--to` URL, or the destination rejected it. Have the user run `kitaru login <managed-url>`, then rerun with `--server <local-url>`. The stored credential is keyed by URL, so `--to` must match the URL that was logged in to. `KITARU_API_KEY` does not help here. |
| `not_found` | 4 | An `--agent` name does not exist on the source. List names with `kitaru --server <local-url> agent list`. |
| `network_error` | 6 | A server is unreachable. Check `kitaru --server <url> status` for each side. Start the local server with `kitaru login --local` (this reselects the local server, so keep passing `--server`). |
| `partial_failure` | 8 | Some records failed. The full report is under `error.details` (same fields as `item`, plus `warnings` and `next_actions`), with each failure in `failed`. The error is retryable: rerun the same command, and records already copied are not copied again. If the same records fail twice, show the user their `error` text. |
