---
name: kitaru-workspace-push
description: Move a local open-source Kitaru workspace to a managed cloud workspace with `kitaru workspace push`. Use when a user who has been running Kitaru against a local server wants to sign up for the managed cloud and bring their agents, agent versions, provider connections, sessions, and insights with them, or asks to copy a workspace from one Kitaru server to another.
---

# Push a local Kitaru workspace to the managed cloud

`kitaru workspace push --to <destination-url>` copies agents, agent versions, provider connections, settled sessions with their nodes, and insights from one Kitaru server to another. This skill walks the user from a local server to a managed workspace: sign up, preview, copy, verify, and finish what the command cannot do.

## Rules

- Inside a project, run the CLI as `uv run kitaru`. Use plain `kitaru` only for an isolated install. The commands below write `kitaru` for brevity.
- The push creates remote state. Do not run it without `--dry-run` until the user has seen the preview for the exact scope being pushed and said yes.
- Tell the user before the push that connection secret values are not copied, so they know they will re-enter them on the destination.
- Never ask the user to paste a secret value, API key, or password into the chat, and never put one in a command you run. Give the user the command and have them run it in their own terminal.
- Never delete local data (`kitaru logout --volumes`) as part of this procedure. The local server stays the source of truth until the user decides otherwise.
- The user makes the judgment calls: which agents to move and when to switch production traffic. Connections belong to the workspace and are always copied; if the user wants to exclude connections, this command cannot do that.

## 1. Check prerequisites

1. **The CLI has the command.** Run `kitaru schema workspace push`. It works offline and prints the command's parameters. If it fails with `invalid_arguments` (unknown command path), the installed CLI predates `kitaru workspace push` (which ships in the Kitaru release after `0.27.8`). Ask the user before running the installer (`curl -fsSL https://kitaru.ai/install | bash`), since it updates packages and agent setup, then check again. If the upgraded CLI still lacks the command, stop and tell the user that the Kitaru release with `workspace push` is not available yet.
2. **Record the source URL before logging in to the cloud.** Run `kitaru status --output json` and read `item.server_url` and `item.server_source`. For a local server this is `http://localhost:8000` unless the user chose another port with `kitaru login --local --port` or `KITARU_LOCAL_PORT`. `kitaru config` holds only CLI preferences and does not report server URLs. If the managed login already happened — or the source is another self-hosted server — confirm the source URL with `kitaru --server <source-url> status --output json`.
3. **The source server is reachable and authenticated.** Run `kitaru --server <local-url> status --output json` and check both exit status and `item.authentication` (`status` can exit 0 with `missing` or `rejected`). If a CLI-owned local server reports `network_error`, its containers may be stopped: `kitaru login --local` starts them again and keeps the database. It also makes the local server the selected one, which is why every command below passes `--server` explicitly.
4. **The user is logged in to the managed cloud and a Kitaru workspace exists.** Have the user run `kitaru login` themselves. It opens a browser device flow where they select or create a Kitaru workspace (14-day trial, no credit card required), waits for the workspace, and stores a credential for its URL. For an existing server, `kitaru login <workspace-url>` stores a credential when the server requires authentication (an unauthenticated server needs no login). Read the managed URL from the login result (`item.server_url`) or from `kitaru status --output json` afterwards (note that `KITARU_API_URL` in the shell overrides the stored login).
5. **Know which server is selected.** `kitaru login` makes the managed workspace the selected server. From here on, `kitaru` without `--server` talks to the managed workspace unless `KITARU_API_URL` is set, so every push command must name the source server with the global `--server <local-url>` option. `--server` takes precedence over `KITARU_API_URL` and the stored selection.

Credentials: a destination that requires authentication is authenticated only with the credential `kitaru login` stored for the exact `--to` URL; a destination with no authentication needs no login. `workspace push` ignores `KITARU_API_KEY` and `KITARU_API_TOKEN` for `--to`, using them only for the source. Other CLI commands (`status`, `agent list`, `session list`, `insight list`, `connection list`, `connection update`) use normal CLI credential resolution, where `KITARU_API_KEY` overrides stored credentials and `KITARU_API_TOKEN` is the fallback when no stored credential is used. Unset both `KITARU_API_KEY` and `KITARU_API_TOKEN` on any command targeting a server they do not belong to — especially destination verification and `connection update`.

## 2. Preview with a dry run

```bash
kitaru --server <local-url> workspace push --to <managed-url> --dry-run \
  --output json --machine --non-interactive --no-browser
```

If the user only wants specific agents, include repeatable `--agent <name>` flags here. If they change the agent selection after seeing the preview, rerun the dry run with the new `--agent` flags before confirming.

A dry run creates no destination workspace records. On exit 0, `item.counts` has one entry per kind (`agents`, `agent_versions`, `connections`, `sessions`, `insights`), each with `copied`, `already_present`, `skipped`, and `failed`, where `copied` means "would be copied". Show the user the counts as a small table, then list `item.skipped`, `item.incomplete_connections`, and any top-level `warnings`.

