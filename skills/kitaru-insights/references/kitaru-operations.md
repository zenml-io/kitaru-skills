# Kitaru operations

Use this reference for exact operations. Inspect `kitaru schema`, command help, or discovered MCP schemas before building a call; the installed version wins when it differs from this page. Set `KITARU_ACTIVE_SKILL=kitaru-insights` and use `--output json --machine --non-interactive --no-browser` on CLI calls.

## Contents

- [Check what is installed](#check-what-is-installed)
- [Resolve and pin the scope](#resolve-and-pin-the-scope)
- [Read existing cards](#read-existing-cards)
- [Run Quick analysis](#run-quick-analysis)
- [Count cheaply](#count-cheaply)
- [Export sessions](#export-sessions)
- [Measure with the TypeSafe evaluator](#measure-with-the-typesafe-evaluator)
- [Write, replace, and list cards](#write-replace-and-list-cards)
- [Known gaps](#known-gaps)

## Check what is installed

Confirm the CLI or MCP server can reach the intended server and agent, for example with `kitaru info` and `kitaru agent get AGENT`. Record the `dashboard_url` that `kitaru info --output json` reports in `run.json`: cards link sessions as `DASHBOARD_URL/sessions/SESSION_ID`. It is null when the deployment serves no dashboard. On a ZenML Pro workspace the session page sits under the workspace path, so confirm one link opens before writing a batch that relies on it. Check `kitaru session analyze --help` before offering Quick. When it is missing, the installed Kitaru predates it: Quick is then available only for a single-import scope through `kitaru import analyze`; recommend upgrading for other scopes. Standard and Deep need only read and insight-create operations. MCP `kitaru_failure_matrix` is optional; continue without it in CLI-only hosts.

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

Analyzer cards carry `analyzer_version_id` and, when they came from an import or `kitaru import analyze`, `import_id`. Cards from `kitaru/openai-session-findings` keep their context under `metadata["kitaru.session-findings/v1"]` instead of `kitaru.insights/v1`: `harm` (`high`, `medium`, or `low`), the `checks` behind the finding, and `contributing_session_ids`. Read them as leads that a model verified per session, not as human verdicts. Cards from earlier skill runs carry the provenance key described in [insight-contract.md](insight-contract.md). Match an earlier run by its provenance `scope`, not by title.

## Run Quick analysis

`kitaru session analyze --agent AGENT --sessions-file RUN/population_ids.txt --analyzer ANALYZER@VERSION --wait` (Kitaru releases after 0.27.7) runs each selected analyzer once over exactly the pinned sessions, whether they were imported, recorded live, or a mix. `pick_sample.py --ids-out` writes `population_ids.txt`. Other selectors (positional IDs, `--tag`, `--cohort`, `--import-id`, `--started-after`, `--started-before`, `--filter`) also work and combine as AND; with none, every finished session of the agent is analyzed. The server fixes the matching sessions when it creates the job, so a queued job still reads the sessions that matched at creation. Sessions still in progress are left out.

When the installed CLI lacks `session analyze`, Quick is available only when the scope is exactly one import: `kitaru import analyze IMPORT_ID --analyzer ANALYZER@VERSION --wait` runs over every finished session that import created, not over a pinned subset. For any other scope on such a version, say that Quick needs a newer Kitaru and continue with Standard or Deep.

- Choose the analyzer with the user. `kitaru/post-import-insights@latest` needs no model credentials. `kitaru/openai-post-import-insights@latest` needs OpenAI credentials through a connection or the worker, and bills the user's OpenAI account. Pass a connection with `--analyzer-connection ANALYZER@VERSION=CONNECTION` and parameters with `--analyzer-params ANALYZER@VERSION=JSON`.
- `kitaru/openai-session-findings@latest` (Kitaru 0.27.5 and later) reads the sessions with OpenAI, verifies each problem it finds on every session with OpenAI's Decisions API, and writes at most ten cards, most harmful first. It needs the same OpenAI connection, with Decisions API access on that OpenAI project, and unlike the other two analyzers it sends session content to OpenAI: the system prompt, user messages, tool inputs and outputs, and the final reply. Get the user's agreement to that before selecting it. Its optional `context` parameter takes extra text about the agent, such as a summary of the context brief: `--analyzer-params 'kitaru/openai-session-findings@latest={"context":"..."}'`.
- The server rejects a selection with no finished session or more than its cap (`KITARU_SERVER_ANALYSIS_SESSION_LIMIT`, 1,000 by default). Split a larger scope into batches and report each job. Below an analyzer's own session minimum, its task is recorded as skipped and writes no cards.
- Cards from `kitaru session analyze` never record an `import_id`, even when you select with `--import-id`, so they do not appear in an import's dashboard view. To file cards under one import, use `kitaru import analyze IMPORT_ID` instead, which covers that whole import. When every analyzed session came from one import, `kitaru/post-import-insights` cards still name that import in their investigation prompt.
- The worker that claims the analyzer task must run a compatible Kitaru and analyzer package. A worker on Kitaru 0.27.7 or older fails a `session analyze` task with a validation error saying `import_id` is required, because its task model only knows import-scoped analysis. `kitaru-post-import-insights` 0.4.0 and older fail with "every post-import insight session must have an import ID" when a selected session was recorded live. In either case, report which package to upgrade on the worker; when the scope is one import, `kitaru import analyze` still works, otherwise continue with Standard or Deep.
- A worker claiming analyzer tasks must be running (`kitaru worker start --claim analyzer`). Without one the job stays queued; report that rather than waiting indefinitely.
- The terminal receipt lists one task per analyzer; read its cards with `kitaru insight list --filter '{"field":"task_id","op":"in","value":[...]}'`.
- To compare time windows, run one job per window over the pinned IDs that started in it: split `population_ids.txt` by start time, or combine `--sessions-file RUN/population_ids.txt` with `--started-after` and `--started-before`, which combine as AND. Use one idempotency key per window (`RUN_ID-quick-last`, `RUN_ID-quick-this`). Both jobs' cards land in the same list without an import, so keep each job's task ID in `run.json` to tell them apart.
- `kitaru/post-import-insights` keeps one card per family and fills a page of six. Exact retries after a failure, repeating tool cycles, and repeated tool calls are one family, so only one of them becomes a card even when the others were detected. When the user cares about tools or loops, add `tool_stats.py` counts rather than reading a missing card as absence.
- Each call adds new cards; nothing replaces earlier ones. Pass `--idempotency-key` so a retried call after a lost response does not start a second job, and confirm with the user before any deliberate rerun.
- MCP: `kitaru_workflow_start` with `operation: "analysis"`, `agent_id`, `analyzers` (1 to 20 entries, each with `analyzer` and optional `version`, `params`, `connection_id`, and `min_sessions`), an optional session `filter`, and `idempotency_key`. Express pinned IDs as `{"field":"id","op":"in","value":[...]}` with at most 100 values per `in`, joining batches with `or`; tags, cohort versions, imports, and time windows are filter conditions on `tag`, `cohort_version_id`, `import_id`, and `started_at`. It returns the queued job; read it with `kitaru_activity_read`. Analyzers can also run at import time through `kitaru_session_import` with `analyzers`.

## Count cheaply

- Session fields from the scope pages give status, origin, cost, `llm_call_count`, `tool_call_count`, `started_at`, and `ended_at`.
- `kitaru session nodes SESSION --filter '{"field":"node_type","op":"eq","value":"tool_call"}'` lists one kind of node. `node_type` is the only node filter field; read `status`, `error`, and `tool_name` from the result.
- For per-tool counts over the whole scope, export every pinned session with short fields and run `tool_stats.py` on that folder. Split `population_ids.txt` into files of about 200 IDs and run `kitaru session read --sessions-file RUN/tools/ids.N.txt --max-chars 300 --output json > RUN/tools/export/batch-N.read.json` for each. This reads every node of every session, so estimate the size first (sessions times their average node count) and include it in the approval. Short fields keep the export small; identical-argument repeats then compare the first 300 characters of each input.
- MCP `kitaru_failure_matrix` takes a session `filter` (an `id` `in` list works), `state_by` (`tool`, `span`, or `node`), optional `compare_filter`, and `max_sessions` (default 200, at most 500). Its summary reports how many sessions were capped. `kitaru_failure_matrix_cell` lists the sessions and failing nodes behind one cell.

## Export sessions

Export with `kitaru session read` (Kitaru 0.27.7 and later), which fetches every picked session with its nodes in one call and renders each as a compact transcript: each model call's new text only, repeated payloads pointing back at their first appearance, system-prompt changes flagged, node errors kept whole, recognizable credentials masked in structured payloads, and every cut marked `[+N chars]`. Plain text is not redacted, so the transcripts stay as sensitive as the traces. Write the picked IDs with `pick_sample.py --picks-out RUN/picked.txt`, then run:

```bash
kitaru session read --sessions-file RUN/picked.txt --max-chars 1500 --output json > RUN/export/picked.read.json
python3 scripts/condense_sessions.py RUN/export RUN/transcripts
```

The JSON gives each step's `node_id` UUID and its `index`, the zero-based position of the node in the session; the text output shows only `[index]`, so always export JSON. `condense_sessions.py` writes one transcript per session with both on each step line and a `manifest.json` with `estimated_tokens` for balancing readers. `--reasoning` adds the visible reasoning of model calls; add it only when a pattern depends on it, since it grows every transcript. To see one cut node whole, run `kitaru session read SESSION --node N --full`, where `N` is the `[N]` position in the transcript.

When the installed CLI has no `session read`, export the raw records instead. For each picked session:

```bash
kitaru session get SESSION_ID --output json > RUN/export/SESSION_ID.session.json
kitaru session nodes SESSION_ID --include-payloads --size 1000 --output json > RUN/export/SESSION_ID.nodes.json
```

When `page.next_cursor` is not null, fetch the next page with `--cursor` into `SESSION_ID.nodes.2.json`, and so on, then run the same `condense_sessions.py` command. Its transcripts use the same zero-based `[N]` positions.

MCP `kitaru_session_read` takes `session_ids` (at most 10) plus `max_chars`, `full`, `reasoning`, and `node`, and returns the transcripts under `data.transcripts`. Every transcript then passes through the agent's own context, which defeats the run folder, so use MCP export only for a handful of sessions when no CLI is available. The condenser accepts a saved `kitaru_session_read` result named `NAME.read.json`, and saved `kitaru_activity_read` session and node results named as above.

## Measure with the TypeSafe evaluator

Jev measurement runs as an ordinary Kitaru evaluation, so its results are stored as evaluation rows with their evaluator version and params. Follow `kitaru-investigation`'s TypeSafe reference (`references/typesafe-evaluator.md`) for package installation, registration, connections, and consent; this section covers only what the insights run adds.

- Find a registered TypeSafe evaluator with `kitaru evaluator list` and `kitaru evaluator version list`; its entrypoint is `kitaru_typesafe_evaluator.judge:judge`. Reuse an existing version. Its questions are params, so a new set of questions needs no new registration.
- Write the params to `RUN/measure/jev-params.json`: `{"state": "outcome", "questions": {"insights.p1": {"type": "noul", "instructions": "..."}}}`. Question names allow letters, digits, `-`, `_`, and `.`. Use `"state": "full"` only when a question needs the system prompt or model messages; `include` narrows either view.
- Run: `kitaru session evaluate --sessions-file RUN/population_ids.txt --evaluator EVALUATOR@VERSION --evaluator-params "EVALUATOR@VERSION=$(cat RUN/measure/jev-params.json)" --evaluator-connection EVALUATOR@VERSION=CONNECTION --wait --idempotency-key RUN_ID-jev-1`. Run the agreement check first with a sessions file holding only the read sessions.
- Each session answers every question in one request. A session above Jev's input limit produces an `unavailable` row per question; invalid params or credentials fail the task.
- Read the rows: `kitaru evaluation list --filter '{"field":"task_id","op":"in","value":[TASK_IDS]}' --size 1000 --output json`, following cursors, saving each page under `RUN/measure/evaluations/`. Then `python3 scripts/evaluations_to_judgments.py RUN/measure/evaluations/*.json --out RUN/measure/judgments/jev.jsonl`.
- MCP: `kitaru_workflow_start` with `operation: "evaluation"` takes `session_ids` (at most 100) and `evaluators` (at most 100), so the CLI with `--sessions-file` suits a whole-scope run.

## Write, replace, and list cards

- CLI: `kitaru insight create --agent AGENT --insight-file RUN/cards.json --idempotency-key KEY`. The file holds one card object or an array of 1 to 100 cards; `--insight-file` (Kitaru 0.27.4 and later) replaces repeated `--insight 'JSON'` arguments. `python3 scripts/check_cards.py RUN/cards.json --emit-command AGENT --idempotency-key KEY` checks the file and prints a safely quoted command for it. On older CLIs, write the batch with MCP instead of quoting each card by hand.
- MCP: `kitaru_review_manage` with `operation: "create_insights"`, `agent_id`, `insights` (1 to 100), and `idempotency_key`.
- Use the run ID plus a batch number as the idempotency key, so a retried write cannot duplicate the batch.
- Update wording with `kitaru insight update ID --title ... --description ...` or MCP `update_insight`. Data and metadata cannot be updated; replace the card instead.
- Delete with `kitaru insight delete ID --force`, or MCP `kitaru_delete` with kind `insight` when the server runs in destructive mode. Delete only cards whose provenance run ID belongs to an earlier skill run the user chose to replace, list them first, and get explicit confirmation; deletion is permanent.

After writing, list the new cards with `kitaru insight list --agent AGENT --filter '{"field":"import_id","op":"is_null"}'` and match them by run ID. Servers older than that filter reject `is_null` on `import_id` with HTTP 422; then list by `--agent` alone, following cursors, and match the run ID locally. In the dashboard, skill cards appear under the agent's Insights tab in the view for insights without an import, when the installed dashboard has that view.

## Known gaps

- Cards have no first-class session links or provenance fields; this skill stores both in metadata.
- The server does not group a hand-written batch under a run, so runs over the same agent share one list. The provenance run ID is how agents tell them apart.
