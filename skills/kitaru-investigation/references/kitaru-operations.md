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

1. Check whether `kitaru` is available in the active project environment. If it is missing, inspect the project's current setup instructions and the official Kitaru installation guide. Do not infer a package manager, virtual environment, or install command from repository layout alone. Explain and obtain approval before changing the project environment.
2. Run `kitaru status` to resolve the selected server, credentials, compatibility, dashboard URL, and worker readiness. Use `kitaru doctor` when a check fails or its cause is unclear.
3. Treat MCP as preferred, not required. If no native tools are discovered, distinguish among a missing `kitaru[mcp]` installation, absent host configuration, a server left in read-only mode, and host configuration added after the coding-agent process started.
4. MCP write operations require `standard` or `destructive` mode. Prefer `standard` for investigation, cohort, evaluator, and workflow writes. Reserve `destructive` for explicitly requested deletes or cancellations.
5. A host normally discovers new MCP configuration only after restart. Before restart, preserve the current repository, agent/version, trace source, completed setup, and next action in a compact checkpoint. Tell the user how to resume with the host's documented mechanism rather than assuming one command works everywhere.
6. When CLI covers the next operation, state that fallback in one sentence and continue. Do not make transport selection another user decision unless the missing MCP capability changes the result or blocks the next operation.

## Operation map

| Need | Structured CLI | Native MCP |
|---|---|---|
| Check connection and worker readiness | `kitaru status`; use `kitaru doctor` for independent diagnostics | No single equivalent; use bounded reads only after the server is configured |
| Resolve agent or version | `kitaru agent get AGENT`; `kitaru agent version get AGENT@VERSION` | `kitaru_registry_read`, `get` or `get_version`, kind `agent` |
| Import a local trace payload | `kitaru session import FILE --importer IMPORTER@VERSION --agent AGENT@VERSION`, optionally `--join-on JSON_POINTER`, `--tag TAG`, and `--wait`; current tag application requires waiting | `kitaru_session_import` uses an existing payload blob and exact importer and agent versions; it cannot read a local file |
| Record a new agent run | Use the repository's verified Kitaru-integrated agent entrypoint | No generic MCP operation; running the agent may execute tools or mutate external state |
| List eligible sessions | `kitaru session list --agent AGENT` with bounded filters and pagination; use `--tag TAG` to find a marked smoke population, then subtract its exact IDs | `kitaru_activity_read`, `list`, kind `session` |
| Read a complete session | `kitaru session get SESSION`; `kitaru session nodes SESSION --include-payloads` with pagination | `kitaru_activity_read`, `get` session then `list_children` session nodes with payloads |
| Create investigation and fixed worklist | `kitaru investigation create NAME --agent AGENT --session UUID --session-question 'UUID:KEY=QUESTION'`, repeating session and question options; optionally add `--session-highlights 'UUID:KEY=JSON_ARRAY'` | `kitaru_review_manage`, `create_investigation` with ordered session inputs, each carrying its questions and optional highlights |
| Read or resume investigation | `kitaru investigation get ID`; `kitaru investigation session list ID` | `kitaru_review_read`, `get` investigation then `list_sessions` |
| Set linked-session verdict | `kitaru investigation session verdict INVESTIGATION SESSION acceptable|problematic|uncertain`; the CLI cannot clear a verdict | `kitaru_review_manage`, `set_session_verdict`; use null only to clear an existing verdict deliberately |
| Complete investigation | `kitaru investigation update INVESTIGATION --status completed` | `kitaru_review_manage`, `update_investigation` with `status=completed` |
| Write whole-session or node annotation | `kitaru annotation create --session SESSION --value JSON [--selector JSON]` | `kitaru_review_manage`, `create_annotation` |
| Answer investigation question | `kitaru annotation create --investigation-session ID --question-key KEY --value JSON [--selector JSON]` | `kitaru_review_manage`, `answer_question` |
| Read or revise annotation | `kitaru annotation list|get|update` | `kitaru_review_read`, `list` or `get`; `kitaru_review_manage`, `update_annotation` |
| Create cohort snapshot | `kitaru cohort create NAME --agent AGENT --session SESSION...`; later `kitaru cohort version create` | `kitaru_cohorts_manage`, `create` or `create_version` |
| Scaffold and load-check evaluator file | `kitaru evaluator scaffold NAME`; `kitaru evaluator test PATH --entrypoint NAME` | Local coding-agent work, no MCP equivalent; the CLI test does not invoke the evaluator against sessions |
| Register immutable evaluator version | `kitaru evaluator register NAME --script PATH --entrypoint NAME`; later `kitaru evaluator version register EVALUATOR` | `kitaru_evaluators_manage`; MCP requires an existing script blob or exact package pin |
| Start evaluation batch | `kitaru session evaluate ... --evaluator EVALUATOR@VERSION`, optionally `--wait` | `kitaru_workflow_start`, `evaluation` |
| Inspect evaluation work | `kitaru job get|watch`; `kitaru evaluation list|get` | `kitaru_activity_read`, job or evaluation and bounded children |

## Resource contracts