A dry run can also exit `8` (`partial_failure`) before producing `item` — for example, when the destination already has a connection with the same name for a different provider. In that case, read the report from `error.details`, show the counts and the failing entry in `error.details.failed`, and stop until the user resolves the conflict (such as renaming one connection) and reruns the dry run.

Remind the user before confirming:

- A destination agent with the same name is reused, and the source agent's sessions and insights land under it.
- Connections are always considered because they belong to the workspace, even when `--agent` filters the agents.

## 3. Get confirmation

Ask two separate questions and wait for each answer:

1. "Copy these records from `<local-url>` to `<managed-url>`? This uploads full session inputs, outputs, node payloads, and non-secret env values from agent run specs and connections to `<managed-url>`." State the exact agent scope (all agents or the named `--agent` list) and counts again.
2. If `incomplete_connections` is not empty: "These connections will arrive without their secret values, because the server never returns them. You will re-enter them on the destination afterwards. OK?"

## 4. Run the push

```bash
kitaru --server <local-url> workspace push --to <managed-url> \
  --output json --machine --non-interactive --no-browser
```

Pass the exact `--agent` options confirmed in the preview. Capture stdout and stderr, and keep the output: a later rerun reports previously copied records as `already_present` and no longer repeats `unmapped_references` for them. `incomplete_connections` is reported on every run until the keys are set.

## 5. Read the report

On success (exit code 0) the report is the JSON document on stdout. `warnings` and `next_actions` are top-level fields. The rest is under `item`:

| Field | Meaning | What to tell the user |
|---|---|---|
| `counts` | Per-kind totals of `copied`, `already_present`, `skipped`, `failed` | The headline result (workspace-wide totals across all pushed agents). |
| `skipped` | `kind`, `record`, `reason` for each skipped record | In-progress sessions (can be pushed on a rerun once settled), replay result sessions (never copied), and any agent versions, sessions, or insights whose agent failed to copy (`Its agent was not copied.`). |
| `failed` | `kind`, `record`, `error`, `retryable` | Empty on success. `retryable` says whether a rerun can fix that record. See `partial_failure` below. |
| `incomplete_connections` | `connection`, `missing_keys`, and the `command` that sets them | These connections exist on the destination without their secret values. They do not work until the user sets every listed key. |
| `unmapped_references` | `insight`, `source_insight_id`, and `references` (`id`, `kind`) | These copied insights still mention records that exist only on the source, such as a skipped session, the import that created the sessions, or an analyzer version. Those links lead nowhere on the destination. The same list is stored in each insight's `kitaru.push/v1` metadata. |
| `not_copied` | Kinds a push never copies | Recreate the ones the user needs. |
| `details_truncated` | `true` when a detail list dropped entries after 200 items | The counts are still complete. |

Explain each non-empty list in plain language, and read every entry in `warnings` to the user. Pay particular attention to these warnings:

- **Run-spec secrets dropped:** agent versions whose run spec named secrets were copied without them; the user must reattach destination secret IDs before running them.
- **Renumbered agent versions:** versions match by content (ignoring `secret_ids`), so a copy can carry a different version number on the destination; sessions and insights still link to the matching copy.
- **Sessions without an agent version:** if an agent version failed to copy, its sessions were ingested with no `agent_version_id`. A rerun copies the missing version but **does not relink** already-copied sessions — those sessions stay unversioned unless deleted on the destination before rerunning.
- **Connection non-secret differences:** an existing destination connection with the same name and provider kept its own non-secret `env` values.

Insight references to copied sessions, their referenced nodes, and agents are rewritten to the destination IDs, and the source server URL inside insights is replaced with the destination API URL. Sessions, agents, and agent versions get new IDs on the destination.

## 6. Verify on the destination

Unset any source `KITARU_API_KEY` and `KITARU_API_TOKEN` for these commands so they use the stored destination credential. The list commands return one page with `count` (items in this page) and `page.truncated`. There is no total, so use `--size 1000` and follow `page.next_cursor` with `--cursor` while `page.truncated` is true.

```bash
env -u KITARU_API_KEY -u KITARU_API_TOKEN kitaru --server <managed-url> agent list --size 1000 --output json
env -u KITARU_API_KEY -u KITARU_API_TOKEN kitaru --server <managed-url> agent version list <agent-name> --size 1000 --output json
env -u KITARU_API_KEY -u KITARU_API_TOKEN kitaru --server <managed-url> session list --agent <agent-name> --size 1000 --output json
env -u KITARU_API_KEY -u KITARU_API_TOKEN kitaru --server <managed-url> insight list --agent <agent-name> --size 1000 --output json
env -u KITARU_API_KEY -u KITARU_API_TOKEN kitaru --server <managed-url> connection list --size 1000 --output json
```

