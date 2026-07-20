# Project adaptation

Read this file during preflight and boundary selection. The checked-in Kitaru
support demo is a conformance example, not a template whose identifiers should
be copied.

## Inspect before proposing code

Search the user's repository for:

- `KitaruAgent(...)` construction;
- `.register(...)` calls and stable module entrypoints;
- source and candidate variants;
- `@scorer` declarations;
- `@agent.protection(...)` declarations;
- tool names, schemas, and implementations;
- existing live-provider test markers and spend guards;
- repository instructions governing tests and CI.

Do not import application modules merely to inspect them if import-time code can
make provider calls or mutate external state. Prefer source inspection first.

Summarize the result:

| Requirement | Selected value | Evidence | State |
|---|---|---|---|
| Source agent | name and entrypoint | file and symbol | READY or HOLD |
| Source version | exact ID or label | registration or trace | READY or HOLD |
| Candidate agent | entrypoint | file and symbol | READY or HOLD |
| Objective | scorer name and threshold | declaration | READY or HOLD |
| Protections | expected IDs | declarations | READY or HOLD |
| Tool policy | read, write, unknown | definitions | READY or HOLD |

A completion-only protection does not establish domain safety. Require at least
one protection for the behavior that must not occur. If the relevant business
rule is unknown, ask the user rather than inventing it.

## Classify tools

| Classification | Meaning during imported replay |
|---|---|
| Read | A recorded exact match may be served. A miss is still blocked under the safe fallback policy. |
| Write | Never permit a miss to reach the live callable. A candidate attempt can still be recorded as evidence for a protection. |
| Unknown | Treat as write-capable until the user or code establishes otherwise. |

Explain the consequence in the user's terms. For example:

> `issue_refund` can move money. During this replay, an exact recorded
> response can be returned to the agent, but a changed call is blocked before
> the real refund function runs. The blocked attempt still tells us whether the
> candidate tried the forbidden action.

Permit approved project-relative source and test paths when they identify the
code under review. Keep absolute user paths, trace-derived paths, secrets,
prompts, customer data, and raw tool values out of reports.

## Trace selection

Use this order:

1. Use an exact trace ID or trace URL supplied by the user.
2. For JSONL, preview or parse identities without writing and summarize the
   available traces.
3. If the host has an explicit Langfuse integration or browser automation,
   offer to use it for read-only discovery.
4. Otherwise direct the user to the Langfuse trace view and ask for the exact
   trace ID.

Do not guess IDs. Do not claim that Kitaru discovered remote candidates.

Rank candidates using:

| Signal | Prefer | Avoid |
|---|---|---|
| State | terminal completed or failed trace | active or partially ingested trace |
| Failure | clear user-visible problem | vague dissatisfaction with no evidence |
| Tools | complete results and stable schemas | missing results or opaque side effects |
| Version | verified source version | conflicting source fields |
| Decision room | meaningful choice remains after a boundary | trace already effectively finished |
| Representativeness | recurring production path | one-off anomaly unless incident-specific |

A root-input-only trace can support a diagnostic counterfactual. It cannot by
itself support a comparable CI gate.

## Enumerate and validate boundaries

Load the immutable bundle with
`load_imported_replay_evidence(execution_id)`.

For each observation, group replay parts by `message_index`:

- a group containing only model text and tool calls is a model-message
  candidate;
- a group containing only tool results is a tool-result candidate;
- mixed or incomplete groups are not candidates.

For every candidate, construct an `ImportedReplayBoundary` from its
observation ID, sequence, occurrence, and tool call ID when required. Validate
it with:

```python
prepare_imported_replay_history(
    evidence,
    boundary=boundary,
    fallback_policy=ImportedReplayFallbackPolicy.BLOCK,
)
```

Catch `ImportedReplayPreparationError` and show the rejection reason. Never
silently downgrade a rejected boundary to root input.

Prefer the latest valid tool-result boundary that:

- preserves a meaningful decision for the candidate;
- keeps the relevant recorded responses available;
- uses tool names and schemas compatible with the candidate;
- does not start after the behavior being tested.

If a model-message boundary is stronger for the actual question, explain why
before selecting it.

## Adaptation changes

If required code is missing, propose the smallest coherent change:

- a stable registered candidate entrypoint;
- one objective tied to the intended outcome;
- one or more domain protections tied to forbidden behavior;
- a narrow replay helper or test.

Show the exact files and intended behavior before editing. Keep application
logic out of the skill repository. Do not copy the support demo's agent names,
versions, tool names, prompts, scorer, or protection IDs.

## Preflight completion

Preflight completes only when every required item is either READY or explicitly
accepted as a diagnostic-only HOLD. Paid replay cannot start while a relevant
tool remains unknown or while no domain protection exists.
