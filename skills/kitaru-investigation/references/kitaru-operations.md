# Kitaru operations

Use this reference before reading or mutating Kitaru investigation state. Treat the installed Kitaru schema and discovered MCP tools as authoritative when they differ from this reference.

## Contents

- [Transport policy](#transport-policy)
- [Operation map](#operation-map)
- [Resource contracts](#resource-contracts)
- [Setup and transport readiness](#setup-and-transport-readiness)
- [Frontend bridge and failure](#frontend-bridge-and-failure)
- [Known product boundaries](#known-product-boundaries)
- [Mutation and retry rules](#mutation-and-retry-rules)

## Transport policy

Prefer native MCP when an exact bounded operation exists. CLI-only operation is supported. Use the CLI when the operation requires a local file or evaluator script, benefits from built-in wait or watch behavior, or the relevant MCP tool is unavailable.

For agent-facing CLI calls, use these flags when the installed command schema exposes them:

```text
--output json --machine --non-interactive --no-browser
```

The deliberate frontend handoff may present or open one resolved URL. Do not open a browser for ordinary CLI calls.

Before relying on exact syntax:

1. inspect the installed `kitaru schema` output or command help;
2. inspect discovered MCP tools and their input schemas when MCP is available;
3. prefer exact IDs and versions over names;
4. preserve JSON results and carry returned IDs into the next call.

Do not use direct REST calls to fill a missing CLI or MCP contract.

## Setup and transport readiness

Treat setup as part of reaching the first usable session, not as an unexplained prerequisite:

1. Treat MCP as preferred, not required. Inventory discovered native MCP tools first. If no native tools are discovered, distinguish among a missing `kitaru[mcp]` installation, absent host configuration, a server left in read-only mode, and host configuration added after the coding-agent process started. For absent host configuration or a mode too low for the next write, offer `kitaru setup` (Kitaru 0.26.0 or later; `uv run kitaru setup` inside a project) and run it only with approval. It registers `kitaru-mcp` with every detected coding agent in `standard` mode by default (`--mode read-only|standard|destructive`) against the global `--server` target, and replaces an earlier `kitaru` entry. Unless `--no-skills` is passed, it also rewrites each installed Kitaru skill directory from the current release, overwriting local edits; `--no-mcp` skips registration. A host restart follows.
2. MCP write operations require `standard` or `destructive` mode. Modes are cumulative: a `destructive`-mode server also exposes every `standard` write tool, so use its ordinary write tools normally. Reserve destructive actions for explicitly requested deletes or cancellations.
3. Check whether `kitaru` is available in the active project environment only when the next operation and its handoff cannot be completed through the discovered MCP tools. Investigation creation through either transport can return the product-owned review link, so do not install the CLI or recreate the investigation solely to obtain a link. If neither transport can complete the operation and handoff, inspect the project's current setup instructions and the official Kitaru installation guide; when MCP is connected, the read-only `kitaru_docs_search` tool searches the guides bundled with the installed Kitaru version and returns links to the published pages. Do not infer a package manager, virtual environment, or install command from repository layout alone. Explain and obtain approval before changing the project environment.
4. Run `kitaru status` under the same condition to resolve the selected server, credentials, compatibility, dashboard URL, and worker readiness. Its top-level `dashboard_url` is the resolved dashboard base: the server-reported dashboard URL, or the server URL itself when the server serves the bundled UI. Use it rather than the raw `server.dashboard_url`, which can be empty when the server serves the bundled UI. Use `kitaru doctor` when a check fails or its cause is unclear.
5. A host normally discovers new MCP configuration only after restart. Before restart, preserve the current repository, agent/version, trace source, completed setup, and next action in a compact checkpoint. Tell the user how to resume with the host's documented mechanism rather than assuming one command works everywhere.
6. When CLI covers the next operation, state that fallback in one sentence and continue. Do not make transport selection another user decision unless the missing MCP capability changes the result or blocks the next operation.

## Operation map

| Need | Structured CLI | Native MCP |
|---|---|---|
| Check connection and worker readiness | `kitaru status`; use `kitaru doctor` for independent diagnostics | No single equivalent; use bounded reads only after the server is configured |
| Resolve agent or version | `kitaru agent get AGENT`; `kitaru agent version get AGENT@VERSION` | `kitaru_registry_read`, `get` or `get_version`, kind `agent` |
| Resolve installed importers | `kitaru importer list`; inspect an exact match with `kitaru importer get IMPORTER` | `kitaru_registry_read`, `list` or `get`, kind `importer` |
| Import a local trace payload | `kitaru session import FILE --importer IMPORTER@VERSION --agent AGENT@VERSION`, optionally `--join-on JSON_POINTER`, `--tag TAG`, and `--wait`; current tag application requires waiting | `kitaru_session_import` uses an existing payload blob and exact importer and agent versions; it cannot read a local file |
| Import from a provider API | `kitaru session import --importer IMPORTER@VERSION --agent AGENT@VERSION --since 7d --connection CONNECTION --wait`; omit FILE | `kitaru_session_import` with API `source`, exact importer ID/version, and agent-version ID |
| Read provider connections | `kitaru connection list`; `kitaru connection get CONNECTION` | `kitaru_connection_read`, `list` or `get`; secret values are never returned |
| Configure provider credentials | `kitaru connection create NAME --importer IMPORTER`; `kitaru connection set-default CONNECTION` | `kitaru_connections_manage`, `create`, `update`, or `set_default`, in standard mode |
| Resolve analyzers | `kitaru analyzer list`; `kitaru analyzer get ANALYZER` | `kitaru_registry_read`, kind `analyzer` |
| Read persisted insights | `kitaru insight list --agent AGENT`; `kitaru insight get ID` | `kitaru_review_read`, `list` or `get`, kind `insight` |
| Inspect import outcome | `kitaru import get ID`; `kitaru job get JOB_ID` or `watch JOB_ID` | `kitaru_activity_read`, kind `import` or `job` |
| Record a new agent run | Use the repository's verified Kitaru-integrated agent entrypoint | No generic MCP operation; running the agent may execute tools or mutate external state |
| List eligible sessions | `kitaru session list --agent AGENT` with bounded filters and pagination; use `--tag TAG` to find a marked smoke population, then subtract its exact IDs | `kitaru_activity_read`, `list`, kind `session` |
| Scan whole sessions as compact transcripts | `kitaru session read SESSION...` or `--sessions-file PATH`; `--max-chars N`, `--full`, `--reasoning`, `--node N` | `kitaru_session_read` with up to 10 `session_ids`, `max_chars`, `full`, `reasoning`, and `node` |
| Read a complete session | `kitaru session get SESSION`; `kitaru session nodes SESSION --include-payloads` with pagination | `kitaru_activity_read`, `get` session then `list_children` session nodes with payloads |
| Locate where failed sessions first go wrong | No CLI equivalent | `kitaru_failure_matrix` with a session `filter` and optional `compare_filter`; `kitaru_failure_matrix_cell` lists one cell's sessions |
| Create investigation and fixed worklist | `kitaru investigation create NAME --agent AGENT --session UUID --session-question 'UUID:KEY=QUESTION'`, repeating session and question options; optionally add `--session-highlights 'UUID:KEY=JSON_ARRAY'` | `kitaru_review_manage`, `create_investigation` with ordered session inputs, each carrying its questions and optional highlights; both return `links.review` when the server reports a dashboard |
| Read or resume investigation | `kitaru investigation get ID`; `kitaru investigation session list ID` | `kitaru_review_read`, `get` investigation, which also returns `links.review` when available (CLI `get` does not), then `list_sessions` |
| Set linked-session verdict | `kitaru investigation session verdict INVESTIGATION SESSION acceptable|problematic|uncertain`; the CLI cannot clear a verdict | `kitaru_review_manage`, `set_session_verdict`; use null only to clear an existing verdict deliberately |
| Complete investigation | `kitaru investigation update INVESTIGATION --status completed` | `kitaru_review_manage`, `update_investigation` with `status=completed` |
| Write whole-session or node annotation | `kitaru annotation create --session SESSION --value JSON [--selector JSON]` | `kitaru_review_manage`, `create_annotation` |
| Answer investigation question | `kitaru annotation create --investigation-session ID --question-key KEY --value JSON [--selector JSON]` | `kitaru_review_manage`, `answer_question` |
| Read or revise annotation | `kitaru annotation list|get|update` | `kitaru_review_read`, `list` or `get`; `kitaru_review_manage`, `update_annotation` |
| Create cohort snapshot | `kitaru cohort create NAME --agent AGENT --session SESSION...`; later `kitaru cohort version create` | `kitaru_cohorts_manage`, `create` or `create_version` |
| Scaffold and load-check evaluator file | `kitaru evaluator scaffold NAME`; `kitaru evaluator test PATH --entrypoint NAME` | Local coding-agent work, no MCP equivalent; the CLI test does not invoke the evaluator against sessions |
| Register immutable evaluator version | `kitaru evaluator register NAME --agent-id AGENT --script PATH --entrypoint NAME` for an agent-scoped parent; omit `--agent-id` only for an intentionally global parent; later `kitaru evaluator version register EVALUATOR` | `kitaru_evaluators_manage`; MCP requires an existing script blob or exact package pin, and scoped parent creation requires its installed create schema to expose `agent_id` |
| Start evaluation batch | `kitaru session evaluate ... --evaluator EVALUATOR@VERSION`, optionally `--wait` | `kitaru_workflow_start`, `evaluation` |
| Inspect evaluation work | `kitaru job get|watch`; `kitaru evaluation list|get` | `kitaru_activity_read`, job or evaluation and bounded children |

## Resource contracts

### MCP bounds

- MCP list operations return one page of at most 100 items. Continue through opaque cursors rather than requesting an unbounded population.
- MCP investigation creation accepts at most 100 sessions. Every session input needs a non-empty list of uniquely keyed questions. Split larger review rounds into explicit follow-up investigations.
- MCP evaluation starts accept at most 100 session IDs, 100 evaluator selections, and 100 total session/evaluator pairs. Split a larger matrix into separately identified batches.
- Every evaluation batch must contain sessions from exactly one agent. A scoped evaluator is eligible only when its `agent_id` matches that agent. A null `agent_id` is only a candidate global scope because deleting a scoped evaluator's agent also clears the field. Use a null-scoped parent only when a trusted creation record or known default-catalog identity establishes deliberate global scope, or after revalidating its criterion, implementation, and intended reuse for the batch's agent. Otherwise exclude it.
- Evaluator scope cannot be edited through evaluator update or version registration. Re-read the parent before creating a version or starting work, but do not treat a newly null scope as proof of global portability. When the MCP evaluator-create schema lacks `agent_id`, use CLI registration for a scoped parent instead of silently creating a global evaluator.

### Pre-investigation setup

- Use `kitaru status` first when server selection, credentials, compatibility, or live-worker readiness is uncertain. Use `kitaru doctor` when one of those checks fails or the cause is unclear.
- Prefer an exact agent version when recording or importing a session. If a session has no `agent_version_id`, report that provenance gap and reconcile it from other evidence only when the program revision is still unambiguous.
- Inspect the repository before running an agent to record a session. Explain the inputs, credentials, tool effects, and external mutations that may occur, and obtain any approval required by those effects.
- Use the CLI for a local import payload because MCP never reads local files. Use MCP for an existing Kitaru blob or a bounded provider API selection.
- Import creates a job and does not make sessions available synchronously unless the CLI waits successfully. Inspect the job and resulting sessions before starting an investigation.
- In a Python SDK context, `client.sessions.get_with_nodes(...)` returns one session with every node in one unpaginated response. This does not replace the bounded CLI or MCP paths for an agent host.
- Session filters can select sessions produced by one exact experiment run. They do not by themselves express every non-experiment session, so define broader replay exclusions explicitly instead of assuming an inverse filter exists.
- After setup, resolve the exact agent version and session population again. Do not rely on an earlier name-only lookup.

### Session reading and failure location

- `kitaru session read` and the read-only `kitaru_session_read` tool (Kitaru 0.27.7 or later) render whole sessions as compact transcripts, one line per node: each model call's new text only, short tool arguments and results, and errors never cut. Prefer them to paging node JSON when scanning or selecting sessions.
- Every field longer than `max_chars` (default 300) is cut and ends in `[+N chars]`. Before quoting a field, summarizing it as complete, or writing a highlight, read it uncut: pass `--full`, or `--node N --full` for one node (MCP `node` with `full`, one session only), or read the node payloads. Never summarize a cut field as the whole record.
- Transcript step numbers are zero-based node positions, not node IDs. Take the exact node ID and RFC 6901 JSON Pointer for a selector or highlight from the session node read.
- The read-only `kitaru_failure_matrix` MCP tool (Kitaru 0.27.2 or later) counts failed sessions by the last step that went right and the first step that went wrong, over the sessions a `filter` selects (for example `agent_id` or `cohort_version_id`). It reads at most `max_sessions` most recent sessions per group (default 200), so state that bound. `compare_filter` contrasts a second group, such as a replay's `experiment_run_id`. `kitaru_failure_matrix_cell` lists the sessions and repeated notes behind one cell. Failed sessions without a located step are counted separately.
- Use matrix cells to choose sessions for review, not as verdicts. A failure that raised no error is placed only by a human annotation on the failing node with the value `{"first_failure": true, "note": "..."}`. Never write that annotation from an agent suggestion.

### Provider imports and connections

These operations require Kitaru 0.26.0 or later; check installed schemas before use. Built-in API importers include Langfuse, LangSmith, Braintrust, Phoenix, Logfire, and MLflow (Kitaru 0.27.2 or later). The separately packaged ElevenLabs and Mastra importers are development packages, not published or in the default catalog; treat them as available only when the installed importer catalog lists them. Inspect the selected importer's schema for provider-specific fields; the Kitaru JSONL importer accepts files only.

- For an API import, omit FILE and supply `--since` or repeat `--trace-id` for exact source traces. CLI `--since` and `--until` accept timestamps or durations such as `7d`. Use `--query` for provider selection fields and `--params` for parser settings; do not repeat a dedicated selection flag's key inside `--query`. FILE cannot combine with `--since`, `--until`, `--trace-id`, `--query`, or `--connection`.
- MCP `kitaru_session_import` requires `importer_id`, integer `importer_version`, and `agent_version_id`. Set `source` to `{"type":"api","query":{"since":"2026-09-01T00:00:00Z"},"connection_id":"UUID"}` or `{"type":"blob","blob_id":"UUID"}`. API query timestamps must be timezone-aware absolute timestamps, not CLI durations; without `trace_ids`, `since` is required. Choose an actual bounded population rather than copying the example date.
- Inspect existing connections and reuse one matching the intended provider account and project before creating another. Do not change a provider default unless that broader change is requested. Create a connection from a bare importer or analyzer parent name: `kitaru connection create NAME --importer kitaru/langfuse`, or `--analyzer kitaru/openai-post-import-insights`. Do not append `@latest` here. Alternatively use `--provider PROVIDER`; choose exactly one source. MCP connection creation takes `name`, `provider`, `env`, and `secrets` directly.
- CLI creation accepts repeated `--set KEY=VALUE` and `--set-secret KEY=VALUE`; non-interactive creation must supply every required schema property. Keep credentials out of conversation and logs; use the user's secure credential-entry mechanism when values are unavailable. Reads return `secret_keys`, not secret values. Updating secrets replaces the whole secret map, so retain every required key. CLI `--set` merges existing environment values; MCP `env` updates replace the environment map.
- An explicit connection wins over the provider default; otherwise credentials come from the worker environment. From Kitaru 0.27.6, a connection must hold every required key: a task that uses a connection takes none of that plugin's connection keys from the worker environment, so a partial connection fails instead of borrowing worker credentials. Self-hosted servers and workers must both run 0.27.6 or later for this behavior. Resolution happens when the import is created, so a new default does not repair an already queued import. Without a connection, a credential-equipped worker must also declare eligibility, for example `--selector kitaru/requires-credentials=langfuse,openai`. Credentials in the importing terminal alone do not equip a separate worker.

### Import analysis and insight provenance

Select analyzers when creating the import. `--analyzer kitaru/post-import-insights@latest` selects deterministic checks without model credentials. `--analyzer kitaru/openai-post-import-insights@latest` selects OpenAI-assisted findings and requires OpenAI credentials. It defaults to `gpt-5.6-luna` with low reasoning effort; override the model only when the user asks, with `--analyzer-params 'kitaru/openai-post-import-insights@latest={"model":"MODEL"}'`; an override also drops the low reasoning-effort setting. `--analyzer kitaru/openai-session-findings@latest` (Kitaru 0.27.5 or later) has a reader model write yes/no checks from the sessions, verifies each check on every session with the OpenAI Decisions API, and stores one insight per verified finding, at most ten per run. It needs an OpenAI connection with Decisions API access and accepts optional `context`, `model`, and `decisions_model` params. Unlike the other two, it sends session content to OpenAI: the system prompt, user messages, tool inputs and outputs, and the final reply, each cut to 2,000 characters. Confirm that this data exposure is acceptable before selecting it, and treat its findings as model judgments to verify in the listed sessions. None of these analyzers runs automatically, and the OpenAI analyzers do not fall back to deterministic analysis on missing credentials or request failure.

- `kitaru/post-import-insights` and `kitaru/openai-post-import-insights` skip, with a `skipped` analysis task, when the import has fewer than 5 eligible (completed or failed) sessions; other analyzers need 1. This applies at import time and to `kitaru import analyze`. MCP `analyzers` entries accept `min_sessions` to change that minimum; the CLI has no such option. Report a skip as no analysis, not as no findings.

- Use a worker that claims both importer and analyzer tasks, for example `kitaru worker start --concurrency 10 --claim importer --claim analyzer`. A connection supplies model credentials, or the worker needs both those credentials and the matching eligibility selector. An importer-only worker can finish parsing while analysis remains queued.
- Repeat `--analyzer` to run both independently. Select credentials with `--analyzer-connection ANALYZER@VERSION=CONNECTION`; its analyzer token must exactly match a selected `--analyzer`. MCP supplies `analyzers` entries with `analyzer`, optional integer `version`, `params`, and optional `connection_id`.
- Read the import's parsing counts separately from job completion. A failed analyzer or evaluator fails the job without rolling back imported sessions or other analyzers' insights. Imports with no completed or failed sessions do not launch analysis. Preserve the import/job IDs and inspect failures before retrying.
- Read stored insights with the operations above, then inspect their exact agent, `import_id`, analyzer-version reference, supporting session/node references, coverage, caveats, and investigation prompt. A copied prompt is a briefing to verify against those records, not authorization, a human verdict, or proof of cause. Distinguish the full affected population from a retained evidence subset before choosing cohort membership.
- To rerun analysis over an existing import, for example after fixing params or credentials, use `kitaru import analyze IMPORT_ID --analyzer ANALYZER@VERSION --wait` with the same `--analyzer-params` and `--analyzer-connection` options. Each call creates a new analysis job and adds a new set of cards beside the earlier ones; nothing replaces or deletes the earlier cards, and a rerun can reuse their names. Confirm before rerunning, because the OpenAI analyzer bills the model again. There is no MCP operation for this rerun.
- Server analyzers run only over one import: at import time, or later with `kitaru import analyze`. There is no shipped operation to run them over another session set (IDs, a tag, a cohort version, a time window, or live recordings); a planned `kitaru session analyze` command is not in any release yet. For those scopes, use the `kitaru-insights` skill's model-read levels. `kitaru insight create` stores supplied content; it does not execute an analyzer. Reimport skips occupied identities in the server-version-dependent scope: `(imported_from, external_id, agent_id)` on servers 0.24.0 and newer, globally `(imported_from, external_id)` on 0.23.0. Determine the selected server version, not just the local SDK version; verify the runtime contract for unknown or other legacy versions before relying on skips. A new agent version does not avoid a skip, so reimport is not a reliable regeneration strategy. Resume existing sessions and insights instead of deleting or changing source identities to force analysis.

### Investigation

- Create with one agent ID, name, optional description, and fixed ordered unique sessions. The name has 1-255 ASCII letters or digits with only internal hyphens or underscores, for example `refund-review`; it starts and ends with a letter or digit. Every linked session carries its own non-empty fixed question list and optional per-question highlights.
- Treat the investigation ID as durable identity. Do not assume names are unique.
- Status moves forward through `pending`, `in_progress`, and `completed`.
- The first investigation answer starts the investigation. Session verdicts do not start or complete it.
- Completion is an explicit investigation update. The server does not require every question to have an answer or every session to have a verdict, so inspect both coverage dimensions before completing it.
- Update can change name, description, or status.
- The response exposes metadata, but public create and update do not write that metadata.
- There is no cancel transition.
- Deletion is destructive and removes linked investigation sessions and investigation answers.

### Investigation session

- Verdict is null, `acceptable`, `problematic`, or `uncertain`. A null verdict means only that no verdict is recorded; question-answer annotations determine review coverage separately.
- Sessions, order, per-session questions, and per-question highlights are fixed at investigation creation.
- A highlight contains a prose description and selector into canonical session or node evidence. Conversational summaries are not a separately persisted investigation-view object.
- Current operations cannot append, reorder, or replace the fixed worklist. Create a follow-up investigation for another round.

### Annotation

- A manual annotation uses `session_id`, optional selector, and JSON value.
- An investigation answer uses `investigation_session_id`, stable `question_key`, optional selector, and JSON value. The session ID is derived from the linked session.
- The CLI parses `--value` as JSON. For a string annotation, preserve the JSON double quotes inside the shell argument: `--value '"Agent observation: The refund exceeded the approval limit."'`. Do not pass `--value 'Agent observation: ...'`; shell quotes group that text but do not make it a JSON string. Use a JSON encoder rather than hand-escaping text that contains quotes, backslashes, or line breaks.
- Repeating an investigation answer for the same investigation-session and question key creates another annotation row. It does not replace or upsert the earlier answer.
- A selector contains an optional node ID, an optional RFC 6901 JSON Pointer into that node or the session response, and an optional character span. A span requires a path, and a supplied node must belong to the session.
- A null selector targets the whole session.
- Annotation update replaces only the value of one exact annotation ID. It cannot change the selector, question key, or investigation link. Deletion is a separate exact-ID destructive operation.
- Manual annotations are independent of an investigation. Investigation answers are deleted with their investigation.

## Frontend bridge and failure

Resolve the frontend URL in this order:

1. Read `links.review` from the structured result of `kitaru investigation create` or MCP `create_investigation` (Kitaru 0.27.2 or later for MCP). Use it unchanged when it exists. If the creation response is gone, re-read the exact investigation with `kitaru_review_read` `get`, which returns the same link when the server reports a dashboard.
2. If no link was returned, for example by an older server, CLI, or another client, reuse the dashboard base URL already verified during readiness. If it is not available, read the top-level `dashboard_url` once from `kitaru status`. Then append the compatibility route below using the exact agent and investigation IDs.

```text
DASHBOARD_URL/agents/AGENT_ID/investigations/INVESTIGATION_ID/review
```

Current managed and self-hosted servers report the Kitaru UI base directly as `dashboard_url`, and `kitaru status` resolves a server that serves the bundled UI to its own URL; do not translate `/workspaces/` into `/kitaru-workspaces/` or otherwise rewrite its path. Strip one trailing slash before appending the route. The route carries agent and investigation identifiers only. Do not add sessions, questions, annotations, judgments, or trace contents as path or query data. Treat this construction as a compatibility path, not a substitute for a returned `links.review` contract.

Present the resolved URL as the first-line clickable action, say whether it opened automatically, explain investigation answer versus whole-session verdict versus independent manual annotation in one sentence, and pause. If the environment provides an ordinary open-URL action and the user asks to open the page, use it. Do not use Computer Use, browser automation, tab control, or a browser-specific integration to navigate or annotate on the user's behalf.

When no returned or documented URL reaches the investigation, preserve the investigation and stop. Report:

- the exact investigation and agent IDs;
- the attempted URL, unrecognized dashboard shape, or a null top-level `dashboard_url` from `kitaru status`;
- that frontend review is the intended interaction and the skill will not recreate it in chat;
- one concise retry or product-bug action.

Low-level CLI and MCP annotation operations remain available when a user explicitly requests agent-facing annotation work. They are not an automatic fallback for a broken frontend handoff.

## Known product boundaries

- Current structured CLI and MCP investigation creation return a direct review URL in `links.review` when the server reports a dashboard URL or serves the bundled UI. MCP investigation `get` returns it too; CLI `get` does not. Investigation creation succeeds even if the server-information request fails; in that case the result has the investigation, no review link, and a warning.
- On an older server or client that returns no link, use the documented compatibility route from the resolved dashboard base URL, agent ID, and investigation ID.
- A missing or invalid documented frontend route blocks the intended human review experience. There is no supported automatic in-chat substitute in this skill.
- No public write path exists for the structured agent-context brief or accepted-behavior record.
- No operation appends sessions to an active investigation.
- No persisted skipped-session state exists.
- No first-class suggestion, suggestion disposition, or accepted-behavior resource exists.
- No conditional-write revision, edit history, or undo contract exists for review writes.
- Evaluator versions do not carry a typed link to the accepted behavior and annotations that produced them.
- Server-enforced discovery, development, and test label isolation is unresolved.

Do not improvise around these boundaries. Preserve what can be preserved in Kitaru, keep provisional context visible in chat, and stop honestly when the missing contract matters to the user's next step.

## Mutation and retry rules

- Explain the exact remote object or compute job before creating it.
- Show and confirm exact cohort membership once, inline, before creation. Treat an evaluator card that preserves an already accepted behavior as a checksum; require a new decision only when it changes a boundary, permitted equivalence, or missing-evidence rule.
- Pass a fresh idempotency key with each logical create: CLI `--idempotency-key KEY` or MCP `idempotency_key` (Kitaru 0.23.0 or later). Check the installed schema per command; for example, `kitaru evaluator register` and `kitaru agent register` take none. Reuse a key only to retry the same create after a lost response; the server then replays the original result. The server keeps keys for a limited window (900 seconds by default).
- After a dropped response, read current state before retrying. Writes without a key, including verdicts, investigation and annotation updates, and CLI evaluator registration, have no replay protection: retry one only when the re-read shows it is missing. Retrying answer creation without the original key can append a duplicate annotation.
- Create a second answer for the same investigation-session and question key only when another annotation is intentional. Correct a known answer through exact-ID update.
- Never use destructive deletion as investigation cancellation.
- Never expose secret values, prompts, trace contents, local paths, or session identifiers through analytics.