`item.counts` holds workspace-wide totals, not per-agent counts. Sum the paged destination counts across every pushed agent for `agent_versions`, `sessions`, and `insights` (and check `agents` and `connections` once for the workspace); each total should be at least `copied + already_present`. A destination that had data before the push holds more. Check `env -u KITARU_API_KEY -u KITARU_API_TOKEN kitaru --server <managed-url> status --output json`: when `item.dashboard_url` is present, give the user the dashboard link and ask them to open one copied session and one copied insight (and click a session link inside the insight to confirm it resolves).

Rerunning the push is safe. Records are matched before they are written, so a second run against unchanged source data reports previously copied records as `already_present` and creates no duplicates (skipped records stay skipped, and an agent version edited since the first push is copied as a new version). Rerun it later to bring over sessions recorded since the first push.

## 7. Next steps for the user

1. **Re-enter connection secrets.** For each entry under `incomplete_connections`, give the user its `command` to run in their own terminal (with any source `KITARU_API_KEY`/`KITARU_API_TOKEN` unset), with the `<value>` placeholders left for them to fill in. It has this shape:

   ```bash
   kitaru --server <managed-url> connection update <connection-name> \
     --set-secret KEY_ONE=<value> --set-secret KEY_TWO=<value> [--default]
   ```

   `--set-secret` replaces all stored secret values of the connection, so the command names every secret key in one call: the missing ones and any the destination already held at push time, which the user must re-enter too. A connection copied without its secret values is never the provider default on the destination; the command ends with `--default` when the source connection was the default and the destination had none for that provider at push time, so it becomes the default only once its secrets are set. If the connection or provider default was changed on the destination after the push, re-check it first so the command does not overwrite newer keys or defaults. To keep secret values out of shell history, suggest reading them into variables (`read -rs KEY_ONE`) and passing `--set-secret KEY_ONE="$KEY_ONE"` (or using the shell's leading-space history ignore). Do not run this command yourself.
2. **Reattach run-spec secrets** on agent versions if the report warned about them. Match each destination version by content or display version rather than by source version number, because destination version numbers can differ.
3. **Point the SDK and workers at the managed workspace.** Set `KITARU_API_URL` to the managed URL and `KITARU_API_KEY` to an API key the user creates in the managed workspace dashboard, wherever the agent, CI, and workers run. Update any configured agent IDs or agent-version IDs to the destination UUIDs, and restart workers so they register with the new server. If the MCP server was registered against the local URL, rerun `kitaru --server <managed-url> setup --no-skills` and restart the coding agent so it picks up the new MCP configuration.
4. **Recreate what was not copied**, if the user needs it: cohorts, evaluators, evaluations, investigations, annotations, experiments, replays, tags, importers, and analyzers. Sessions that were in progress can be pushed with a rerun once they settle.
5. **Leave the local server alone** until the user is satisfied. `kitaru logout --volumes` deletes its database and is the user's decision.

## Troubleshooting

Failures are JSON on stderr under `error`, with `kind`, `message`, and often `hint`.

| `error.kind` | Exit code | Cause and fix |
|---|---|---|
| `invalid_arguments` | 2 | `--to` is not an absolute HTTP(S) URL, or it is the same server as the source (also caught when two URLs reach one server, such as `localhost` and `127.0.0.1`). After `kitaru login`, the selected server is the managed workspace: add `--server <local-url>`. |
| `invalid_configuration` | 2 | No source server could be resolved, `KITARU_API_URL` is invalid, or a server returned an unreadable/incompatible response. Pass `--server <local-url>` and verify client/server versions match. |
| `authentication_failed` | 3 | No stored credential for the `--to` URL, or a server rejected its credential (HTTP 401). Have the user run `kitaru login <managed-url>` (or log in to an authenticated source), then rerun with `--server <local-url>`. The stored credential is keyed by URL, so `--to` must match the URL that was logged in to. `KITARU_API_KEY` does not authenticate `--to`. |
| `forbidden` | 3 | A server returned HTTP 403 during a write. Check the user's permissions on the destination workspace (or source) before retrying. |
| `not_found` | 4 | An `--agent` name does not exist on the source. List names with `kitaru --server <local-url> agent list`. |
| `network_error` | 6 | A server is unreachable, timed out, or returned HTTP 5xx. Check `kitaru --server <url> status --output json` for each side. For a stopped CLI-owned local server, `kitaru login --local` starts it (and reselects the local server, so keep passing `--server`). |
| `partial_failure` | 8 | Some records failed (including provider conflicts during `--dry-run`). The full report is under `error.details` (same fields as `item`, plus `warnings` and `next_actions`), with each failure in `failed`. In text output a summary report is printed after the error message. The error is retryable only when every failure is: rerun the same command, and records already copied are not copied again (note that sessions already copied without an agent version are not relinked by a rerun). Insights that cite a record that failed in this run are held back and written on the rerun. When a failure is not retryable, such as a same-named connection with a different provider on the destination, show the user its `error` text instead of rerunning. |
