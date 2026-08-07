# Kitaru operations

Use this reference before reading or mutating Kitaru investigation state. Treat the installed Kitaru schema and discovered MCP tools as authoritative when they differ from this reference.

## Contents

- [Transport policy](#transport-policy)
- [Operation map](#operation-map)
- [Resource contracts](#resource-contracts)
- [Frontend bridge and fallback](#frontend-bridge-and-fallback)
- [Known product boundaries](#known-product-boundaries)
- [Mutation and retry rules](#mutation-and-retry-rules)

## Transport policy

Prefer native MCP when an exact bounded operation exists. Use the CLI when the operation requires a local evaluator script, benefits from built-in wait or watch behavior, or the relevant MCP tool is unavailable.

For agent-facing CLI calls, request structured output and disable incidental interaction with the installed equivalents of:

```text
--output json --machine --non-interactive --no-browser
```

The deliberate frontend handoff is the one browser exception. Do not open a browser for ordinary CLI calls.

Before relying on exact syntax:

1. inspect the installed `kitaru schema` output or command help;
2. inspect the discovered MCP input schema;
3. prefer exact IDs and versions over names;
4. preserve JSON results and carry returned IDs into the next call.

Do not use direct REST calls to fill a missing CLI or MCP contract.

## Operation map

| Need | Structured CLI | Native MCP |
|---|---|---|
| Check connection and worker readiness | `kitaru status`; use `kitaru doctor` for independent diagnostics | No single equivalent; use bounded reads only after the server is configured |
| Resolve agent or version | `kitaru agent get AGENT`; `kitaru agent version get AGENT@VERSION` | `kitaru_registry_read`, `get` or `get_version`, kind `agent` |
| Import a local trace payload | `kitaru session import FILE --importer IMPORTER@VERSION --agent AGENT@VERSION`, optionally `--wait` | `kitaru_session_import` uses an existing payload blob and exact importer and agent versions; it cannot read a local file |
| Record a new agent run | Use the repository's verified Kitaru-integrated agent entrypoint | No generic MCP operation; running the agent may execute tools or mutate external state |
| List eligible sessions | `kitaru session list --agent AGENT` with bounded filters and pagination | `kitaru_activity_read`, `list`, kind `session` |
| Read a complete session | `kitaru session get SESSION`; `kitaru session nodes SESSION --include-payloads` with pagination | `kitaru_activity_read`, `get` session then `list_children` session nodes with payloads |
| Create investigation and fixed worklist | `kitaru investigation create NAME --agent AGENT --question KEY=QUESTION --session UUID [--session-view 'UUID=JSON']` | `kitaru_review_manage`, `create_investigation` |
| Read or resume investigation | `kitaru investigation get ID`; `kitaru investigation session list ID` | `kitaru_review_read`, `get` investigation then `list_sessions` |
| Complete or skip linked session | `kitaru investigation session complete INVESTIGATION SESSION`; corresponding `skip` command | `kitaru_review_manage`, `set_session_status` |
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
- MCP investigation creation accepts at most 100 questions and 100 sessions. Split larger review rounds into explicit follow-up investigations.
- MCP evaluation starts accept at most 100 session IDs, 100 evaluator selections, and 100 total session/evaluator pairs. Split a larger matrix into separately identified batches.

### Pre-investigation setup

- Use `kitaru status` first when server selection, credentials, compatibility, or live-worker readiness is uncertain. Use `kitaru doctor` when one of those checks fails or the cause is unclear.
- Inspect the repository before running an agent to record a session. Explain the inputs, credentials, tool effects, and external mutations that may occur, and obtain any approval required by those effects.
- Use the CLI for a local import payload because MCP never reads local files. Use MCP import only when the payload already exists as a Kitaru blob.
- Import creates a job and does not make sessions available synchronously unless the CLI waits successfully. Inspect the job and resulting sessions before starting an investigation.
- After setup, resolve the exact agent version and session population again. Do not rely on an earlier name-only lookup.

### Investigation

- Create with one agent ID, name, optional description, fixed ordered questions, and fixed ordered unique sessions.
- Treat the investigation ID as durable identity. Do not assume names are unique.
- Status moves through `pending`, `in_progress`, and `completed` as answers and linked-session settlement occur.
- The first answer starts the investigation. Completing or skipping every linked session completes it.
- Update changes only name or description.
- The response exposes metadata, but public create and update do not write that metadata.
- There is no cancel transition.
- Deletion is destructive and removes linked investigation sessions and investigation answers.

### Investigation session

- Status is `pending`, `completed`, or `skipped`.
- Sessions, order, questions, and views are fixed at investigation creation.
- A view contains a version, summary, and curated items. Each item contains a label, description, and selectors into canonical evidence.
- Current operations cannot append, reorder, or replace the fixed worklist. Create a follow-up investigation for another round.

### Annotation

- A manual annotation uses `session_id`, optional selector, and JSON value.
- An investigation answer uses `investigation_session_id`, stable `question_key`, optional selector, and JSON value. The session ID is derived from the linked session.
- Repeating an investigation answer for the same investigation-session and question key upserts that answer.
- A selector may target a node's input, output, error, metadata, attributes, or model parameters, a JSON Pointer within that payload, and an optional character span.
- A null selector targets the whole session.
- Annotation update replaces only the value. Deletion is a separate exact-ID destructive operation.
- Manual annotations are independent of an investigation. Investigation answers are deleted with their investigation.

## Frontend bridge and fallback

When creation or product configuration exposes an investigation review link, open that link once and pause for the user. The URL must contain only an opaque investigation ID.

When no link or agreed URL constructor exists:

1. retain the same investigation and question keys;
2. read each session through activity operations;
3. collect the human answer in chat;
4. persist it through `answer_question` or `annotation create`;
5. settle the linked session;
6. re-read progress after every dropped or ambiguous response.

This is an interaction fallback, not a different persistence model.

## Known product boundaries

- No public write path exists for the structured agent-context brief or accepted-behavior record.
- No operation appends sessions to an active investigation.
- No first-class suggestion, suggestion disposition, or accepted-behavior resource exists.
- No conditional-write revision, edit history, or undo contract exists for review writes.
- Evaluator versions do not carry a typed link to the accepted behavior and annotations that produced them.
- Server-enforced discovery, development, and test label isolation is unresolved.

Do not improvise around these boundaries. Preserve what can be preserved in Kitaru, keep provisional context visible in chat, and stop honestly when the missing contract matters to the user's next step.

## Mutation and retry rules

- Explain the exact remote object or compute job before creating it.
- Require exact confirmation for cohort membership and evaluator rubrics.
- After a dropped response, read current state before retrying. General request idempotency is not guaranteed.
- Treat annotation question upsert as scoped only to the same investigation-session and question key.
- Never use destructive deletion as investigation cancellation.
- Never expose secret values, prompts, trace contents, local paths, or session identifiers through analytics.
