# Kitaru operations

Use this reference for exact operations. Inspect `kitaru schema`, command help, or discovered MCP schemas before building a call; the installed version wins when it differs from this page. Set `KITARU_ACTIVE_SKILL=kitaru-insights` and use `--output json --machine --non-interactive --no-browser` on CLI calls.

## Contents

- [Check what is installed](#check-what-is-installed)
- [Resolve and pin the scope](#resolve-and-pin-the-scope)
- [Read existing cards](#read-existing-cards)
- [Run Quick analysis](#run-quick-analysis)
- [Count cheaply](#count-cheaply)
- [Export sessions](#export-sessions)
- [Write, replace, and list cards](#write-replace-and-list-cards)
- [Known gaps](#known-gaps)

## Check what is installed

Confirm the CLI or MCP server can reach the intended server and agent, for example with `kitaru info` and `kitaru agent get AGENT`. Check `kitaru session analyze --help` before offering Quick; when it is missing, say the installed Kitaru predates it, recommend upgrading, and continue with Standard or Deep, which need only read and insight-create operations. MCP `kitaru_failure_matrix` is optional; continue without it in CLI-only hosts.

## Resolve and pin the scope

`kitaru session list` selects sessions with flags that combine as AND:

- `--agent AGENT`, `--status completed|failed|in_progress`, `--origin imported|recorded|replay`, `--tag TAG` (one tag), `--cohort COHORT_VERSION`;
- `--started-after` and `--started-before`, ISO 8601 with a timezone;
- `--filter JSON` for anything else, such as `{"field":"import_id","op":"eq","value":"UUID"}` or `{"field":"experiment_run_id","op":"eq","value":"UUID"}`;
- `--size` up to 1000 and `--cursor` for the next page; `--sort` only supports `created`.

The JSON output is an envelope with `items` and `page.next_cursor`. Follow cursors until `next_cursor` is null, and save each page under `RUN/scope/`.

Leave out in-progress sessions unless the user asks for them; analysis skips them anyway. Pin the result: `pick_sample.py` writes the full pinned ID list into `sample.json` as `population_ids`. Later steps use those IDs, never the original selector, so a "last 7 days" scope cannot drift while the run is in progress.

For an explicit ID list, filter with `{"field":"id","op":"in","value":[...]}`; one `in` holds at most 100 values, so split longer lists into batches. A filter also allows at most 30 conditions and depth 5. Reject a scope whose sessions belong to more than one agent; cards attach to exactly one agent.

MCP reads sessions with `kitaru_activity_read`: `list` with kind `session`, a `filter`, `size` up to 100, and `cursor`.

## Read existing cards

- CLI: `kitaru insight list --agent AGENT --size 100`, following cursors; `kitaru insight get ID`.
- MCP: `kitaru_review_read` with `list` or `get` and kind `insight`.
- Filter with `--filter` on `id`, `agent_id`, `import_id` (`eq`, `in`, and `is_null` on servers that support it), `task_id`, `name`, and `type`.

Analyzer cards carry `analyzer_version_id` and, for an import, `import_id`. Cards from earlier skill runs carry the provenance key described in [insight-contract.md](insight-contract.md). Match an earlier run by its provenance `scope`, not by title.

## Run Quick analysis

`kitaru session analyze --agent AGENT --sessions-file RUN/population_ids.txt --analyzer ANALYZER@VERSION --wait` runs an analyzer over exactly the pinned sessions. `pick_sample.py --ids-out` writes `population_ids.txt`. Other selectors (`--tag`, `--cohort`, `--import-id`, `--started-after`, `--started-before`, `--filter`, or positional IDs) also work and combine as AND.

- When every pinned session comes from one import, also pass `--import-id IMPORT_ID`. The cards then record that import and appear in its dashboard view.
- If the task fails with a validation error about `import_id`, the analyzer's environment runs an older Kitaru that only accepts import-scoped tasks. Retry with `--import-id` when the scope is one import; otherwise report that Quick needs a newer Kitaru on the analyzer side, and continue with Standard or Deep.
- Choose the analyzer with the user. `kitaru/post-import-insights@latest` needs no model credentials. `kitaru/openai-post-import-insights@latest` needs OpenAI credentials through a connection or the worker, and bills the user's OpenAI account. Pass a connection with `--analyzer-connection ANALYZER@VERSION=CONNECTION`.
- The server rejects a selection with no finished sessions or more than its limit (1,000 by default). Split a larger scope into batches and report each job. Below an analyzer's own session minimum, its task is recorded as skipped and writes no cards.
- A worker claiming analyzer tasks must be running (`kitaru worker start --claim analyzer`). Without one the job stays queued; report that rather than waiting indefinitely.
- The terminal receipt lists one task per analyzer; read its cards with `kitaru insight list --filter '{"field":"task_id","op":"in","value":[...]}'`. Cards record an `import_id` only when `--import-id` was given.
- Each call adds new cards; nothing replaces earlier ones. Confirm before rerunning.
- MCP: `kitaru_workflow_start` with `operation: "analysis"`, `agent_id`, `analyzers`, and any of `session_ids` (up to 1,000), `tag`, `cohort_version_id`, `import_id`, `started_after`, `started_before`, and `idempotency_key`. It has no raw `filter` field. It returns the queued job; read it with `kitaru_activity_read`.

## Count cheaply

- Session fields from the scope pages give status, origin, cost, `llm_call_count`, `tool_call_count`, `started_at`, and `ended_at`.
- `kitaru session nodes SESSION --filter '{"field":"node_type","op":"eq","value":"tool_call"}'` lists one kind of node. `node_type` is the only node filter field; read `status`, `error`, and `tool_name` from the result.
- MCP `kitaru_failure_matrix` takes a session `filter` (an `id` `in` list works), `state_by` (`tool`, `span`, or `node`), optional `compare_filter`, and `max_sessions` (default 200, at most 500). Its summary reports how many sessions were capped. `kitaru_failure_matrix_cell` lists the sessions and failing nodes behind one cell.

## Export sessions

There is no export or transcript command. Export with the CLI, which writes payloads straight to files. For each picked session:

```bash
kitaru session get SESSION_ID --output json > RUN/export/SESSION_ID.session.json
kitaru session nodes SESSION_ID --include-payloads --size 1000 --output json > RUN/export/SESSION_ID.nodes.json
```

When `page.next_cursor` is not null, fetch the next page with `--cursor` into `SESSION_ID.nodes.2.json`, and so on. Then run:

```bash
python3 scripts/condense_sessions.py RUN/export RUN/transcripts
```

MCP can read the same data (`kitaru_activity_read` `get` with kind `session`, and `list_children` with kind `session_nodes`, `parent_id`, `include_payloads: true`, `size` up to 100), but every payload then passes through the agent's own context, which defeats the run folder. Use MCP export only for a handful of sessions when no CLI is available; the condenser accepts saved MCP results.

## Write, replace, and list cards

- CLI: `kitaru insight create --agent AGENT --insight 'JSON' [--insight 'JSON' ...] --idempotency-key KEY`. One call takes 1 to 100 cards. `python3 scripts/check_cards.py RUN/cards.json --emit-command AGENT --idempotency-key KEY` prints a safely quoted command.
- MCP: `kitaru_review_manage` with `operation: "create_insights"`, `agent_id`, `insights` (1 to 100), and `idempotency_key`.
- Use the run ID plus a batch number as the idempotency key, so a retried write cannot duplicate the batch.
- Update wording with `kitaru insight update ID --title ... --description ...` or MCP `update_insight`. Data and metadata cannot be updated; replace the card instead.
- Delete with `kitaru insight delete ID --force`, or MCP `kitaru_delete` with kind `insight` when the server runs in destructive mode. Delete only cards whose provenance run ID belongs to an earlier skill run the user chose to replace, list them first, and get explicit confirmation; deletion is permanent.

After writing, list the new cards with `kitaru insight list --agent AGENT --filter '{"field":"import_id","op":"is_null"}'` and match them by run ID. Servers older than that filter reject `is_null` on `import_id` with HTTP 422; then list by `--agent` alone, following cursors, and match the run ID locally. In the dashboard, skill cards appear under the agent's Insights tab in the view for insights without an import, when the installed dashboard has that view.

## Known gaps

- Cards have no first-class session links or provenance fields; this skill stores both in metadata.
- The server does not group a hand-written batch under a run, so runs over the same agent share one list. The provenance run ID is how agents tell them apart.
- `--insight` takes inline JSON only; use `check_cards.py --emit-command` or MCP rather than quoting by hand.
- There is no compact transcript operation; `condense_sessions.py` builds one from exported JSON.