### MCP bounds

- MCP list operations return one page of at most 100 items. Continue through opaque cursors rather than requesting an unbounded population.
- MCP investigation creation accepts at most 100 sessions. Every session input needs a non-empty list of uniquely keyed questions. Split larger review rounds into explicit follow-up investigations.
- MCP evaluation starts accept at most 100 session IDs, 100 evaluator selections, and 100 total session/evaluator pairs. Split a larger matrix into separately identified batches.

### Pre-investigation setup

- Use `kitaru status` first when server selection, credentials, compatibility, or live-worker readiness is uncertain. Use `kitaru doctor` when one of those checks fails or the cause is unclear.
- Prefer an exact agent version when recording or importing a session. If a session has no `agent_version_id`, report that provenance gap and reconcile it from other evidence only when the program revision is still unambiguous.
- Inspect the repository before running an agent to record a session. Explain the inputs, credentials, tool effects, and external mutations that may occur, and obtain any approval required by those effects.
- Use the CLI for a local import payload because MCP never reads local files. Use MCP import only when the payload already exists as a Kitaru blob.
- Import creates a job and does not make sessions available synchronously unless the CLI waits successfully. Inspect the job and resulting sessions before starting an investigation.
- In a Python SDK context, `client.sessions.get_with_nodes(...)` returns one session with every node in one unpaginated response. This does not replace the bounded CLI or MCP paths for an agent host.
- Session filters can select sessions produced by one exact experiment run. They do not by themselves express every non-experiment session, so define broader replay exclusions explicitly instead of assuming an inverse filter exists.
- After setup, resolve the exact agent version and session population again. Do not rely on an earlier name-only lookup.

### Investigation

- Create with one agent ID, name, optional description, and fixed ordered unique sessions. Every linked session carries its own non-empty fixed question list and optional per-question highlights.
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
- Repeating an investigation answer for the same investigation-session and question key creates another annotation row. It does not replace or upsert the earlier answer.
- A selector contains an optional node ID, an optional RFC 6901 JSON Pointer into that node or the session response, and an optional character span. A span requires a path, and a supplied node must belong to the session.
- A null selector targets the whole session.
- Annotation update replaces only the value of one exact annotation ID. It cannot change the selector, question key, or investigation link. Deletion is a separate exact-ID destructive operation.
- Manual annotations are independent of an investigation. Investigation answers are deleted with their investigation.

## Frontend bridge and failure

Resolve the frontend URL in this order:

1. Use an investigation review link returned by Kitaru when one exists.
2. Otherwise, read `dashboard_url` from `kitaru status` or equivalent product configuration and construct one of the documented routes below from the exact agent and investigation IDs.

| Dashboard kind | Recognized dashboard URL | Investigation review URL |
|---|---|---|
| Managed Cloud | `ORIGIN/workspaces/WORKSPACE_ID` | `ORIGIN/kitaru-workspaces/WORKSPACE_ID/agents/AGENT_ID/investigations/INVESTIGATION_ID/review` |
| Direct Kitaru UI | A product-configured base URL confirmed to serve the Kitaru UI directly | `DASHBOARD_URL/agents/AGENT_ID/investigations/INVESTIGATION_ID/review` |

Parse the URL and replace only the managed Cloud path shape; do not perform a global text replacement. Use the direct route only when product configuration or server information confirms that the dashboard URL serves Kitaru UI at its base, such as a self-hosted server reporting a non-null `ui_version`. Do not treat every dashboard URL that fails the managed Cloud match as a direct Kitaru UI. Strip a trailing slash before appending the direct route. The route carries agent and investigation identifiers only. Do not add sessions, questions, annotations, judgments, or trace contents as path or query data.

Present the resolved URL as the first-line clickable action, say whether it opened automatically, explain investigation answer versus whole-session verdict versus independent manual annotation in one sentence, and pause. If the environment provides an ordinary open-URL action and the user asks to open the page, use it. Do not use Computer Use, browser automation, tab control, or a browser-specific integration to navigate or annotate on the user's behalf.

When no returned or documented URL reaches the investigation, preserve the investigation and stop. Report:

- the exact investigation and agent IDs;
- the attempted URL, unrecognized dashboard shape, or missing `dashboard_url`;
- that frontend review is the intended interaction and the skill will not recreate it in chat;
- one concise retry or product-bug action.

Low-level CLI and MCP annotation operations remain available when a user explicitly requests agent-facing annotation work. They are not an automatic fallback for a broken frontend handoff.

## Known product boundaries

- Current CLI and native MCP investigation creation return the investigation resource without a direct review URL. They expose the agent and investigation IDs needed to construct the documented frontend route from the `dashboard_url` returned by `kitaru status`.
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
- After a dropped response, read current state before retrying. General request idempotency is not guaranteed, and retrying answer creation can append a duplicate annotation.
- Create a second answer for the same investigation-session and question key only when another annotation is intentional. Correct a known answer through exact-ID update.
- Never use destructive deletion as investigation cancellation.
- Never expose secret values, prompts, trace contents, local paths, or session identifiers through analytics.
